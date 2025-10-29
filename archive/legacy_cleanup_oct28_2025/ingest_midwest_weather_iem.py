#!/usr/bin/env python3
"""
Iowa Environmental Mesonet (IEM) Weather Data Scraper
Scrapes Midwest weather data from IEM for agricultural forecasting
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from bigquery_utils import load_to_bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the Midwest region networks
MIDWEST_NETWORKS = [
    "IACLIMATE",  # Iowa
    "ILCLIMATE",  # Illinois  
    "INCLIMATE",  # Indiana
    "MICLIMATE",  # Michigan
    "MNCLIMATE",  # Minnesota
    "MOCLIMATE",  # Missouri
    "NDCLIMATE",  # North Dakota
    "NECLIMATE",  # Nebraska
    "OHCLIMATE",  # Ohio
    "SDCLIMATE",  # South Dakota
    "WICLIMATE"   # Wisconsin
]

def get_midwest_weather_data(days_back=30):
    """
    Scrape Midwest weather data from Iowa Environmental Mesonet
    """
    logger.info(f"Scraping Midwest weather data for last {days_back} days")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    all_data = []
    
    for network in MIDWEST_NETWORKS:
        logger.info(f"Processing network: {network}")
        
        try:
            # Get station list for this network
            stations_url = f"https://mesonet.agron.iastate.edu/request/coop/fe.phtml?network={network}"
            response = requests.get(stations_url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get stations for {network}: {response.status_code}")
                continue
                
            # Parse station data (simplified - get first 3 stations per network)
            # In production, you'd parse the HTML to get all stations
            sample_stations = [f"{network}001", f"{network}002", f"{network}003"]
            
            for station in sample_stations:
                try:
                    # Get weather data for this station
                    data_url = f"https://mesonet.agron.iastate.edu/cgi-bin/request/coop.py"
                    params = {
                        'network': network,
                        'station': station,
                        'year1': start_date.year,
                        'month1': start_date.month,
                        'day1': start_date.day,
                        'year2': end_date.year,
                        'month2': end_date.month,
                        'day2': end_date.day,
                        'vars[]': ['high', 'low', 'precip'],
                        'format': 'csv'
                    }
                    
                    response = requests.get(data_url, params=params, timeout=30)
                    
                    if response.status_code == 200 and len(response.content) > 100:
                        # Parse CSV data
                        from io import StringIO
                        df = pd.read_csv(StringIO(response.text), skiprows=5)
                        
                        if not df.empty:
                            df['network'] = network
                            df['station'] = station
                            df['region'] = 'US_Midwest'
                            all_data.append(df)
                            logger.info(f"Got {len(df)} records from {station}")
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Error getting data for {station}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing network {network}: {e}")
            continue
    
    if not all_data:
        logger.error("No data collected from any network")
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Total records collected: {len(combined_df)}")
    
    # Process and standardize columns
    processed_df = standardize_weather_data(combined_df)
    
    return processed_df

def standardize_weather_data(df):
    """
    Standardize weather data to match BigQuery schema
    """
    logger.info("Standardizing weather data")
    
    # Rename columns to match our schema
    df = df.rename(columns={
        'day': 'date',
        'high': 'temp_max',
        'low': 'temp_min',
        'precip': 'precip_mm'
    })
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Add required columns
    df['station_id'] = df['station']
    df['source_name'] = 'IEM_Midwest'
    df['confidence_score'] = 0.95
    df['ingest_timestamp_utc'] = datetime.utcnow()
    df['provenance_uuid'] = df.apply(lambda x: f"iem_{x['network']}_{x['station']}_{x['date']}", axis=1)
    
    # Select and order columns to match schema
    final_df = df[[
        'date', 'region', 'station_id', 'precip_mm', 
        'temp_max', 'temp_min', 'source_name', 
        'confidence_score', 'ingest_timestamp_utc', 'provenance_uuid'
    ]].copy()
    
    # Remove any rows with all NaN values
    final_df = final_df.dropna(subset=['temp_max', 'temp_min', 'precip_mm'], how='all')
    
    logger.info(f"Standardized data: {len(final_df)} records")
    return final_df

def main():
    """
    Main execution function
    """
    logger.info("Starting Midwest weather data ingestion")
    
    try:
        # Get weather data
        weather_df = get_midwest_weather_data(days_back=30)
        
        if weather_df is not None and not weather_df.empty:
            # Load to BigQuery
            logger.info("Loading data to BigQuery")
            load_to_bigquery(
                weather_df, 
                'cbi-v14.forecasting_data_warehouse.weather_data',
                write_disposition='WRITE_APPEND'
            )
            logger.info(f"Successfully loaded {len(weather_df)} weather records")
        else:
            logger.warning("No weather data to load")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
