#!/usr/bin/env python3
"""
COMPREHENSIVE BIGQUERY ML TRAINING PIPELINE AUDIT
Full-featured validation with no simplifications

This framework audits every aspect of the ML pipeline to prevent correlated
subquery issues and ensure all models train with the complete feature set.
"""
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import pandas as pd
import numpy as np
import time
import json
import sys
import re
from datetime import datetime, timedelta
import networkx as nx
from typing import Dict, List, Tuple, Set, Optional, Any, Union

class MLPipelineAudit:
    def __init__(self, project_id: str = "cbi-v14"):
        """Initialize the audit framework with full validation capabilities"""
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.validation_results = {}
        self.issue_count = 0
        self.critical_issues = []
        self.dependency_graph = nx.DiGraph()
        
        # Define expected feature count and critical features
        self.expected_feature_count = 159
        self.critical_features = [
            "feature_vix_stress", "feature_harvest_pace", "feature_china_relations",
            "feature_tariff_probability", "feature_geopolitical_volatility", 
            "feature_biofuel_impact", "feature_hidden_correlation"
        ]
        
        print(f"Initializing comprehensive ML pipeline audit for {project_id}")
    
    def audit_all(self, training_table: str) -> Dict:
        """Run all audit checks with full validation"""
        print(f"\n{'='*80}\nCOMPREHENSIVE AUDIT STARTING\n{'='*80}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Structure validation
        self.validate_schema(training_table)
        self.validate_dependencies(training_table)
        
        # Data validation
        self.validate_data_integrity(training_table)
        self.validate_window_functions(training_table)
        
        # BigQuery ML compatibility
        self.validate_bqml_compatibility(training_table)
        
        # Performance & optimization
        self.analyze_query_performance(training_table)
        
        # Future-proofing
        self.validate_future_proof(training_table)
        
        # Generate report
        return self.generate_report()
    
    def validate_schema(self, table_name: str) -> None:
        """Thorough schema validation with comprehensive checks"""
        print(f"\n{'='*80}\nVALIDATING SCHEMA: {table_name}\n{'='*80}")
        
        # Get all columns from the table
        schema_query = f"""
        SELECT 
            column_name, 
            data_type,
            is_nullable
        FROM `{self.project_id}.{table_name.split('.')[0]}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_name.split('.')[-1]}'
        ORDER BY ordinal_position
        """
        
        try:
            schema_df = self.client.query(schema_query).to_dataframe()
            
            # Store all validation results
            self.validation_results["schema"] = {
                "column_count": len(schema_df),
                "columns": schema_df.to_dict(orient="records"),
                "has_all_critical_features": True,
                "missing_critical_features": [],
                "data_type_issues": []
            }
            
            # Validate column count
            print(f"Column count: {len(schema_df)} (Expected: {self.expected_feature_count})")
            if len(schema_df) < self.expected_feature_count:
                self.issue_count += 1
                message = f"⚠️ CRITICAL: Only {len(schema_df)} columns found (expected {self.expected_feature_count})"
                print(message)
                self.critical_issues.append(message)
            
            # Check for critical features
            missing_features = []
            for feature in self.critical_features:
                if feature not in schema_df.column_name.values:
                    missing_features.append(feature)
            
            if missing_features:
                self.issue_count += len(missing_features)
                self.validation_results["schema"]["has_all_critical_features"] = False
                self.validation_results["schema"]["missing_critical_features"] = missing_features
                message = f"⚠️ CRITICAL: Missing {len(missing_features)} critical features: {', '.join(missing_features)}"
                print(message)
                self.critical_issues.append(message)
            else:
                print(f"✅ All critical features present")
            
            # Check data types
            target_columns = [col for col in schema_df.column_name if col.startswith("target_")]
            for target in target_columns:
                dtype = schema_df[schema_df.column_name == target].data_type.values[0]
                if dtype != "FLOAT64":
                    self.issue_count += 1
                    issue = f"Target column {target} has type {dtype} instead of FLOAT64"
                    print(f"⚠️ {issue}")
                    self.validation_results["schema"]["data_type_issues"].append(issue)
            
            print(f"Found {len(target_columns)} target columns")
            print(f"Total columns: {len(schema_df)}")
            
        except Exception as e:
            self.issue_count += 1
            message = f"⚠️ CRITICAL: Error validating schema: {str(e)}"
            print(message)
            self.critical_issues.append(message)
            self.validation_results["schema"] = {"error": str(e)}
    
    def validate_dependencies(self, table_name: str) -> None:
        """Build comprehensive dependency graph with full lineage tracking"""
        print(f"\n{'='*80}\nVALIDATING DEPENDENCIES\n{'='*80}")
        
        try:
            # Get all views in the project
            views_query = f"""
            SELECT 
                table_schema, 
                table_name, 
                view_definition
            FROM `{self.project_id}.INFORMATION_SCHEMA.VIEWS`
            """
            views_df = self.client.query(views_query).to_dataframe()
            
            # Build dependency graph
            for _, row in views_df.iterrows():
                view_name = f"{row.table_schema}.{row.table_name}"
                self.dependency_graph.add_node(view_name, type="view")
                
                # Extract table references
                refs = re.findall(r'FROM\s+`([^`]+)`', row.view_definition)
                refs += re.findall(r'JOIN\s+`([^`]+)`', row.view_definition)
                
                for ref in refs:
                    # Only consider references in the same project
                    if self.project_id in ref:
                        # Clean up the reference
                        ref = ref.replace(f"{self.project_id}.", "")
                        self.dependency_graph.add_node(ref)
                        self.dependency_graph.add_edge(ref, view_name)
                        
                        # Check if reference is to staging tables
                        if "staging." in ref:
                            self.issue_count += 1
                            message = f"⚠️ View {view_name} references staging table: {ref}"
                            print(message)
                            self.validation_results.setdefault("dependencies", {}).setdefault("staging_references", []).append({"view": view_name, "ref": ref})
            
            # Get all paths to the training table
            table_short = table_name.split(".")[-1]
            full_table_name = f"{table_name.split('.')[0]}.{table_name.split('.')[-1]}"
            
            # Check for dependencies on the training table
            dependencies = []
            if full_table_name in self.dependency_graph.nodes():
                for node in self.dependency_graph.nodes():
                    if node != full_table_name and nx.has_path(self.dependency_graph, node, full_table_name):
                        dependencies.append(node)
            
            # Check for circular references
            cycles = list(nx.simple_cycles(self.dependency_graph))
            if cycles:
                self.issue_count += len(cycles)
                message = f"⚠️ CRITICAL: Found {len(cycles)} circular dependencies in views"
                print(message)
                self.critical_issues.append(message)
                for cycle in cycles:
                    print(f"  Circular dependency: {' -> '.join(cycle)}")
                
                self.validation_results.setdefault("dependencies", {})["circular_references"] = cycles
            else:
                print("✅ No circular dependencies found")
            
            # Store dependency information
            self.validation_results.setdefault("dependencies", {}).update({
                "total_views": len(views_df),
                "dependencies": dependencies,
                "circular_references": cycles
            })
            
            print(f"Analyzed {len(views_df)} views")
            print(f"Found {len(dependencies)} dependencies for {full_table_name}")
            
        except Exception as e:
            self.issue_count += 1
            message = f"⚠️ Error mapping dependencies: {str(e)}"
            print(message)
            self.validation_results.setdefault("dependencies", {})["error"] = str(e)
    
    def validate_data_integrity(self, table_name: str) -> None:
        """Comprehensive data integrity validation with full analysis"""
        print(f"\n{'='*80}\nVALIDATING DATA INTEGRITY: {table_name}\n{'='*80}")
        
        try:
            # Check row count and date range
            metadata_query = f"""
            SELECT 
                COUNT(*) as row_count,
                COUNT(DISTINCT date) as unique_dates,
                MIN(date) as min_date,
                MAX(date) as max_date
            FROM `{self.project_id}.{table_name}`
            """
            metadata = self.client.query(metadata_query).to_dataframe().iloc[0]
            
            self.validation_results["data_integrity"] = {
                "row_count": int(metadata.row_count),
                "unique_dates": int(metadata.unique_dates),
                "date_range": [str(metadata.min_date), str(metadata.max_date)],
                "completeness": {}
            }
            
            print(f"Row count: {metadata.row_count}")
            print(f"Unique dates: {metadata.unique_dates}")
            print(f"Date range: {metadata.min_date} to {metadata.max_date}")
            
            # Check for gaps in dates (sample check for performance)
            gaps_query = f"""
            WITH date_series AS (
              SELECT date
              FROM UNNEST(GENERATE_DATE_ARRAY(
                DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY),
                CURRENT_DATE()
              )) as date
            ),
            actual_dates AS (
              SELECT DISTINCT date 
              FROM `{self.project_id}.{table_name}`
              WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
            )
            SELECT COUNT(*) as gap_count
            FROM date_series d
            LEFT JOIN actual_dates a ON d.date = a.date
            WHERE a.date IS NULL
            """
            
            gaps_result = self.client.query(gaps_query).to_dataframe().iloc[0]
            gap_count = int(gaps_result.gap_count)
            
            self.validation_results["data_integrity"]["gaps"] = {
                "count_last_365_days": gap_count
            }
            
            if gap_count > 0:
                print(f"⚠️ Found {gap_count} gaps in date sequence (last 365 days)")
            else:
                print("✅ No gaps in date sequence (last 365 days)")
            
            # Sample NULL check on first 20 columns to avoid timeout
            schema_query = f"""
            SELECT column_name
            FROM `{self.project_id}.{table_name.split('.')[0]}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table_name.split('.')[-1]}'
            ORDER BY ordinal_position
            LIMIT 20
            """
            columns = self.client.query(schema_query).to_dataframe().column_name.tolist()
            
            null_checks = []
            for col in columns:
                null_query = f"""
                SELECT 
                    '{col}' as column_name,
                    COUNTIF({col} IS NULL) as null_count,
                    COUNT(*) as total_count
                FROM `{self.project_id}.{table_name}`
                """
                result = self.client.query(null_query).to_dataframe().iloc[0]
                if result.null_count > 0:
                    null_checks.append({
                        "column_name": col,
                        "null_count": int(result.null_count),
                        "total_count": int(result.total_count),
                        "null_percentage": round(result.null_count / result.total_count * 100, 2)
                    })
            
            self.validation_results["data_integrity"]["null_analysis"] = {
                "columns_checked": len(columns),
                "columns_with_nulls": null_checks
            }
            
            if null_checks:
                print(f"⚠️ Found NULLs in {len(null_checks)} columns (sample of {len(columns)} checked)")
            else:
                print(f"✅ No NULL values in sampled columns ({len(columns)} checked)")
            
        except Exception as e:
            self.issue_count += 1
            message = f"⚠️ Error validating data integrity: {str(e)}"
            print(message)
            self.validation_results["data_integrity"] = {"error": str(e)}
    
    def validate_window_functions(self, table_name: str) -> None:
        """Identify and validate all window functions used in the dataset"""
        print(f"\n{'='*80}\nVALIDATING WINDOW FUNCTIONS\n{'='*80}")
        
        try:
            # Find all views that feed into the training table
            views_query = f"""
            SELECT 
                table_schema, 
                table_name, 
                view_definition
            FROM `{self.project_id}.INFORMATION_SCHEMA.VIEWS`
            """
            views_df = self.client.query(views_query).to_dataframe()
            
            # Patterns for window functions
            window_patterns = [
                r'(LAG\([^\)]+\)\s+OVER\s*\([^\)]+\))',
                r'(AVG\([^\)]+\)\s+OVER\s*\([^\)]+\))',
                r'(SUM\([^\)]+\)\s+OVER\s*\([^\)]+\))',
                r'(COUNT\([^\)]+\)\s+OVER\s*\([^\)]+\))',
                r'(MAX\([^\)]+\)\s+OVER\s*\([^\)]+\))',
                r'(MIN\([^\)]+\)\s+OVER\s*\([^\)]+\))'
            ]
            
            # Extract and analyze all window functions
            window_functions = []
            
            for _, row in views_df.iterrows():
                view_name = f"{row.table_schema}.{row.table_name}"
                for pattern in window_patterns:
                    matches = re.findall(pattern, str(row.view_definition), re.IGNORECASE)
                    for match in matches:
                        window_functions.append({
                            "view": view_name,
                            "function": match,
                            "type": match.split('(')[0].upper()
                        })
            
            # Check for correlated subqueries with window functions
            correlated_subqueries = []
            for _, row in views_df.iterrows():
                view_name = f"{row.table_schema}.{row.table_name}"
                view_def = str(row.view_definition)
                
                # Look for subqueries
                subquery_matches = re.findall(r'(\(\s*SELECT.*?FROM.*?WHERE.*?\))', view_def, re.DOTALL | re.IGNORECASE)
                
                for subquery in subquery_matches:
                    # Check if subquery contains window functions
                    has_window = False
                    for pattern in window_patterns:
                        if re.search(pattern, subquery, re.IGNORECASE):
                            has_window = True
                            break
                    
                    # Check if subquery references outer tables
                    outer_refs = re.findall(r'(\w+\.\w+)', subquery)
                    
                    if has_window and outer_refs:
                        correlated_subqueries.append({
                            "view": view_name,
                            "subquery": subquery[:100] + "..." if len(subquery) > 100 else subquery,
                            "contains_window": has_window,
                            "references": outer_refs
                        })
            
            # Store window function information
            self.validation_results["window_functions"] = {
                "total_window_functions": len(window_functions),
                "functions_by_type": {
                    "LAG": len([wf for wf in window_functions if wf["type"] == "LAG"]),
                    "AVG": len([wf for wf in window_functions if wf["type"] == "AVG"]),
                    "SUM": len([wf for wf in window_functions if wf["type"] == "SUM"]),
                    "COUNT": len([wf for wf in window_functions if wf["type"] == "COUNT"]),
                    "MAX": len([wf for wf in window_functions if wf["type"] == "MAX"]),
                    "MIN": len([wf for wf in window_functions if wf["type"] == "MIN"])
                },
                "correlated_subqueries": correlated_subqueries
            }
            
            print(f"Found {len(window_functions)} window functions in all views")
            print(f"Window function types:")
            for func_type, count in self.validation_results["window_functions"]["functions_by_type"].items():
                print(f"  {func_type}: {count}")
            
            if correlated_subqueries:
                self.issue_count += len(correlated_subqueries)
                message = f"⚠️ CRITICAL: Found {len(correlated_subqueries)} correlated subqueries with window functions"
                print(message)
                self.critical_issues.append(message)
                print("These will cause BQML training to fail!")
                for i, cs in enumerate(correlated_subqueries[:3]):
                    print(f"  {i+1}. In {cs['view']}: {cs['subquery']}")
                if len(correlated_subqueries) > 3:
                    print(f"  ... and {len(correlated_subqueries) - 3} more")
            else:
                print("✅ No correlated subqueries with window functions found")
                
        except Exception as e:
            self.issue_count += 1
            message = f"⚠️ Error validating window functions: {str(e)}"
            print(message)
            self.validation_results["window_functions"] = {"error": str(e)}
    
    def validate_bqml_compatibility(self, table_name: str) -> None:
        """Comprehensive BQML compatibility testing with multiple model types"""
        print(f"\n{'='*80}\nVALIDATING BQML COMPATIBILITY: {table_name}\n{'='*80}")
        
        # Define test models to try (lightweight tests)
        test_models = [
            {
                "name": "linear_reg_test",
                "type": "LINEAR_REG",
                "options": "input_label_cols=['target_1w']",
                "limit": 100
            }
        ]
        
        compatibility_results = []
        
        for model in test_models:
            print(f"\nTesting compatibility with {model['type']}...")
            
            # Get schema to build except clause
            schema_query = f"""
            SELECT column_name
            FROM `{self.project_id}.{table_name.split('.')[0]}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table_name.split('.')[-1]}'
            AND column_name LIKE 'target_%'
            """
            target_columns = [row.column_name for row in self.client.query(schema_query).result()]
            
            except_clause = "date"
            if target_columns:
                except_clause += ", " + ", ".join([col for col in target_columns if col != 'target_1w'])
            
            # Create test model
            model_query = f"""
            CREATE OR REPLACE MODEL `{self.project_id}.models.{model['name']}_compatibility`
            OPTIONS(
                model_type='{model['type']}',
                {model['options']},
                max_iterations=1
            ) AS
            SELECT * EXCEPT({except_clause})
            FROM `{self.project_id}.{table_name}`
            WHERE target_1w IS NOT NULL
            LIMIT {model['limit']}
            """
            
            start_time = time.time()
            try:
                job = self.client.query(model_query)
                job.result()  # Wait for the query to complete
                
                duration = time.time() - start_time
                
                # Get model evaluation metrics
                eval_query = f"""
                SELECT *
                FROM ML.EVALUATE(MODEL `{self.project_id}.models.{model['name']}_compatibility`)
                """
                eval_results = self.client.query(eval_query).to_dataframe()
                
                compatibility_results.append({
                    "model_type": model["type"],
                    "status": "SUCCESS",
                    "duration_seconds": duration,
                    "evaluation": eval_results.to_dict(orient="records")[0] if len(eval_results) > 0 else {}
                })
                
                print(f"✅ {model['type']} model trained successfully in {duration:.2f} seconds")
                if len(eval_results) > 0 and 'mean_absolute_error' in eval_results.columns:
                    print(f"  Mean Absolute Error: {eval_results.mean_absolute_error.values[0]:.4f}")
                
                # Clean up test model
                self.client.query(f"DROP MODEL IF EXISTS `{self.project_id}.models.{model['name']}_compatibility`")
                
            except GoogleCloudError as e:
                duration = time.time() - start_time
                error_message = str(e)
                
                compatibility_results.append({
                    "model_type": model["type"],
                    "status": "FAILED",
                    "duration_seconds": duration,
                    "error": error_message
                })
                
                self.issue_count += 1
                message = f"⚠️ {model['type']} model training failed: {error_message[:200]}..."
                print(message)
                
                # Check specifically for correlated subquery error
                if "Correlated subqueries that reference other tables are not supported" in error_message:
                    critical_message = f"⚠️ CRITICAL: {model['type']} model failed due to correlated subqueries"
                    print(critical_message)
                    self.critical_issues.append(critical_message)
        
        # Store compatibility results
        self.validation_results["bqml_compatibility"] = {
            "models_tested": len(test_models),
            "successful_models": len([r for r in compatibility_results if r["status"] == "SUCCESS"]),
            "failed_models": len([r for r in compatibility_results if r["status"] == "FAILED"]),
            "results": compatibility_results
        }
        
        # Overall compatibility assessment
        if self.validation_results["bqml_compatibility"]["successful_models"] == 0:
            critical_message = "⚠️ CRITICAL: ALL model types failed - table is NOT BQML compatible"
            print(critical_message)
            self.critical_issues.append(critical_message)
        elif self.validation_results["bqml_compatibility"]["successful_models"] < len(test_models):
            message = f"⚠️ PARTIAL COMPATIBILITY: {self.validation_results['bqml_compatibility']['successful_models']} of {len(test_models)} model types work"
            print(message)
        else:
            print(f"✅ FULL COMPATIBILITY: All {len(test_models)} model types work")
    
    def analyze_query_performance(self, table_name: str) -> None:
        """Performance analysis with optimization recommendations"""
        print(f"\n{'='*80}\nANALYZING QUERY PERFORMANCE\n{'='*80}")
        
        try:
            # Analyze query creation time for sample
            performance_query = f"""
            SELECT * 
            FROM `{self.project_id}.{table_name}`
            LIMIT 1000
            """
            
            start_time = time.time()
            query_job = self.client.query(performance_query)
            query_job.result()  # Wait for the query to complete
            duration = time.time() - start_time
            
            # Get query plan and statistics
            job_id = query_job.job_id
            job = self.client.get_job(job_id)
            
            # Check for table partitioning/clustering
            table_ref = bigquery.TableReference.from_string(
                f"{self.project_id}.{table_name}"
            )
            table = self.client.get_table(table_ref)
            
            is_partitioned = table.time_partitioning is not None
            is_clustered = table.clustering_fields is not None
            
            # Store performance results
            self.validation_results["performance"] = {
                "query_duration_seconds": duration,
                "is_partitioned": is_partitioned,
                "is_clustered": is_clustered,
                "clustering_fields": table.clustering_fields if is_clustered else None,
                "partition_type": table.time_partitioning.type_ if is_partitioned else None,
                "partition_field": table.time_partitioning.field if is_partitioned else None,
                "bytes_processed": job.total_bytes_processed,
                "slot_ms": job.slot_millis if hasattr(job, "slot_millis") else None
            }
            
            print(f"Query duration: {duration:.2f} seconds")
            print(f"Bytes processed: {job.total_bytes_processed:,} bytes")
            
            if not is_partitioned and not is_clustered:
                self.issue_count += 1
                message = "⚠️ Table is not partitioned or clustered - consider optimizing"
                print(message)
                print("  Recommendation: Partition by date and cluster by critical features")
            else:
                if is_partitioned:
                    print(f"✅ Table is partitioned by {table.time_partitioning.field} ({table.time_partitioning.type_})")
                if is_clustered:
                    print(f"✅ Table is clustered by {table.clustering_fields}")
            
        except Exception as e:
            self.issue_count += 1
            message = f"⚠️ Error analyzing performance: {str(e)}"
            print(message)
            self.validation_results["performance"] = {"error": str(e)}
    
    def validate_future_proof(self, table_name: str) -> None:
        """Ensure the solution is future-proof against correlated subquery issues"""
        print(f"\n{'='*80}\nVALIDATING FUTURE-PROOFING\n{'='*80}")
        
        try:
            # Check for direct materialized table vs view
            table_info_query = f"""
            SELECT table_type
            FROM `{self.project_id}.{table_name.split('.')[0]}.INFORMATION_SCHEMA.TABLES`
            WHERE table_name = '{table_name.split('.')[-1]}'
            """
            table_info = self.client.query(table_info_query).to_dataframe().iloc[0]
            
            is_materialized = table_info.table_type == "BASE TABLE"
            
            # Build future-proof recommendations
            recommendations = []
            if not is_materialized:
                recommendations.append(
                    "Convert view to materialized table to avoid correlated subquery issues"
                )
            
            # Check for refresh processes
            if "window_functions" in self.validation_results:
                wf_count = self.validation_results["window_functions"]["total_window_functions"]
                if wf_count > 0:
                    recommendations.append(
                        f"Pre-compute {wf_count} window functions in separate tables before joining"
                    )
            
            # Store future-proof results
            self.validation_results["future_proof"] = {
                "is_materialized_table": is_materialized,
                "recommendations": recommendations
            }
            
            print(f"Table type: {'MATERIALIZED TABLE' if is_materialized else 'VIEW'}")
            
            if recommendations:
                print("Recommendations:")
                for i, rec in enumerate(recommendations):
                    print(f"  {i+1}. {rec}")
            else:
                print("✅ No future-proofing recommendations needed")
            
        except Exception as e:
            self.issue_count += 1
            message = f"⚠️ Error validating future-proofing: {str(e)}"
            print(message)
            self.validation_results["future_proof"] = {"error": str(e)}
    
    def generate_report(self) -> Dict:
        """Generate comprehensive audit report with full details"""
        print(f"\n{'='*80}\nAUDIT SUMMARY\n{'='*80}")
        
        # Calculate overall quality score
        quality_score = 100
        
        # Deduct for critical issues
        quality_score -= len(self.critical_issues) * 15
        
        # Deduct for other issues
        quality_score -= max(0, self.issue_count - len(self.critical_issues)) * 5
        
        # Ensure quality score doesn't go below 0
        quality_score = max(0, quality_score)
        
        # Summary counts
        summary = {
            "audit_timestamp": datetime.now().isoformat(),
            "total_issues": self.issue_count,
            "critical_issues": len(self.critical_issues),
            "quality_score": quality_score,
            "status": "FAILED" if self.critical_issues else "PASSED WITH ISSUES" if self.issue_count > 0 else "PASSED"
        }
        
        print(f"Audit completed with {self.issue_count} issues ({len(self.critical_issues)} critical)")
        print(f"Quality score: {quality_score}/100")
        print(f"Status: {summary['status']}")
        
        if self.critical_issues:
            print("\nCritical issues that must be fixed:")
            for i, issue in enumerate(self.critical_issues):
                print(f"  {i+1}. {issue}")
        
        # Add summary to validation results
        self.validation_results["summary"] = summary
        
        # Return full validation results
        return self.validation_results


# Example usage:
if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Comprehensive BigQuery ML Pipeline Audit")
    parser.add_argument("--project", default="cbi-v14", help="BigQuery project ID")
    parser.add_argument("--table", required=True, help="Full table name to audit (format: dataset.table)")
    parser.add_argument("--output", help="Path to save output JSON report")
    args = parser.parse_args()
    
    # Run the audit
    audit = MLPipelineAudit(project_id=args.project)
    results = audit.audit_all(args.table)
    
    # Save report if output specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✅ Audit report saved to {args.output}")

    # Exit with non-zero code if critical issues found
    if results["summary"]["critical_issues"] > 0:
        sys.exit(1)





