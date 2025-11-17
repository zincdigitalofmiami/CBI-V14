#!/usr/bin/env python3
"""
Brazil Weather Data Collection from Google BigQuery NOAA Dataset
=================================================================
Backup solution for Brazil weather since INMET API is not accessible.
Uses Google BigQuery public dataset: bigquery-public-data.noaa_gsod
Temperature in CELSIUS (convert from Fahrenheit in NOAA data)
Saves to external drive in parquet format
"""

from google.cloud import bigquery
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

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
RAW_DIR = EXTERNAL_DRIVE / "TrainingData/raw/brazil_weather"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Key soybean production regions in Brazil
BRAZIL_REGIONS = {
    'Mato Grosso': {
        'states': ['MT'],
        'production_weight': 0.355,
        'key_cities': ['Cuiabá', 'Sinop', 'Sorriso', 'Alta Floresta']
    },
    'Mato Grosso do Sul': {
        'states': ['MS'], 
        'production_weight': 0.108,
        'key_cities': ['Campo Grande', 'Dourados']
    },
    'Rio Grande do Sul': {
        'states': ['RS'],
        'production_weight': 0.087,
        'key_cities': ['Porto Alegre', 'Santa Maria']
    },
    'Paraná': {
        'states': ['PR'],
        'production_weight': 0.085,
        'key_cities': ['Curitiba', 'Londrina']
    },
    'Goiás': {
        'states': ['GO'],
        'production_weight': 0.065,
        'key_cities': ['Goiânia']
    }
}

def fahrenheit_to_celsius(f):
    """Convert Fahrenheit to Celsius"""
    if f is None or pd.isna(f):
        return None
    return (f - 32) * 5/9

def collect_brazil_weather():
    """
    Collect Brazil weather data from BigQuery NOAA GSOD dataset
    """
    logger.info("="*80)
    logger.info("BRAZIL WEATHER COLLECTION FROM BIGQUERY")
    logger.info("="*80)
    logger.info("Using Google BigQuery public dataset: bigquery-public-data.noaa_gsod")
    logger.info(f"Date range: {START_DATE} to {END_DATE}")
    logger.info("="*80)
    
    # Build query for Brazil stations
    query = f"""
    WITH brazil_stations AS (
        SELECT DISTINCT
            usaf,
            wban,
            name,
            country,
            state,
            lat,
            lon
        FROM `bigquery-public-data.noaa_gsod.stations`
        WHERE country = 'BR'
            AND state IN ('MT', 'MS', 'RS', 'PR', 'GO', 'SP', 'MG', 'BA', 'SC', 'TO')
            AND lat IS NOT NULL
            AND lon IS NOT NULL
    ),
    weather_data AS (
        SELECT 
            s.usaf,
            s.name as station_name,
            s.state,
            s.lat,
            s.lon,
            w.date,
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
        FROM brazil_stations s
        CROSS JOIN UNNEST(
            GENERATE_DATE_ARRAY(DATE('{START_DATE}'), DATE('{END_DATE}'), INTERVAL 1 YEAR)
        ) AS year_start
        JOIN `bigquery-public-data.noaa_gsod.gsod*` w
        ON s.usaf = w.stn
        WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y', year_start) 
                                AND FORMAT_DATE('%Y', DATE_ADD(year_start, INTERVAL 1 YEAR))
            AND w.date BETWEEN DATE('{START_DATE}') AND DATE('{END_DATE}')
    )
    SELECT 
        date,
        usaf as station_id,
        station_name,
        state,
        lat,
        lon,
        temp,
        max as temp_max_f,
        min as temp_min_f,
        prcp as precipitation_inches,
        dewp as dew_point_f,
        slp as sea_level_pressure,
        stp as station_pressure,
        visib as visibility_miles,
        wdsp as wind_speed,
        gust as wind_gust,
        sndp as snow_depth_inches
    FROM weather_data
    WHERE temp != 9999.9  -- Filter out missing values
    ORDER BY date, station_id
    """
    
    logger.info("Executing BigQuery query...")
    
    try:
        # Execute query
        df = CLIENT.query(query).to_dataframe()
        
        if df.empty:
            logger.error("No data returned from BigQuery")
            return None
        
        logger.info(f"Retrieved {len(df)} weather records")
        
        # Convert temperatures from Fahrenheit to Celsius
        logger.info("Converting temperatures to Celsius...")
        df['temp_c'] = df['temp'].apply(fahrenheit_to_celsius)
        df['temp_max_c'] = df['temp_max_f'].apply(fahrenheit_to_celsius)
        df['temp_min_c'] = df['temp_min_f'].apply(fahrenheit_to_celsius)
        df['dew_point_c'] = df['dew_point_f'].apply(fahrenheit_to_celsius)
        
        # Convert precipitation from inches to mm
        df['precipitation_mm'] = df['precipitation_inches'] * 25.4
        
        # Add region information based on state
        def get_region(state):
            for region, info in BRAZIL_REGIONS.items():
                if state in info['states']:
                    return region
            return 'Other'
        
        df['region'] = df['state'].apply(get_region)
        
        # Add production weight
        def get_production_weight(region):
            if region in BRAZIL_REGIONS:
                return BRAZIL_REGIONS[region]['production_weight']
            return 0.0
        
        df['production_weight'] = df['region'].apply(get_production_weight)
        
        # Filter to key regions
        df_key_regions = df[df['region'] != 'Other'].copy()
        
        logger.info(f"Filtered to {len(df_key_regions)} records in key soybean regions")
        
        # Save by state
        for state in df_key_regions['state'].unique():
            state_df = df_key_regions[df_key_regions['state'] == state]
            
            if not state_df.empty:
                output_file = RAW_DIR / f"brazil_{state}_weather.parquet"
                state_df.to_parquet(output_file, index=False)
                logger.info(f"Saved {len(state_df)} records for {state} to {output_file.name}")
        
        # Save combined file
        combined_file = RAW_DIR / "brazil_weather_combined.parquet"
        df_key_regions.to_parquet(combined_file, index=False)
        
        # Summary statistics
        logger.info("="*80)
        logger.info("COLLECTION SUMMARY")
        logger.info("="*80)
        logger.info(f"Total records: {len(df_key_regions)}")
        logger.info(f"Date range: {df_key_regions['date'].min()} to {df_key_regions['date'].max()}")
        logger.info(f"Stations: {df_key_regions['station_id'].nunique()}")
        logger.info(f"States covered: {sorted(df_key_regions['state'].unique())}")
        
        # Production-weighted averages
        total_weight = df_key_regions.groupby('date')['production_weight'].first().sum()
        if total_weight > 0:
            weighted_temp = (df_key_regions.groupby('date').apply(
                lambda x: (x['temp_c'] * x['production_weight']).sum() / x['production_weight'].sum()
            )).mean()
            
            logger.info(f"\n🌾 Production-weighted average temperature: {weighted_temp:.1f}°C")
        
        logger.info(f"\n✅ Saved to: {combined_file}")
        
        return df_key_regions
        
    except Exception as e:
        logger.error(f"Error querying BigQuery: {e}")
        return None

def main():
    """Main execution"""
    df = collect_brazil_weather()
    
    if df is not None and not df.empty:
        logger.info("\n✅ Brazil weather collection successful!")
        return 0
    else:
        logger.error("\n❌ Brazil weather collection failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
