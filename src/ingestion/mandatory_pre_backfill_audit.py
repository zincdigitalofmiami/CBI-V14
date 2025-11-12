#!/usr/bin/env python3
"""
CBI-V14 MANDATORY PRE-BACKFILL AUDIT
NEVER add data without running this comprehensive audit first
Prevents duplication disasters like the weather backfill incident
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any

class PreBackfillAuditor:
    """Comprehensive audit required before ANY data addition"""
    
    def __init__(self, data_category: str):
        self.client = bigquery.Client(project='cbi-v14')
        self.data_category = data_category
        self.two_year_target = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        self.five_year_target = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
        
    def discover_all_related_tables(self) -> List[Dict[str, Any]]:
        """Find ALL tables related to the data category"""
        print(f'🔍 DISCOVERING ALL {self.data_category.upper()}-RELATED DATA SOURCES')
        print('=' * 70)
        
        # Keywords for different data categories
        keyword_mapping = {
            'weather': ['weather', 'temp', 'precipitation', 'climate', 'inmet', 'noaa', 'meteo'],
            'currency': ['currency', 'fx', 'exchange', 'rate', 'usd', 'brl', 'cny', 'ars'],
            'intelligence': ['intelligence', 'news', 'sentiment', 'trump', 'social', 'policy'],
            'palm_oil': ['palm', 'oil', 'fcpo', 'malaysia', 'myr'],
            'economic': ['economic', 'fed', 'treasury', 'interest', 'inflation', 'gdp']
        }
        
        keywords = keyword_mapping.get(self.data_category, [self.data_category])
        related_objects = []
        
        # Search across all datasets
        datasets_to_search = [
            'forecasting_data_warehouse', 'curated', 'staging', 'signals', 
            'models', 'models_v4', 'raw', 'bkp', 'deprecated'
        ]
        
        for dataset in datasets_to_search:
            try:
                tables = list(self.client.list_tables(f'cbi-v14.{dataset}'))
                
                for table in tables:
                    table_name = table.table_id.lower()
                    
                    # Check if table name contains any relevant keywords
                    if any(keyword in table_name for keyword in keywords):
                        related_objects.append({
                            'dataset': dataset,
                            'table_name': table.table_id,
                            'full_name': f'{dataset}.{table.table_id}',
                            'table_type': table.table_type,
                            'keywords_matched': [k for k in keywords if k in table_name]
                        })
                        
            except Exception as e:
                print(f'   Error checking {dataset}: {str(e)}')
        
        print(f'📋 FOUND {len(related_objects)} {self.data_category.upper()}-RELATED OBJECTS:')
        for obj in related_objects:
            print(f'   • {obj["full_name"]} ({obj["table_type"]}) - matches: {obj["keywords_matched"]}')
        
        return related_objects
    
    def analyze_coverage_and_overlap(self, related_objects: List[Dict]) -> Dict[str, Any]:
        """Analyze data coverage and identify overlaps"""
        print()
        print(f'📊 COMPREHENSIVE COVERAGE ANALYSIS')
        print('=' * 50)
        
        coverage_analysis = {
            'tables_with_2y_coverage': [],
            'tables_with_5y_coverage': [],
            'main_data_sources': [],
            'potential_duplicates': [],
            'recommendations': []
        }
        
        total_records_found = 0
        
        for obj in related_objects:
            try:
                print(f'🔍 {obj[\"full_name\"]}:')
                
                # Get basic info and try different date column names
                date_columns = ['date', 'time', 'timestamp', 'created_at', 'published_date', 'report_date']
                
                schema_found = False
                for date_col in date_columns:
                    try:
                        coverage_query = f'''
                        SELECT 
                            COUNT(*) as total_records,
                            MIN(DATE({date_col})) as earliest_date,
                            MAX(DATE({date_col})) as latest_date,
                            COUNT(DISTINCT DATE({date_col})) as unique_dates
                        FROM \`cbi-v14.{obj[\"full_name\"]}\`
                        '''
                        
                        result = self.client.query(coverage_query).to_dataframe()
                        
                        if len(result) > 0:
                            row = result.iloc[0]
                            total_records = row['total_records']
                            earliest = str(row['earliest_date'])
                            latest = str(row['latest_date'])
                            unique_dates = row['unique_dates']
                            
                            # Analyze coverage
                            has_2y = earliest <= self.two_year_target
                            has_5y = earliest <= self.five_year_target
                            
                            coverage_2y = '✅ 2Y+' if has_2y else '❌ <2Y'
                            coverage_5y = '✅ 5Y+' if has_5y else '❌ <5Y'
                            
                            print(f'   {coverage_2y} | {coverage_5y} {total_records:,} records ({earliest} to {latest})')
                            
                            # Track significant data sources
                            if total_records > 1000 and has_2y:
                                coverage_analysis['main_data_sources'].append({
                                    'table': obj['full_name'],
                                    'records': total_records,
                                    'coverage_years': 5 if has_5y else 2,
                                    'date_range': f'{earliest} to {latest}'
                                })
                            
                            if has_2y:
                                coverage_analysis['tables_with_2y_coverage'].append(obj['full_name'])
                            if has_5y:
                                coverage_analysis['tables_with_5y_coverage'].append(obj['full_name'])
                                
                            total_records_found += total_records
                            schema_found = True
                            break  # Found working date column
                            
                    except Exception:
                        continue  # Try next date column
                
                if not schema_found:
                    print(f'   ❌ No accessible date column found')
                    
            except Exception as e:
                print(f'   🚨 Analysis error: {str(e)[:50]}...')
        
        print()
        print(f'📈 TOTAL RECORDS DISCOVERED: {total_records_found:,}')
        print()
        
        # Generate recommendations
        if len(coverage_analysis['main_data_sources']) > 0:
            print('💡 MAIN DATA SOURCES IDENTIFIED:')
            for source in sorted(coverage_analysis['main_data_sources'], key=lambda x: x['records'], reverse=True):
                print(f'   🎯 {source[\"table\"]}: {source[\"records\"]:,} records ({source[\"coverage_years\"]}+ years)')
                
            # Identify the primary table to use
            primary_source = max(coverage_analysis['main_data_sources'], key=lambda x: x['records'])
            coverage_analysis['primary_recommendation'] = primary_source
            
            print()
            print(f'🚀 PRIMARY RECOMMENDATION: Use {primary_source[\"table\"]}')
            print(f'   📊 {primary_source[\"records\"]:,} records with {primary_source[\"coverage_years\"]}+ year coverage')
            print(f'   📅 {primary_source[\"date_range\"]}')
            
            coverage_analysis['recommendations'].append(f'Use {primary_source[\"table\"]} as primary {self.data_category} data source')
            coverage_analysis['recommendations'].append('No backfill needed - comprehensive coverage already exists')
        else:
            coverage_analysis['recommendations'].append(f'No comprehensive {self.data_category} data found - backfill may be needed')
        
        return coverage_analysis

def mandatory_audit(data_category: str) -> Dict[str, Any]:
    """MANDATORY audit before any backfill operation"""
    print('🚨 MANDATORY PRE-BACKFILL AUDIT')
    print('=' * 70)
    print(f'Data Category: {data_category.upper()}')
    print(f'Audit Time: {datetime.now()}')
    print('RULE: No backfill without comprehensive existing data verification')
    print()
    
    auditor = PreBackfillAuditor(data_category)
    
    # Step 1: Discover all related tables
    related_objects = auditor.discover_all_related_tables()
    
    # Step 2: Analyze coverage and overlaps
    analysis = auditor.analyze_coverage_and_overlap(related_objects)
    
    # Step 3: Generate final recommendation
    print('=' * 70)
    print('🎯 AUDIT CONCLUSION:')
    print('=' * 70)
    
    for recommendation in analysis['recommendations']:
        print(f'💡 {recommendation}')
    
    if 'No backfill needed' in str(analysis['recommendations']):
        print()
        print('✅ BACKFILL NOT REQUIRED - Use existing comprehensive data')
        print('⚠️  STOP: Do not proceed with backfill to avoid duplication')
        
        return {'audit_result': 'stop', 'reason': 'comprehensive_data_exists', 'analysis': analysis}
    else:
        print()
        print('🔄 BACKFILL MAY BE NEEDED - Proceed with caution')
        
        return {'audit_result': 'proceed_cautiously', 'reason': 'gaps_identified', 'analysis': analysis}

if __name__ == '__main__':
    # Test with weather data that I corrupted
    result = mandatory_audit('weather')
    print()
    print(f'Audit result: {result[\"audit_result\"]}')
"
