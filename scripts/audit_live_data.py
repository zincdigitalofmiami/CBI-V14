#!/usr/bin/env python3
"""
Comprehensive Live Data Audit for CBI-V14
==========================================

Audits BigQuery datasets and external drive exports for:
- Training table completeness and consistency
- Regime data coverage
- Raw intelligence naming and population
- Legacy dataset usage
- External export file synchronization

Excludes: Readiness scoring (focuses on data location, naming, and completeness)

Author: Kirk Musick
Date: November 14, 2025
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd
import pyarrow.parquet as pq

# Configuration
PROJECT_ID = "cbi-v14"
TRAINING_DATASET = "training"
RAW_INTELLIGENCE_DATASET = "raw_intelligence"
LEGACY_DATASETS = ["forecasting_data_warehouse", "models_v4"]

HORIZONS = ["1w", "1m", "3m", "6m", "12m"]
SURFACES = ["prod", "full"]

MANDATORY_COLUMNS = ["date", "regime", "training_weight"]
TARGET_COLUMNS = {
    "1w": "target_1w",
    "1m": "target_1m",
    "3m": "target_3m",
    "6m": "target_6m",
    "12m": "target_12m"
}

EXPECTED_START_DATE = "2000-01-01"
EXTERNAL_DRIVE_PATH = Path("/Users/kirkmusick/Documents/GitHub/CBI-V14/TrainingData/exports")

# Expected regime names (from regime_weights table)
EXPECTED_REGIMES = [
    "historical_pre2000",
    "early_2000s_2000_2007",
    "financial_crisis_2008",
    "recovery_2010_2016",
    "trade_war_2017_2019",
    "covid_2020",
    "inflation_2021_2022",
    "trump_2023_2025"
]

# Report storage
audit_results = {
    "timestamp": datetime.now().isoformat(),
    "training_tables": {},
    "regime_data": {},
    "raw_intelligence": {},
    "legacy_usage": {},
    "external_exports": {},
    "cross_checks": {},
    "summary": {}
}


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def audit_training_tables(client: bigquery.Client):
    """Audit all training tables in the training dataset"""
    print_section("TRAINING TABLES AUDIT")
    
    results = {}
    schema_baseline = None
    
    for surface in SURFACES:
        for horizon in HORIZONS:
            table_name = f"zl_training_{surface}_allhistory_{horizon}"
            table_id = f"{PROJECT_ID}.{TRAINING_DATASET}.{table_name}"
            
            print(f"Checking: {table_name}")
            
            table_result = {
                "exists": False,
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "mandatory_columns_present": {},
                "date_range": {},
                "issues": []
            }
            
            try:
                # Check if table exists
                table = client.get_table(table_id)
                table_result["exists"] = True
                
                # Get row count
                query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
                result = client.query(query).result()
                table_result["row_count"] = list(result)[0].cnt
                
                # Get column info
                table_result["column_count"] = len(table.schema)
                table_result["columns"] = [field.name for field in table.schema]
                
                # Check mandatory columns
                for col in MANDATORY_COLUMNS:
                    table_result["mandatory_columns_present"][col] = col in table_result["columns"]
                
                # Check target column for this horizon
                target_col = TARGET_COLUMNS[horizon]
                table_result["mandatory_columns_present"][target_col] = target_col in table_result["columns"]
                
                # Get date range
                date_query = f"""
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(DISTINCT date) as unique_dates
                FROM `{table_id}`
                """
                date_result = client.query(date_query).result()
                date_row = list(date_result)[0]
                table_result["date_range"] = {
                    "earliest": str(date_row.earliest_date) if date_row.earliest_date else None,
                    "latest": str(date_row.latest_date) if date_row.latest_date else None,
                    "unique_dates": date_row.unique_dates
                }
                
                # Check if backfilled to expected start
                if table_result["date_range"]["earliest"]:
                    if table_result["date_range"]["earliest"] > EXPECTED_START_DATE:
                        table_result["issues"].append(
                            f"Start date {table_result['date_range']['earliest']} later than expected {EXPECTED_START_DATE}"
                        )
                
                # Check for missing mandatory columns
                missing_cols = [col for col, present in table_result["mandatory_columns_present"].items() 
                               if not present]
                if missing_cols:
                    table_result["issues"].append(f"Missing mandatory columns: {', '.join(missing_cols)}")
                
                # Schema consistency check (compare to first prod table as baseline)
                if surface == "prod" and schema_baseline is None:
                    schema_baseline = sorted(table_result["columns"])
                elif surface == "prod":
                    current_schema = sorted(table_result["columns"])
                    if current_schema != schema_baseline:
                        # Find differences
                        missing = set(schema_baseline) - set(current_schema)
                        extra = set(current_schema) - set(schema_baseline)
                        if missing:
                            table_result["issues"].append(f"Missing columns vs baseline: {', '.join(missing)}")
                        if extra:
                            table_result["issues"].append(f"Extra columns vs baseline: {', '.join(extra)}")
                
                print(f"  ✓ Rows: {table_result['row_count']:,}, Cols: {table_result['column_count']}, "
                      f"Date range: {table_result['date_range']['earliest']} to {table_result['date_range']['latest']}")
                
                if table_result["issues"]:
                    print(f"  ⚠ Issues: {'; '.join(table_result['issues'])}")
                
            except NotFound:
                table_result["issues"].append("Table does not exist")
                print(f"  ✗ Table not found")
            except Exception as e:
                table_result["issues"].append(f"Error: {str(e)}")
                print(f"  ✗ Error: {str(e)}")
            
            results[table_name] = table_result
    
    audit_results["training_tables"] = results
    return results


def audit_regime_data(client: bigquery.Client):
    """Audit regime calendar and weights tables"""
    print_section("REGIME DATA AUDIT")
    
    results = {}
    
    # Check regime_calendar
    print("Checking: regime_calendar")
    calendar_result = {
        "exists": False,
        "row_count": 0,
        "date_range": {},
        "regime_coverage": {},
        "issues": []
    }
    
    try:
        table_id = f"{PROJECT_ID}.{TRAINING_DATASET}.regime_calendar"
        table = client.get_table(table_id)
        calendar_result["exists"] = True
        
        # Row count
        query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
        result = client.query(query).result()
        calendar_result["row_count"] = list(result)[0].cnt
        
        # Date range
        date_query = f"""
        SELECT 
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM `{table_id}`
        """
        date_result = client.query(date_query).result()
        date_row = list(date_result)[0]
        calendar_result["date_range"] = {
            "earliest": str(date_row.earliest_date),
            "latest": str(date_row.latest_date)
        }
        
        # Regime coverage
        regime_query = f"""
        SELECT 
            regime,
            COUNT(*) as days
        FROM `{table_id}`
        GROUP BY regime
        ORDER BY regime
        """
        regime_result = client.query(regime_query).result()
        calendar_result["regime_coverage"] = {
            row.regime: row.days for row in regime_result
        }
        
        print(f"  ✓ Rows: {calendar_result['row_count']:,}, "
              f"Date range: {calendar_result['date_range']['earliest']} to {calendar_result['date_range']['latest']}")
        print(f"  ✓ Regimes covered: {len(calendar_result['regime_coverage'])}")
        
    except NotFound:
        calendar_result["issues"].append("Table does not exist")
        print(f"  ✗ Table not found")
    except Exception as e:
        calendar_result["issues"].append(f"Error: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    results["regime_calendar"] = calendar_result
    
    # Check regime_weights
    print("\nChecking: regime_weights")
    weights_result = {
        "exists": False,
        "row_count": 0,
        "weights": {},
        "weight_range": {},
        "issues": []
    }
    
    try:
        table_id = f"{PROJECT_ID}.{TRAINING_DATASET}.regime_weights"
        table = client.get_table(table_id)
        weights_result["exists"] = True
        
        # Get weights
        query = f"""
        SELECT 
            regime,
            weight
        FROM `{table_id}`
        ORDER BY regime
        """
        result = client.query(query).result()
        weights = {row.regime: row.weight for row in result}
        weights_result["weights"] = weights
        weights_result["row_count"] = len(weights)
        
        # Weight range
        if weights:
            weights_result["weight_range"] = {
                "min": min(weights.values()),
                "max": max(weights.values())
            }
            
            # Check if weights are in expected 50-5000 scale
            if weights_result["weight_range"]["min"] < 50 or weights_result["weight_range"]["max"] > 5000:
                weights_result["issues"].append(
                    f"Weights outside expected 50-5000 range: {weights_result['weight_range']}"
                )
        
        # Check for expected regimes
        missing_regimes = set(EXPECTED_REGIMES) - set(weights.keys())
        if missing_regimes:
            weights_result["issues"].append(f"Missing regimes: {', '.join(missing_regimes)}")
        
        print(f"  ✓ Rows: {weights_result['row_count']}")
        print(f"  ✓ Weight range: {weights_result['weight_range']['min']} - {weights_result['weight_range']['max']}")
        
        if weights_result["issues"]:
            print(f"  ⚠ Issues: {'; '.join(weights_result['issues'])}")
        
    except NotFound:
        weights_result["issues"].append("Table does not exist")
        print(f"  ✗ Table not found")
    except Exception as e:
        weights_result["issues"].append(f"Error: {str(e)}")
        print(f"  ✗ Error: {str(e)}")
    
    results["regime_weights"] = weights_result
    
    audit_results["regime_data"] = results
    return results


def audit_raw_intelligence(client: bigquery.Client):
    """Audit raw_intelligence dataset tables"""
    print_section("RAW INTELLIGENCE DATASET AUDIT")
    
    results = {
        "table_count": 0,
        "tables": {},
        "naming_issues": [],
        "missing_tables": []
    }
    
    # List all tables
    dataset_id = f"{PROJECT_ID}.{RAW_INTELLIGENCE_DATASET}"
    tables = list(client.list_tables(dataset_id))
    results["table_count"] = len(tables)
    
    print(f"Found {len(tables)} tables in {RAW_INTELLIGENCE_DATASET}\n")
    
    # Expected naming pattern: {category}_{source_name}
    naming_pattern_violations = []
    
    for table in tables:
        table_name = table.table_id
        table_id = f"{dataset_id}.{table_name}"
        
        table_info = {
            "row_count": 0,
            "date_range": {},
            "columns": [],
            "naming_valid": True,
            "issues": []
        }
        
        # Check naming pattern
        if table_name.count("_") < 1:
            table_info["naming_valid"] = False
            table_info["issues"].append(f"Name doesn't follow {{category}}_{{source}} pattern")
            naming_pattern_violations.append(table_name)
        
        try:
            # Get row count
            query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
            result = client.query(query).result()
            table_info["row_count"] = list(result)[0].cnt
            
            # Get schema
            table_obj = client.get_table(table_id)
            table_info["columns"] = [field.name for field in table_obj.schema]
            
            # Try to get date range if 'date' column exists
            if 'date' in table_info["columns"]:
                date_query = f"""
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM `{table_id}`
                """
                date_result = client.query(date_query).result()
                date_row = list(date_result)[0]
                table_info["date_range"] = {
                    "earliest": str(date_row.earliest_date) if date_row.earliest_date else None,
                    "latest": str(date_row.latest_date) if date_row.latest_date else None
                }
            
            print(f"{table_name}: {table_info['row_count']:,} rows", end="")
            if table_info["date_range"]:
                print(f", {table_info['date_range']['earliest']} to {table_info['date_range']['latest']}", end="")
            if not table_info["naming_valid"]:
                print(f" ⚠ Naming issue", end="")
            print()
            
        except Exception as e:
            table_info["issues"].append(f"Error: {str(e)}")
            print(f"{table_name}: ✗ Error: {str(e)}")
        
        results["tables"][table_name] = table_info
    
    # Specifically check for commodity_soybean_oil_prices
    print("\nChecking for specific tables:")
    print(f"  commodity_soybean_oil_prices: ", end="")
    if "commodity_soybean_oil_prices" in results["tables"]:
        soy_info = results["tables"]["commodity_soybean_oil_prices"]
        print(f"✓ Found ({soy_info['row_count']:,} rows)")
    else:
        print("✗ Not found")
        results["missing_tables"].append("commodity_soybean_oil_prices")
    
    results["naming_issues"] = naming_pattern_violations
    
    audit_results["raw_intelligence"] = results
    return results


def audit_legacy_datasets(client: bigquery.Client):
    """Check for recently updated tables in legacy datasets"""
    print_section("LEGACY DATASET USAGE AUDIT")
    
    results = {
        "datasets_checked": LEGACY_DATASETS,
        "recent_updates": []
    }
    
    cutoff_date = datetime.now() - timedelta(days=30)
    
    for dataset_name in LEGACY_DATASETS:
        print(f"\nChecking dataset: {dataset_name}")
        dataset_id = f"{PROJECT_ID}.{dataset_name}"
        
        try:
            tables = list(client.list_tables(dataset_id))
            print(f"  Found {len(tables)} tables")
            
            for table in tables:
                table_id = f"{dataset_id}.{table.table_id}"
                
                try:
                    table_obj = client.get_table(table_id)
                    
                    # Check last modified time
                    if table_obj.modified and table_obj.modified > cutoff_date:
                        # Get row count
                        query = f"SELECT COUNT(*) as cnt FROM `{table_id}`"
                        result = client.query(query).result()
                        row_count = list(result)[0].cnt
                        
                        update_info = {
                            "dataset": dataset_name,
                            "table": table.table_id,
                            "last_modified": table_obj.modified.isoformat(),
                            "row_count": row_count
                        }
                        results["recent_updates"].append(update_info)
                        
                        print(f"    ⚠ {table.table_id}: Modified {table_obj.modified}, {row_count:,} rows")
                
                except Exception as e:
                    print(f"    Error checking {table.table_id}: {str(e)}")
        
        except NotFound:
            print(f"  Dataset not found (this is OK if intentionally removed)")
        except Exception as e:
            print(f"  Error accessing dataset: {str(e)}")
    
    if not results["recent_updates"]:
        print("\n✓ No legacy tables updated in the last 30 days")
    else:
        print(f"\n⚠ Found {len(results['recent_updates'])} recently updated legacy tables")
    
    audit_results["legacy_usage"] = results
    return results


def audit_external_exports():
    """Audit Parquet exports on external drive"""
    print_section("EXTERNAL DRIVE EXPORTS AUDIT")
    
    results = {
        "export_path": str(EXTERNAL_DRIVE_PATH),
        "path_exists": EXTERNAL_DRIVE_PATH.exists(),
        "files": {},
        "missing_files": []
    }
    
    if not EXTERNAL_DRIVE_PATH.exists():
        print(f"✗ Export path does not exist: {EXTERNAL_DRIVE_PATH}")
        audit_results["external_exports"] = results
        return results
    
    print(f"Checking exports in: {EXTERNAL_DRIVE_PATH}\n")
    
    for surface in SURFACES:
        for horizon in HORIZONS:
            expected_filename = f"zl_training_{surface}_allhistory_{horizon}.parquet"
            file_path = EXTERNAL_DRIVE_PATH / expected_filename
            
            file_info = {
                "exists": file_path.exists(),
                "size_bytes": 0,
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "issues": []
            }
            
            print(f"Checking: {expected_filename}")
            
            if file_path.exists():
                try:
                    # Get file size
                    file_info["size_bytes"] = file_path.stat().st_size
                    
                    # Read parquet metadata
                    parquet_file = pq.ParquetFile(file_path)
                    file_info["row_count"] = parquet_file.metadata.num_rows
                    
                    # Get schema
                    schema = parquet_file.schema_arrow
                    file_info["column_count"] = len(schema)
                    file_info["columns"] = schema.names
                    
                    print(f"  ✓ {file_info['size_bytes']/1024/1024:.2f} MB, "
                          f"{file_info['row_count']:,} rows, "
                          f"{file_info['column_count']} columns")
                
                except Exception as e:
                    file_info["issues"].append(f"Error reading file: {str(e)}")
                    print(f"  ✗ Error: {str(e)}")
            else:
                file_info["issues"].append("File does not exist")
                results["missing_files"].append(expected_filename)
                print(f"  ✗ File not found")
            
            results["files"][expected_filename] = file_info
    
    if results["missing_files"]:
        print(f"\n⚠ Missing {len(results['missing_files'])} export files")
    else:
        print(f"\n✓ All expected export files found")
    
    audit_results["external_exports"] = results
    return results


def cross_check_data():
    """Cross-check consistency between BigQuery and exports"""
    print_section("CROSS-CHECKS")
    
    results = {
        "row_count_matches": [],
        "row_count_mismatches": [],
        "schema_matches": [],
        "schema_mismatches": [],
        "deprecated_patterns": []
    }
    
    training_tables = audit_results.get("training_tables", {})
    export_files = audit_results.get("external_exports", {}).get("files", {})
    
    print("Comparing BigQuery tables to Parquet exports:\n")
    
    for surface in SURFACES:
        for horizon in HORIZONS:
            table_name = f"zl_training_{surface}_allhistory_{horizon}"
            file_name = f"{table_name}.parquet"
            
            if table_name in training_tables and file_name in export_files:
                table_info = training_tables[table_name]
                file_info = export_files[file_name]
                
                print(f"{table_name}:")
                
                # Compare row counts
                if table_info.get("row_count") == file_info.get("row_count"):
                    print(f"  ✓ Row counts match: {table_info['row_count']:,}")
                    results["row_count_matches"].append(table_name)
                else:
                    mismatch = {
                        "table": table_name,
                        "bigquery_rows": table_info.get("row_count"),
                        "parquet_rows": file_info.get("row_count")
                    }
                    results["row_count_mismatches"].append(mismatch)
                    print(f"  ✗ Row count mismatch: BQ={table_info.get('row_count'):,}, "
                          f"Parquet={file_info.get('row_count'):,}")
                
                # Compare schemas
                bq_cols = sorted(table_info.get("columns", []))
                parquet_cols = sorted(file_info.get("columns", []))
                
                if bq_cols == parquet_cols:
                    print(f"  ✓ Schemas match: {len(bq_cols)} columns")
                    results["schema_matches"].append(table_name)
                else:
                    missing_in_parquet = set(bq_cols) - set(parquet_cols)
                    missing_in_bq = set(parquet_cols) - set(bq_cols)
                    
                    mismatch = {
                        "table": table_name,
                        "missing_in_parquet": list(missing_in_parquet),
                        "missing_in_bq": list(missing_in_bq)
                    }
                    results["schema_mismatches"].append(mismatch)
                    
                    if missing_in_parquet:
                        print(f"  ⚠ Missing in Parquet: {', '.join(list(missing_in_parquet)[:5])}")
                    if missing_in_bq:
                        print(f"  ⚠ Missing in BigQuery: {', '.join(list(missing_in_bq)[:5])}")
    
    # Check for deprecated naming patterns
    print("\nChecking for deprecated naming patterns:")
    all_tables = list(training_tables.keys())
    deprecated_found = False
    
    for table in all_tables:
        if "production_training_data" in table or "forecasting_data_warehouse" in table:
            results["deprecated_patterns"].append(table)
            deprecated_found = True
            print(f"  ⚠ Deprecated pattern: {table}")
    
    if not deprecated_found:
        print(f"  ✓ No deprecated naming patterns found")
    
    audit_results["cross_checks"] = results
    return results


def generate_summary():
    """Generate final audit summary"""
    print_section("AUDIT SUMMARY")
    
    summary = {
        "status": "PASS",
        "critical_issues": [],
        "warnings": [],
        "recommendations": []
    }
    
    # Training tables summary
    training = audit_results.get("training_tables", {})
    total_tables = len(SURFACES) * len(HORIZONS)
    existing_tables = sum(1 for t in training.values() if t.get("exists"))
    
    print(f"Training Tables: {existing_tables}/{total_tables} exist")
    if existing_tables < total_tables:
        missing = [name for name, info in training.items() if not info.get("exists")]
        summary["critical_issues"].append(f"Missing training tables: {', '.join(missing)}")
        summary["status"] = "FAIL"
    
    # Check for issues in existing tables
    tables_with_issues = [name for name, info in training.items() 
                         if info.get("exists") and info.get("issues")]
    if tables_with_issues:
        print(f"  ⚠ {len(tables_with_issues)} tables have issues")
        summary["warnings"].extend([f"{name}: {'; '.join(info['issues'])}" 
                                   for name, info in training.items() if name in tables_with_issues])
    
    # Regime data summary
    regime = audit_results.get("regime_data", {})
    regime_calendar = regime.get("regime_calendar", {})
    regime_weights = regime.get("regime_weights", {})
    
    print(f"\nRegime Data:")
    print(f"  regime_calendar: {'✓' if regime_calendar.get('exists') else '✗'}")
    print(f"  regime_weights: {'✓' if regime_weights.get('exists') else '✗'}")
    
    if not regime_calendar.get("exists"):
        summary["critical_issues"].append("regime_calendar table missing")
        summary["status"] = "FAIL"
    if not regime_weights.get("exists"):
        summary["critical_issues"].append("regime_weights table missing")
        summary["status"] = "FAIL"
    
    # Raw intelligence summary
    raw_intel = audit_results.get("raw_intelligence", {})
    print(f"\nRaw Intelligence: {raw_intel.get('table_count', 0)} tables")
    if raw_intel.get("naming_issues"):
        print(f"  ⚠ {len(raw_intel['naming_issues'])} naming violations")
        summary["warnings"].append(f"Raw intelligence naming issues: {len(raw_intel['naming_issues'])} tables")
    if raw_intel.get("missing_tables"):
        print(f"  ⚠ Missing expected tables: {', '.join(raw_intel['missing_tables'])}")
        summary["critical_issues"].extend([f"Missing table: {t}" for t in raw_intel['missing_tables']])
    
    # Legacy usage summary
    legacy = audit_results.get("legacy_usage", {})
    recent_updates = legacy.get("recent_updates", [])
    print(f"\nLegacy Dataset Usage: {len(recent_updates)} recent updates")
    if recent_updates:
        summary["warnings"].append(f"Legacy tables still being updated: {len(recent_updates)} tables")
        for update in recent_updates[:3]:  # Show first 3
            print(f"  ⚠ {update['dataset']}.{update['table']}")
    
    # Export summary
    exports = audit_results.get("external_exports", {})
    if not exports.get("path_exists"):
        summary["critical_issues"].append("Export path does not exist")
        summary["status"] = "FAIL"
    else:
        missing_exports = exports.get("missing_files", [])
        print(f"\nExternal Exports: {len(exports.get('files', {})) - len(missing_exports)}/{len(exports.get('files', {}))} files")
        if missing_exports:
            summary["warnings"].append(f"Missing export files: {len(missing_exports)}")
    
    # Cross-check summary
    cross = audit_results.get("cross_checks", {})
    mismatches = len(cross.get("row_count_mismatches", []))
    if mismatches > 0:
        summary["warnings"].append(f"Row count mismatches: {mismatches} tables")
        summary["recommendations"].append("Re-export tables with row count mismatches")
    
    deprecated = cross.get("deprecated_patterns", [])
    if deprecated:
        summary["warnings"].append(f"Deprecated naming patterns found: {len(deprecated)}")
        summary["recommendations"].append("Rename or archive tables with deprecated patterns")
    
    # Final verdict
    print("\n" + "=" * 80)
    print(f"FINAL VERDICT: {summary['status']}")
    print("=" * 80)
    
    if summary["critical_issues"]:
        print(f"\n❌ CRITICAL ISSUES ({len(summary['critical_issues'])}):")
        for issue in summary["critical_issues"]:
            print(f"  - {issue}")
    
    if summary["warnings"]:
        print(f"\n⚠ WARNINGS ({len(summary['warnings'])}):")
        for warning in summary["warnings"][:10]:  # Show first 10
            print(f"  - {warning}")
    
    if summary["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS ({len(summary['recommendations'])}):")
        for rec in summary["recommendations"]:
            print(f"  - {rec}")
    
    if summary["status"] == "PASS" and not summary["critical_issues"]:
        print("\n✅ All data is correctly located and fully backfilled under the new architecture")
    
    audit_results["summary"] = summary
    return summary


def save_audit_report():
    """Save detailed audit report to JSON and markdown"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_path = Path(f"/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/audits/live_data_audit_{timestamp}.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w') as f:
        json.dump(audit_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed JSON report saved to: {json_path}")
    
    # Save markdown summary
    md_path = Path(f"/Users/kirkmusick/Documents/GitHub/CBI-V14/docs/audits/LIVE_DATA_AUDIT_{timestamp}.md")
    
    with open(md_path, 'w') as f:
        f.write(f"# Live Data Audit Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status**: {audit_results['summary']['status']}\n\n")
        
        f.write("## Executive Summary\n\n")
        
        summary = audit_results['summary']
        if summary.get('critical_issues'):
            f.write(f"### ❌ Critical Issues ({len(summary['critical_issues'])})\n\n")
            for issue in summary['critical_issues']:
                f.write(f"- {issue}\n")
            f.write("\n")
        
        if summary.get('warnings'):
            f.write(f"### ⚠ Warnings ({len(summary['warnings'])})\n\n")
            for warning in summary['warnings'][:20]:
                f.write(f"- {warning}\n")
            f.write("\n")
        
        # Training tables detail
        f.write("## Training Tables\n\n")
        f.write("| Table | Exists | Rows | Columns | Date Range | Issues |\n")
        f.write("|-------|--------|------|---------|------------|--------|\n")
        
        for name, info in audit_results.get('training_tables', {}).items():
            exists = "✓" if info.get('exists') else "✗"
            rows = f"{info.get('row_count', 0):,}"
            cols = info.get('column_count', 0)
            date_range = ""
            if info.get('date_range'):
                dr = info['date_range']
                if dr.get('earliest') and dr.get('latest'):
                    date_range = f"{dr['earliest']} to {dr['latest']}"
            issues = "; ".join(info.get('issues', []))[:50] if info.get('issues') else ""
            f.write(f"| {name} | {exists} | {rows} | {cols} | {date_range} | {issues} |\n")
        
        f.write("\n")
        
        # Raw intelligence summary
        f.write("## Raw Intelligence Tables\n\n")
        f.write(f"**Total tables**: {audit_results.get('raw_intelligence', {}).get('table_count', 0)}\n\n")
        
        raw_intel = audit_results.get('raw_intelligence', {}).get('tables', {})
        f.write("| Table | Rows | Date Range |\n")
        f.write("|-------|------|------------|\n")
        
        for name, info in sorted(raw_intel.items())[:30]:  # Show first 30
            rows = f"{info.get('row_count', 0):,}"
            date_range = ""
            if info.get('date_range'):
                dr = info['date_range']
                if dr.get('earliest') and dr.get('latest'):
                    date_range = f"{dr['earliest']} to {dr['latest']}"
            f.write(f"| {name} | {rows} | {date_range} |\n")
        
        f.write("\n")
        
        # Cross-checks
        f.write("## Cross-Checks\n\n")
        cross = audit_results.get('cross_checks', {})
        f.write(f"- Row count matches: {len(cross.get('row_count_matches', []))}\n")
        f.write(f"- Row count mismatches: {len(cross.get('row_count_mismatches', []))}\n")
        f.write(f"- Schema matches: {len(cross.get('schema_matches', []))}\n")
        f.write(f"- Schema mismatches: {len(cross.get('schema_mismatches', []))}\n")
        f.write(f"- Deprecated patterns: {len(cross.get('deprecated_patterns', []))}\n")
        
        f.write("\n---\n\n")
        f.write(f"*Full details in JSON report: {json_path.name}*\n")
    
    print(f"📄 Markdown summary saved to: {md_path}")
    
    return json_path, md_path


def main():
    """Main audit execution"""
    print("=" * 80)
    print("  CBI-V14 COMPREHENSIVE LIVE DATA AUDIT")
    print("  Focus: Data location, completeness, and naming consistency")
    print("=" * 80)
    print(f"\nStarting audit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✓ Connected to BigQuery project: {PROJECT_ID}\n")
    except Exception as e:
        print(f"✗ Failed to connect to BigQuery: {str(e)}")
        sys.exit(1)
    
    # Run audits
    try:
        audit_training_tables(client)
        audit_regime_data(client)
        audit_raw_intelligence(client)
        audit_legacy_datasets(client)
        audit_external_exports()
        cross_check_data()
        generate_summary()
        save_audit_report()
        
        print(f"\n✅ Audit completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return exit code based on status
        if audit_results['summary']['status'] == 'FAIL':
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\n✗ Audit failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

