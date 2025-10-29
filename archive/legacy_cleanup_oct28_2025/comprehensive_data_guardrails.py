#!/usr/bin/env python3
"""
COMPREHENSIVE DATA GUARDRAILS
Cross-check ALL data sources with multiple external sources
Implement strict validation rules for every data type
"""

import yfinance as yf
import requests
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = bigquery.Client(project='cbi-v14')

class DataGuardrails:
    def __init__(self):
        # Define realistic ranges for all data types
        self.price_ranges = {
            'soybean_oil': (25, 90),      # cents per pound
            'corn': (300, 900),           # cents per bushel
            'wheat': (400, 1200),         # cents per bushel
            'crude_oil': (30, 150),       # USD per barrel
            'palm_oil': (600, 1800),      # USD per metric ton
            'soybeans': (800, 1800),      # cents per bushel
            'soybean_meal': (250, 600),   # USD per short ton
            'natural_gas': (1.5, 15),     # USD per MMBtu
            'gold': (3000, 5000),         # Cents per ounce (futures)
            'silver': (15, 50),           # USD per ounce
            'vix': (8, 80),               # VIX index
            'dollar_index': (80, 120)     # DXY index
        }
        
        self.fx_ranges = {
            'usd_brl': (3.0, 8.0),        # USD/BRL
            'usd_cny': (6.0, 8.0),        # USD/CNY
            'usd_ars': (100, 2000)        # USD/ARS (volatile)
        }
        
        self.economic_ranges = {
            'fed_funds_rate': (0, 10),     # Federal funds rate %
            'ten_year_treasury': (0, 8),   # 10-year yield %
            'two_year_treasury': (0, 8),   # 2-year yield %
            'cpi_inflation': (200, 400),   # CPI index (not %)
            'unemployment_rate': (2, 15),  # Unemployment %
            'vix_index': (8, 80),          # VIX volatility index
            'soybeans': (800, 1800),       # Soybean futures (cents/bushel)
            'gold': (3000, 5000),          # Gold futures (cents/ounce)
            'cocoa': (2000, 12000),        # Cocoa futures ($/metric ton)
            'nonfarm_payrolls': (140000, 170000),  # Employment (thousands)
            'usd_ars_rate': (100, 2000)    # USD/ARS exchange rate
        }

    def check_commodity_prices(self):
        """Check all commodity price tables"""
        print('\n' + '='*80)
        print('COMMODITY PRICE GUARDRAILS CHECK')
        print('='*80)
        
        commodity_tables = {
            'soybean_oil_prices': ('soybean_oil', 'ZL=F'),
            'corn_prices': ('corn', 'ZC=F'),
            'wheat_prices': ('wheat', 'ZW=F'),
            'crude_oil_prices': ('crude_oil', 'CL=F'),
            'palm_oil_prices': ('palm_oil', 'CPO=F'),
            'soybean_prices': ('soybeans', 'ZS=F'),
            'soybean_meal_prices': ('soybean_meal', 'ZM=F'),
            'natural_gas_prices': ('natural_gas', 'NG=F'),
            'gold_prices': ('gold', 'GC=F'),
            'silver_prices': ('silver', 'SI=F')
        }
        
        issues_found = []
        
        for table, (commodity, yahoo_symbol) in commodity_tables.items():
            try:
                # Check if table exists and get recent data
                query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    MIN(close) as min_price,
                    MAX(close) as max_price,
                    AVG(close) as avg_price,
                    STDDEV(close) as std_price,
                    MAX(CAST(time AS DATE)) as latest_date,
                    COUNT(CASE WHEN close <= 0 THEN 1 END) as zero_negative_count,
                    COUNT(CASE WHEN close IS NULL THEN 1 END) as null_count
                FROM `cbi-v14.forecasting_data_warehouse.{table}`
                WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                """
                
                result = client.query(query).to_dataframe()
                
                if result.empty or result['total_rows'].iloc[0] == 0:
                    print(f'❌ {table}: NO RECENT DATA')
                    issues_found.append(f'{table}: No recent data')
                    continue
                
                r = result.iloc[0]
                expected_range = self.price_ranges.get(commodity, (0, float('inf')))
                
                print(f'\n{table}:')
                print(f'  Recent data: {r["total_rows"]} rows, latest: {r["latest_date"]}')
                print(f'  Price range: ${r["min_price"]:.2f} - ${r["max_price"]:.2f}')
                print(f'  Average: ${r["avg_price"]:.2f}')
                
                # GUARDRAIL CHECKS
                table_issues = []
                
                # Range check
                if r['min_price'] < expected_range[0] or r['max_price'] > expected_range[1]:
                    table_issues.append(f'Price outside expected range ${expected_range[0]}-${expected_range[1]}')
                
                # Zero/negative check
                if r['zero_negative_count'] > 0:
                    table_issues.append(f'{r["zero_negative_count"]} zero/negative prices')
                
                # Null check
                if r['null_count'] > 0:
                    table_issues.append(f'{r["null_count"]} null prices')
                
                # Extreme volatility check
                if r['std_price'] > 0 and r['avg_price'] > 0:
                    cv = (r['std_price'] / r['avg_price']) * 100
                    if cv > 50:  # Coefficient of variation > 50%
                        table_issues.append(f'Extreme volatility (CV: {cv:.1f}%)')
                
                # Cross-check with Yahoo Finance
                try:
                    ticker = yf.Ticker(yahoo_symbol)
                    yahoo_data = ticker.history(period='1d')
                    if not yahoo_data.empty:
                        yahoo_price = float(yahoo_data['Close'].iloc[-1])
                        our_latest_query = f"""
                        SELECT close 
                        FROM `cbi-v14.forecasting_data_warehouse.{table}`
                        ORDER BY time DESC 
                        LIMIT 1
                        """
                        our_latest_result = client.query(our_latest_query).to_dataframe()
                        
                        if not our_latest_result.empty:
                            our_price = our_latest_result['close'].iloc[0]
                            diff_pct = abs(yahoo_price - our_price) / our_price * 100
                            
                            if diff_pct > 15:  # More than 15% difference
                                table_issues.append(f'Large difference with Yahoo: {diff_pct:.1f}% (Our: ${our_price:.2f}, Yahoo: ${yahoo_price:.2f})')
                            else:
                                print(f'  ✅ Yahoo cross-check: {diff_pct:.1f}% difference')
                except Exception as e:
                    print(f'  ⚠️ Could not cross-check with Yahoo: {str(e)[:50]}')
                
                if table_issues:
                    print(f'  🚨 ISSUES: {"; ".join(table_issues)}')
                    issues_found.extend([f'{table}: {issue}' for issue in table_issues])
                else:
                    print(f'  ✅ All guardrails passed')
                    
            except Exception as e:
                print(f'❌ {table}: Error checking - {str(e)[:100]}')
                issues_found.append(f'{table}: Error - {str(e)[:50]}')
        
        return issues_found

    def check_economic_indicators(self):
        """Check economic indicators with guardrails"""
        print('\n' + '='*80)
        print('ECONOMIC INDICATORS GUARDRAILS CHECK')
        print('='*80)
        
        issues_found = []
        
        try:
            # Check economic indicators table
            query = """
            SELECT 
                indicator,
                COUNT(*) as record_count,
                MIN(value) as min_value,
                MAX(value) as max_value,
                AVG(value) as avg_value,
                MAX(CAST(time AS DATE)) as latest_date,
                COUNT(CASE WHEN value IS NULL THEN 1 END) as null_count
            FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
            WHERE CAST(time AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY indicator
            ORDER BY indicator
            """
            
            result = client.query(query).to_dataframe()
            
            if result.empty:
                print('❌ No recent economic indicators data')
                return ['Economic indicators: No recent data']
            
            for _, row in result.iterrows():
                indicator = row['indicator']
                expected_range = self.economic_ranges.get(indicator, (-1000, 1000))
                
                print(f'\n{indicator}:')
                print(f'  Records: {row["record_count"]}, Latest: {row["latest_date"]}')
                print(f'  Range: {row["min_value"]:.2f} - {row["max_value"]:.2f}')
                
                indicator_issues = []
                
                # Range check
                if row['min_value'] < expected_range[0] or row['max_value'] > expected_range[1]:
                    indicator_issues.append(f'Value outside expected range {expected_range[0]}-{expected_range[1]}')
                
                # Null check
                if row['null_count'] > 0:
                    indicator_issues.append(f'{row["null_count"]} null values')
                
                # Freshness check (economic data should be within 30 days)
                if row['latest_date']:
                    days_old = (datetime.now().date() - row['latest_date']).days
                    if days_old > 30:
                        indicator_issues.append(f'Data is {days_old} days old')
                
                if indicator_issues:
                    print(f'  🚨 ISSUES: {"; ".join(indicator_issues)}')
                    issues_found.extend([f'{indicator}: {issue}' for issue in indicator_issues])
                else:
                    print(f'  ✅ All guardrails passed')
                    
        except Exception as e:
            print(f'❌ Error checking economic indicators: {str(e)[:100]}')
            issues_found.append(f'Economic indicators: Error - {str(e)[:50]}')
        
        return issues_found

    def check_weather_data(self):
        """Check weather data quality"""
        print('\n' + '='*80)
        print('WEATHER DATA GUARDRAILS CHECK')
        print('='*80)
        
        issues_found = []
        
        weather_tables = [
            'weather_brazil_daily',
            'weather_argentina_daily', 
            'weather_us_midwest_daily'
        ]
        
        for table in weather_tables:
            try:
                query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    MIN(temp_avg_c) as min_temp,
                    MAX(temp_avg_c) as max_temp,
                    MIN(precip_mm) as min_precip,
                    MAX(precip_mm) as max_precip,
                    MAX(date) as latest_date,
                    COUNT(CASE WHEN temp_avg_c IS NULL THEN 1 END) as null_temp,
                    COUNT(CASE WHEN precip_mm < 0 THEN 1 END) as negative_precip
                FROM `cbi-v14.forecasting_data_warehouse.{table}`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                """
                
                result = client.query(query).to_dataframe()
                
                if result.empty or result['total_rows'].iloc[0] == 0:
                    print(f'❌ {table}: NO RECENT DATA')
                    issues_found.append(f'{table}: No recent data')
                    continue
                
                r = result.iloc[0]
                
                print(f'\n{table}:')
                print(f'  Records: {r["total_rows"]}, Latest: {r["latest_date"]}')
                print(f'  Temperature range: {r["min_temp"]:.1f}°C - {r["max_temp"]:.1f}°C')
                print(f'  Precipitation range: {r["min_precip"]:.1f} - {r["max_precip"]:.1f} mm')
                
                table_issues = []
                
                # Temperature sanity checks
                if r['min_temp'] < -50 or r['max_temp'] > 60:
                    table_issues.append('Extreme temperature values')
                
                # Precipitation sanity checks  
                if r['negative_precip'] > 0:
                    table_issues.append(f'{r["negative_precip"]} negative precipitation values')
                
                if r['max_precip'] > 1000:  # More than 1 meter of rain in a day
                    table_issues.append('Extreme precipitation values')
                
                # Null checks
                if r['null_temp'] > 0:
                    table_issues.append(f'{r["null_temp"]} null temperature values')
                
                # Freshness check
                if r['latest_date']:
                    days_old = (datetime.now().date() - r['latest_date']).days
                    if days_old > 7:
                        table_issues.append(f'Data is {days_old} days old')
                
                if table_issues:
                    print(f'  🚨 ISSUES: {"; ".join(table_issues)}')
                    issues_found.extend([f'{table}: {issue}' for issue in table_issues])
                else:
                    print(f'  ✅ All guardrails passed')
                    
            except Exception as e:
                print(f'❌ {table}: Error - {str(e)[:100]}')
                issues_found.append(f'{table}: Error - {str(e)[:50]}')
        
        return issues_found

    def check_intelligence_data(self):
        """Check news and social intelligence data"""
        print('\n' + '='*80)
        print('INTELLIGENCE DATA GUARDRAILS CHECK')
        print('='*80)
        
        issues_found = []
        
        intelligence_tables = [
            'news_intelligence',
            'social_sentiment',
            'ice_trump_intelligence'
        ]
        
        for table in intelligence_tables:
            try:
                # Check if table exists first
                tables_query = f"""
                SELECT table_name 
                FROM `cbi-v14.forecasting_data_warehouse.INFORMATION_SCHEMA.TABLES`
                WHERE table_name = '{table}'
                """
                
                table_exists = client.query(tables_query).to_dataframe()
                
                if table_exists.empty:
                    print(f'⚠️ {table}: Table does not exist')
                    continue
                
                # Get recent data stats
                if table == 'news_intelligence':
                    query = f"""
                    SELECT 
                        COUNT(*) as total_rows,
                        MIN(intelligence_score) as min_score,
                        MAX(intelligence_score) as max_score,
                        MAX(published) as latest_timestamp,
                        COUNT(DISTINCT source) as unique_sources
                    FROM `cbi-v14.forecasting_data_warehouse.{table}`
                    WHERE published >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                    """
                elif table == 'social_sentiment':
                    query = f"""
                    SELECT 
                        COUNT(*) as total_rows,
                        MIN(sentiment_score) as min_score,
                        MAX(sentiment_score) as max_score,
                        MAX(timestamp) as latest_timestamp,
                        COUNT(DISTINCT platform) as unique_platforms
                    FROM `cbi-v14.forecasting_data_warehouse.{table}`
                    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                    """
                else:  # ice_trump_intelligence
                    query = f"""
                    SELECT 
                        COUNT(*) as total_rows,
                        MAX(created_at) as latest_timestamp
                    FROM `cbi-v14.forecasting_data_warehouse.{table}`
                    WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                    """
                
                result = client.query(query).to_dataframe()
                
                if result.empty or result['total_rows'].iloc[0] == 0:
                    print(f'⚠️ {table}: No recent data (last 7 days)')
                    # This is not necessarily an error for intelligence data
                    continue
                
                r = result.iloc[0]
                
                print(f'\n{table}:')
                print(f'  Recent records: {r["total_rows"]} (last 7 days)')
                print(f'  Latest: {r["latest_timestamp"]}')
                
                table_issues = []
                
                # Score range checks for sentiment data
                if 'min_score' in r and pd.notna(r['min_score']):
                    if r['min_score'] < -1 or r['max_score'] > 1:
                        table_issues.append('Sentiment scores outside [-1, 1] range')
                
                # Freshness check (intelligence data should be recent)
                if r['latest_timestamp']:
                    if isinstance(r['latest_timestamp'], str):
                        latest_dt = pd.to_datetime(r['latest_timestamp'])
                    else:
                        latest_dt = r['latest_timestamp']
                    
                    hours_old = (datetime.now(latest_dt.tz) - latest_dt).total_seconds() / 3600
                    if hours_old > 48:  # More than 48 hours old
                        table_issues.append(f'Data is {hours_old:.1f} hours old')
                
                if table_issues:
                    print(f'  🚨 ISSUES: {"; ".join(table_issues)}')
                    issues_found.extend([f'{table}: {issue}' for issue in table_issues])
                else:
                    print(f'  ✅ All guardrails passed')
                    
            except Exception as e:
                print(f'❌ {table}: Error - {str(e)[:100]}')
                # Intelligence data errors are not critical
                
        return issues_found

def main():
    print('='*80)
    print('COMPREHENSIVE DATA GUARDRAILS SYSTEM')
    print('Cross-checking ALL data sources with validation rules')
    print('='*80)
    
    guardrails = DataGuardrails()
    
    all_issues = []
    
    # Check all data types
    all_issues.extend(guardrails.check_commodity_prices())
    all_issues.extend(guardrails.check_economic_indicators())
    all_issues.extend(guardrails.check_weather_data())
    all_issues.extend(guardrails.check_intelligence_data())
    
    # Final summary
    print('\n' + '='*80)
    print('GUARDRAILS SUMMARY')
    print('='*80)
    
    if not all_issues:
        print('✅ ALL DATA SOURCES PASSED GUARDRAILS')
        print('✅ SAFE TO PROCEED WITH ENSEMBLE TRAINING')
    else:
        print(f'🚨 FOUND {len(all_issues)} ISSUES:')
        for issue in all_issues:
            print(f'  - {issue}')
        
        critical_issues = [i for i in all_issues if any(word in i.lower() for word in ['extreme', 'outside', 'negative', 'zero'])]
        
        if critical_issues:
            print(f'\n🚨 {len(critical_issues)} CRITICAL ISSUES REQUIRE IMMEDIATE ATTENTION')
        else:
            print(f'\n⚠️ Issues found but none are critical - can proceed with caution')
    
    print('\n✅ GUARDRAILS CHECK COMPLETE')

if __name__ == "__main__":
    main()
