#!/usr/bin/env python3
"""
Production Weather Data Collection V2
======================================
Uses exact institutional-grade endpoints provided:
1. US Midwest: NOAA GHCN-D via BigQuery (bigquery-public-data.noaa_public.ghcn_d.*)
2. Brazil: INMET API (https://apitempo.inmet.gov.br/estacao/diaria/)
3. Argentina: SMN API (https://ws.smn.gob.ar/data/observations/)
4. Global Backup: NASA POWER API
5. Forecast: NOAA GFS via BigQuery

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
import numpy as np

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
NOAA_API_TOKEN = "rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi"  # Move to env

# External drive paths
EXTERNAL_DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
STAGING_DIR = EXTERNAL_DRIVE / "TrainingData/staging"
QUARANTINE_DIR = EXTERNAL_DRIVE / "TrainingData/quarantine"
STAGING_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# 1. US MIDWEST - NOAA GHCN-D via BigQuery
# ============================================================================

def collect_us_midwest_ghcnd():
    """
    Collect US Midwest weather from NOAA GHCN-D via BigQuery.
    Dataset: bigquery-public-data.noaa_public.ghcn_d.*
    """
    logger.info("="*80)
    logger.info("1. COLLECTING US MIDWEST - NOAA GHCN-D")
    logger.info("="*80)
    
    query = f"""
    WITH midwest_stations AS (
        SELECT DISTINCT
            id as station_id,
            latitude,
            longitude,
            elevation,
            state,
            name
        FROM `bigquery-public-data.ghcn_d.ghcnd_stations`
        WHERE state IN ('IA', 'IL', 'IN', 'MN', 'OH', 'NE', 'KS', 'SD', 'WI', 'MO')
            AND latitude IS NOT NULL
            AND longitude IS NOT NULL
    ),
    weather_data AS (
        SELECT
            s.station_id,
            s.state,
            s.name as station_name,
            s.latitude,
            s.longitude,
            d.date,
            d.element,
            d.value,
            d.qflag
        FROM midwest_stations s
        JOIN `bigquery-public-data.ghcn_d.ghcnd_*` d
        ON s.station_id = d.id
        WHERE d.date BETWEEN DATE('{START_DATE}') AND DATE('{END_DATE}')
            AND d.element IN ('TMAX', 'TMIN', 'PRCP')
            AND d.qflag IS NULL  -- Only quality-controlled data
    ),
    pivoted AS (
        SELECT 
            station_id,
            state,
            station_name,
            latitude,
            longitude,
            date,
            MAX(CASE WHEN element = 'TMAX' THEN value / 10.0 END) as tmax_c,  -- Convert from tenths
            MAX(CASE WHEN element = 'TMIN' THEN value / 10.0 END) as tmin_c,
            MAX(CASE WHEN element = 'PRCP' THEN value / 10.0 END) as prcp_mm
        FROM weather_data
        GROUP BY 1,2,3,4,5,6
    )
    SELECT 
        *,
        'US_MIDWEST' as region,
        'NOAA_GHCND' as source,
        0.98 as reliability
    FROM pivoted
    WHERE (tmax_c BETWEEN -50 AND 60)  -- Validation
        AND (tmin_c BETWEEN -60 AND 50)
        AND (prcp_mm >= 0 AND prcp_mm < 500)  -- Max reasonable daily precip
    ORDER BY date, station_id
    """
    
    try:
        logger.info("  Executing BigQuery query...")
        df = CLIENT.query(query).to_dataframe()
        
        if df.empty:
            logger.warning("  No data returned")
            return None
        
        logger.info(f"  ✅ Retrieved {len(df):,} records")
        logger.info(f"  📅 Date range: {df['date'].min()} to {df['date'].max()}")
        logger.info(f"  📍 Stations: {df['station_id'].nunique()}")
        logger.info(f"  🌡️ Avg temp: {df['tmax_c'].mean():.1f}°C")
        
        return df
        
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
        return None

# ============================================================================
# 2. BRAZIL - INMET API
# ============================================================================

def collect_brazil_inmet():
    """
    Collect Brazil weather from INMET API.
    Endpoint: https://apitempo.inmet.gov.br/estacao/diaria/{start}/{end}
    """
    logger.info("\n" + "="*80)
    logger.info("2. COLLECTING BRAZIL - INMET API")
    logger.info("="*80)
    
    # Process in chunks (INMET limits date ranges)
    all_data = []
    current_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    
    # Key soybean production states
    target_states = ['MT', 'MS', 'PR', 'GO', 'RS']
    
    while current_date < end_date:
        chunk_end = min(current_date + timedelta(days=365), end_date)
        
        url = f"https://apitempo.inmet.gov.br/estacao/diaria/{current_date.strftime('%Y-%m-%d')}/{chunk_end.strftime('%Y-%m-%d')}"
        
        try:
            logger.info(f"  Fetching {current_date.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    
                    # Filter to key states if UF field exists
                    if 'UF' in df.columns:
                        df = df[df['UF'].isin(target_states)]
                    
                    if not df.empty:
                        all_data.append(df)
                        logger.info(f"    ✅ Got {len(df)} records")
            elif response.status_code == 204:
                logger.info(f"    No data for this period")
            else:
                logger.warning(f"    HTTP {response.status_code}")
                
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"    ❌ Error: {e}")
        
        current_date = chunk_end + timedelta(days=1)
    
    if not all_data:
        logger.warning("  No INMET data collected")
        return None
    
    # Combine and standardize
    combined = pd.concat(all_data, ignore_index=True)
    
    # Standardize column names
    rename_map = {
        'DT_MEDICAO': 'date',
        'CD_ESTACAO': 'station_id',
        'DC_NOME': 'station_name',
        'UF': 'state',
        'TEM_MAX': 'tmax_c',
        'TEM_MIN': 'tmin_c',
        'CHUVA': 'prcp_mm',
        'PRECIP_TOT': 'prcp_mm',  # Alternative name
        'UMD_MAX': 'humidity_max',
        'UMD_MIN': 'humidity_min'
    }
    
    combined.rename(columns=rename_map, inplace=True)
    
    # Convert date
    if 'date' in combined.columns:
        combined['date'] = pd.to_datetime(combined['date'])
    
    # Add metadata
    combined['region'] = 'BRAZIL'
    combined['source'] = 'INMET'
    combined['reliability'] = 0.90
    
    # Validation and quarantine
    valid_mask = (
        (combined['tmax_c'] >= -10) & (combined['tmax_c'] <= 50) &
        (combined['tmin_c'] >= -15) & (combined['tmin_c'] <= 45) &
        (combined['prcp_mm'] >= 0) & (combined['prcp_mm'] < 500)
    )
    
    quarantined = combined[~valid_mask]
    if len(quarantined) > 0:
        quarantine_file = QUARANTINE_DIR / f"inmet_quarantine_{datetime.now().strftime('%Y%m%d')}.parquet"
        quarantined.to_parquet(quarantine_file, index=False)
        logger.warning(f"  ⚠️ Quarantined {len(quarantined)} invalid records")
    
    combined = combined[valid_mask]
    
    logger.info(f"  ✅ Collected {len(combined)} valid INMET records")
    return combined

# ============================================================================
# 3. ARGENTINA - SMN API
# ============================================================================

def collect_argentina_smn():
    """
    Collect Argentina weather from SMN API.
    Endpoint: https://ws.smn.gob.ar/data/observations/{station}/{year}/{month}
    """
    logger.info("\n" + "="*80)
    logger.info("3. COLLECTING ARGENTINA - SMN API")
    logger.info("="*80)
    
    # Key stations for soybean regions
    stations = {
        '87576': {'name': 'Rosario', 'lat': -32.92, 'lon': -60.78},
        '87582': {'name': 'Buenos Aires', 'lat': -34.82, 'lon': -58.54},
        '87418': {'name': 'Córdoba', 'lat': -31.31, 'lon': -64.22},
        '87344': {'name': 'Pergamino', 'lat': -33.93, 'lon': -60.55}
    }
    
    all_data = []
    
    # Process month by month for last 2 years (older data may not be available via API)
    start_year = max(2023, int(START_DATE[:4]))
    
    for year in range(start_year, datetime.now().year + 1):
        for month in range(1, 13):
            if datetime(year, month, 1) > datetime.now():
                break
                
            for station_id, station_info in stations.items():
                url = f"https://ws.smn.gob.ar/data/observations/{station_id}/{year}/{month:02d}"
                
                try:
                    logger.info(f"  Fetching {station_info['name']} {year}-{month:02d}...")
                    response = requests.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            df = pd.DataFrame(data)
                            df['station_id'] = f'SMN_{station_id}'
                            df['station_name'] = station_info['name']
                            df['latitude'] = station_info['lat']
                            df['longitude'] = station_info['lon']
                            all_data.append(df)
                            logger.info(f"    ✅ Got {len(df)} records")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.debug(f"    No data or error: {e}")
    
    if not all_data:
        logger.warning("  No SMN data collected")
        return None
    
    # Combine and standardize
    combined = pd.concat(all_data, ignore_index=True)
    
    # Standardize columns (adjust based on actual API response)
    if 'fecha' in combined.columns:
        combined['date'] = pd.to_datetime(combined['fecha'])
    elif 'date' in combined.columns:
        combined['date'] = pd.to_datetime(combined['date'])
    
    # Map temperature and precipitation fields
    rename_map = {
        'temp': 'tavg_c',
        'temperatura': 'tavg_c',
        'temp_max': 'tmax_c',
        'temp_min': 'tmin_c',
        'precip': 'prcp_mm',
        'precipitacion': 'prcp_mm',
        'humidity': 'humidity_pct',
        'humedad': 'humidity_pct'
    }
    
    combined.rename(columns=rename_map, inplace=True)
    
    # Add metadata
    combined['region'] = 'ARGENTINA'
    combined['source'] = 'SMN'
    combined['reliability'] = 0.85
    
    logger.info(f"  ✅ Collected {len(combined)} SMN records")
    return combined

# ============================================================================
# 4. NASA POWER - Global Backup
# ============================================================================

def collect_nasa_power_backup():
    """
    Collect weather from NASA POWER API for key regions as backup.
    """
    logger.info("\n" + "="*80)
    logger.info("4. COLLECTING BACKUP - NASA POWER")
    logger.info("="*80)
    
    # Key locations for gap filling
    locations = [
        {'name': 'Mato Grosso, BR', 'lat': -13.0, 'lon': -55.0, 'region': 'BRAZIL'},
        {'name': 'Paraná, BR', 'lat': -24.5, 'lon': -51.5, 'region': 'BRAZIL'},
        {'name': 'Santa Fe, AR', 'lat': -31.0, 'lon': -61.0, 'region': 'ARGENTINA'},
        {'name': 'Iowa, US', 'lat': 42.0, 'lon': -93.5, 'region': 'US_MIDWEST'}
    ]
    
    all_data = []
    
    for loc in locations:
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        
        params = {
            'parameters': 'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,WS2M',
            'community': 'AG',
            'longitude': loc['lon'],
            'latitude': loc['lat'],
            'start': START_DATE.replace('-', ''),
            'end': END_DATE.replace('-', ''),
            'format': 'JSON'
        }
        
        try:
            logger.info(f"  Fetching {loc['name']}...")
            response = requests.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'properties' in data and 'parameter' in data['properties']:
                    params_data = data['properties']['parameter']
                    
                    # Convert each parameter to DataFrame
                    dfs = []
                    for param, values in params_data.items():
                        df = pd.DataFrame(list(values.items()), columns=['date', param])
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                        dfs.append(df.set_index('date'))
                    
                    # Combine all parameters
                    df = pd.concat(dfs, axis=1).reset_index()
                    
                    # Add location info
                    df['station_name'] = loc['name']
                    df['latitude'] = loc['lat']
                    df['longitude'] = loc['lon']
                    df['region'] = loc['region']
                    
                    # Rename columns
                    df.rename(columns={
                        'T2M': 'tavg_c',
                        'T2M_MAX': 'tmax_c',
                        'T2M_MIN': 'tmin_c',
                        'PRECTOTCORR': 'prcp_mm',
                        'RH2M': 'humidity_pct',
                        'WS2M': 'wind_speed_ms'
                    }, inplace=True)
                    
                    all_data.append(df)
                    logger.info(f"    ✅ Got {len(df)} records")
                    
        except Exception as e:
            logger.error(f"    ❌ Error: {e}")
        
        time.sleep(2)  # Rate limiting
    
    if not all_data:
        return None
    
    combined = pd.concat(all_data, ignore_index=True)
    combined['source'] = 'NASA_POWER'
    combined['reliability'] = 0.90
    
    logger.info(f"  ✅ Collected {len(combined)} NASA POWER records")
    return combined

# ============================================================================
# 5. NOAA GFS - Forecast Layer
# ============================================================================

def collect_noaa_gfs_forecast():
    """
    Collect 16-day weather forecast from NOAA GFS via BigQuery.
    """
    logger.info("\n" + "="*80)
    logger.info("5. COLLECTING FORECAST - NOAA GFS")
    logger.info("="*80)
    
    query = """
    SELECT
        forecast_time,
        temperature_2m_above_ground AS temp_c,
        total_precipitation_surface AS precip_mm,
        soil_moisture_0_10cm_below_ground AS soil_moisture,
        ST_X(geography) as longitude,
        ST_Y(geography) as latitude,
        CASE
            WHEN ST_CONTAINS(
                ST_GEOGFROMTEXT('POLYGON((-100 25, -100 50, -80 50, -80 25, -100 25))'),
                geography
            ) THEN 'US_MIDWEST'
            WHEN ST_CONTAINS(
                ST_GEOGFROMTEXT('POLYGON((-60 -35, -60 5, -35 5, -35 -35, -60 -35))'),
                geography
            ) THEN 'BRAZIL'
            WHEN ST_CONTAINS(
                ST_GEOGFROMTEXT('POLYGON((-75 -55, -75 -20, -50 -20, -50 -55, -75 -55))'),
                geography
            ) THEN 'ARGENTINA'
            ELSE 'OTHER'
        END as region
    FROM `bigquery-public-data.noaa_global_forecast_system.NOAA_GFS0P25`
    WHERE DATE(forecast_time) BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), INTERVAL 16 DAY)
        AND creation_time = (
            SELECT MAX(creation_time)
            FROM `bigquery-public-data.noaa_global_forecast_system.NOAA_GFS0P25`
        )
    LIMIT 10000
    """
    
    try:
        logger.info("  Executing BigQuery query...")
        df = CLIENT.query(query).to_dataframe()
        
        if not df.empty:
            df = df[df['region'] != 'OTHER']
            df['source'] = 'NOAA_GFS_FORECAST'
            df['reliability'] = 0.95
            
            logger.info(f"  ✅ Retrieved {len(df)} forecast records")
            logger.info(f"  📅 Forecast range: {df['forecast_time'].min()} to {df['forecast_time'].max()}")
            
            return df
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
    
    return None

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("PRODUCTION WEATHER DATA COLLECTION")
    logger.info("="*80)
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info("Sources: NOAA GHCN-D, INMET, SMN, NASA POWER, NOAA GFS")
    logger.info("="*80)
    
    all_data = []
    source_summary = {}
    
    # 1. US Midwest - NOAA GHCN-D
    us_data = collect_us_midwest_ghcnd()
    if us_data is not None:
        all_data.append(us_data)
        source_summary['NOAA_GHCND'] = len(us_data)
    
    # 2. Brazil - INMET
    brazil_data = collect_brazil_inmet()
    if brazil_data is not None:
        all_data.append(brazil_data)
        source_summary['INMET'] = len(brazil_data)
    
    # 3. Argentina - SMN
    argentina_data = collect_argentina_smn()
    if argentina_data is not None:
        all_data.append(argentina_data)
        source_summary['SMN'] = len(argentina_data)
    
    # 4. NASA POWER Backup
    nasa_data = collect_nasa_power_backup()
    if nasa_data is not None:
        all_data.append(nasa_data)
        source_summary['NASA_POWER'] = len(nasa_data)
    
    # 5. NOAA GFS Forecast
    forecast_data = collect_noaa_gfs_forecast()
    if forecast_data is not None:
        # Save forecast separately
        forecast_file = STAGING_DIR / "weather_forecast_16day.parquet"
        forecast_data.to_parquet(forecast_file, index=False)
        logger.info(f"  💾 Forecast saved to {forecast_file.name}")
    
    if not all_data:
        logger.error("❌ No weather data collected!")
        return 1
    
    # Combine all historical data
    logger.info("\n" + "="*80)
    logger.info("COMBINING & SAVING DATA")
    logger.info("="*80)
    
    combined = pd.concat(all_data, ignore_index=True)
    
    # Ensure date column is datetime
    if 'date' in combined.columns:
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined.sort_values(['date', 'region'])
    
    # Save to staging
    output_file = STAGING_DIR / "weather_2000_2025.parquet"
    combined.to_parquet(output_file, index=False)
    
    # Summary
    logger.info("="*80)
    logger.info("COLLECTION SUMMARY")
    logger.info("="*80)
    logger.info(f"✅ Total records: {len(combined):,}")
    
    if 'date' in combined.columns:
        logger.info(f"📅 Date range: {combined['date'].min()} to {combined['date'].max()}")
    
    logger.info("\n📊 Records by source:")
    for source, count in source_summary.items():
        pct = (count / len(combined)) * 100
        logger.info(f"   {source}: {count:,} ({pct:.1f}%)")
    
    if 'region' in combined.columns:
        logger.info("\n🌍 Records by region:")
        for region, count in combined.groupby('region').size().items():
            pct = (count / len(combined)) * 100
            logger.info(f"   {region}: {count:,} ({pct:.1f}%)")
    
    # Data quality metrics
    if 'tmax_c' in combined.columns:
        temp_coverage = combined['tmax_c'].notna().mean()
        logger.info(f"\n📈 Temperature coverage: {temp_coverage:.1%}")
    
    if 'prcp_mm' in combined.columns:
        precip_coverage = combined['prcp_mm'].notna().mean()
        logger.info(f"📈 Precipitation coverage: {precip_coverage:.1%}")
    
    if 'reliability' in combined.columns:
        avg_reliability = (combined['reliability'] * combined.groupby('source').transform('size')).sum() / len(combined)
        logger.info(f"📈 Weighted avg reliability: {avg_reliability:.2f}")
    
    logger.info(f"\n✅ Weather data saved to: {output_file}")
    logger.info("✅ WEATHER COLLECTION COMPLETE!")
    logger.info("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
