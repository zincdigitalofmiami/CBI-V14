#!/usr/bin/env python3
"""
PHASE 3: Daily Signal Calculations
Calculate Chris's Big 4 signals from latest data
"""

from google.cloud import bigquery
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/signals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def calculate_vix_stress():
    """Calculate VIX stress signal"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = """
        SELECT 
            CASE 
                WHEN close_price > 30 THEN 1.0
                WHEN close_price > 20 THEN 0.5
                ELSE 0.0
            END as vix_stress_score
        FROM `cbi-v14.forecasting_data_warehouse.vix_daily`
        ORDER BY date DESC
        LIMIT 1
        """
        
        result = client.query(query).to_dataframe()
        score = float(result['vix_stress_score'].iloc[0])
        
        logger.info(f"✅ VIX Stress: {score}")
        return score
        
    except Exception as e:
        logger.error(f"❌ VIX stress calculation failed: {e}")
        return 0.0


def calculate_harvest_pace():
    """Calculate harvest pace signal"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = """
        SELECT 
            AVG(CAST(brazil_harvest_signals as FLOAT64) + 
                CAST(argentina_harvest_signals as FLOAT64)) / 2 as harvest_pace
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 7
        """
        
        result = client.query(query).to_dataframe()
        score = float(result['harvest_pace'].iloc[0])
        
        logger.info(f"✅ Harvest Pace: {score:.2f}")
        return score
        
    except Exception as e:
        logger.error(f"❌ Harvest pace calculation failed: {e}")
        return 0.0


def calculate_china_relations():
    """Calculate China relations signal"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = """
        SELECT china_weighted_score
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
        """
        
        result = client.query(query).to_dataframe()
        score = float(result['china_weighted_score'].iloc[0])
        
        logger.info(f"✅ China Relations: {score:.2f}")
        return score
        
    except Exception as e:
        logger.error(f"❌ China relations calculation failed: {e}")
        return 0.0


def calculate_tariff_threat():
    """Calculate tariff threat signal"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        query = """
        SELECT tariff_weighted_score
        FROM `cbi-v14.models.training_dataset`
        ORDER BY date DESC
        LIMIT 1
        """
        
        result = client.query(query).to_dataframe()
        score = float(result['tariff_weighted_score'].iloc[0])
        
        logger.info(f"✅ Tariff Threat: {score:.2f}")
        return score
        
    except Exception as e:
        logger.error(f"❌ Tariff threat calculation failed: {e}")
        return 0.0


def save_signals(vix, harvest, china, tariff):
    """Save calculated signals to BigQuery"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.signals.daily_calculations"
        
        import pandas as pd
        df = pd.DataFrame([{
            'date': datetime.now().date(),
            'vix_stress_score': vix,
            'harvest_pace_score': harvest,
            'china_relations_score': china,
            'tariff_threat_score': tariff,
            'calculated_timestamp': datetime.now()
        }])
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Saved signals to {table_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery save failed: {e}")
        return False


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("DAILY SIGNAL CALCULATION")
    logger.info("="*80)
    
    # Calculate all signals
    vix = calculate_vix_stress()
    harvest = calculate_harvest_pace()
    china = calculate_china_relations()
    tariff = calculate_tariff_threat()
    
    # Save to BigQuery
    success = save_signals(vix, harvest, china, tariff)
    
    logger.info("="*80)
    logger.info(f"✅ Daily signals complete")
    logger.info("="*80)
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

