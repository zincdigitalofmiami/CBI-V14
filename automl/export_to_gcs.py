#!/usr/bin/env python3
"""
Export enhanced dataset to GCS for Vertex AI AutoML training
"""

from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'
DATASET_ID = 'models_v4'
GCS_BUCKET = 'gs://forecasting-app-raw-data-bucket/automl'

# Columns to exclude (known NULL or not needed for training)
EXCLUDE_COLS = [
    'econ_gdp_growth',
    'econ_unemployment_rate', 
    'treasury_10y_yield',
    'news_article_count',
    'news_avg_score'
]

def export_for_automl():
    """Export enhanced features to GCS Parquet"""
    
    client = bigquery.Client(project=PROJECT_ID)
    
    logger.info("="*80)
    logger.info("EXPORTING DATASET TO GCS FOR AUTOML")
    logger.info("="*80)
    
    # Export full dataset
    export_query = f"""
    EXPORT DATA OPTIONS(
        uri='{GCS_BUCKET}/enhanced_features/*.parquet',
        format='PARQUET',
        overwrite=true
    ) AS
    SELECT * EXCEPT({', '.join(EXCLUDE_COLS)})
    FROM `{PROJECT_ID}.{DATASET_ID}.enhanced_features_automl`
    """
    
    logger.info(f"Exporting to: {GCS_BUCKET}/enhanced_features/")
    logger.info(f"Excluding columns: {', '.join(EXCLUDE_COLS)}")
    
    try:
        job = client.query(export_query)
        job.result()
        logger.info("✅ Export complete!")
        
        # Export succeeded
        logger.info(f"   Exported dataset successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        return False


def main():
    """Main execution"""
    success = export_for_automl()
    
    if success:
        logger.info("\n✅ Dataset ready for AutoML training")
        logger.info(f"   Location: {GCS_BUCKET}/enhanced_features/")
        logger.info("\nNext: Start ARIMA baseline models in parallel")
    else:
        logger.error("\n❌ Export failed")
        
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

