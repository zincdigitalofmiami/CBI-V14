#!/usr/bin/env python3
"""
Production Weather Data Collection
===================================
Uses institutional-grade, verified sources for weather data:
1. NOAA GHCN-D (BigQuery) - Primary for all regions
2. INMET API - Brazil specific
3. SMN API - Argentina specific
4. NASA POWER - Backup for missing data
5. NOAA GFS - Forecasts

Date range: 2000-01-01 to present
Output: TrainingData/staging/weather_2000_2025.parquet
"""

from google.cloud import bigquery
import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json
import time
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
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# Region definitions with production weights
REGIONS = {
    'US_MIDWEST': {
        'states': ['IA', 'IL', 'IN', 'MN', 'OH', 'NE', 'KS', 'SD', 'WI', 'MO'],
        'production_weight': 0.30,
        'bbox': (-100, 25, -80, 50),  # (west, south, east, north)
    },
    'BRAZIL': {
        'country': 'BR',
        'states': ['MT', 'MS', 'RS', 'PR', 'GO'],  # Key soybean states
        'production_weight': 0.40,
        'bbox': (-60, -35, -35, 5),
        'key_cities': ['Cuiabá', 'Sinop', 'Sorriso', 'Campo Grande', 'Dourados']
    },
    'ARGENTINA': {
        'country': 'AR',
        'production_weight': 0.15,
        'bbox': (-75, -55, -50, -20),
        'key_stations': ['87576', '87576', '87418']  # Rosario, Buenos Aires, Córdoba
    }
}

def collect_noaa_ghcnd_all_regions():
    """
    Collect weather data from NOAA GHCN-D via BigQuery for all regions.
    This is the PRIMARY source for historical daily weather data.
    """
    logger.info("="*80)
    logger.info("COLLECTING NOAA GHCN-D DATA (PRIMARY SOURCE)")
    logger.info("="*80)
    
    # Build comprehensive query for all regions
    query = f"""
    WITH station_selection AS (
        SELECT DISTINCT
            id as station_id,
            latitude,
            longitude,
            elevation,
            state,
            name,
            CASE
                WHEN state IN ('IA', 'IL', 'IN', 'MN', 'OH', 'NE', 'KS', 'SD', 'WI', 'MO') THEN 'US_MIDWEST'
                WHEN SUBSTR(id, 1, 2) = 'BR' THEN 'BRAZIL'
                WHEN SUBSTR(id, 1, 2) = 'AR' THEN 'ARGENTINA'
                ELSE 'OTHER'
            END as region
        FROM `bigquery-public-data.ghcn_d.ghcnd_stations`
        WHERE 
            (state IN ('IA', 'IL', 'IN', 'MN', 'OH', 'NE', 'KS', 'SD', 'WI', 'MO')  -- US Midwest
            OR SUBSTR(id, 1, 2) = 'BR'  -- Brazil stations
            OR SUBSTR(id, 1, 2) = 'AR')  -- Argentina stations
            AND latitude IS NOT NULL
            AND longitude IS NOT NULL
    ),
    weather_data AS (
        SELECT 
            s.station_id,
            s.region,
            s.latitude,
            s.longitude,
            s.name as station_name,
            s.state,
            d.date,
            MAX(CASE WHEN d.element = 'TMAX' THEN d.value / 10.0 END) as tmax_c,  -- Convert from tenths of C
            MAX(CASE WHEN d.element = 'TMIN' THEN d.value / 10.0 END) as tmin_c,  -- Convert from tenths of C
            MAX(CASE WHEN d.element = 'PRCP' THEN d.value / 10.0 END) as prcp_mm, -- Convert from tenths of mm
            MAX(CASE WHEN d.element = 'SNOW' THEN d.value END) as snow_mm,
            MAX(CASE WHEN d.element = 'SNWD' THEN d.value END) as snow_depth_mm,
            MAX(CASE WHEN d.element = 'TAVG' THEN d.value / 10.0 END) as tavg_c
        FROM station_selection s
        JOIN `bigquery-public-data.ghcn_d.ghcnd_*` d
        ON s.station_id = d.id
        WHERE d.date BETWEEN DATE('{START_DATE}') AND DATE('{END_DATE}')
            AND d.element IN ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD', 'TAVG')
            AND d.qflag IS NULL  -- Only use quality-controlled data
        GROUP BY 1,2,3,4,5,6,7
    )
    SELECT 
        *,
        (tmax_c + tmin_c) / 2 as tmean_calculated_c,
        EXTRACT(YEAR FROM date) as year,
        EXTRACT(MONTH FROM date) as month
    FROM weather_data
    WHERE region != 'OTHER'
    ORDER BY date, station_id
    """
    
    logger.info("Executing BigQuery query...")
    
    try:
        # Execute query
        df = CLIENT.query(query).to_dataframe()
        
        if df.empty:
            logger.error("No data returned from NOAA GHCN-D")
            return None
        
        logger.info(f"✅ Retrieved {len(df):,} records from NOAA GHCN-D")
        logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"   Regions: {df['region'].value_counts().to_dict()}")
        logger.info(f"   Stations: {df['station_id'].nunique()}")
        
        # Add production weights
        df['production_weight'] = df['region'].map({
            'US_MIDWEST': REGIONS['US_MIDWEST']['production_weight'],
            'BRAZIL': REGIONS['BRAZIL']['production_weight'],
            'ARGENTINA': REGIONS['ARGENTINA']['production_weight']
        })
        
        # Add data source
        df['source'] = 'NOAA_GHCND'
        df['reliability'] = 0.98  # Very high reliability
        
        return df
        
    except Exception as e:
        logger.error(f"Error querying NOAA GHCN-D: {e}")
        return None

def collect_inmet_brazil(days_back=30):
    """
    Collect Brazil weather from INMET API.
    Used for recent data and to supplement NOAA.
    """
    logger.info("\n" + "="*80)
    logger.info("COLLECTING INMET BRAZIL DATA (SUPPLEMENT)")
    logger.info("="*80)
    
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # Key INMET stations for soybean regions
    stations = {
        'A901': 'Cuiabá-MT',
        'A908': 'Água Boa-MT', 
        'A909': 'Alto Araguaia-MT',
        'A702': 'Campo Grande-MS',
        'A756': 'Água Clara-MS'
    }
    
    all_data = []
    
    for station_id, station_name in stations.items():
        url = f"https://apitempo.inmet.gov.br/estacao/diaria/{start_date}/{end_date}/{station_id}"
        
        try:
            logger.info(f"  Fetching {station_name} ({station_id})...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df['station_id'] = f'INMET_{station_id}'
                    df['station_name'] = station_name
                    all_data.append(df)
                    logger.info(f"    ✅ Got {len(df)} records")
            elif response.status_code == 204:
                logger.warning(f"    No data available for {station_name}")
            else:
                logger.error(f"    HTTP {response.status_code} for {station_name}")
                
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"    Error fetching {station_name}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Standardize column names
        if 'DT_MEDICAO' in combined_df.columns:
            combined_df['date'] = pd.to_datetime(combined_df['DT_MEDICAO'])
        if 'TEM_MAX' in combined_df.columns:
            combined_df['tmax_c'] = pd.to_numeric(combined_df['TEM_MAX'], errors='coerce')
        if 'TEM_MIN' in combined_df.columns:
            combined_df['tmin_c'] = pd.to_numeric(combined_df['TEM_MIN'], errors='coerce')
        if 'CHUVA' in combined_df.columns:
            combined_df['prcp_mm'] = pd.to_numeric(combined_df['CHUVA'], errors='coerce')
        
        combined_df['source'] = 'INMET'
        combined_df['region'] = 'BRAZIL'
        combined_df['reliability'] = 0.90
        
        logger.info(f"✅ Collected {len(combined_df)} INMET records")
        return combined_df
    
    return None

def collect_smn_argentina(year=2025, month=10):
    """
    Collect Argentina weather from SMN API.
    """
    logger.info("\n" + "="*80)
    logger.info("COLLECTING SMN ARGENTINA DATA (SUPPLEMENT)")
    logger.info("="*80)
    
    stations = {
        '87576': 'Rosario',
        '87582': 'Buenos Aires',
        '87418': 'Córdoba'
    }
    
    all_data = []
    
    for station_id, station_name in stations.items():
        url = f"https://ws.smn.gob.ar/data/observations/{station_id}/{year}/{month:02d}"
        
        try:
            logger.info(f"  Fetching {station_name} ({station_id})...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    df['station_id'] = f'SMN_{station_id}'
                    df['station_name'] = station_name
                    all_data.append(df)
                    logger.info(f"    ✅ Got {len(df)} records")
            else:
                logger.error(f"    HTTP {response.status_code} for {station_name}")
                
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"    Error fetching {station_name}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df['source'] = 'SMN'
        combined_df['region'] = 'ARGENTINA'
        combined_df['reliability'] = 0.85
        
        logger.info(f"✅ Collected {len(combined_df)} SMN records")
        return combined_df
    
    return None

def collect_nasa_power_backup(lat, lon, start_date, end_date):
    """
    Collect weather from NASA POWER API as backup for missing station data.
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    params = {
        'parameters': 'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M',
        'community': 'AG',
        'longitude': lon,
        'latitude': lat,
        'start': start_date.replace('-', ''),
        'end': end_date.replace('-', ''),
        'format': 'JSON'
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'properties' in data and 'parameter' in data['properties']:
                params_data = data['properties']['parameter']
                
                # Convert to DataFrame
                df = pd.DataFrame(params_data)
                df['date'] = pd.to_datetime(df.index)
                df['latitude'] = lat
                df['longitude'] = lon
                df['source'] = 'NASA_POWER'
                df['reliability'] = 0.90
                
                # Rename columns to standard names
                df.rename(columns={
                    'T2M': 'tavg_c',
                    'T2M_MAX': 'tmax_c',
                    'T2M_MIN': 'tmin_c',
                    'PRECTOTCORR': 'prcp_mm',
                    'RH2M': 'humidity_pct',
                    'WS2M': 'wind_speed_ms'
                }, inplace=True)
                
                return df
                
    except Exception as e:
        logger.error(f"Error fetching NASA POWER data: {e}")
    
    return None

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("PRODUCTION WEATHER DATA COLLECTION")
    logger.info("="*80)
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info("Sources: NOAA GHCN-D (primary), INMET, SMN, NASA POWER (backup)")
    logger.info("="*80)
    
    all_data = []
    
    # 1. PRIMARY: NOAA GHCN-D for all regions
    noaa_df = collect_noaa_ghcnd_all_regions()
    if noaa_df is not None:
        all_data.append(noaa_df)
    
    # 2. SUPPLEMENT: INMET for recent Brazil data
    inmet_df = collect_inmet_brazil(days_back=30)
    if inmet_df is not None:
        all_data.append(inmet_df)
    
    # 3. SUPPLEMENT: SMN for recent Argentina data
    smn_df = collect_smn_argentina(year=2025, month=11)
    if smn_df is not None:
        all_data.append(smn_df)
    
    # 4. BACKUP: NASA POWER for key regions with missing data (example)
    # Mato Grosso, Brazil (core soybean region)
    nasa_df = collect_nasa_power_backup(-15.8, -47.9, "2025-11-01", "2025-11-16")
    if nasa_df is not None:
        nasa_df['region'] = 'BRAZIL'
        all_data.append(nasa_df)
    
    if not all_data:
        logger.error("❌ No weather data collected!")
        return 1
    
    # Combine all sources
    logger.info("\n" + "="*80)
    logger.info("COMBINING ALL SOURCES")
    logger.info("="*80)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Sort by date and region
    combined_df = combined_df.sort_values(['date', 'region', 'station_id'])
    
    # Save to staging
    output_file = STAGING_DIR / "weather_2000_2025.parquet"
    combined_df.to_parquet(output_file, index=False)
    
    # Summary statistics
    logger.info("="*80)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Total records: {len(combined_df):,}")
    logger.info(f"📅 Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    
    # Source breakdown
    source_counts = combined_df['source'].value_counts()
    logger.info("\n📊 Records by source:")
    for source, count in source_counts.items():
        pct = (count / len(combined_df)) * 100
        logger.info(f"   {source}: {count:,} ({pct:.1f}%)")
    
    # Regional breakdown
    if 'region' in combined_df.columns:
        region_counts = combined_df['region'].value_counts()
        logger.info("\n🌍 Records by region:")
        for region, count in region_counts.items():
            pct = (count / len(combined_df)) * 100
            logger.info(f"   {region}: {count:,} ({pct:.1f}%)")
    
    # Data quality
    logger.info("\n📈 Data quality:")
    logger.info(f"   Temperature coverage: {combined_df['tmax_c'].notna().mean():.1%}")
    logger.info(f"   Precipitation coverage: {combined_df['prcp_mm'].notna().mean():.1%}")
    
    # Reliability weighted average
    if 'reliability' in combined_df.columns:
        avg_reliability = combined_df['reliability'].mean()
        logger.info(f"   Average reliability: {avg_reliability:.2f}")
    
    logger.info(f"\n✅ Weather data saved to: {output_file}")
    logger.info("✅ WEATHER COLLECTION COMPLETE!")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
