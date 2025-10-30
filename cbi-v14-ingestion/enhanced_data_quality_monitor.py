#!/usr/bin/env python3
"""
CBI-V14 Enhanced Data Quality Monitor
Implements comprehensive data quality checks, anomaly detection, and cross-source validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
from typing import Dict, List, Any, Optional, Tuple
import requests
import yfinance as yf
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class CrossSourceValidator:
    """Validate data consistency across multiple sources"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def validate_fx_cross_sources(self) -> Dict[str, Any]:
        """Compare FX rates across Yahoo Finance and existing BigQuery data"""
        logger.info("Running cross-source FX validation...")
        
        results = {
            'status': 'unknown',
            'discrepancies': [],
            'correlations': {},
            'timestamp': datetime.now().isoformat()
        }
        
        currency_pairs = ['USD/BRL', 'USD/CNY', 'USD/ARS']
        
        for pair in currency_pairs:
            try:
                # Get recent data from BigQuery
                from_curr, to_curr = pair.split('/')
                bq_query = f'''
                SELECT date, rate
                FROM `{PROJECT_ID}.{DATASET_ID}.currency_data`
                WHERE from_currency = '{from_curr}' AND to_currency = '{to_curr}'
                AND date >= CURRENT_DATE() - 7
                ORDER BY date DESC
                '''
                
                bq_data = self.client.query(bq_query).to_dataframe()
                
                if len(bq_data) > 0:
                    # Get corresponding Yahoo data
                    yahoo_symbol = f'{from_curr}{to_curr}=X'
                    ticker = yf.Ticker(yahoo_symbol)
                    yahoo_data = ticker.history(period='7d')
                    
                    if not yahoo_data.empty:
                        yahoo_data = yahoo_data.reset_index()
                        yahoo_data['date'] = yahoo_data['Date'].dt.date
                        yahoo_data['rate'] = yahoo_data['Close']
                        
                        # Find overlapping dates
                        bq_data['date'] = pd.to_datetime(bq_data['date']).dt.date
                        common_dates = set(bq_data['date']).intersection(set(yahoo_data['date']))
                        
                        if len(common_dates) >= 3:  # Need at least 3 days for comparison
                            # Calculate correlation and mean difference
                            bq_subset = bq_data[bq_data['date'].isin(common_dates)].sort_values('date')
                            yahoo_subset = yahoo_data[yahoo_data['date'].isin(common_dates)].sort_values('date')
                            
                            correlation = np.corrcoef(bq_subset['rate'], yahoo_subset['rate'])[0, 1]
                            mean_diff_pct = ((yahoo_subset['rate'].mean() - bq_subset['rate'].mean()) / bq_subset['rate'].mean()) * 100
                            
                            results['correlations'][pair] = {
                                'correlation': correlation,
                                'mean_diff_pct': mean_diff_pct,
                                'overlapping_days': len(common_dates)
                            }
                            
                            # Flag discrepancies
                            if correlation < 0.95:
                                results['discrepancies'].append(f"{pair}: Low correlation {correlation:.3f} between sources")
                            
                            if abs(mean_diff_pct) > 2.0:
                                results['discrepancies'].append(f"{pair}: Mean difference {mean_diff_pct:.2f}% between sources")
                                
                            logger.info(f"✅ {pair}: r={correlation:.3f}, diff={mean_diff_pct:.2f}%")
                        else:
                            results['discrepancies'].append(f"{pair}: Insufficient overlapping data for comparison")
                    else:
                        results['discrepancies'].append(f"{pair}: No Yahoo data available for comparison")
                else:
                    results['discrepancies'].append(f"{pair}: No BigQuery data available for comparison")
                    
            except Exception as e:
                results['discrepancies'].append(f"{pair}: Error in cross-validation - {str(e)}")
                logger.error(f"Cross-validation error for {pair}: {str(e)}")
        
        # Overall status
        if len(results['discrepancies']) == 0:
            results['status'] = 'excellent'
        elif len(results['discrepancies']) <= 2:
            results['status'] = 'acceptable'
        else:
            results['status'] = 'concerning'
            
        return results

class StatisticalAnomalyDetector:
    """Detect statistical anomalies in financial data"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def detect_outliers_3sigma(self, data_type: str, lookback_days: int = 30) -> Dict[str, Any]:
        """Detect 3σ outliers in recent data"""
        logger.info(f"Running 3σ anomaly detection for {data_type}...")
        
        results = {
            'outliers_found': [],
            'distribution_alerts': [],
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if data_type == 'fx_rates':
                # Check FX rate anomalies
                fx_query = f'''
                WITH recent_fx AS (
                  SELECT 
                    CONCAT(from_currency, '/', to_currency) as pair,
                    date,
                    rate,
                    LAG(rate) OVER (PARTITION BY from_currency, to_currency ORDER BY date) as prev_rate
                  FROM `{PROJECT_ID}.{DATASET_ID}.currency_data`
                  WHERE date >= CURRENT_DATE() - {lookback_days}
                  AND from_currency = 'USD' AND to_currency IN ('BRL', 'CNY', 'ARS')
                ),
                fx_changes AS (
                  SELECT 
                    pair,
                    date,
                    rate,
                    (rate - prev_rate) / prev_rate as daily_change
                  FROM recent_fx 
                  WHERE prev_rate IS NOT NULL
                )
                SELECT 
                  pair,
                  AVG(daily_change) as mean_change,
                  STDDEV(daily_change) as std_change,
                  MIN(daily_change) as min_change,
                  MAX(daily_change) as max_change,
                  COUNT(*) as obs_count
                FROM fx_changes 
                GROUP BY pair
                '''
                
                fx_stats = self.client.query(fx_query).to_dataframe()
                
                for _, row in fx_stats.iterrows():
                    pair = row['pair']
                    mean_change = row['mean_change']
                    std_change = row['std_change']
                    min_change = row['min_change']
                    max_change = row['max_change']
                    
                    # 3σ outlier detection
                    lower_bound = mean_change - 3 * std_change
                    upper_bound = mean_change + 3 * std_change
                    
                    if min_change < lower_bound:
                        results['outliers_found'].append(f"{pair}: Extreme negative move {min_change:.4f} < {lower_bound:.4f}")
                    
                    if max_change > upper_bound:
                        results['outliers_found'].append(f"{pair}: Extreme positive move {max_change:.4f} > {upper_bound:.4f}")
                    
                    # Distribution health checks
                    if std_change > 0.05:  # >5% daily volatility
                        results['distribution_alerts'].append(f"{pair}: High volatility σ={std_change:.4f}")
                    
                    if abs(mean_change) > 0.01:  # >1% daily drift
                        results['distribution_alerts'].append(f"{pair}: Trending μ={mean_change:.4f}")
                    
                    results['summary'][pair] = {
                        'mean_daily_change': mean_change,
                        'volatility': std_change,
                        'observations': int(row['obs_count'])
                    }
                    
                logger.info(f"✅ FX anomaly detection complete: {len(results['outliers_found'])} outliers found")
                
            elif data_type == 'interest_rates':
                # Check interest rate anomalies
                rates_query = f'''
                WITH recent_rates AS (
                  SELECT 
                    indicator,
                    DATE(time) as date,
                    value,
                    LAG(value) OVER (PARTITION BY indicator ORDER BY time) as prev_value
                  FROM `{PROJECT_ID}.{DATASET_ID}.economic_indicators`
                  WHERE DATE(time) >= CURRENT_DATE() - {lookback_days}
                  AND indicator IN ('fed_funds_rate', 'ten_year_treasury', 'yield_curve')
                ),
                rate_changes AS (
                  SELECT 
                    indicator,
                    date,
                    value,
                    (value - prev_value) as daily_change
                  FROM recent_rates 
                  WHERE prev_value IS NOT NULL
                )
                SELECT 
                  indicator,
                  AVG(daily_change) as mean_change,
                  STDDEV(daily_change) as std_change,
                  MIN(daily_change) as min_change,
                  MAX(daily_change) as max_change,
                  COUNT(*) as obs_count
                FROM rate_changes 
                GROUP BY indicator
                '''
                
                rates_stats = self.client.query(rates_query).to_dataframe()
                
                for _, row in rates_stats.iterrows():
                    indicator = row['indicator']
                    std_change = row['std_change']
                    min_change = row['min_change']
                    max_change = row['max_change']
                    
                    # Interest rates move more slowly - use tighter bounds
                    if abs(min_change) > 0.5:  # >50bp single-day move
                        results['outliers_found'].append(f"{indicator}: Large negative move {min_change:.3f}bp")
                    
                    if abs(max_change) > 0.5:  # >50bp single-day move
                        results['outliers_found'].append(f"{indicator}: Large positive move {max_change:.3f}bp")
                    
                    results['summary'][indicator] = {
                        'volatility': std_change,
                        'observations': int(row['obs_count'])
                    }
                
                logger.info(f"✅ Interest rates anomaly detection complete: {len(results['outliers_found'])} outliers found")
                
        except Exception as e:
            logger.error(f"Anomaly detection error for {data_type}: {str(e)}")
            results['outliers_found'].append(f"Detection failed: {str(e)}")
        
        return results

class TimeSeriesContinuityTester:
    """Test time series data for continuity and business day alignment"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def test_business_day_continuity(self, data_type: str) -> Dict[str, Any]:
        """Test that data follows proper business day sequencing"""
        logger.info(f"Testing business day continuity for {data_type}...")
        
        results = {
            'missing_business_days': [],
            'unexpected_weekend_data': [],
            'holiday_alignment': [],
            'gap_analysis': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if data_type == 'fx_rates':
                # FX markets trade 24/5 (Sun evening - Fri evening)
                fx_query = f'''
                SELECT 
                    CONCAT(from_currency, '/', to_currency) as pair,
                    date,
                    EXTRACT(DAYOFWEEK FROM date) as day_of_week
                FROM `{PROJECT_ID}.{DATASET_ID}.currency_data`
                WHERE date >= CURRENT_DATE() - 30
                AND from_currency = 'USD' AND to_currency IN ('BRL', 'CNY', 'ARS')
                ORDER BY pair, date
                '''
                
                fx_data = self.client.query(fx_query).to_dataframe()
                
                # Check for weekend data (shouldn't exist for most FX)
                weekend_data = fx_data[fx_data['day_of_week'].isin([1, 7])]  # Sunday=1, Saturday=7
                if len(weekend_data) > 0:
                    results['unexpected_weekend_data'] = weekend_data[['pair', 'date']].to_dict('records')
                
                # Check for missing business days
                for pair in fx_data['pair'].unique():
                    pair_data = fx_data[fx_data['pair'] == pair]
                    pair_data = pair_data.sort_values('date')
                    
                    if len(pair_data) > 1:
                        date_diffs = pair_data['date'].diff().dt.days.dropna()
                        
                        # Business days shouldn't have gaps > 3 days (Friday to Monday)
                        large_gaps = date_diffs[date_diffs > 4]
                        if len(large_gaps) > 0:
                            results['gap_analysis'][pair] = {
                                'max_gap_days': int(large_gaps.max()),
                                'gap_count': len(large_gaps),
                                'gaps': large_gaps.tolist()
                            }
                
                logger.info(f"✅ FX continuity test complete")
                
        except Exception as e:
            logger.error(f"Continuity test error for {data_type}: {str(e)}")
            results['missing_business_days'].append(f"Test failed: {str(e)}")
        
        return results

class SchemaEvolutionMonitor:
    """Monitor schema changes and unit consistency"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def monitor_schema_stability(self, table_name: str) -> Dict[str, Any]:
        """Monitor schema changes in critical tables"""
        logger.info(f"Monitoring schema stability for {table_name}...")
        
        results = {
            'schema_changes': [],
            'unit_consistency': [],
            'data_type_issues': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get current schema
            table_ref = self.client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{table_name}")
            current_schema = [(field.name, field.field_type, field.mode) for field in table_ref.schema]
            
            # Check for unit consistency in rate/price columns
            if table_name == 'currency_data':
                # Check if rates are in consistent units (should be direct rates, not percentages)
                sample_query = f'''
                SELECT 
                    CONCAT(from_currency, '/', to_currency) as pair,
                    MIN(rate) as min_rate,
                    MAX(rate) as max_rate,
                    AVG(rate) as avg_rate
                FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
                WHERE date >= CURRENT_DATE() - 7
                GROUP BY from_currency, to_currency
                '''
                
                rate_data = self.client.query(sample_query).to_dataframe()
                
                for _, row in rate_data.iterrows():
                    pair = row['pair']
                    min_rate = row['min_rate']
                    max_rate = row['max_rate']
                    avg_rate = row['avg_rate']
                    
                    # Check for unit inconsistencies
                    if 'USD/BRL' in pair and (avg_rate < 1.0 or avg_rate > 100.0):
                        results['unit_consistency'].append(f"{pair}: Possible unit error - avg rate {avg_rate:.4f}")
                    elif 'USD/CNY' in pair and (avg_rate < 1.0 or avg_rate > 50.0):
                        results['unit_consistency'].append(f"{pair}: Possible unit error - avg rate {avg_rate:.4f}")
                    elif 'USD/ARS' in pair and (avg_rate < 10.0 or avg_rate > 10000.0):
                        results['unit_consistency'].append(f"{pair}: Possible unit error - avg rate {avg_rate:.4f}")
            
            elif table_name == 'economic_indicators':
                # Check interest rate units (should be percentages)
                sample_query = f'''
                SELECT 
                    indicator,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    AVG(value) as avg_value
                FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
                WHERE DATE(time) >= CURRENT_DATE() - 7
                AND indicator IN ('fed_funds_rate', 'ten_year_treasury')
                GROUP BY indicator
                '''
                
                rate_data = self.client.query(sample_query).to_dataframe()
                
                for _, row in rate_data.iterrows():
                    indicator = row['indicator']
                    avg_value = row['avg_value']
                    
                    # Check if rates are in percentage (not decimal) form
                    if avg_value < 0.5:  # Likely decimal form instead of percentage
                        results['unit_consistency'].append(f"{indicator}: Possible unit error - rates may be in decimal instead of percentage form (avg: {avg_value:.4f})")
            
            logger.info(f"✅ Schema monitoring complete for {table_name}")
            
        except Exception as e:
            logger.error(f"Schema monitoring error for {table_name}: {str(e)}")
            results['schema_changes'].append(f"Monitoring failed: {str(e)}")
        
        return results

class MissingDatasetAuditor:
    """Audit availability of missing critical datasets"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def audit_missing_datasets(self) -> Dict[str, Any]:
        """Comprehensive audit of missing datasets mentioned by user"""
        logger.info("Auditing missing critical datasets...")
        
        results = {
            'palm_oil': {'status': 'unknown', 'details': {}},
            'cftc_data': {'status': 'unknown', 'details': {}},
            'biofuel_policy': {'status': 'unknown', 'details': {}},
            'sp500_data': {'status': 'unknown', 'details': {}},
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Check Palm Oil Data (15-25% of price variance per user)
        try:
            palm_query = '''
            SELECT 
                COUNT(*) as total_records,
                MIN(DATE(time)) as earliest_date,
                MAX(DATE(time)) as latest_date,
                DATE_DIFF(CURRENT_DATE(), MAX(DATE(time)), DAY) as days_behind
            FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
            '''
            
            palm_result = self.client.query(palm_query).to_dataframe()
            
            if len(palm_result) > 0 and palm_result['total_records'].iloc[0] > 0:
                results['palm_oil']['status'] = 'available'
                results['palm_oil']['details'] = {
                    'records': int(palm_result['total_records'].iloc[0]),
                    'latest_date': str(palm_result['latest_date'].iloc[0]),
                    'days_behind': int(palm_result['days_behind'].iloc[0])
                }
                
                if palm_result['days_behind'].iloc[0] > 5:
                    results['recommendations'].append("Palm oil data is stale - implement daily updates (15-25% price variance)")
            else:
                results['palm_oil']['status'] = 'missing'
                results['recommendations'].append("CRITICAL: Palm oil data missing - represents 15-25% of price variance")
                
        except Exception as e:
            results['palm_oil']['status'] = 'error'
            results['palm_oil']['details'] = {'error': str(e)}
        
        # 2. Check CFTC Data (affected by government shutdown)
        try:
            # Check if we have any CFTC tables
            cftc_tables = ['cftc_cot', 'vw_cftc_positions_oilseeds_weekly', 'vw_cftc_soybean_oil_weekly']
            cftc_found = False
            
            for table in cftc_tables:
                try:
                    # Try forecasting_data_warehouse first
                    cftc_query = f'''
                    SELECT COUNT(*) as records, MAX(DATE(report_date)) as latest_date
                    FROM `{PROJECT_ID}.forecasting_data_warehouse.{table}`
                    '''
                    cftc_result = self.client.query(cftc_query).to_dataframe()
                    
                    if len(cftc_result) > 0 and cftc_result['records'].iloc[0] > 0:
                        results['cftc_data']['status'] = 'available'
                        results['cftc_data']['details'] = {
                            'table': table,
                            'records': int(cftc_result['records'].iloc[0]),
                            'latest_date': str(cftc_result['latest_date'].iloc[0])
                        }
                        cftc_found = True
                        break
                        
                except:
                    # Try curated dataset
                    try:
                        cftc_query = f'''
                        SELECT COUNT(*) as records, MAX(DATE(report_date)) as latest_date
                        FROM `{PROJECT_ID}.curated.{table}`
                        '''
                        cftc_result = self.client.query(cftc_query).to_dataframe()
                        
                        if len(cftc_result) > 0 and cftc_result['records'].iloc[0] > 0:
                            results['cftc_data']['status'] = 'available'
                            results['cftc_data']['details'] = {
                                'table': f"curated.{table}",
                                'records': int(cftc_result['records'].iloc[0]),
                                'latest_date': str(cftc_result['latest_date'].iloc[0])
                            }
                            cftc_found = True
                            break
                    except:
                        continue
            
            if not cftc_found:
                results['cftc_data']['status'] = 'missing'
                results['recommendations'].append("CFTC positioning data missing - critical for institutional analysis")
                
        except Exception as e:
            results['cftc_data']['status'] = 'error'
            results['cftc_data']['details'] = {'error': str(e)}
        
        # 3. Check Biofuel Policy Data
        try:
            biofuel_query = '''
            SELECT 
                COUNT(*) as total_records,
                MAX(DATE(date)) as latest_date,
                DATE_DIFF(CURRENT_DATE(), MAX(DATE(date)), DAY) as days_behind
            FROM `cbi-v14.forecasting_data_warehouse.biofuel_policy`
            '''
            
            biofuel_result = self.client.query(biofuel_query).to_dataframe()
            
            if len(biofuel_result) > 0 and biofuel_result['total_records'].iloc[0] > 0:
                results['biofuel_policy']['status'] = 'available'
                results['biofuel_policy']['details'] = {
                    'records': int(biofuel_result['total_records'].iloc[0]),
                    'latest_date': str(biofuel_result['latest_date'].iloc[0]),
                    'days_behind': int(biofuel_result['days_behind'].iloc[0])
                }
            else:
                results['biofuel_policy']['status'] = 'missing'
                results['recommendations'].append("Biofuel policy data missing - important for demand fundamentals")
                
        except Exception as e:
            results['biofuel_policy']['status'] = 'error'
            results['biofuel_policy']['details'] = {'error': str(e)}
        
        # 4. Check S&P 500 Data
        try:
            sp500_query = '''
            SELECT 
                COUNT(*) as total_records,
                MAX(DATE(time)) as latest_date,
                DATE_DIFF(CURRENT_DATE(), MAX(DATE(time)), DAY) as days_behind
            FROM `cbi-v14.forecasting_data_warehouse.sp500_prices`
            '''
            
            sp500_result = self.client.query(sp500_query).to_dataframe()
            
            if len(sp500_result) > 0 and sp500_result['total_records'].iloc[0] > 0:
                results['sp500_data']['status'] = 'available' 
                results['sp500_data']['details'] = {
                    'records': int(sp500_result['total_records'].iloc[0]),
                    'latest_date': str(sp500_result['latest_date'].iloc[0]),
                    'days_behind': int(sp500_result['days_behind'].iloc[0])
                }
            else:
                results['sp500_data']['status'] = 'missing'
                results['recommendations'].append("S&P 500 data missing - important for risk-on/risk-off sentiment")
                
        except Exception as e:
            results['sp500_data']['status'] = 'error'
            results['sp500_data']['details'] = {'error': str(e)}
        
        return results

# Comprehensive data quality assessment function
def comprehensive_data_quality_assessment() -> Dict[str, Any]:
    """Run all data quality checks"""
    logger.info("🔍 Starting comprehensive data quality assessment...")
    
    # Initialize all monitors
    cross_source = CrossSourceValidator()
    anomaly_detector = StatisticalAnomalyDetector()
    continuity_tester = TimeSeriesContinuityTester()
    missing_auditor = MissingDatasetAuditor()
    
    # Run all tests
    results = {
        'assessment_timestamp': datetime.now().isoformat(),
        'cross_source_validation': cross_source.validate_fx_cross_sources(),
        'fx_anomaly_detection': anomaly_detector.detect_outliers_3sigma('fx_rates'),
        'rates_anomaly_detection': anomaly_detector.detect_outliers_3sigma('interest_rates'),
        'business_day_continuity': continuity_tester.test_business_day_continuity('fx_rates'),
        'missing_dataset_audit': missing_auditor.audit_missing_datasets(),
        'overall_score': 'pending'
    }
    
    # Calculate overall data quality score
    issues_count = 0
    issues_count += len(results['cross_source_validation']['discrepancies'])
    issues_count += len(results['fx_anomaly_detection']['outliers_found'])
    issues_count += len(results['rates_anomaly_detection']['outliers_found'])
    issues_count += len(results['business_day_continuity']['missing_business_days'])
    issues_count += len(results['missing_dataset_audit']['recommendations'])
    
    if issues_count == 0:
        results['overall_score'] = 'excellent'
    elif issues_count <= 3:
        results['overall_score'] = 'good'
    elif issues_count <= 8:
        results['overall_score'] = 'acceptable'
    else:
        results['overall_score'] = 'concerning'
    
    # Generate summary
    print("=" * 80)
    print("COMPREHENSIVE DATA QUALITY ASSESSMENT RESULTS")
    print("=" * 80)
    print(f"Overall Quality Score: {results['overall_score'].upper()}")
    print(f"Total Issues Found: {issues_count}")
    print()
    
    # Detailed results
    print("📊 CROSS-SOURCE VALIDATION:")
    if results['cross_source_validation']['discrepancies']:
        for disc in results['cross_source_validation']['discrepancies']:
            print(f"  ⚠️  {disc}")
    else:
        print("  ✅ No cross-source discrepancies found")
    print()
    
    print("📈 ANOMALY DETECTION:")
    fx_outliers = results['fx_anomaly_detection']['outliers_found']
    rates_outliers = results['rates_anomaly_detection']['outliers_found']
    
    if fx_outliers or rates_outliers:
        for outlier in fx_outliers + rates_outliers:
            print(f"  🚨 {outlier}")
    else:
        print("  ✅ No statistical outliers detected")
    print()
    
    print("📅 BUSINESS DAY CONTINUITY:")
    continuity_issues = results['business_day_continuity']['missing_business_days']
    if continuity_issues:
        for issue in continuity_issues:
            print(f"  ⚠️  {issue}")
    else:
        print("  ✅ Business day continuity verified")
    print()
    
    print("📋 MISSING CRITICAL DATASETS:")
    recommendations = results['missing_dataset_audit']['recommendations']
    if recommendations:
        for rec in recommendations:
            print(f"  🔴 {rec}")
    else:
        print("  ✅ All critical datasets available")
    print()
    
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    # Run comprehensive assessment
    assessment_results = comprehensive_data_quality_assessment()
    
    # Save results
    import json
    with open(f"/Users/zincdigital/CBI-V14/logs/data_quality_assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.json", "w") as f:
        json.dump(assessment_results, f, indent=2, default=str)
    
    # Exit with appropriate code
    exit_code = 0 if assessment_results['overall_score'] in ['excellent', 'good'] else 1
    exit(exit_code)







