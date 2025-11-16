#!/usr/bin/env python3
"""
Collect data from Google's massive public datasets.
Free up to 1TB/month processing, contains decades of data.

Author: AI Assistant
Date: November 16, 2025
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from google.cloud import bigquery
from pytrends import TrendReq
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
RAW_DIR = DRIVE / "TrainingData/raw/google_datasets"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Initialize BigQuery client
client = bigquery.Client(project='cbi-v14')

def collect_noaa_weather_data():
    """
    Collect comprehensive weather data from NOAA GSOD (Global Surface Summary of Day).
    Available from 1929-present, covers 30,000+ stations globally.
    """
    logger.info("Collecting NOAA weather data from BigQuery public dataset...")
    
    query = """
    WITH stations AS (
        -- Get stations in key agricultural regions
        SELECT DISTINCT
            usaf,
            wban,
            name,
            country,
            state,
            lat,
            lon
        FROM `bigquery-public-data.noaa_gsod.stations`
        WHERE country IN ('US', 'BR', 'AR', 'CN', 'IN', 'UA', 'RU')
            AND lat BETWEEN -60 AND 60  -- Agricultural zones
            AND lon IS NOT NULL
            AND lat IS NOT NULL
    ),
    weather_data AS (
        SELECT 
            PARSE_DATE('%Y%m%d', CAST(g.year * 10000 + g.mo * 100 + g.da AS STRING)) as date,
            s.country,
            s.state,
            s.name as station_name,
            s.lat,
            s.lon,
            
            -- Temperature (Fahrenheit)
            g.temp,  -- Mean temperature
            g.max,   -- Max temperature
            g.min,   -- Min temperature
            
            -- Precipitation
            g.prcp,  -- Total precipitation (inches)
            g.sndp,  -- Snow depth (inches)
            
            -- Wind
            g.wdsp,  -- Wind speed (knots)
            g.mxspd, -- Max sustained wind speed
            g.gust,  -- Max wind gust
            
            -- Pressure & Humidity
            g.slp,   -- Sea level pressure
            g.stp,   -- Station pressure
            g.dewp,  -- Dew point
            
            -- Visibility
            g.visib, -- Visibility (miles)
            
            -- Weather events (binary flags)
            g.fog,
            g.rain_drizzle,
            g.snow_ice_pellets,
            g.hail,
            g.thunder,
            g.tornado_funnel_cloud
            
        FROM `bigquery-public-data.noaa_gsod.gsod*` g
        INNER JOIN stations s
            ON g.stn = s.usaf AND g.wban = s.wban
        WHERE g.year >= 2000
            AND g.year <= EXTRACT(YEAR FROM CURRENT_DATE())
    )
    SELECT 
        date,
        country,
        state,
        
        -- Aggregate by country/state
        AVG(temp) as avg_temp,
        MAX(max) as max_temp,
        MIN(min) as min_temp,
        AVG(prcp) as avg_precip,
        SUM(CASE WHEN prcp > 0 THEN 1 ELSE 0 END) as rainy_days,
        MAX(prcp) as max_daily_precip,
        AVG(wdsp) as avg_wind_speed,
        AVG(dewp) as avg_dewpoint,
        
        -- Extreme weather counts
        SUM(CAST(fog AS INT64)) as fog_stations,
        SUM(CAST(thunder AS INT64)) as thunder_stations,
        SUM(CAST(hail AS INT64)) as hail_stations,
        
        COUNT(DISTINCT station_name) as reporting_stations
        
    FROM weather_data
    WHERE temp < 999.9  -- Filter out missing values (999.9 is NOAA's missing indicator)
    GROUP BY date, country, state
    ORDER BY date, country, state
    """
    
    # Execute query
    df = client.query(query).to_dataframe()
    
    # Save by country
    for country in df['country'].unique():
        country_df = df[df['country'] == country]
        output_path = RAW_DIR / f"noaa_weather_{country.lower()}_2000_2025.parquet"
        country_df.to_parquet(output_path, compression='zstd')
        logger.info(f"Saved {country}: {len(country_df)} rows to {output_path}")
    
    logger.info(f"Total weather data collected: {len(df)} rows")
    return df


def collect_fred_economic_data():
    """
    Collect ALL Federal Reserve Economic Data (FRED) from BigQuery.
    Contains 1000s of economic time series.
    """
    logger.info("Collecting FRED economic data from BigQuery public dataset...")
    
    # Get all relevant series
    series_query = """
    SELECT DISTINCT
        series_id,
        title,
        units,
        frequency,
        seasonal_adjustment,
        popularity,
        group_popularity
    FROM `bigquery-public-data.federal_reserve_economic_data.fred_series_metadata`
    WHERE (
        -- Interest rates
        REGEXP_CONTAINS(series_id, r'(DFF|DGS|SOFR|IORB|PRIME|TB3MS|TB6MS)')
        -- Inflation
        OR REGEXP_CONTAINS(series_id, r'(CPI|PCE|PPI|DFED|T5YIE|T10YIE)')
        -- Currency
        OR REGEXP_CONTAINS(series_id, r'(DEX|TWE)')
        -- Commodities
        OR REGEXP_CONTAINS(series_id, r'(DCOIL|GAS|GOLD|SILVER|WHEAT|CORN|SOYBEAN)')
        -- Economic indicators
        OR REGEXP_CONTAINS(series_id, r'(GDP|UNRATE|PAYEMS|INDPRO|RETAIL|UMCSENT|VIX)')
        -- Agricultural specific
        OR REGEXP_CONTAINS(title, r'(?i)(agricultural|farm|crop|livestock|fertilizer)')
    )
    AND popularity >= 10  -- Filter out rarely used series
    ORDER BY group_popularity DESC, popularity DESC
    """
    
    series_df = client.query(series_query).to_dataframe()
    logger.info(f"Found {len(series_df)} relevant FRED series")
    
    # Get actual data for these series
    data_query = f"""
    SELECT 
        d.series_id,
        d.date,
        d.value,
        m.title,
        m.units,
        m.frequency
    FROM `bigquery-public-data.federal_reserve_economic_data.fred_data` d
    INNER JOIN `bigquery-public-data.federal_reserve_economic_data.fred_series_metadata` m
        ON d.series_id = m.series_id
    WHERE d.series_id IN ({','.join([f"'{s}'" for s in series_df['series_id'].head(500)])})
        AND d.date >= '2000-01-01'
        AND d.value IS NOT NULL
    ORDER BY d.series_id, d.date
    """
    
    # Execute in chunks if needed
    df = client.query(data_query).to_dataframe()
    
    # Pivot to wide format
    pivot_df = df.pivot_table(
        index='date',
        columns='series_id',
        values='value',
        aggfunc='first'
    )
    
    # Save
    output_path = RAW_DIR / "fred_comprehensive_2000_2025.parquet"
    pivot_df.to_parquet(output_path, compression='zstd')
    logger.info(f"Saved FRED data: {pivot_df.shape} to {output_path}")
    
    # Also save metadata
    series_df.to_csv(RAW_DIR / "fred_series_metadata.csv", index=False)
    
    return pivot_df


def collect_international_trade_data():
    """
    Collect UN Comtrade international trade data.
    Focus on agricultural commodities.
    """
    logger.info("Collecting international trade data from BigQuery...")
    
    query = """
    SELECT 
        year,
        reporter_iso3,
        partner_iso3,
        commodity_code,
        commodity,
        trade_flow,  -- Import/Export
        trade_value_usd,
        quantity,
        quantity_unit
    FROM `bigquery-public-data.international_trade.comtrade_exports`
    WHERE year >= 2000
        AND commodity_code IN (
            '1201',  -- Soybeans
            '1507',  -- Soybean oil
            '2304',  -- Soybean meal/cake
            '1005',  -- Corn/maize
            '1001',  -- Wheat
            '1511',  -- Palm oil
            '1514',  -- Rapeseed oil
            '1512'   -- Sunflower oil
        )
        AND reporter_iso3 IN ('USA', 'BRA', 'ARG', 'CHN', 'IND', 'CAN', 'UKR', 'RUS')
    ORDER BY year, reporter_iso3, commodity_code
    """
    
    df = client.query(query).to_dataframe()
    
    # Calculate trade balances and flows
    trade_summary = df.groupby(['year', 'reporter_iso3', 'commodity']).agg({
        'trade_value_usd': 'sum',
        'quantity': 'sum'
    }).reset_index()
    
    # Save
    output_path = RAW_DIR / "un_comtrade_agriculture_2000_2025.parquet"
    df.to_parquet(output_path, compression='zstd')
    logger.info(f"Saved trade data: {len(df)} rows to {output_path}")
    
    return df


def collect_covid_impact_data():
    """
    Collect COVID-19 data as proxy for supply chain disruptions.
    """
    logger.info("Collecting COVID-19 impact data...")
    
    query = """
    SELECT 
        date,
        location_key,
        country_name,
        subregion1_name as state,
        
        -- Health metrics
        new_confirmed,
        new_deceased,
        cumulative_confirmed,
        cumulative_deceased,
        
        -- Economic impact
        stringency_index,  -- Policy stringency
        government_response_index,
        economic_support_index,
        containment_health_index,
        
        -- Mobility (supply chain proxy)
        mobility_retail_and_recreation,
        mobility_grocery_and_pharmacy,
        mobility_transit_stations,
        mobility_workplaces
        
    FROM `bigquery-public-data.covid19_open_data.covid19_open_data`
    WHERE date >= '2020-01-01'
        AND country_code IN ('US', 'BR', 'AR', 'CN', 'IN')
        AND aggregation_level <= 1  -- Country or state level
    ORDER BY date, location_key
    """
    
    df = client.query(query).to_dataframe()
    
    # Save
    output_path = RAW_DIR / "covid_impact_2020_2025.parquet"
    df.to_parquet(output_path, compression='zstd')
    logger.info(f"Saved COVID data: {len(df)} rows to {output_path}")
    
    return df


def collect_google_trends_data():
    """
    Collect Google Trends data for sentiment analysis.
    Search volume is a great proxy for public concern.
    """
    logger.info("Collecting Google Trends data...")
    
    # Initialize PyTrends
    pytrends = TrendReq(hl='en-US', tz=360)
    
    # Keywords to track
    keywords_sets = [
        ['soybean prices', 'crop failure', 'drought', 'food prices'],
        ['china trade war', 'tariffs', 'trump china', 'trade deal'],
        ['biofuel', 'ethanol', 'renewable diesel', 'biodiesel'],
        ['inflation', 'fed rates', 'recession', 'economic crisis'],
        ['ukraine war', 'russia sanctions', 'grain exports', 'food crisis']
    ]
    
    all_trends = []
    
    for keywords in keywords_sets:
        try:
            # Build payload
            pytrends.build_payload(
                keywords,
                timeframe='2004-01-01 2025-12-31',  # Google Trends starts 2004
                geo='',  # Worldwide
                gprop=''
            )
            
            # Get interest over time
            interest_df = pytrends.interest_over_time()
            
            if not interest_df.empty:
                interest_df = interest_df.drop('isPartial', axis=1, errors='ignore')
                all_trends.append(interest_df)
                logger.info(f"Collected trends for: {keywords}")
                
        except Exception as e:
            logger.warning(f"Failed to get trends for {keywords}: {e}")
    
    # Combine all trends
    if all_trends:
        trends_df = pd.concat(all_trends, axis=1)
        trends_df = trends_df.loc[:, ~trends_df.columns.duplicated()]  # Remove duplicate columns
        
        # Save
        output_path = RAW_DIR / "google_trends_2004_2025.parquet"
        trends_df.to_parquet(output_path, compression='zstd')
        logger.info(f"Saved Google Trends: {trends_df.shape} to {output_path}")
        
        return trends_df
    
    return pd.DataFrame()


def collect_all_google_datasets():
    """
    Master function to collect all Google public datasets.
    """
    print("="*80)
    print("COLLECTING GOOGLE PUBLIC DATASETS")
    print("="*80)
    
    results = {}
    
    # 1. Weather data (most comprehensive)
    try:
        weather_df = collect_noaa_weather_data()
        results['weather'] = weather_df.shape
        print(f"✅ Weather data: {weather_df.shape}")
    except Exception as e:
        print(f"❌ Weather collection failed: {e}")
    
    # 2. Economic data (FRED)
    try:
        fred_df = collect_fred_economic_data()
        results['fred'] = fred_df.shape
        print(f"✅ FRED data: {fred_df.shape}")
    except Exception as e:
        print(f"❌ FRED collection failed: {e}")
    
    # 3. Trade data
    try:
        trade_df = collect_international_trade_data()
        results['trade'] = trade_df.shape
        print(f"✅ Trade data: {trade_df.shape}")
    except Exception as e:
        print(f"❌ Trade collection failed: {e}")
    
    # 4. COVID impact (supply chain proxy)
    try:
        covid_df = collect_covid_impact_data()
        results['covid'] = covid_df.shape
        print(f"✅ COVID data: {covid_df.shape}")
    except Exception as e:
        print(f"❌ COVID collection failed: {e}")
    
    # 5. Google Trends (sentiment)
    try:
        trends_df = collect_google_trends_data()
        results['trends'] = trends_df.shape
        print(f"✅ Google Trends: {trends_df.shape}")
    except Exception as e:
        print(f"❌ Trends collection failed: {e}")
    
    print("\n" + "="*80)
    print("GOOGLE DATASETS COLLECTION COMPLETE")
    print(f"Results: {results}")
    print("="*80)
    
    return results


if __name__ == "__main__":
    # Note: Requires GOOGLE_APPLICATION_CREDENTIALS environment variable
    # or authenticated gcloud CLI
    
    collect_all_google_datasets()
