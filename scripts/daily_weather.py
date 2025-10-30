#!/usr/bin/env python3
"""
PHASE 3: Daily Weather Updates
Pulls from NOAA + INMET Brazil
"""

import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/zincdigital/CBI-V14/logs/weather.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

NOAA_TOKEN = "rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi"
PROJECT_ID = "cbi-v14"

# Key production regions
REGIONS = {
    'noaa_iowa': {
        'station': 'GHCND:USC00134101',  # Des Moines
        'name': 'Iowa'
    },
    'noaa_argentina': {
        'station': 'GHCND:AR000875852',  # Rosario area
        'name': 'Argentina'
    }
}

def get_noaa_weather(station_id, region_name):
    """Get weather from NOAA"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = f"https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
        params = {
            'datasetid': 'GHCND',
            'stationid': station_id,
            'startdate': yesterday,
            'enddate': yesterday,
            'datatypeid': ['TMAX', 'TMIN', 'PRCP'],
            'units': 'metric'
        }
        headers = {'token': NOAA_TOKEN}
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        data = response.json()
        
        if 'results' in data:
            weather = {
                'date': yesterday,
                'region': region_name,
                'temp_max_c': None,
                'temp_min_c': None,
                'precipitation_mm': None,
                'humidity_pct': None,
                'source': 'noaa',
                'ingest_timestamp': datetime.now()
            }
            
            for result in data['results']:
                if result['datatype'] == 'TMAX':
                    weather['temp_max_c'] = result['value']
                elif result['datatype'] == 'TMIN':
                    weather['temp_min_c'] = result['value']
                elif result['datatype'] == 'PRCP':
                    weather['precipitation_mm'] = result['value']
            
            logger.info(f"✅ {region_name}: {weather['temp_max_c']}°C, {weather['precipitation_mm']}mm")
            return weather
        else:
            logger.warning(f"No NOAA data for {region_name}")
            return None
            
    except Exception as e:
        logger.error(f"❌ NOAA failed for {region_name}: {e}")
        return None


def get_inmet_brazil():
    """Get weather from INMET Brazil (Mato Grosso)"""
    try:
        # INMET API endpoint for Mato Grosso region
        url = "https://apitempo.inmet.gov.br/estacao/dados/"
        # Note: INMET requires station code - placeholder for now
        logger.warning("⚠️  INMET Brazil integration pending - need station codes")
        return None
        
    except Exception as e:
        logger.error(f"❌ INMET failed: {e}")
        return None


def save_to_bigquery(weather_data):
    """Save weather to BigQuery"""
    if not weather_data:
        logger.warning("No weather data to save")
        return False
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.weather.daily_updates"
        
        import pandas as pd
        df = pd.DataFrame([weather_data])
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        logger.info(f"✅ Saved weather to {table_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery save failed: {e}")
        return False


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("DAILY WEATHER UPDATE")
    logger.info("="*80)
    
    all_weather = []
    
    # Get NOAA weather for key regions
    for key, config in REGIONS.items():
        weather = get_noaa_weather(config['station'], config['name'])
        if weather:
            all_weather.append(weather)
    
    # Get INMET Brazil
    brazil_weather = get_inmet_brazil()
    if brazil_weather:
        all_weather.append(brazil_weather)
    
    # Save to BigQuery
    for weather in all_weather:
        save_to_bigquery(weather)
    
    logger.info("="*80)
    logger.info(f"✅ Daily weather update complete: {len(all_weather)} regions")
    logger.info("="*80)
    
    return len(all_weather) > 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

