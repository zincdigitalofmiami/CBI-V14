#!/usr/bin/env python3
"""
Comprehensive Weather Data Collection from Google BigQuery
===========================================================
Collects weather data for US Midwest, Brazil, and Argentina
from Google BigQuery public dataset: bigquery-public-data.noaa_gsod
Temperature in FAHRENHEIT for US, CELSIUS for Brazil/Argentina
Saves to external drive in parquet format
Date range: 2000-01-01 to present
"""

from google.cloud import bigquery
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CLIENT = bigquery.Client(project='cbi-v14')
START_DATE = "2000-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

# External drive paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/weather"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Define regions and their key agricultural areas
REGIONS = {
    'US_MIDWEST': {
        'country': 'US',
        'states': ['IA', 'IL', 'IN', 'MN', 'MO', 'NE', 'OH', 'SD', 'WI', 'KS', 'ND'],
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inches',
        'production_weight': 0.30  # US produces ~30% of global soybeans
    },
    'BRAZIL': {
        'country': 'BR',
        'states': ['MT', 'MS', 'RS', 'PR', 'GO', 'SP', 'MG', 'BA', 'SC', 'TO'],
        'temperature_unit': 'celsius',
        'precipitation_unit': 'mm',
        'production_weight': 0.40  # Brazil produces ~40% of global soybeans
    },
    'ARGENTINA': {
        'country': 'AR',
        'states': None,  # Argentina doesn't use state codes in NOAA data
        'temperature_unit': 'celsius',
        'precipitation_unit': 'mm',
        'production_weight': 0.15  # Argentina produces ~15% of global soybeans
    }
}

def fahrenheit_to_celsius(f):
    """Convert Fahrenheit to Celsius"""
    if f is None or pd.isna(f) or f == 9999.9:
        return None
    return (f - 32) * 5/9

def inches_to_mm(inches):
    """Convert inches to millimeters"""
    if inches is None or pd.isna(inches) or inches == 99.99:
        return None
    return inches * 25.4

def collect_regional_weather(region_name, region_config):
    """
    Collect weather data for a specific region from BigQuery
    """
    logger.info(f"Collecting weather for {region_name}...")
    
    # Build the WHERE clause for the query
    where_conditions = [f"country = '{region_config['country']}'"]
    if region_config['states']:
        states_str = "', '".join(region_config['states'])
        where_conditions.append(f"state IN ('{states_str}')")
    
    where_clause = " AND ".join(where_conditions)
    
    # Query to get weather data
    query = f"""
    WITH regional_stations AS (
        SELECT DISTINCT
            usaf,
            wban,
            name,
            country,
            state,
            lat,
            lon
        FROM `bigquery-public-data.noaa_gsod.stations`
        WHERE {where_clause}
            AND lat IS NOT NULL
            AND lon IS NOT NULL
            AND end > '2000-01-01'  -- Station should have recent data
    ),
    weather_data AS (
        SELECT 
            s.usaf,
            s.name as station_name,
            s.state,
            s.lat,
            s.lon,
            w.date,
            w.year,
            w.temp,  -- Mean temperature (Fahrenheit)
            w.max,   -- Max temperature (Fahrenheit)
            w.min,   -- Min temperature (Fahrenheit)
            w.prcp,  -- Precipitation (inches)
            w.dewp,  -- Dew point (Fahrenheit)
            w.slp,   -- Sea level pressure
            w.stp,   -- Station pressure
            w.visib, -- Visibility
            w.wdsp,  -- Wind speed
            w.gust,  -- Wind gust
            w.sndp   -- Snow depth
        FROM regional_stations s
        JOIN `bigquery-public-data.noaa_gsod.gsod*` w
        ON s.usaf = w.stn
        WHERE DATE(PARSE_DATE('%Y', CAST(w.year AS STRING))) >= DATE('{START_DATE}')
            AND w.date BETWEEN DATE('{START_DATE}') AND DATE('{END_DATE}')
            AND w.temp != 9999.9  -- Filter out missing values
    )
    SELECT *
    FROM weather_data
    ORDER BY date, usaf
    """
    
    try:
        # Execute query
        logger.info(f"  Querying BigQuery...")
        df = CLIENT.query(query).to_dataframe()
        
        if df.empty:
            logger.warning(f"  No data returned for {region_name}")
            return None
        
        logger.info(f"  Retrieved {len(df)} records for {region_name}")
        logger.info(f"  Stations: {df['usaf'].nunique()}")
        logger.info(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Add region metadata
        df['region'] = region_name
        df['station_id'] = df['usaf'].astype(str)
        
        # Handle temperature conversions
        if region_config['temperature_unit'] == 'celsius':
            logger.info(f"  Converting temperatures to Celsius...")
            df['temp_c'] = df['temp'].apply(fahrenheit_to_celsius)
            df['temp_max_c'] = df['max'].apply(fahrenheit_to_celsius)
            df['temp_min_c'] = df['min'].apply(fahrenheit_to_celsius)
            df['dew_point_c'] = df['dewp'].apply(fahrenheit_to_celsius)
            
            # Keep Fahrenheit columns for reference
            df.rename(columns={
                'temp': 'temp_f',
                'max': 'temp_max_f',
                'min': 'temp_min_f',
                'dewp': 'dew_point_f'
            }, inplace=True)
        else:
            # US Midwest - keep in Fahrenheit
            df.rename(columns={
                'temp': 'temp_f',
                'max': 'temp_max_f',
                'min': 'temp_min_f',
                'dewp': 'dew_point_f'
            }, inplace=True)
        
        # Handle precipitation conversions
        if region_config['precipitation_unit'] == 'mm':
            logger.info(f"  Converting precipitation to mm...")
            df['precipitation_mm'] = df['prcp'].apply(inches_to_mm)
            df['snow_depth_mm'] = df['sndp'].apply(inches_to_mm)
            
            # Keep inches columns for reference
            df.rename(columns={
                'prcp': 'precipitation_inches',
                'sndp': 'snow_depth_inches'
            }, inplace=True)
        else:
            # US - keep in inches
            df.rename(columns={
                'prcp': 'precipitation_inches',
                'sndp': 'snow_depth_inches'
            }, inplace=True)
        
        # Add production weight
        df['production_weight'] = region_config['production_weight']
        
        # Clean up columns
        df = df.drop(columns=['year'], errors='ignore')
        
        # Filter out extreme outliers (data quality)
        if 'temp_f' in df.columns:
            df = df[(df['temp_f'] > -100) & (df['temp_f'] < 150)]
        
        return df
        
    except Exception as e:
        logger.error(f"  Error collecting {region_name} weather: {e}")
        return None

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("COMPREHENSIVE WEATHER DATA COLLECTION FROM BIGQUERY")
    logger.info("="*80)
    logger.info("Source: Google BigQuery public dataset (bigquery-public-data.noaa_gsod)")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info("Regions: US Midwest, Brazil, Argentina")
    logger.info("="*80)
    
    all_data = []
    success_regions = []
    
    # Collect data for each region
    for region_name, region_config in REGIONS.items():
        logger.info(f"\n{'='*40}")
        logger.info(f"Processing {region_name}")
        logger.info(f"{'='*40}")
        
        df = collect_regional_weather(region_name, region_config)
        
        if df is not None and not df.empty:
            all_data.append(df)
            success_regions.append(region_name)
            
            # Save regional file
            regional_file = RAW_DIR / f"{region_name.lower()}_weather.parquet"
            df.to_parquet(regional_file, index=False)
            logger.info(f"  ✅ Saved to {regional_file.name}")
    
    if not all_data:
        logger.error("\n❌ No weather data collected for any region!")
        return 1
    
    # Combine all regions
    logger.info("\n" + "="*80)
    logger.info("Combining all regions...")
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Save combined file
    combined_file = RAW_DIR / "global_weather_combined.parquet"
    combined_df.to_parquet(combined_file, index=False)
    
    # Summary statistics
    logger.info("="*80)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Successful regions: {', '.join(success_regions)}")
    logger.info(f"📊 Total records: {len(combined_df):,}")
    logger.info(f"📅 Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    logger.info(f"🌍 Countries: {combined_df.groupby('region')['station_id'].nunique().to_dict()}")
    logger.info(f"💾 Output directory: {RAW_DIR}")
    
    # Regional summaries
    for region in success_regions:
        region_data = combined_df[combined_df['region'] == region]
        logger.info(f"\n{region}:")
        logger.info(f"  Records: {len(region_data):,}")
        logger.info(f"  Stations: {region_data['station_id'].nunique()}")
        
        if 'temp_c' in region_data.columns:
            temp_col = 'temp_c'
            unit = '°C'
        else:
            temp_col = 'temp_f'
            unit = '°F'
        
        logger.info(f"  Avg temperature: {region_data[temp_col].mean():.1f}{unit}")
        
        if 'precipitation_mm' in region_data.columns:
            precip_col = 'precipitation_mm'
            unit = 'mm'
        else:
            precip_col = 'precipitation_inches'
            unit = 'inches'
        
        monthly_precip = region_data.groupby(pd.Grouper(key='date', freq='M'))[precip_col].sum().mean()
        logger.info(f"  Avg monthly precipitation: {monthly_precip:.1f} {unit}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ WEATHER COLLECTION COMPLETE!")
    logger.info(f"✅ All data saved to: {RAW_DIR}")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
