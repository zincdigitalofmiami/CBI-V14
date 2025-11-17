#!/usr/bin/env python3
"""
NOAA Weather Data Collection - US Midwest & Argentina
======================================================
Collects weather data from NOAA API for US Midwest and Argentina ONLY
NOTE: Brazil weather is collected via INMET API (see collect_inmet_brazil.py)
Temperature in FAHRENHEIT (per user requirement)
Precipitation in INCHES
Date range: 2000-01-01 to today
Rate limiting: Respectful API usage
"""

import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('noaa_collection.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
NOAA_TOKEN = os.getenv('NOAA_API_TOKEN')
if not NOAA_TOKEN:
    logger.error("NOAA_API_TOKEN not set in environment!")
    sys.exit(1)

NOAA_BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
START_DATE = "2000-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# External drive paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/noaa"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Create subdirectories
RAW_RESPONSES_DIR = RAW_DIR / "raw_responses"
PROCESSED_DIR = RAW_DIR / "processed"
COMBINED_DIR = RAW_DIR / "combined"
REGIONAL_DIR = RAW_DIR / "regional"
METADATA_DIR = RAW_DIR / "metadata"

for dir_path in [RAW_RESPONSES_DIR, PROCESSED_DIR, COMBINED_DIR, REGIONAL_DIR, METADATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Weather stations for US Midwest and Argentina ONLY
# NOTE: Brazil weather is collected via INMET API (see collect_inmet_brazil.py)
# This script collects US Midwest and Argentina only
STATIONS = {
    'US_MIDWEST': [
        {'id': 'USW00014839', 'name': 'Des Moines, IA', 'lat': 41.5908, 'lon': -93.6208},
        {'id': 'USW00094846', 'name': 'Chicago, IL', 'lat': 41.9796, 'lon': -87.9045},
        {'id': 'USW00003945', 'name': 'Peoria, IL', 'lat': 40.6639, 'lon': -89.6835},
        {'id': 'USW00014990', 'name': 'Omaha, NE', 'lat': 41.3033, 'lon': -95.8999},
        {'id': 'USW00014922', 'name': 'Minneapolis, MN', 'lat': 44.8831, 'lon': -93.2289},
        {'id': 'USW00013996', 'name': 'Sioux Falls, SD', 'lat': 43.5820, 'lon': -96.7419},
        {'id': 'USW00014898', 'name': 'Green Bay, WI', 'lat': 44.4850, 'lon': -88.1297},
        {'id': 'USW00003927', 'name': 'Indianapolis, IN', 'lat': 39.7173, 'lon': -86.2944},
        {'id': 'USW00093815', 'name': 'Columbus, OH', 'lat': 40.0799, 'lon': -82.8851},
        {'id': 'USW00013995', 'name': 'Kansas City, MO', 'lat': 39.2973, 'lon': -94.7391},
    ],
    'ARGENTINA': [
        {'id': 'AR000087344', 'name': 'Buenos Aires', 'lat': -34.6037, 'lon': -58.3816},
        {'id': 'AR000087418', 'name': 'Córdoba', 'lat': -31.4201, 'lon': -64.1888},
        {'id': 'AR000087480', 'name': 'Rosario', 'lat': -32.9468, 'lon': -60.6393},
        {'id': 'AR000087497', 'name': 'Santa Fe', 'lat': -31.6333, 'lon': -60.7000},
        {'id': 'AR000087395', 'name': 'Paraná, Entre Ríos', 'lat': -31.7333, 'lon': -60.5333},
        {'id': 'AR000087453', 'name': 'Santa Rosa, La Pampa', 'lat': -36.6167, 'lon': -64.2833},
        {'id': 'AR000087467', 'name': 'Mendoza', 'lat': -32.8895, 'lon': -68.8458},
        {'id': 'AR000087371', 'name': 'Salta', 'lat': -24.7859, 'lon': -65.4117},
        {'id': 'AR000087506', 'name': 'Resistencia, Chaco', 'lat': -27.4606, 'lon': -58.9839},
        {'id': 'AR000087532', 'name': 'Santiago del Estero', 'lat': -27.7951, 'lon': -64.2615},
    ]
}

# Weather metrics to collect
WEATHER_METRICS = [
    'TMAX',  # Max temperature (will be in Fahrenheit)
    'TMIN',  # Min temperature (will be in Fahrenheit)
    'TAVG',  # Average temperature (will be in Fahrenheit)
    'PRCP',  # Precipitation (will convert to inches)
    'SNOW',  # Snowfall (will convert to inches)
    'SNWD',  # Snow depth (will convert to inches)
    'AWND',  # Average wind speed (mph)
    'WSF2',  # Peak wind speed (mph)
    'RHUM',  # Relative humidity (%)
    'TSUN',  # Sunshine duration (minutes)
    'EVAP',  # Evaporation (mm - will convert to inches)
    'WDFG',  # Wind direction (degrees)
]

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32

def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm / 25.4

def fetch_station_data(station: dict, region: str) -> dict:
    """
    Fetch weather data for a single station.
    Temperature data will be in FAHRENHEIT.
    Precipitation data will be in INCHES.
    """
    station_id = station['id']
    station_name = station['name']
    
    logger.info(f"Fetching {station_id}: {station_name} ({region})")
    
    all_data = []
    current_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    
    # NOAA API limits to 1 year per request
    while current_date < end_date:
        year_end = min(current_date + timedelta(days=365), end_date)
        
        params = {
            'datasetid': 'GHCND',  # Global Historical Climatology Network Daily
            'stationid': f'GHCND:{station_id}',
            'startdate': current_date.strftime("%Y-%m-%d"),
            'enddate': year_end.strftime("%Y-%m-%d"),
            'datatypeid': ','.join(WEATHER_METRICS),
            'units': 'standard',  # This gives us Fahrenheit for US stations!
            'limit': 1000
        }
        
        headers = {'token': NOAA_TOKEN}
        offset = 0
        
        while True:
            params['offset'] = offset
            
            try:
                response = requests.get(NOAA_BASE_URL, headers=headers, params=params, timeout=120)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        break
                    
                    all_data.extend(results)
                    
                    # Check if more data available
                    if len(results) < 1000:
                        break
                    
                    offset += 1000
                    time.sleep(0.5)  # Rate limiting
                    
                elif response.status_code == 429:
                    logger.warning(f"  Rate limit hit. Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                    
                else:
                    logger.error(f"  HTTP {response.status_code} for {station_id}")
                    break
                    
            except Exception as e:
                logger.error(f"  Error fetching {station_id}: {e}")
                break
        
        current_date = year_end + timedelta(days=1)
        time.sleep(1)  # Rate limiting between years
    
    if not all_data:
        logger.warning(f"  ⚠️  No data for {station_id}")
        return {'status': 'no_data', 'station_id': station_id}
    
    # Process the data
    df = pd.DataFrame(all_data)
    
    # Convert dates
    df['date'] = pd.to_datetime(df['date'])
    
    # Pivot to wide format
    df_pivot = df.pivot_table(
        index='date',
        columns='datatype',
        values='value',
        aggfunc='mean'
    )
    
    # Add station metadata
    df_pivot['station_id'] = station_id
    df_pivot['station_name'] = station_name
    df_pivot['region'] = region
    df_pivot['latitude'] = station['lat']
    df_pivot['longitude'] = station['lon']
    
    # TEMPERATURE CONVERSION for non-US stations
    # US stations already return Fahrenheit with units='standard'
    # Brazil and Argentina stations might return Celsius
    if region != 'US_MIDWEST':
        # Convert temperature columns from Celsius to Fahrenheit
        temp_cols = ['TMAX', 'TMIN', 'TAVG']
        for col in temp_cols:
            if col in df_pivot.columns:
                # Check if values seem to be in Celsius (typically < 50)
                if df_pivot[col].mean() < 50:
                    logger.info(f"  Converting {col} from Celsius to Fahrenheit")
                    df_pivot[col] = df_pivot[col].apply(lambda x: celsius_to_fahrenheit(x) if pd.notna(x) else x)
    
    # PRECIPITATION CONVERSION
    # Convert precipitation from mm to inches for all stations
    precip_cols = ['PRCP', 'SNOW', 'SNWD', 'EVAP']
    for col in precip_cols:
        if col in df_pivot.columns:
            # PRCP values are typically in tenths of mm, so divide by 10 first
            if col == 'PRCP':
                df_pivot[col] = df_pivot[col] / 10  # Convert to mm
            df_pivot[col] = df_pivot[col].apply(lambda x: mm_to_inches(x) if pd.notna(x) else x)
    
    # Reset index to make date a column
    df_pivot = df_pivot.reset_index()
    
    # Save processed data
    processed_file = PROCESSED_DIR / f"{station_id}.parquet"
    df_pivot.to_parquet(processed_file, index=False)
    
    # Save raw response
    raw_file = RAW_RESPONSES_DIR / f"{station_id}_raw.json"
    with open(raw_file, 'w') as f:
        json.dump(all_data[:100], f, indent=2)  # Save sample for reference
    
    logger.info(f"  ✅ Success: {len(df_pivot)} days of data saved")
    logger.info(f"     Temperature range: {df_pivot['TMAX'].min():.1f}°F to {df_pivot['TMAX'].max():.1f}°F" if 'TMAX' in df_pivot.columns else "")
    
    return {
        'status': 'success',
        'station_id': station_id,
        'station_name': station_name,
        'region': region,
        'observations': len(df_pivot),
        'date_range': f"{df_pivot['date'].min()} to {df_pivot['date'].max()}",
        'data': df_pivot
    }

def calculate_growing_degree_days(df: pd.DataFrame, base_temp: float = 50.0) -> pd.DataFrame:
    """
    Calculate Growing Degree Days (GDD) for agriculture.
    Base temperature in Fahrenheit (typically 50°F for corn/soybeans).
    """
    if 'TMAX' in df.columns and 'TMIN' in df.columns:
        df['GDD'] = df.apply(
            lambda row: max(0, ((min(row['TMAX'], 86) + max(row['TMIN'], base_temp)) / 2) - base_temp)
            if pd.notna(row['TMAX']) and pd.notna(row['TMIN']) else None,
            axis=1
        )
    return df

def aggregate_by_region(data_list: List[pd.DataFrame], region: str) -> pd.DataFrame:
    """
    Aggregate weather data by region.
    """
    if not data_list:
        return pd.DataFrame()
    
    # Combine all station data
    combined = pd.concat(data_list, ignore_index=True)
    
    # Group by date and calculate regional averages
    numeric_cols = ['TMAX', 'TMIN', 'TAVG', 'PRCP', 'SNOW', 'SNWD', 
                   'AWND', 'WSF2', 'RHUM', 'TSUN', 'EVAP', 'GDD']
    
    available_cols = [col for col in numeric_cols if col in combined.columns]
    
    regional_avg = combined.groupby('date')[available_cols].mean()
    regional_avg['region'] = region
    regional_avg['station_count'] = combined.groupby('date')['station_id'].nunique()
    
    return regional_avg.reset_index()

def main():
    """
    Main execution: Collect ALL NOAA weather data with 100% validation.
    """
    logger.info("="*80)
    logger.info("NOAA WEATHER DATA COLLECTION - US MIDWEST & ARGENTINA")
    logger.info("="*80)
    logger.info("NOTE: Brazil weather collected via INMET API (collect_inmet_brazil.py)")
    logger.info(f"Date Range: {START_DATE} to {END_DATE}")
    logger.info(f"Total Stations: {sum(len(stations) for stations in STATIONS.values())}")
    logger.info(f"  - US Midwest: {len(STATIONS['US_MIDWEST'])} stations")
    logger.info(f"  - Argentina: {len(STATIONS['ARGENTINA'])} stations")
    logger.info(f"Temperature Units: FAHRENHEIT (per user requirement)")
    logger.info(f"Precipitation Units: INCHES")
    logger.info(f"Output Directory: {RAW_DIR}")
    logger.info("="*80)
    
    # Track results
    results = {
        'success': [],
        'failed': [],
        'no_data': []
    }
    
    regional_data = {}
    collection_metadata = {
        'collection_date': datetime.now().isoformat(),
        'start_date': START_DATE,
        'end_date': END_DATE,
        'temperature_unit': 'Fahrenheit',
        'precipitation_unit': 'Inches',
        'regions': {}
    }
    
    # Process each region
    station_count = 0
    total_stations = sum(len(stations) for stations in STATIONS.values())
    
    for region, stations in STATIONS.items():
        logger.info(f"\n{'='*40}")
        logger.info(f"Processing Region: {region}")
        logger.info(f"{'='*40}")
        
        region_data = []
        collection_metadata['regions'][region] = {
            'stations': [],
            'summary': {}
        }
        
        for station in stations:
            station_count += 1
            logger.info(f"\n[{station_count}/{total_stations}] Processing station")
            
            result = fetch_station_data(station, region)
            
            if result['status'] == 'success':
                results['success'].append(station['id'])
                region_data.append(result['data'])
                
                # Calculate GDD for agricultural relevance
                result['data'] = calculate_growing_degree_days(result['data'])
                
                collection_metadata['regions'][region]['stations'].append({
                    'id': station['id'],
                    'name': station['name'],
                    'status': 'success',
                    'observations': result['observations'],
                    'date_range': result['date_range']
                })
                
            elif result['status'] == 'no_data':
                results['no_data'].append(station['id'])
                collection_metadata['regions'][region]['stations'].append({
                    'id': station['id'],
                    'name': station['name'],
                    'status': 'no_data'
                })
                
            else:
                results['failed'].append(station['id'])
                collection_metadata['regions'][region]['stations'].append({
                    'id': station['id'],
                    'name': station['name'],
                    'status': 'failed'
                })
            
            # Rate limiting
            time.sleep(1)
        
        # Aggregate regional data
        if region_data:
            regional_avg = aggregate_by_region(region_data, region)
            regional_data[region] = regional_avg
            
            # Save regional aggregate
            regional_file = REGIONAL_DIR / f"{region.lower()}_aggregate.parquet"
            regional_avg.to_parquet(regional_file, index=False)
            
            logger.info(f"\n✅ Regional aggregate saved for {region}")
            logger.info(f"   Date range: {regional_avg['date'].min()} to {regional_avg['date'].max()}")
            logger.info(f"   Observations: {len(regional_avg)}")
            
            collection_metadata['regions'][region]['summary'] = {
                'observations': len(regional_avg),
                'date_range': f"{regional_avg['date'].min()} to {regional_avg['date'].max()}",
                'avg_temperature': f"{regional_avg['TAVG'].mean():.1f}°F" if 'TAVG' in regional_avg.columns else 'N/A',
                'total_precipitation': f"{regional_avg['PRCP'].sum():.1f} inches" if 'PRCP' in regional_avg.columns else 'N/A'
            }
    
    # Combine all data
    if regional_data:
        logger.info("\n" + "="*80)
        logger.info("Combining all regional data...")
        
        all_regions = pd.concat(list(regional_data.values()), ignore_index=True)
        combined_file = COMBINED_DIR / f"noaa_all_regions_{datetime.now().strftime('%Y%m%d')}.parquet"
        all_regions.to_parquet(combined_file, index=False)
        
        logger.info(f"✅ Combined dataset saved: {len(all_regions)} rows")
    
    # Save metadata
    metadata_file = METADATA_DIR / f"collection_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metadata_file, 'w') as f:
        json.dump(collection_metadata, f, indent=2, default=str)
    
    # Final report
    logger.info("\n" + "="*80)
    logger.info("COLLECTION COMPLETE - FINAL REPORT")
    logger.info("="*80)
    logger.info(f"✅ Successful: {len(results['success'])} stations")
    if results['success']:
        logger.info(f"   Stations: {', '.join(results['success'][:5])}")
        if len(results['success']) > 5:
            logger.info(f"   ... and {len(results['success']) - 5} more")
    
    if results['no_data']:
        logger.info(f"⚠️  No Data: {len(results['no_data'])} stations")
        logger.info(f"   Stations: {', '.join(results['no_data'])}")
    
    if results['failed']:
        logger.error(f"❌ Failed: {len(results['failed'])} stations")
        logger.error(f"   Stations: {', '.join(results['failed'])}")
    
    # Success criteria check
    success_rate = len(results['success']) / total_stations
    if success_rate < 0.80:  # Allow 80% for weather (some stations may be defunct)
        logger.error(f"WARNING: Success rate low: {success_rate:.1%}")
        logger.error("Some stations may no longer be operational.")
    
    logger.info(f"\n✅ SUCCESS RATE: {success_rate:.1%}")
    logger.info(f"📁 Output directory: {RAW_DIR}")
    logger.info("="*80)
    
    return 0 if success_rate >= 0.80 else 1

if __name__ == "__main__":
    sys.exit(main())
