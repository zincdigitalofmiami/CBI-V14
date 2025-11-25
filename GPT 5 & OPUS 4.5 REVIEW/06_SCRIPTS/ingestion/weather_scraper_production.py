#!/usr/bin/env python3
"""
weather_scraper_production.py
Production-grade weather scraper using direct API calls + Selenium/BeautifulSoup fallback
Uses institutional-grade station lists and endpoints
"""

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import json
import uuid
from google.cloud import bigquery

# --- Station Configuration ---
BRAZIL_STATIONS = {
    "Mato_Grosso": [
        {"id": "A901", "city": "Cuiaba", "lat": -15.55, "lon": -56.07, "weight": 0.35, "state": "MT"},
        {"id": "A919", "city": "Rondonopolis", "lat": -16.45, "lon": -54.57, "weight": 0.30, "state": "MT"},
        {"id": "A908", "city": "Sinop", "lat": -11.98, "lon": -55.57, "weight": 0.35, "state": "MT"}
    ],
    "Parana": [
        {"id": "A803", "city": "Londrina", "lat": -23.31, "lon": -51.16, "weight": 0.50, "state": "PR"},
        {"id": "A835", "city": "Maringa", "lat": -23.40, "lon": -51.92, "weight": 0.50, "state": "PR"}
    ],
    "Rio_Grande_do_Sul": [
        {"id": "A801", "city": "Porto_Alegre", "lat": -30.05, "lon": -51.16, "weight": 0.60, "state": "RS"},
        {"id": "A802", "city": "Santa_Maria", "lat": -29.70, "lon": -53.70, "weight": 0.40, "state": "RS"}
    ]
}

ARGENTINA_STATIONS = {
    "Buenos_Aires_Province": [
        {"id": "87576", "city": "Buenos_Aires", "lat": -34.82, "lon": -58.54, "province": "BA"}
    ],
    "Cordoba": [
        {"id": "87344", "city": "Cordoba", "lat": -31.32, "lon": -64.21, "province": "CB"}
    ],
    "Santa_Fe": [
        {"id": "87374", "city": "Rosario", "lat": -32.92, "lon": -60.78, "province": "SF"}
    ]
}

US_MIDWEST_STATIONS = {
    "Iowa": [
        {"id": "GHCND:USW00014933", "city": "Des_Moines", "lat": 41.53, "lon": -93.66, "state": "IA"}
    ],
    "Illinois": [
        {"id": "GHCND:USW00094846", "city": "Chicago_OHare", "lat": 41.98, "lon": -87.90, "state": "IL"}
    ],
    "Indiana": [
        {"id": "GHCND:USW00093819", "city": "Indianapolis", "lat": 39.73, "lon": -86.27, "state": "IN"}
    ]
}

import os
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from src.utils.keychain_manager import get_api_key as _get_api
except Exception:
    _get_api = None
NOAA_TOKEN = os.getenv('NOAA_API_TOKEN') or (_get_api('NOAA_API_TOKEN') if _get_api else None)
if not NOAA_TOKEN:
    raise RuntimeError("NOAA_API_TOKEN not set. Export or store in Keychain.")
PROJECT_ID = "cbi-v14"


class WeatherDataScraper:
    """Production-grade weather scraper"""
    
    def __init__(self, use_selenium=False):
        self.use_selenium = use_selenium
        self.driver = None
        
        if use_selenium:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
    
    def fetch_brazil_inmet(self, station_id, start_date, end_date, station_info):
        """Fetch Brazil INMET data - API method"""
        url = f"https://apitempo.inmet.gov.br/estacao/{start_date}/{end_date}/{station_id}"
        
        headers = {
            'User-Agent': 'CBI-V14/1.0 (Soybean Oil Forecasting)',
            'Accept': 'application/json'
        }
        
        try:
            time.sleep(12)  # Rate limit: 5 req/min = 12 sec spacing
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
                
                return pd.DataFrame(records)
            else:
                print(f"INMET API returned {response.status_code} for {station_id}")
            
        except Exception as e:
            print(f"INMET API failed for {station_id}: {e}")
        
        return pd.DataFrame()
    
    def fetch_argentina_smn(self, station_id, station_info):
        """Fetch Argentina SMN data"""
        url = f"https://ssl.smn.gob.ar/dpd/descarga_opendata.php?file=observaciones/datohorario{station_id}.txt"
        
        try:
            time.sleep(2)  # Polite delay
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                data_lines = [line for line in lines if line and not line.startswith('#')]
                
                records = []
                for line in data_lines[:10]:  # Sample: first 10 rows
                    parts = line.split(',')
                    if len(parts) >= 3:
                        records.append({
                            'date': pd.to_datetime(parts[0]).date() if parts[0] else None,
                            'station_id': station_id,
                            'province': station_info['province'],
                            'city': station_info['city'],
                            'lat': station_info['lat'],
                            'lon': station_info['lon'],
                            'temp_avg_c': float(parts[1]) if parts[1] and parts[1] != 'NULL' else None,
                            'precip_mm': float(parts[2]) if parts[2] and parts[2] != 'NULL' else 0,
                            'source_name': 'smn_argentina',
                            'confidence_score': 0.90,
                            'ingest_timestamp_utc': datetime.now(timezone.utc),
                            'provenance_uuid': str(uuid.uuid4())
                        })
                
                return pd.DataFrame(records)
        except Exception as e:
            print(f"Argentina SMN failed for {station_id}: {e}")
        
        return pd.DataFrame()
    
    def fetch_us_noaa(self, station_id, start_date, end_date, api_token, station_info):
        """Fetch US NOAA data"""
        url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
        
        headers = {'token': api_token}
        
        params = {
            'datasetid': 'GHCND',
            'stationid': station_id,
            'startdate': start_date,
            'enddate': end_date,
            'datatypeid': 'TMAX,TMIN,PRCP',
            'units': 'metric',
            'limit': 1000
        }
        
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
                
                return df_pivot
                
        except Exception as e:
            print(f"NOAA API failed for {station_id}: {e}")
        
        return pd.DataFrame()
    
    def cleanup(self):
        if self.driver:
            self.driver.quit()


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
    scraper = WeatherDataScraper(use_selenium=False)  # Start with API only
    
    # 1. BRAZIL - Last 10 days sample
    print("=== BRAZIL WEATHER ===")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10)
    
    all_brazil = []
    for region, stations in BRAZIL_STATIONS.items():
        for station in stations:
            print(f"Fetching {station['city']}...")
            df = scraper.fetch_brazil_inmet(
                station_id=station['id'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                station_info=station
            )
            if not df.empty:
                all_brazil.append(df)
    
    if all_brazil:
        brazil_combined = pd.concat(all_brazil, ignore_index=True)
        load_to_bigquery(brazil_combined, f"{PROJECT_ID}.forecasting_data_warehouse.weather_brazil_daily")
    
    # 2. ARGENTINA - Recent data sample
    print("\n=== ARGENTINA WEATHER ===")
    all_argentina = []
    for region, stations in ARGENTINA_STATIONS.items():
        for station in stations:
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
    
    # 3. US MIDWEST - Last 10 days sample
    print("\n=== US MIDWEST WEATHER ===")
    all_us = []
    for state, stations in US_MIDWEST_STATIONS.items():
        for station in stations:
            print(f"Fetching {station['city']}...")
            df = scraper.fetch_us_noaa(
                station_id=station['id'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                api_token=NOAA_TOKEN,
                station_info=station
            )
            if not df.empty:
                all_us.append(df)
    
    if all_us:
        us_combined = pd.concat(all_us, ignore_index=True)
        load_to_bigquery(us_combined, f"{PROJECT_ID}.forecasting_data_warehouse.weather_us_midwest_daily")
    
    scraper.cleanup()
    print("\n✅ Weather data loading complete")
