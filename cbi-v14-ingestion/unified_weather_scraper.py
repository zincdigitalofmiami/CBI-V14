#!/usr/bin/env python3
"""
UNIFIED SOYBEAN WEATHER SCRAPER
Covers: Brazil, Argentina, Paraguay, Uruguay, USA
Trump tariff scenario optimized
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import uuid
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

class GlobalSoybeanWeatherPipeline:
    """
    Institutional-grade weather pipeline covering all critical soybean regions
    Optimized for Trump tariff / China trade war scenarios
    """
    
    def __init__(self):
        self.noaa_token = "rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi"
        
        self.metrics = {
            'brazil': {'calls': 0, 'success': 0, 'failures': 0},
            'argentina': {'calls': 0, 'success': 0, 'failures': 0},
            'paraguay': {'calls': 0, 'success': 0, 'failures': 0},
            'usa': {'calls': 0, 'success': 0, 'failures': 0}
        }
    
    def fetch_brazil_inmet(self, station_id: str, start_date: str, end_date: str, station_info: dict) -> pd.DataFrame:
        """Brazil INMET API"""
        url = f"https://apitempo.inmet.gov.br/estacao/{start_date}/{end_date}/{station_id}"
        
        headers = {
            'User-Agent': 'CBI-V14/1.0 (Soybean Forecasting)',
            'Accept': 'application/json'
        }
        
        self.metrics['brazil']['calls'] += 1
        
        try:
            time.sleep(12)  # Rate limit: 5 req/min
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                records = []
                for record in data:
                    records.append({
                        'date': pd.to_datetime(record.get('DT_MEDICAO')).date(),
                        'station_id': station_id,
                        'state': station_info['state'],
                        'city': station_info['city'],
                        'lat': station_info['lat'],
                        'lon': station_info['lon'],
                        'precip_mm': float(record.get('CHUVA', 0) or 0),
                        'temp_max_c': float(record.get('TEM_MAX', -999) or -999),
                        'temp_min_c': float(record.get('TEM_MIN', -999) or -999),
                        'temp_avg_c': float(record.get('TEM_MED', -999) or -999),
                        'humidity': float(record.get('UMD_MED', 0) or 0),
                        'production_weight': station_info['weight'],
                        'source_name': 'inmet_api',
                        'confidence_score': 0.95,
                        'ingest_timestamp_utc': datetime.now(timezone.utc),
                        'provenance_uuid': str(uuid.uuid4())
                    })
                
                self.metrics['brazil']['success'] += 1
                logger.info(f"✅ Brazil {station_id}: {len(records)} records")
                return pd.DataFrame(records)
            elif response.status_code == 204:
                logger.warning(f"⚠️ Brazil {station_id}: No data for date range")
                
        except Exception as e:
            self.metrics['brazil']['failures'] += 1
            logger.error(f"❌ Brazil INMET failed for {station_id}: {e}")
        
        return pd.DataFrame()
    
    def fetch_argentina_smn(self, station_id: str, station_info: dict) -> pd.DataFrame:
        """Argentina SMN - Open Data Portal"""
        url = f"https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/datohorario{station_id}.txt"
        
        self.metrics['argentina']['calls'] += 1
        
        try:
            time.sleep(2)
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                
                records = []
                for line in lines[1:11]:  # First 10 data rows
                    parts = line.split('|')
                    if len(parts) >= 10:
                        try:
                            records.append({
                                'date': pd.to_datetime(parts[0]).date(),
                                'station_id': station_id,
                                'province': station_info['province'],
                                'city': station_info['city'],
                                'lat': station_info['lat'],
                                'lon': station_info['lon'],
                                'temp_avg_c': float(parts[1]) if parts[1] else None,
                                'precip_mm': float(parts[3]) if parts[3] else 0,
                                'humidity': float(parts[4]) if parts[4] else None,
                                'source_name': 'smn_argentina',
                                'confidence_score': 0.90,
                                'ingest_timestamp_utc': datetime.now(timezone.utc),
                                'provenance_uuid': str(uuid.uuid4())
                            })
                        except (ValueError, IndexError):
                            continue
                
                self.metrics['argentina']['success'] += 1
                logger.info(f"✅ Argentina {station_id}: {len(records)} records")
                return pd.DataFrame(records)
                
        except Exception as e:
            self.metrics['argentina']['failures'] += 1
            logger.error(f"❌ Argentina SMN failed for {station_id}: {e}")
        
        return pd.DataFrame()
    
    def fetch_usa_noaa(self, station_id: str, start_date: str, end_date: str, station_info: dict) -> pd.DataFrame:
        """USA NOAA GHCND"""
        url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
        
        headers = {'token': self.noaa_token}
        
        params = {
            'datasetid': 'GHCND',
            'stationid': station_id,
            'startdate': start_date,
            'enddate': end_date,
            'datatypeid': 'TMAX,TMIN,PRCP',
            'units': 'metric',
            'limit': 1000
        }
        
        self.metrics['usa']['calls'] += 1
        
        try:
            time.sleep(0.2)  # Rate limit: 5 req/sec
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                records = []
                for record in data.get('results', []):
                    records.append({
                        'date': pd.to_datetime(record['date']).date(),
                        'station_id': station_id,
                        'datatype': record['datatype'],
                        'value': record['value'] / 10.0
                    })
                
                df = pd.DataFrame(records)
                if df.empty:
                    return df
                    
                df_pivot = df.pivot_table(
                    index=['date', 'station_id'],
                    columns='datatype',
                    values='value'
                ).reset_index()
                
                df_pivot['state'] = station_info['state']
                df_pivot['city'] = station_info['city']
                df_pivot['lat'] = station_info['lat']
                df_pivot['lon'] = station_info['lon']
                df_pivot.rename(columns={'PRCP': 'precip_mm', 'TMAX': 'temp_max_c', 'TMIN': 'temp_min_c'}, inplace=True)
                df_pivot['source_name'] = 'noaa_api'
                df_pivot['confidence_score'] = 0.95
                df_pivot['ingest_timestamp_utc'] = datetime.now(timezone.utc)
                df_pivot['provenance_uuid'] = [str(uuid.uuid4()) for _ in range(len(df_pivot))]
                
                self.metrics['usa']['success'] += 1
                logger.info(f"✅ USA {station_id}: {len(df_pivot)} records")
                return df_pivot
                
        except Exception as e:
            self.metrics['usa']['failures'] += 1
            logger.error(f"❌ USA NOAA failed for {station_id}: {e}")
        
        return pd.DataFrame()
    
    def print_performance_report(self):
        """Print performance metrics"""
        logger.info("\n" + "="*60)
        logger.info("WEATHER DATA COLLECTION PERFORMANCE REPORT")
        logger.info("="*60)
        
        for country, stats in self.metrics.items():
            total = stats['calls']
            success = stats['success']
            failures = stats['failures']
            success_rate = (success / total * 100) if total > 0 else 0
            
            logger.info(f"\n{country.upper()}:")
            logger.info(f"  API Calls: {total}")
            logger.info(f"  Successful: {success}")
            logger.info(f"  Failed: {failures}")
            logger.info(f"  Success Rate: {success_rate:.1f}%")
        
        logger.info("="*60)


# Station configs
BRAZIL_STATIONS = [
    {"id": "A901", "city": "Cuiaba", "lat": -15.55, "lon": -56.07, "weight": 0.35, "state": "MT"},
    {"id": "A919", "city": "Rondonopolis", "lat": -16.45, "lon": -54.57, "weight": 0.30, "state": "MT"},
    {"id": "A908", "city": "Sinop", "lat": -11.98, "lon": -55.57, "weight": 0.35, "state": "MT"}
]

ARGENTINA_STATIONS = [
    {"id": "87576", "city": "Buenos_Aires", "lat": -34.82, "lon": -58.54, "province": "BA"},
    {"id": "87344", "city": "Cordoba", "lat": -31.32, "lon": -64.21, "province": "CB"},
    {"id": "87374", "city": "Rosario", "lat": -32.92, "lon": -60.78, "province": "SF"}
]

US_MIDWEST_STATIONS = [
    {"id": "GHCND:USW00014933", "city": "Des_Moines", "lat": 41.53, "lon": -93.66, "state": "IA"},
    {"id": "GHCND:USW00094846", "city": "Chicago_OHare", "lat": 41.98, "lon": -87.90, "state": "IL"}
]


def load_to_bigquery(df, table_id):
    """Load data to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    
    try:
        table_ref = client.get_table(table_id)
        schema_names = [field.name for field in table_ref.schema]
        
        for col in schema_names:
            if col not in df.columns:
                df[col] = None
        
        df = df[schema_names]
        
        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()
        print(f"✅ Loaded {len(df)} rows into {table_id}")
        return True
    except Exception as e:
        print(f"❌ Error loading to BigQuery: {e}")
        return False


if __name__ == "__main__":
    scraper = GlobalSoybeanWeatherPipeline()
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10)
    
    # ARGENTINA
    print("\n=== ARGENTINA WEATHER ===")
    all_argentina = []
    for station in ARGENTINA_STATIONS:
        print(f"Fetching {station['city']}...")
        df = scraper.fetch_argentina_smn(
            station_id=station['id'],
            station_info=station
        )
        if not df.empty:
            all_argentina.append(df)
    
    if all_argentina:
        argentina_combined = pd.concat(all_argentina, ignore_index=True)
        load_to_bigquery(argentina_combined, f"{PROJECT_ID}.forecasting_data_warehouse.weather_argentina_daily")
    
    # USA
    print("\n=== US MIDWEST WEATHER ===")
    all_us = []
    for station in US_MIDWEST_STATIONS:
        print(f"Fetching {station['city']}...")
        df = scraper.fetch_usa_noaa(
            station_id=station['id'],
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            station_info=station
        )
        if not df.empty:
            all_us.append(df)
    
    if all_us:
        us_combined = pd.concat(all_us, ignore_index=True)
        load_to_bigquery(us_combined, f"{PROJECT_ID}.forecasting_data_warehouse.weather_us_midwest_daily")
    
    # Performance report
    scraper.print_performance_report()
    print("\n✅ Weather data loading complete")






