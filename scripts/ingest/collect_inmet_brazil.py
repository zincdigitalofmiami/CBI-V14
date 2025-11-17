#!/usr/bin/env python3
"""
INMET Brazil Weather Data Collection
====================================
Collects weather data from INMET (Brazilian National Institute of Meteorology)
Focus on major soybean production regions in Brazil
Temperature in CELSIUS (INMET native), saves to parquet
Date range: 2000-01-01 to today
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('inmet_collection.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
INMET_BASE_URL = "https://apitempo.inmet.gov.br/estacao"
# Start with recent data (last 30 days) for testing, then expand to full history
START_DATE = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
END_DATE = datetime.now().strftime("%Y-%m-%d")
# For full historical collection, use: START_DATE = "2000-01-01"

# External drive paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/inmet"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Priority weather stations in major soybean production regions
# Based on 35.5% global production concentration in Mato Grosso
STATIONS = {
    # Mato Grosso (Primary soybean region)
    'A901': {  # Sorriso
        'name': 'Sorriso',
        'state': 'Mato Grosso',
        'lat': -12.5446,
        'lon': -55.7125,
        'priority': 1,
        'production_weight': 0.355
    },
    'A923': {  # Sinop
        'name': 'Sinop',
        'state': 'Mato Grosso',
        'lat': -11.8653,
        'lon': -55.5058,
        'priority': 1,
        'production_weight': 0.152
    },
    'A936': {  # Alta Floresta
        'name': 'Alta Floresta',
        'state': 'Mato Grosso',
        'lat': -9.8709,
        'lon': -56.0862,
        'priority': 1,
        'production_weight': 0.128
    },
    # Mato Grosso do Sul
    'A702': {  # Campo Grande
        'name': 'Campo Grande',
        'state': 'MS',
        'lat': -20.4427,
        'lon': -54.6479,
        'priority': 2,
        'production_weight': 0.073
    },
    'A736': {  # Dourados
        'name': 'Dourados',
        'state': 'MS',
        'lat': -22.2192,
        'lon': -54.8055,
        'priority': 2,
        'production_weight': 0.108
    }
}

def safe_float(value):
    """Safely convert value to float, handling None and invalid values"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def fetch_station_data(station_id: str, station_info: dict) -> pd.DataFrame:
    """
    Fetch weather data for a specific INMET station.
    INMET API endpoint: /estacao/diaria/{start_date}/{end_date}/{station_id}
    """
    logger.info(f"Fetching {station_id}: {station_info['name']}, {station_info['state']}")
    
    start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    
    # INMET API can handle date ranges, but let's do it in chunks to be safe
    all_records = []
    current_date = start_date
    
    # Process in 1-year chunks
    while current_date < end_date:
        chunk_end = min(current_date + timedelta(days=365), end_date)
        
        try:
            # Use the correct INMET API endpoint format
            # Format: /estacao/{start}/{end}/{station_id}
            url = f"https://apitempo.inmet.gov.br/estacao/{current_date.strftime('%Y-%m-%d')}/{chunk_end.strftime('%Y-%m-%d')}/{station_id}"
            
            headers = {
                'User-Agent': 'CBI-V14-Weather-Collector/1.0',
                'Accept': 'application/json'
            }
            
            logger.info(f"  Fetching from: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    all_records.extend(data)
                    logger.info(f"  ✅ Fetched {len(data)} records for {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
                elif isinstance(data, dict) and 'data' in data:
                    records = data['data']
                    if isinstance(records, list) and len(records) > 0:
                        all_records.extend(records)
                        logger.info(f"  ✅ Fetched {len(records)} records for {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
                else:
                    logger.warning(f"  ⚠️  No data for {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")
            
            elif response.status_code == 404:
                logger.warning(f"  ⚠️  Station {station_id} not found or no data for date range")
                break
            
            else:
                logger.warning(f"  ⚠️  HTTP {response.status_code} for {station_id}")
            
            time.sleep(1)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            logger.error(f"  ❌ API request failed: {e}")
            break
        except Exception as e:
            logger.error(f"  ❌ Error processing data: {e}")
            break
        
        current_date = chunk_end + timedelta(days=1)
    
    if not all_records:
        logger.warning(f"  ⚠️  No data collected for {station_id}")
        return pd.DataFrame()
    
    # Process records into DataFrame
    processed_records = []
    
    for record in all_records:
        try:
            # Extract date from INMET format
            date_str = record.get('DT_MEDICAO', '')
            if not date_str:
                continue
            
            # Parse date (INMET format: 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD')
            try:
                record_date = pd.to_datetime(date_str).date()
            except:
                continue
            
            # Extract weather variables (INMET field names)
            precip_mm = safe_float(record.get('CHUVA', None))  # Precipitation in mm
            temp_max = safe_float(record.get('TEM_MAX', None))  # Max temperature in Celsius
            temp_min = safe_float(record.get('TEM_MIN', None))  # Min temperature in Celsius
            temp_avg = safe_float(record.get('TEM_INS', None))  # Instantaneous temp (can use as avg)
            
            # Skip records with no useful data
            if all(v is None for v in [precip_mm, temp_max, temp_min, temp_avg]):
                continue
            
            # Create standardized record
            processed_record = {
                'date': record_date,
                'station_id': f'INMET_{station_id}',
                'station_name': station_info['name'],
                'state': station_info['state'],
                'lat': station_info['lat'],
                'lon': station_info['lon'],
                'precip_mm': precip_mm,
                'temp_max_c': temp_max,  # Celsius (INMET native)
                'temp_min_c': temp_min,  # Celsius (INMET native)
                'temp_avg_c': temp_avg if temp_avg else ((temp_max + temp_min) / 2 if temp_max and temp_min else None),
                'region': 'Brazil',
                'production_weight': station_info['production_weight']
            }
            
            processed_records.append(processed_record)
            
        except Exception as e:
            logger.warning(f"  Failed to process record: {e}")
            continue
    
    if not processed_records:
        logger.warning(f"  ⚠️  No valid records processed for {station_id}")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(processed_records)
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    logger.info(f"  ✅ Processed {len(df)} records for {station_info['name']}")
    
    return df

def main():
    """Execute Brazil weather data collection from INMET"""
    logger.info("="*80)
    logger.info("INMET BRAZIL WEATHER DATA COLLECTION")
    logger.info("="*80)
    logger.info(f"Stations: {len(STATIONS)} (covering {sum(s['production_weight'] for s in STATIONS.values()):.1%} of Brazil soy production)")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info("="*80)
    
    all_data = []
    
    for station_id, station_info in STATIONS.items():
        try:
            df = fetch_station_data(station_id, station_info)
            
            if not df.empty:
                all_data.append(df)
                
                # Save individual station file
                station_file = RAW_DIR / f"{station_id}_{station_info['name'].replace(' ', '_')}.parquet"
                df.to_parquet(station_file, index=False)
                logger.info(f"  💾 Saved to {station_file.name}")
            
            time.sleep(2)  # Rate limiting between stations
            
        except Exception as e:
            logger.error(f"❌ Failed to collect {station_id}: {e}")
            continue
    
    if all_data:
        # Combine all stations
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save combined file
        combined_file = RAW_DIR / "brazil_weather_combined.parquet"
        combined_df.to_parquet(combined_file, index=False)
        
        logger.info("="*80)
        logger.info("COLLECTION SUMMARY")
        logger.info("="*80)
        logger.info(f"✅ Total records: {len(combined_df)}")
        logger.info(f"📅 Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
        logger.info(f"📍 Stations: {combined_df['station_id'].nunique()}")
        logger.info(f"💾 Saved to: {combined_file}")
        
        # Production-weighted averages
        total_weight = combined_df['production_weight'].sum()
        weighted_precip = (combined_df['precip_mm'] * combined_df['production_weight']).sum() / total_weight
        weighted_temp_max = (combined_df['temp_max_c'] * combined_df['production_weight']).sum() / total_weight
        weighted_temp_min = (combined_df['temp_min_c'] * combined_df['production_weight']).sum() / total_weight
        
        logger.info(f"\n🌾 PRODUCTION-WEIGHTED AVERAGES:")
        logger.info(f"  Precipitation: {weighted_precip:.1f} mm")
        logger.info(f"  Max Temperature: {weighted_temp_max:.1f}°C")
        logger.info(f"  Min Temperature: {weighted_temp_min:.1f}°C")
        
    else:
        logger.error("❌ No data collected from any stations")
        sys.exit(1)
    
    logger.info("="*80)
    logger.info("✅ INMET Brazil weather collection completed")
    logger.info("="*80)

if __name__ == "__main__":
    main()

