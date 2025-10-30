#!/usr/bin/env python3
"""
Weekly Critical Data Update - Cron Job
Runs every Monday 6am UTC
Updates: China imports, Argentina crisis, Industrial demand
Per Plan Section 5.2
"""

import logging
from datetime import datetime
from google.cloud import bigquery
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/weekly_data_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ID = 'cbi-v14'


def update_china_imports():
    """
    Update China soybean import data
    Primary: IndexBox scraping (TODO: implement)
    Fallback: Manual known values + USDA
    """
    logger.info("Updating China import data...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # For now: using known values
    # TODO: Implement IndexBox scraping as primary source
    latest_values = {
        'date': datetime.now().date(),
        'china_soybean_imports_mt': 13.9,  # Latest known value
        'china_imports_from_us_mt': 0.0,   # Boycott active
        'updated_at': datetime.now()
    }
    
    # Insert to warehouse
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.china_soybean_imports"
    
    errors = client.insert_rows_json(table_id, [latest_values])
    
    if errors:
        logger.error(f"  ❌ Failed to update China imports: {errors}")
        return False
    else:
        logger.info(f"  ✅ China imports updated: {latest_values['china_soybean_imports_mt']} MT")
        return True


def update_argentina_status():
    """
    Update Argentina export tax and China sales
    Critical for competitive threat monitoring
    """
    logger.info("Updating Argentina crisis status...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Check current status (manual for now)
    # TODO: Automate via news scraping or API
    latest_values = {
        'date': datetime.now().date(),
        'argentina_export_tax': 0.0,  # Crisis active (0% tax)
        'argentina_china_sales_mt': 2.5,
        'argentina_peso_usd': 1000.0,
        'argentina_competitive_threat': 1,  # High threat
        'updated_at': datetime.now()
    }
    
    # Insert to warehouse
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.argentina_crisis_tracker"
    
    errors = client.insert_rows_json(table_id, [latest_values])
    
    if errors:
        logger.error(f"  ❌ Failed to update Argentina status: {errors}")
        return False
    else:
        logger.info(f"  ✅ Argentina updated: {latest_values['argentina_export_tax']}% tax, {latest_values['argentina_china_sales_mt']} MT to China")
        return True


def update_industrial_demand():
    """
    Update industrial demand indicators
    Asphalt, tires, and other non-food uses
    """
    logger.info("Updating industrial demand indicators...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Current metrics (manual tracking)
    # TODO: Automate via Goodyear filings, state DOT reports
    latest_values = {
        'date': datetime.now().date(),
        'asphalt_pilot_count': 12,
        'goodyear_soy_volume': 90.0,
        'green_tire_growth': 12.0,
        'industrial_demand_index': 0.512,
        'updated_at': datetime.now()
    }
    
    # Insert to warehouse
    table_id = f"{PROJECT_ID}.forecasting_data_warehouse.industrial_demand_indicators"
    
    errors = client.insert_rows_json(table_id, [latest_values])
    
    if errors:
        logger.error(f"  ❌ Failed to update industrial demand: {errors}")
        return False
    else:
        logger.info(f"  ✅ Industrial demand updated: index={latest_values['industrial_demand_index']}")
        return True


def update_training_dataset():
    """
    Refresh training dataset with latest warehouse data
    Same UPDATE logic we used earlier
    """
    logger.info("Refreshing training dataset with latest data...")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Update China imports (monthly forward-fill)
    china_update = """
    UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
    SET 
      china_soybean_imports_mt = china.china_soybean_imports_mt,
      china_imports_from_us_mt = china.china_imports_from_us_mt
    FROM (
      SELECT 
        DATE_TRUNC(date, MONTH) as month_start,
        FIRST_VALUE(china_soybean_imports_mt) OVER (
          PARTITION BY DATE_TRUNC(date, MONTH) 
          ORDER BY date DESC
        ) as china_soybean_imports_mt,
        FIRST_VALUE(china_imports_from_us_mt) OVER (
          PARTITION BY DATE_TRUNC(date, MONTH) 
          ORDER BY date DESC
        ) as china_imports_from_us_mt
      FROM `cbi-v14.forecasting_data_warehouse.china_soybean_imports`
      QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, MONTH) ORDER BY date DESC) = 1
    ) china
    WHERE DATE_TRUNC(base.date, MONTH) = china.month_start
    """
    
    job = client.query(china_update)
    result = job.result()
    logger.info(f"  ✅ China imports updated in training dataset")
    
    # Update Argentina (weekly forward-fill)
    argentina_update = """
    UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
    SET 
      argentina_export_tax = argentina.argentina_export_tax,
      argentina_china_sales_mt = argentina.argentina_china_sales_mt,
      argentina_competitive_threat = argentina.argentina_competitive_threat
    FROM (
      SELECT 
        DATE_TRUNC(date, WEEK(MONDAY)) as week_start,
        FIRST_VALUE(argentina_export_tax) OVER (
          PARTITION BY DATE_TRUNC(date, WEEK(MONDAY))
          ORDER BY date DESC
        ) as argentina_export_tax,
        FIRST_VALUE(argentina_china_sales_mt) OVER (
          PARTITION BY DATE_TRUNC(date, WEEK(MONDAY))
          ORDER BY date DESC
        ) as argentina_china_sales_mt,
        FIRST_VALUE(argentina_competitive_threat) OVER (
          PARTITION BY DATE_TRUNC(date, WEEK(MONDAY))
          ORDER BY date DESC
        ) as argentina_competitive_threat
      FROM `cbi-v14.forecasting_data_warehouse.argentina_crisis_tracker`
      QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, WEEK(MONDAY)) ORDER BY date DESC) = 1
    ) argentina
    WHERE DATE_TRUNC(base.date, WEEK(MONDAY)) = argentina.week_start
    """
    
    job = client.query(argentina_update)
    result = job.result()
    logger.info(f"  ✅ Argentina data updated in training dataset")
    
    # Update Industrial (weekly forward-fill)
    industrial_update = """
    UPDATE `cbi-v14.models_v4.training_dataset_super_enriched` base
    SET industrial_demand_index = industrial.industrial_demand_index
    FROM (
      SELECT 
        DATE_TRUNC(date, WEEK(MONDAY)) as week_start,
        FIRST_VALUE(industrial_demand_index) OVER (
          PARTITION BY DATE_TRUNC(date, WEEK(MONDAY))
          ORDER BY date DESC
        ) as industrial_demand_index
      FROM `cbi-v14.forecasting_data_warehouse.industrial_demand_indicators`
      QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, WEEK(MONDAY)) ORDER BY date DESC) = 1
    ) industrial
    WHERE DATE_TRUNC(base.date, WEEK(MONDAY)) = industrial.week_start
    """
    
    job = client.query(industrial_update)
    result = job.result()
    logger.info(f"  ✅ Industrial demand updated in training dataset")
    
    return True


def main():
    """Weekly data update execution"""
    
    logger.info("="*80)
    logger.info("WEEKLY CRITICAL DATA UPDATE")
    logger.info(f"Run time: {datetime.now()}")
    logger.info("="*80)
    
    try:
        # Update warehouse tables
        china_ok = update_china_imports()
        argentina_ok = update_argentina_status()
        industrial_ok = update_industrial_demand()
        
        # Update training dataset
        if china_ok and argentina_ok and industrial_ok:
            dataset_ok = update_training_dataset()
            
            if dataset_ok:
                logger.info("\n✅ ALL UPDATES COMPLETE")
                return True
            else:
                logger.error("\n❌ Training dataset update failed")
                return False
        else:
            logger.error("\n❌ Warehouse updates failed")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ CRITICAL ERROR: {e}")
        # TODO: Send email alert
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)





