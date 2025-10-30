"""
Schema Validation Tool - Vertex AI AutoML
Validates schema types before deployment to catch mismatches
"""
from google.cloud import bigquery
import pandas as pd
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_prediction_schema():
    """Validate schema types before deployment to catch mismatches"""
    # Initialize BigQuery client
    client = bigquery.Client(project='cbi-v14')
    
    # Query the latest data from training dataset
    query = """
    SELECT *
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    ORDER BY date DESC
    LIMIT 1
    """
    
    try:
        # Get the raw data
        df = client.query(query).to_dataframe()
        logger.info(f"✅ Retrieved {len(df.columns)} columns from training dataset")
        
        # Create a schema report
        schema_report = {
            "timestamp": datetime.now().isoformat(),
            "total_columns": len(df.columns),
            "column_types": {},
            "potential_issues": [],
            "null_columns": [],
            "date_columns": [],
            "numeric_columns": {
                "int64": [],
                "float64": []
            }
        }
        
        # Check each column type
        for col in df.columns:
            dtype = str(df[col].dtype)
            value = df[col].iloc[0]
            
            schema_report["column_types"][col] = {
                "dtype": dtype,
                "sample_value": str(value) if pd.notna(value) else "NULL",
                "is_null": bool(pd.isna(value))
            }
            
            # Flag potential schema issues
            if dtype == 'int64':
                schema_report["numeric_columns"]["int64"].append(col)
                # Volume and open interest are known to need STRING conversion
                if 'volume' in col.lower() or 'open_interest' in col.lower():
                    schema_report["potential_issues"].append({
                        "column": col,
                        "issue": f"Column is int64 but model likely expects STRING",
                        "action": "Convert to STRING using df[col].astype(str)"
                    })
            
            if dtype == 'float64':
                schema_report["numeric_columns"]["float64"].append(col)
                # Check for specific columns that may need STRING
                if col in ['zl_volume', 'zl_open_interest']:
                    schema_report["potential_issues"].append({
                        "column": col,
                        "issue": f"Column is float64 but model expects STRING",
                        "action": "Convert to STRING using df[col].astype(str)"
                    })
            
            # Check for NaN values
            if pd.isna(value):
                schema_report["null_columns"].append(col)
            
            # Check for date columns
            if dtype == 'datetime64[ns]' or 'date' in col.lower():
                schema_report["date_columns"].append(col)
        
        # Print detailed report
        logger.info("\n" + "="*70)
        logger.info("SCHEMA VALIDATION REPORT")
        logger.info("="*70)
        logger.info(f"Total columns: {schema_report['total_columns']}")
        logger.info(f"Date columns: {len(schema_report['date_columns'])}")
        logger.info(f"Integer columns: {len(schema_report['numeric_columns']['int64'])}")
        logger.info(f"Float columns: {len(schema_report['numeric_columns']['float64'])}")
        logger.info(f"Columns with NULL values: {len(schema_report['null_columns'])}")
        
        logger.info("\n" + "-"*70)
        logger.info("POTENTIAL SCHEMA ISSUES")
        logger.info("-"*70)
        if schema_report["potential_issues"]:
            for idx, issue in enumerate(schema_report["potential_issues"], 1):
                logger.warning(f"\n⚠️  Issue #{idx}:")
                logger.warning(f"   Column: {issue['column']}")
                logger.warning(f"   Problem: {issue['issue']}")
                logger.warning(f"   Solution: {issue['action']}")
        else:
            logger.info("✅ No potential schema issues detected")
        
        # Show sample of key columns
        logger.info("\n" + "-"*70)
        logger.info("SAMPLE VALUES (First 10 columns)")
        logger.info("-"*70)
        for col in list(df.columns)[:10]:
            val = df[col].iloc[0]
            dtype = df[col].dtype
            logger.info(f"{col:30s} | {str(dtype):15s} | {str(val)[:40]}")
        
        # Show target columns specifically
        target_cols = [col for col in df.columns if 'target' in col.lower()]
        if target_cols:
            logger.info("\n" + "-"*70)
            logger.info("TARGET COLUMNS")
            logger.info("-"*70)
            for col in target_cols:
                val = df[col].iloc[0]
                dtype = df[col].dtype
                logger.info(f"{col:30s} | {str(dtype):15s} | {str(val)[:40]}")
        
        # Save report to file
        output_file = '/Users/zincdigital/CBI-V14/automl/schema_validation_report.json'
        with open(output_file, 'w') as f:
            # Convert for JSON serialization
            json_report = {
                "timestamp": schema_report["timestamp"],
                "total_columns": schema_report["total_columns"],
                "potential_issues": schema_report["potential_issues"],
                "null_columns": schema_report["null_columns"],
                "date_columns": schema_report["date_columns"],
                "numeric_columns": schema_report["numeric_columns"],
                "sample_column_types": {
                    col: info["dtype"] 
                    for col, info in list(schema_report["column_types"].items())[:20]
                }
            }
            json.dump(json_report, f, indent=2)
        
        logger.info(f"\n✅ Schema validation report saved to: {output_file}")
        logger.info("="*70 + "\n")
        
        return schema_report
    
    except Exception as e:
        logger.error(f"❌ Error during schema validation: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("🔍 Starting schema validation...\n")
    try:
        report = validate_prediction_schema()
        
        # Check for critical issues
        critical_issues = len(report["potential_issues"])
        if critical_issues > 0:
            logger.warning(f"\n⚠️  Found {critical_issues} potential schema issues that need attention")
            logger.warning("Review the issues above and apply the suggested fixes")
        else:
            logger.info("\n✅ No schema issues detected - ready for prediction!")
    
    except Exception as e:
        logger.error(f"\n❌ Schema validation failed: {str(e)}")
        exit(1)

