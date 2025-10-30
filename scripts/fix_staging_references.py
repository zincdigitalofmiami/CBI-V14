#!/usr/bin/env python3
"""
Fix Staging References in Views
Updates all views that reference staging tables to point to main tables instead
"""

from google.cloud import bigquery
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_staging_references():
    """
    Update all views that reference staging tables to reference main tables
    """
    client = bigquery.Client()
    
    # Mapping of staging tables to main tables
    staging_to_main = {
        'staging.trump_policy_intelligence': 'forecasting_data_warehouse.trump_policy_intelligence',
        'staging.ice_enforcement_intelligence': 'forecasting_data_warehouse.ice_enforcement_intelligence', 
        'staging.comprehensive_social_intelligence': 'forecasting_data_warehouse.social_sentiment',
        'staging.news_intelligence': 'forecasting_data_warehouse.news_intelligence'
    }
    
    # Views that need updating (from our audit)
    views_to_fix = [
        # forecasting_data_warehouse
        ('forecasting_data_warehouse', 'vw_trump_effect_categories'),
        ('forecasting_data_warehouse', 'vw_dashboard_trump_intel'),
        ('forecasting_data_warehouse', 'vw_ice_trump_daily'),
        ('forecasting_data_warehouse', 'vw_trump_effect_breakdown'),
        ('forecasting_data_warehouse', 'vw_trump_intelligence_dashboard'),
        
        # signals
        ('signals', 'vw_geopolitical_aggregates_comprehensive_daily'),
        ('signals', 'vw_high_priority_social_intelligence'),
        
        # curated
        ('curated', 'vw_usda_export_sales_soy_weekly'),
        ('curated', 'vw_cftc_positions_oilseeds_weekly'),
        ('curated', 'vw_priority_indicators_daily'),
        ('curated', 'vw_cftc_soybean_oil_weekly')
    ]
    
    for dataset, view_name in views_to_fix:
        try:
            logger.info(f"Fixing {dataset}.{view_name}")
            
            # Get current view definition
            query = f"""
            SELECT view_definition
            FROM `cbi-v14.{dataset}.INFORMATION_SCHEMA.VIEWS`
            WHERE table_name = '{view_name}'
            """
            result = client.query(query).to_dataframe()
            
            if result.empty:
                logger.warning(f"View {dataset}.{view_name} not found")
                continue
                
            view_definition = result.iloc[0]['view_definition']
            logger.info(f"Current definition length: {len(view_definition)} characters")
            
            # Replace staging references with main table references
            updated_definition = view_definition
            for staging_ref, main_ref in staging_to_main.items():
                if staging_ref in updated_definition:
                    updated_definition = updated_definition.replace(staging_ref, main_ref)
                    logger.info(f"Replaced {staging_ref} with {main_ref}")
            
            # Check if any changes were made
            if updated_definition == view_definition:
                logger.info(f"No staging references found in {dataset}.{view_name}")
                continue
                
            # Update the view
            create_sql = f"CREATE OR REPLACE VIEW `cbi-v14.{dataset}.{view_name}` AS {updated_definition}"
            
            logger.info(f"Updating view {dataset}.{view_name}")
            job = client.query(create_sql)
            job.result()
            
            logger.info(f"✅ Successfully updated {dataset}.{view_name}")
            
        except Exception as e:
            logger.error(f"❌ Error updating {dataset}.{view_name}: {e}")
            continue
    
    logger.info("Completed fixing staging references")

if __name__ == "__main__":
    fix_staging_references()
