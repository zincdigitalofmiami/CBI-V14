#!/usr/bin/env python3
"""
Open-Meteo Weather Data Scraper for US Midwest
Gets recent weather data to fill the gap from NOAA API limitations
"""

import requests
import pandas as pd
import pandas_gbq
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Key Midwest agricultural coordinates
MIDWEST_COORDINATES = [
    {"name": "Des_Moines_IA", "lat": 41.5868, "lon": -93.6250},  # Iowa
    {"name": "Springfield_IL", "lat": 39.7817, "lon": -89.6501},  # Illinois
    {"name": "Indianapolis_IN", "lat": 39.7684, "lon": -86.1581},  # Indiana
    {"name": "Lansing_MI", "lat": 42.7325, "lon": -84.5555},  # Michigan
    {"name": "Minneapolis_MN", "lat": 44.9778, "lon": -93.2650},  # Minnesota
    {"name": "Jefferson_City_MO", "lat": 38.5767, "lon": -92.1736},  # Missouri
    {"name": "Bismarck_ND", "lat": 46.8083, "lon": -100.7837},  # North Dakota
    {"name": "Lincoln_NE", "lat": 40.8136, "lon": -96.7026},  # Nebraska
    {"name": "Columbus_OH", "lat": 39.9612, "lon": -82.9988},  # Ohio
    {"name": "Pierre_SD", "lat": 44.3683, "lon": -100.3510},  # South Dakota
    {"name": "Madison_WI", "lat": 43.0731, "lon": -89.4012}   # Wisconsin
]

def get_openmeteo_weather_data(start_date, end_date):
    """
    Get weather data from Open-Meteo API for Midwest coordinates
    """
    logger.info(f"Getting Open-Meteo weather data from {start_date} to {end_date}")
    
    all_data = []
    
    for location in MIDWEST_COORDINATES:
        logger.info(f"Processing {location['name']}")
        
        try:
            # Open-Meteo API endpoint
            url = "https://archive-api.open-meteo.com/v1/archive"
            
            params = {
                "latitude": location["lat"],
                "longitude": location["lon"],
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "temperature_unit": "fahrenheit",
                "precipitation_unit": "mm"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if "daily" in data:
                    # Process the daily data
                    dates = data["daily"]["time"]
                    temp_max = data["daily"]["temperature_2m_max"]
                    temp_min = data["daily"]["temperature_2m_min"]
                    precip = data["daily"]["precipitation_sum"]
                    
                    # Create DataFrame for this location
                    location_df = pd.DataFrame({
                        'date': dates,
                        'temp_max': temp_max,
                        'temp_min': temp_min,
                        'precip_mm': precip,
                        'station_id': f"OPENMETEO_{location['name']}",
                        'region': 'US_Midwest',
                        'location_name': location['name'],
                        'latitude': location['lat'],
                        'longitude': location['lon']
                    })
                    
                    all_data.append(location_df)
                    logger.info(f"Got {len(location_df)} records from {location['name']}")
                else:
                    logger.warning(f"No daily data for {location['name']}")
            else:
                logger.warning(f"API error for {location['name']}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting data for {location['name']}: {e}")
            continue
    
    if not all_data:
        logger.error("No data collected from any location")
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Total records collected: {len(combined_df)}")
    
    return combined_df

def standardize_weather_data(df):
    """
    Standardize weather data to match BigQuery schema
    """
    logger.info("Standardizing Open-Meteo weather data")
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Add required columns
    df['source_name'] = 'OpenMeteo_Midwest'
    df['confidence_score'] = 0.90  # Slightly lower confidence than NOAA
    df['ingest_timestamp_utc'] = datetime.utcnow()
    df['provenance_uuid'] = df.apply(lambda x: f"openmeteo_{x['location_name']}_{x['date']}", axis=1)
    
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
    logger.info("Starting Open-Meteo Midwest weather data ingestion")
    
    try:
        # Get weather data for the missing period (2025-09-20 to current)
        start_date = "2025-09-20"
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        weather_df = get_openmeteo_weather_data(start_date, end_date)
        
        if weather_df is not None and not weather_df.empty:
            # Standardize the data
            processed_df = standardize_weather_data(weather_df)
            
            # Load to STAGING first
            logger.info("Loading data to STAGING")
            processed_df.to_gbq(
                destination_table="staging.weather_data_midwest_openmeteo",
                project_id="cbi-v14",
                if_exists="append"
            )
            logger.info(f"Successfully loaded {len(processed_df)} weather records")
        else:
            logger.warning("No weather data to load")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()
