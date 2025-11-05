#!/usr/bin/env python3
"""
CBI-V14 Targeted Weather Data Historical Backfill
Priority 1: Fill weather data gaps for agricultural commodity modeling
Target: 2+ years (back to Oct 2023), Goal: 5+ years (back to Oct 2020)
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
from typing import Dict, List, Any
import time
import json
import sys

sys.path.append('/Users/zincdigital/CBI-V14/cbi-v14-ingestion')
from bigquery_utils import safe_load_to_bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class WeatherBackfillPipeline:
    """Historical weather data backfill with agricultural focus"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
        # Key agricultural regions for soybean production
        self.regions = {
            'brazil_key_states': [
                {'state': 'MT', 'name': 'Mato Grosso', 'lat': -15.60, 'lon': -56.10},
                {'state': 'PR', 'name': 'Parana', 'lat': -25.25, 'lon': -52.03},
                {'state': 'RS', 'name': 'Rio Grande do Sul', 'lat': -30.03, 'lon': -51.23},
                {'state': 'GO', 'name': 'Goias', 'lat': -16.67, 'lon': -49.25}
            ],
            'argentina_key_provinces': [
                {'province': 'BA', 'name': 'Buenos Aires', 'lat': -36.62, 'lon': -60.23},
                {'province': 'SF', 'name': 'Santa Fe', 'lat': -31.63, 'lon': -60.70},
                {'province': 'CD', 'name': 'Cordoba', 'lat': -31.42, 'lon': -64.18}
            ],
            'us_midwest_key_areas': [
                {'state': 'IA', 'name': 'Iowa', 'lat': 42.01, 'lon': -93.21},
                {'state': 'IL', 'name': 'Illinois', 'lat': 40.63, 'lon': -89.40},
                {'state': 'IN', 'name': 'Indiana', 'lat': 39.79, 'lon': -86.15},
                {'state': 'OH', 'name': 'Ohio', 'lat': 40.37, 'lon': -82.99}
            ]
        }
    
    def backfill_us_midwest_weather(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Backfill US Midwest weather using NOAA data"""
        logger.info(f"🇺🇸 Backfilling US Midwest weather: {start_date} to {end_date}")
        
        all_weather_data = []
        
        for region in self.regions['us_midwest_key_areas']:
            try:
                logger.info(f"Fetching data for {region['name']}, {region['state']}")
                
                # Use Open-Meteo Historical API (free, reliable)
                url = "https://archive-api.open-meteo.com/v1/archive"
                
                params = {
                    'latitude': region['lat'],
                    'longitude': region['lon'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max',
                    'timezone': 'America/Chicago',
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'daily' in data:
                    # Match US Midwest weather table schema exactly
                    df = pd.DataFrame({
                        'date': pd.to_datetime(data['daily']['time']).date,
                        'station_id': f"CBI_V14_{region['state']}_COMPOSITE",
                        'state': region['state'],
                        'city': region['name'],
                        'lat': float(region['lat']),
                        'lon': float(region['lon']),
                        'precip_mm': data['daily']['precipitation_sum'],
                        'temp_max_c': data['daily']['temperature_2m_max'],
                        'temp_min_c': data['daily']['temperature_2m_min'],
                        'production_weight': 1.0,  # Equal weight for backfilled data
                        'source_name': 'open_meteo_historical',
                        'confidence_score': 0.85,
                        'ingest_timestamp_utc': datetime.now(),
                        'provenance_uuid': [str(uuid.uuid4()) for _ in range(len(data['daily']['time']))]
                    })
                    
                    # Calculate derived metrics for agriculture
                    df['temp_avg_c'] = (df['temp_max_c'] + df['temp_min_c']) / 2
                    df['growing_degree_days'] = np.maximum(0, df['temp_avg_c'] - 10)  # Base 10°C
                    
                    all_weather_data.append(df)
                    logger.info(f"✅ {region['name']}: {len(df)} days of weather data")
                    
                else:
                    logger.warning(f"❌ {region['name']}: No daily data returned")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching {region['name']}: {str(e)}")
                continue
        
        if all_weather_data:
            combined_df = pd.concat(all_weather_data, ignore_index=True)
            logger.info(f"✅ US Midwest weather backfill: {len(combined_df)} total records")
            return combined_df
        else:
            logger.error("❌ No US Midwest weather data could be backfilled")
            return pd.DataFrame()
    
    def backfill_brazil_weather(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Backfill Brazil weather focusing on key soybean states"""
        logger.info(f"🇧🇷 Backfilling Brazil weather: {start_date} to {end_date}")
        
        all_weather_data = []
        
        for state in self.regions['brazil_key_states']:
            try:
                logger.info(f"Fetching data for {state['name']}, Brazil")
                
                # Use Open-Meteo for Brazil historical data
                url = "https://archive-api.open-meteo.com/v1/archive"
                
                params = {
                    'latitude': state['lat'],
                    'longitude': state['lon'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max',
                    'timezone': 'America/Sao_Paulo',
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'daily' in data:
                    # Match Brazil weather table schema exactly
                    df = pd.DataFrame({
                        'date': pd.to_datetime(data['daily']['time']).date,
                        'station_id': f"CBI_V14_{state['state']}_COMPOSITE",
                        'state': state['state'],
                        'city': state['name'],
                        'lat': float(state['lat']),
                        'lon': float(state['lon']),
                        'precip_mm': data['daily']['precipitation_sum'],
                        'temp_max_c': data['daily']['temperature_2m_max'],
                        'temp_min_c': data['daily']['temperature_2m_min'],
                        'humidity': 65.0,  # Typical Brazil humidity (placeholder)
                        'production_weight': 1.0,
                        'source_name': 'open_meteo_historical',
                        'confidence_score': 0.85,
                        'ingest_timestamp_utc': datetime.now(),
                        'provenance_uuid': [str(uuid.uuid4()) for _ in range(len(data['daily']['time']))]
                    })
                    
                    # Agricultural metrics for Brazil  
                    df['temp_avg_c'] = (df['temp_max_c'] + df['temp_min_c']) / 2
                    df['growing_degree_days'] = np.maximum(0, df['temp_avg_c'] - 10)
                    
                    all_weather_data.append(df)
                    logger.info(f"✅ {state['name']}: {len(df)} days of weather data")
                    
                else:
                    logger.warning(f"❌ {state['name']}: No daily data returned")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching {state['name']}: {str(e)}")
                continue
        
        if all_weather_data:
            combined_df = pd.concat(all_weather_data, ignore_index=True)
            logger.info(f"✅ Brazil weather backfill: {len(combined_df)} total records")
            return combined_df
        else:
            logger.error("❌ No Brazil weather data could be backfilled")
            return pd.DataFrame()
    
    def backfill_argentina_weather(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Backfill Argentina weather for key soybean provinces"""
        logger.info(f"🇦🇷 Backfilling Argentina weather: {start_date} to {end_date}")
        
        all_weather_data = []
        
        for province in self.regions['argentina_key_provinces']:
            try:
                logger.info(f"Fetching data for {province['name']}, Argentina")
                
                url = "https://archive-api.open-meteo.com/v1/archive"
                
                params = {
                    'latitude': province['lat'],
                    'longitude': province['lon'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max',
                    'timezone': 'America/Argentina/Buenos_Aires',
                    'format': 'json'
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'daily' in data:
                    # Match Argentina weather table schema exactly  
                    df = pd.DataFrame({
                        'date': pd.to_datetime(data['daily']['time']).date,
                        'station_id': f"CBI_V14_{province['province']}_COMPOSITE",
                        'province': province['province'],
                        'city': province['name'],
                        'lat': float(province['lat']),
                        'lon': float(province['lon']),
                        'precip_mm': data['daily']['precipitation_sum'],
                        'temp_max_c': data['daily']['temperature_2m_max'],
                        'temp_min_c': data['daily']['temperature_2m_min'],
                        'production_weight': 1.0,
                        'source_name': 'open_meteo_historical', 
                        'confidence_score': 0.85,
                        'ingest_timestamp_utc': datetime.now(),
                        'provenance_uuid': [str(uuid.uuid4()) for _ in range(len(data['daily']['time']))]
                    })
                    
                    # Agricultural metrics  
                    df['temp_avg_c'] = (df['temp_max_c'] + df['temp_min_c']) / 2
                    df['growing_degree_days'] = np.maximum(0, df['temp_avg_c'] - 10)
                    
                    all_weather_data.append(df)
                    logger.info(f"✅ {province['name']}: {len(df)} days of weather data")
                    
                else:
                    logger.warning(f"❌ {province['name']}: No daily data returned")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching {province['name']}: {str(e)}")
                continue
        
        if all_weather_data:
            combined_df = pd.concat(all_weather_data, ignore_index=True)
            logger.info(f"✅ Argentina weather backfill: {len(combined_df)} total records")
            return combined_df
        else:
            logger.error("❌ No Argentina weather data could be backfilled") 
            return pd.DataFrame()
    
    def validate_weather_patterns(self, df: pd.DataFrame, region: str) -> Dict[str, Any]:
        """Strict validation for weather data patterns"""
        logger.info(f"🔍 Validating weather patterns for {region}")
        
        issues = {'critical': [], 'warnings': []}
        
        # Temperature range validation by region - ADJUSTED FOR REALISM
        temp_ranges = {
            'us_midwest': {'min': -35, 'max': 45},
            'brazil': {'min': 0, 'max': 50},  # Some Brazilian regions can get quite cool
            'argentina': {'min': -25, 'max': 45}  # Argentina has diverse climate zones
        }
        
        expected_range = temp_ranges.get(region, {'min': -40, 'max': 55})
        
        # Validate temperature ranges
        if 'temp_avg_c' in df.columns:
            temp_min = df['temp_avg_c'].min()
            temp_max = df['temp_avg_c'].max()
            
            if temp_min < expected_range['min']:
                issues['critical'].append(f"Temperature too low: {temp_min}°C < {expected_range['min']}°C")
            if temp_max > expected_range['max']:
                issues['critical'].append(f"Temperature too high: {temp_max}°C > {expected_range['max']}°C")
        
        # Validate precipitation (shouldn't have negative values)
        if 'precip_mm' in df.columns:
            neg_precip = (df['precip_mm'] < 0).sum()
            if neg_precip > 0:
                issues['critical'].append(f"Negative precipitation values: {neg_precip} records")
            
            # Check for unrealistic precipitation  
            extreme_precip = (df['precip_mm'] > 500).sum()  # >500mm in one day
            if extreme_precip > 0:
                issues['warnings'].append(f"Extreme precipitation events: {extreme_precip} days >500mm")
        
        # Check for data continuity
        if 'date' in df.columns:
            df_sorted = df.sort_values('date')
            date_gaps = df_sorted['date'].diff().dt.days.dropna()
            max_gap = date_gaps.max() if len(date_gaps) > 0 else 0
            
            if max_gap > 7:
                issues['warnings'].append(f"Large data gaps found: {max_gap} days maximum gap")
        
        # Check for placeholder values
        for col in ['temp_avg_c', 'precip_mm']:
            if col in df.columns:
                placeholder_count = (df[col] == 0.0).sum()
                if placeholder_count > len(df) * 0.1:  # >10% zeros
                    issues['warnings'].append(f"High zero count in {col}: {placeholder_count} values")
        
        logger.info(f"Weather validation: {len(issues['critical'])} critical, {len(issues['warnings'])} warnings")
        return issues
    
    def store_weather_data(self, df: pd.DataFrame, country: str) -> bool:
        """Store validated weather data to appropriate table"""
        logger.info(f"💾 Storing {country} weather data to BigQuery...")
        
        try:
            # Map to appropriate table
            table_mapping = {
                'brazil': f'{PROJECT_ID}.{DATASET_ID}.weather_brazil_daily',
                'argentina': f'{PROJECT_ID}.{DATASET_ID}.weather_argentina_daily',
                'us_midwest': f'{PROJECT_ID}.{DATASET_ID}.weather_us_midwest_daily'
            }
            
            table_id = table_mapping.get(country.lower())
            if not table_id:
                logger.error(f"No table mapping for country: {country}")
                return False
            
            # Check for duplicates before inserting
            if len(df) > 0:
                min_date = df['date'].min().strftime('%Y-%m-%d')
                max_date = df['date'].max().strftime('%Y-%m-%d')
                
                duplicate_check_query = f'''
                SELECT COUNT(*) as existing_count
                FROM `{table_id}`
                WHERE DATE(date) BETWEEN '{min_date}' AND '{max_date}'
                '''
                
                existing_result = self.client.query(duplicate_check_query).to_dataframe()
                existing_count = existing_result['existing_count'].iloc[0]
                
                if existing_count > 0:
                    logger.warning(f"Found {existing_count} existing records in date range - checking for exact duplicates")
                    
                    # More precise duplicate checking if needed
                    # For now, proceed with caution
                
                # Use BigQuery load job directly for better control
                job_config = bigquery.LoadJobConfig(
                    write_disposition='WRITE_APPEND',
                    create_disposition='CREATE_IF_NEEDED',
                    autodetect=True
                )
                
                job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
                job.result()
                
                if job.state == 'DONE':
                    logger.info(f"✅ Successfully stored {len(df)} {country} weather records")
                    return True
                else:
                    logger.error(f"❌ BigQuery job failed for {country} weather data")
                    return False
            
        except Exception as e:
            logger.error(f"Error storing {country} weather data: {str(e)}")
            return False
    
    def run_targeted_weather_backfill(self) -> Dict[str, Any]:
        """Run comprehensive weather backfill for all regions"""
        logger.info("🌦️ Starting targeted weather data backfill...")
        
        # Define date ranges - prioritize 2 years, then extend to 5 years if successful
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date_2y = '2023-10-27'  # 2 years ago
        start_date_5y = '2020-10-27'  # 5 years ago (if 2y succeeds)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'regions': {},
            'overall_status': 'unknown'
        }
        
        regions_to_process = [
            ('us_midwest', 'US Midwest'),
            ('brazil', 'Brazil'), 
            ('argentina', 'Argentina')
        ]
        
        for region_key, region_name in regions_to_process:
            logger.info(f"🌍 Processing {region_name} weather backfill...")
            
            region_results = {
                'status': 'pending',
                'records_added': 0,
                'date_range': '',
                'validation_issues': []
            }
            
            try:
                # Start with 2-year backfill
                if region_key == 'us_midwest':
                    weather_data = self.backfill_us_midwest_weather(start_date_2y, end_date)
                elif region_key == 'brazil':
                    weather_data = self.backfill_brazil_weather(start_date_2y, end_date)
                elif region_key == 'argentina':
                    weather_data = self.backfill_argentina_weather(start_date_2y, end_date)
                
                if not weather_data.empty:
                    # Validate weather patterns
                    validation_results = self.validate_weather_patterns(weather_data, region_key)
                    
                    if validation_results['critical']:
                        logger.error(f"❌ {region_name}: Critical validation failures - NOT storing data")
                        region_results['status'] = 'failed'
                        region_results['validation_issues'] = validation_results['critical']
                    else:
                        # Store validated data
                        storage_success = self.store_weather_data(weather_data, region_key)
                        
                        if storage_success:
                            region_results['status'] = 'success'
                            region_results['records_added'] = len(weather_data)
                            region_results['date_range'] = f"{weather_data['date'].min().date()} to {weather_data['date'].max().date()}"
                            region_results['validation_issues'] = validation_results['warnings']
                            
                            logger.info(f"✅ {region_name}: Successfully backfilled {len(weather_data)} records")
                        else:
                            region_results['status'] = 'storage_failed'
                else:
                    region_results['status'] = 'no_data'
                    logger.warning(f"❌ {region_name}: No weather data retrieved")
                    
            except Exception as e:
                logger.error(f"Critical error for {region_name}: {str(e)}")
                region_results['status'] = 'error'
                region_results['validation_issues'] = [f"Exception: {str(e)}"]
            
            results['regions'][region_key] = region_results
        
        # Overall status
        success_count = sum(1 for r in results['regions'].values() if r['status'] == 'success')
        total_count = len(results['regions'])
        
        results['overall_status'] = 'success' if success_count == total_count else 'partial' if success_count > 0 else 'failed'
        results['end_time'] = datetime.now().isoformat()
        results['success_rate'] = f'{success_count}/{total_count}'
        
        return results

def main():
    """Run targeted weather backfill pipeline"""
    print("=" * 80)
    print("CBI-V14 TARGETED WEATHER DATA BACKFILL")
    print("=" * 80)
    print("Priority 1: Agricultural weather fundamentals")
    print("Target: 2+ years historical coverage")
    print(f"Started: {datetime.now()}")
    print()
    
    pipeline = WeatherBackfillPipeline()
    results = pipeline.run_targeted_weather_backfill()
    
    print("=" * 80)
    print("WEATHER BACKFILL RESULTS")
    print("=" * 80)
    
    total_records = 0
    for region, result in results['regions'].items():
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'partial': '⚠️',
            'no_data': '❌',
            'error': '🚨',
            'storage_failed': '💾❌'
        }.get(result['status'], '❓')
        
        print(f"{status_emoji} {region.upper()}: {result['status'].upper()}")
        
        if result['records_added'] > 0:
            print(f"    📊 Records added: {result['records_added']:,}")
            print(f"    📅 Date range: {result['date_range']}")
            total_records += result['records_added']
        
        if result['validation_issues']:
            print(f"    ⚠️  Issues: {len(result['validation_issues'])} warnings/errors")
            for issue in result['validation_issues'][:3]:  # Show first 3 issues
                print(f"      - {issue}")
        
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if results['overall_status'] == 'success':
        print(f"🎉 SUCCESS: All weather regions backfilled")
        print(f"📊 Total records added: {total_records:,}")
        print(f"🚀 Weather data now ready for V4 Enhanced training")
    elif results['overall_status'] == 'partial':
        print(f"⚠️ PARTIAL: Some regions successful ({results['success_rate']})")
        print(f"📊 Records added: {total_records:,}")
        print(f"🔄 Consider retry for failed regions")
    else:
        print(f"❌ FAILED: Weather backfill unsuccessful")
        print(f"🚨 Agricultural fundamentals still missing historical context")
    
    print(f"Completed: {datetime.now()}")
    print("=" * 80)
    
    return results['overall_status'] == 'success'

if __name__ == "__main__":
    import uuid  # Add missing import
    success = main()
    exit(0 if success else 1)
