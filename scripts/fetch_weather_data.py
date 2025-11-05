#!/usr/bin/env python3
"""
Fetch Weather Data from NOAA or USDA for US Midwest region
"""
import os
import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
import sys

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
BASE_TABLE = "training_dataset_super_enriched"

# NOAA API configuration
NOAA_TOKEN = os.getenv('NOAA_TOKEN')  # Get from https://www.ncdc.noaa.gov/cdo-web/token
NOAA_BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"

client = bigquery.Client(project=PROJECT_ID)

print("="*80)
print("🌤️  FETCHING WEATHER DATA")
print("="*80)

# Get date range
query = f"""
SELECT 
  MIN(date) as min_date,
  MAX(date) as max_date
FROM `{PROJECT_ID}.{DATASET_ID}.{BASE_TABLE}`
"""
date_range = client.query(query).to_dataframe().iloc[0]
start_date = date_range['min_date']
end_date = date_range['max_date']

print(f"Date range: {start_date} to {end_date}")

# Weather columns to backfill
WEATHER_COLUMNS = [
    'us_midwest_temp_c',
    'us_midwest_precip_mm',
    'us_midwest_conditions_score',
    'us_midwest_drought_days',
    'us_midwest_flood_days',
    'us_midwest_heat_stress_days'
]

if not NOAA_TOKEN:
    print("\n⚠️  NOAA_TOKEN environment variable not set")
    print("   Get free token at: https://www.ncdc.noaa.gov/cdo-web/token")
    print("   Then set: export NOAA_TOKEN='your_token_here'")
    print("\n💡 Alternative sources:")
    print("   1. USDA Weather Data: https://www.nass.usda.gov/")
    print("   2. Weather.gov API: https://www.weather.gov/documentation/services-web-api")
    print("   3. OpenWeatherMap API: https://openweathermap.org/api")
    print("   4. Historical weather data CSV files")
    sys.exit(1)

print("\n📊 Weather Data Sources:")
print("  1. NOAA Climate Data Online (CDO)")
print("  2. USDA Weather Service")
print("  3. Regional weather station averages")
print("\n⚠️  Weather data fetching requires:")
print("  - Station IDs for Midwest region")
print("  - Data type mappings (temperature, precipitation)")
print("  - Derived features calculation (drought days, heat stress, etc.)")

print("\n" + "="*80)
print("📝 IMPLEMENTATION PLAN")
print("="*80)
print("For each weather column:")
print("  1. Identify weather stations in Midwest region")
print("  2. Fetch daily temperature and precipitation")
print("  3. Calculate derived features:")
print("     - drought_days: Days with precip < threshold")
print("     - flood_days: Days with precip > threshold")
print("     - heat_stress_days: Days with temp > threshold")
print("     - conditions_score: Composite score based on temp/precip")
print("  4. Update BigQuery table")
print("="*80)



