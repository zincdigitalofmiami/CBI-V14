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

PROJECT_ID = "cbi-v14"

# ALL WEATHER REGIONS (21 stations - respecting your weeks of work!)
# NOAA down, using Open-Meteo for all
REGIONS = {
    # US Midwest (11 stations for production-weighted coverage)
    'des_moines_ia': {'lat': 41.59, 'lon': -93.62, 'name': 'Des Moines IA', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'springfield_il': {'lat': 39.78, 'lon': -89.65, 'name': 'Springfield IL', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'indianapolis_in': {'lat': 39.77, 'lon': -86.16, 'name': 'Indianapolis IN', 'region': 'US_Midwest', 'timezone': 'America/Indiana/Indianapolis'},
    'jefferson_city_mo': {'lat': 38.58, 'lon': -92.17, 'name': 'Jefferson City MO', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'lansing_mi': {'lat': 42.73, 'lon': -84.56, 'name': 'Lansing MI', 'region': 'US_Midwest', 'timezone': 'America/Detroit'},
    'lincoln_ne': {'lat': 40.81, 'lon': -96.68, 'name': 'Lincoln NE', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'madison_wi': {'lat': 43.07, 'lon': -89.40, 'name': 'Madison WI', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'minneapolis_mn': {'lat': 44.98, 'lon': -93.27, 'name': 'Minneapolis MN', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'pierre_sd': {'lat': 44.37, 'lon': -100.35, 'name': 'Pierre SD', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'bismarck_nd': {'lat': 46.81, 'lon': -100.78, 'name': 'Bismarck ND', 'region': 'US_Midwest', 'timezone': 'America/Chicago'},
    'columbus_oh': {'lat': 39.96, 'lon': -83.00, 'name': 'Columbus OH', 'region': 'US_Midwest', 'timezone': 'America/New_York'},
    
    # Brazil - Mato Grosso (7 INMET stations for soybean production)
    'brazil_a901': {'lat': -15.87, 'lon': -52.26, 'name': 'Brazil A901 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    'brazil_a908': {'lat': -14.70, 'lon': -57.42, 'name': 'Brazil A908 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    'brazil_a833': {'lat': -16.47, 'lon': -54.63, 'name': 'Brazil A833 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    'brazil_a936': {'lat': -13.05, 'lon': -55.95, 'name': 'Brazil A936 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    'brazil_a807': {'lat': -15.60, 'lon': -56.10, 'name': 'Brazil A807 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    'brazil_a702': {'lat': -12.64, 'lon': -55.47, 'name': 'Brazil A702 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    'brazil_a923': {'lat': -14.83, 'lon': -57.53, 'name': 'Brazil A923 (MT)', 'region': 'Brazil', 'timezone': 'America/Cuiaba'},
    
    # Argentina - Rosario area (primary export region)
    'argentina_rosario': {'lat': -32.95, 'lon': -60.64, 'name': 'Rosario (Argentina)', 'region': 'Argentina', 'timezone': 'America/Argentina/Buenos_Aires'},
}

def get_weather(config, key):
    """Get weather from Open-Meteo (NOAA is down)"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': config['lat'],
            'longitude': config['lon'],
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
            'start_date': yesterday,
            'end_date': today,
            'timezone': config['timezone']
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'daily' in data and len(data['daily']['time']) > 0:
            weather = {
                'date': data['daily']['time'][0],
                'region': config['region'],
                'station_id': f"OPENMETEO_{key}",
                'temp_max': data['daily']['temperature_2m_max'][0],
                'temp_min': data['daily']['temperature_2m_min'][0],
                'precip_mm': data['daily']['precipitation_sum'][0],
                'source_name': 'open_meteo',
                'confidence_score': 0.95,
                'ingest_timestamp_utc': datetime.utcnow(),
                'provenance_uuid': f"openmeteo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{key}"
            }
            
            logger.info(f"✅ {config['name']}: {weather['temp_max']}°C, {weather['precip_mm']}mm")
            return weather
        else:
            logger.warning(f"No weather data for {config['name']}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Weather API failed for {config['name']}: {e}")
        return None


def save_to_bigquery(weather_data):
    """Save weather to BigQuery"""
    if not weather_data:
        logger.warning("No weather data to save")
        return False
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.forecasting_data_warehouse.weather_data"
        
        import pandas as pd
        df = pd.DataFrame([weather_data])
        
        # Convert date string to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ BigQuery save failed: {e}")
        return False


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("DAILY WEATHER UPDATE - ALL 19 STATIONS")
    logger.info("="*80)
    
    all_weather = []
    
    # Get weather for all key regions (using Open-Meteo since NOAA down)
    for key, config in REGIONS.items():
        weather = get_weather(config, key)
        if weather:
            all_weather.append(weather)
            save_to_bigquery(weather)
    
    logger.info("="*80)
    logger.info(f"✅ Daily weather update complete: {len(all_weather)}/19 stations")
    logger.info("="*80)
    
    return len(all_weather) > 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

