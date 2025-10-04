#!/usr/bin/env python3
"""
NOAA Weather Data Ingestion for Agricultural Regions
Fetches precipitation and temperature data
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import os
import sys
import argparse
from bigquery_utils import safe_load_to_bigquery

NOAA_API_TOKEN = "rxoLrCxYOlQyWvVjbBGRlMMhIRElWKZi"
PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
TABLE_ID = "weather_data"

# Station IDs researched for soybean growing regions
STATIONS = {
    "Brazil": [
        "GHCND:BR000083361",  # Cuiaba/Marechal Rondon Airport, Mato Grosso
        "GHCND:BR000083531"   # Campo Grande, Mato Grosso do Sul
    ],
    "Argentina": [
        "GHCND:AR000875760",  # Buenos Aires Aero
        "GHCND:AR000875850"   # Rosario Aero
    ],
    "US": [
        "GHCND:USW00014933",  # Des Moines International Airport, Iowa
        "GHCND:USW00094846"   # Chicago O'Hare, Illinois
    ]
}

def fetch_noaa_data(station_id, start_date, end_date, datatypes=["TMAX", "TMIN", "PRCP"]):
    """
    Fetch weather data from NOAA API
    
    API Docs: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
    Rate limit: 5 requests per second, 10,000 per day
    
    datatypes:
    - PRCP: Precipitation (tenths of mm)
    - TMAX: Maximum temperature (tenths of degrees C)
    - TMIN: Minimum temperature (tenths of degrees C)
    """
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    
    headers = {"token": NOAA_API_TOKEN}
    
    params = {
        "datasetid": "GHCND",  # Global Historical Climatology Network Daily
        "stationid": station_id,
        "startdate": start_date,
        "enddate": end_date,
        "datatypeid": ",".join(datatypes),
        "units": "metric",
        "limit": 1000  # Max per request
    }
    
    try:
        print(f"  Fetching {station_id} from {start_date} to {end_date}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 429:
            print("  Rate limited. Waiting 10 seconds...")
            time.sleep(10)
            return None
        
        response.raise_for_status()
        data = response.json()
        
        if "results" not in data:
            print(f"  No data for {station_id}")
            return None
        
        print(f"  Retrieved {len(data['results'])} observations")
        return data["results"]
        
    except requests.exceptions.RequestException as e:
        print(f"  Request failed: {e}")
        return None

def process_noaa_results(results, region, station_id):
    """
    Convert NOAA results to BigQuery format
    
    NOAA returns one row per datatype per date, need to pivot
    """
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    
    # Parse date
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Pivot: one row per date with columns for each datatype
    pivot = df.pivot_table(
        index='date',
        columns='datatype',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Convert from tenths to actual units
    if 'PRCP' in pivot.columns:
        pivot['precip_mm'] = pivot['PRCP'] / 10.0
    else:
        pivot['precip_mm'] = None
    
    if 'TMAX' in pivot.columns:
        pivot['temp_max'] = pivot['TMAX'] / 10.0
    else:
        pivot['temp_max'] = None
    
    if 'TMIN' in pivot.columns:
        pivot['temp_min'] = pivot['TMIN'] / 10.0
    else:
        pivot['temp_min'] = None
    
    # Add metadata
    pivot['region'] = region
    pivot['station_id'] = station_id
    
    # Select final columns
    pivot = pivot[['date', 'region', 'station_id', 'precip_mm', 'temp_max', 'temp_min']]
    
    return pivot

def load_to_bigquery(df):
    """Load weather data to BigQuery"""
    if df.empty:
        return False
    
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=[
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("region", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("station_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("precip_mm", "FLOAT64"),
            bigquery.SchemaField("temp_max", "FLOAT64"),
            bigquery.SchemaField("temp_min", "FLOAT64"),
        ],
    )
    
    try:
        print(f"  Loading {len(df)} rows to {table_ref}")
        job = safe_load_to_bigquery(client, df, table_ref, job_config)
        job.result()
        print(f"  Success")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False

def backfill_weather(years=2):
    """Backfill weather data for all stations"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"\nBackfilling weather from {start_date.date()} to {end_date.date()}")
    print("=" * 60)
    
    total_rows = 0
    
    for region, station_list in STATIONS.items():
        for station_id in station_list:
            print(f"\nRegion: {region}, Station: {station_id}")
            
            # Fetch in 1-year chunks
            current_start = start_date
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=365), end_date)
                
                start_str = current_start.strftime("%Y-%m-%d")
                end_str = current_end.strftime("%Y-%m-%d")
                
                results = fetch_noaa_data(station_id, start_str, end_str)
                
                if results:
                    df = process_noaa_results(results, region, station_id)
                    if load_to_bigquery(df):
                        total_rows += len(df)
                
                current_start = current_end + timedelta(days=1)
                time.sleep(0.5)  # Rate limiting
    
    print(f"\nBackfill complete: {total_rows} rows loaded")
    return total_rows

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--years", type=int, default=2)
    args = parser.parse_args()
    
    if args.backfill:
        backfill_weather(years=args.years)
    else:
        parser.print_help()
