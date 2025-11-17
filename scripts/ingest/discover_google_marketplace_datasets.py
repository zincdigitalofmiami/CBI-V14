#!/usr/bin/env python3
"""
Google Cloud Marketplace Dataset Discovery & Testing
=====================================================
Crawls BigQuery public datasets, tests access, documents schemas
Identifies ALL free datasets available for immediate use
"""

import os
from google.cloud import bigquery
import pandas as pd
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/docs/data-sources/google-marketplace")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize BigQuery client
client = bigquery.Client(project='cbi-v14')

# Target datasets from user's list
TARGET_DATASETS = {
    'weather': [
        'noaa-public.ghcn-d',
        'bigquery-public-data.noaa_global_forecast_system',
        'bigquery-public-data.noaa_gsod',  # Alternative NOAA dataset
    ],
    'events': [
        'bigquery-public-data.gdelt_bq.events',
        'gdelt-bq.gdeltv2.events',  # Alternative GDELT location
    ],
    'economic': [
        'bls-public-data.cpi_unemployment',
        'bigquery-public-data.federal_reserve_economic_data',  # FRED alternative
    ],
    'political': [
        'federal-election-commission.fec_2024',
    ],
    'trade': [
        'bigquery-public-data.international_trade.comtrade_exports',
        'bigquery-public-data.international_trade.comtrade_imports',
    ],
    'agricultural': [
        'bigquery-public-data.usda_nass',  # USDA NASS data
    ],
    'energy': [
        'bigquery-public-data.eia',  # EIA data if available
    ]
}

def list_all_public_datasets() -> List[str]:
    """
    List ALL public datasets available in BigQuery.
    Note: We test direct access rather than listing, as cross-project listing is limited.
    """
    logger.info("Testing direct access to known public datasets...")
    
    # Known public datasets to test
    known_datasets = [
        # NOAA Weather
        'noaa-public.ghcn-d',
        'bigquery-public-data.noaa_gsod',
        'bigquery-public-data.noaa_global_forecast_system',
        
        # GDELT Events
        'bigquery-public-data.gdelt_bq.events',
        'gdelt-bq.gdeltv2.events',
        
        # Economic
        'bls-public-data.cpi_unemployment',
        'bigquery-public-data.federal_reserve_economic_data',
        
        # Political
        'federal-election-commission.fec_2024',
        
        # Trade
        'bigquery-public-data.international_trade.comtrade_exports',
        'bigquery-public-data.international_trade.comtrade_imports',
        
        # Agricultural
        'bigquery-public-data.usda_nass',
        
        # Other useful datasets
        'bigquery-public-data.covid19_open_data',
        'bigquery-public-data.census_bureau_acs',
    ]
    
    accessible_datasets = []
    
    for dataset_id in known_datasets:
        try:
            # Try to access the dataset
            test_result = test_dataset_access(dataset_id)
            if test_result['accessible']:
                accessible_datasets.append(dataset_id)
                logger.info(f"  ✅ {dataset_id}")
            else:
                logger.info(f"  ❌ {dataset_id}: {test_result.get('error', 'Unknown')}")
        except Exception as e:
            logger.warning(f"  ⚠️  {dataset_id}: {e}")
    
    return accessible_datasets

def test_dataset_access(dataset_id: str) -> Dict:
    """
    Test access to a dataset and get its schema.
    Handles both dataset-only IDs and dataset.table IDs.
    """
    logger.info(f"Testing access to {dataset_id}...")
    
    result = {
        'dataset_id': dataset_id,
        'accessible': False,
        'tables': [],
        'error': None,
        'sample_query': None
    }
    
    try:
        # Parse dataset ID (might be dataset.table format)
        parts = dataset_id.split('.')
        if len(parts) == 3:
            # Format: project.dataset.table
            project_id = parts[0]
            dataset_id_only = f"{parts[0]}.{parts[1]}"
            table_id = parts[2]
            full_table_id = dataset_id
        elif len(parts) == 2:
            # Format: project.dataset
            project_id = parts[0]
            dataset_id_only = dataset_id
            table_id = None
            full_table_id = None
        else:
            raise ValueError(f"Invalid dataset ID format: {dataset_id}")
        
        # Try to access the dataset
        dataset_ref = client.get_dataset(dataset_id_only)
        result['accessible'] = True
        result['description'] = dataset_ref.description if dataset_ref.description else None
        
        # List tables in dataset
        tables = list(client.list_tables(dataset_ref))
        result['tables'] = [table.table_id for table in tables]
        
        logger.info(f"  ✅ Accessible: {len(tables)} tables found")
        
        # If specific table was provided, use it; otherwise use first table
        target_table = table_id if table_id else (tables[0].table_id if tables else None)
        
        if target_table:
            full_table_path = f"{dataset_id_only}.{target_table}"
            table_ref = client.get_table(full_table_path)
            
            result['sample_table'] = target_table
            result['sample_schema'] = [
                {
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description
                }
                for field in table_ref.schema
            ]
            result['num_rows'] = table_ref.num_rows if hasattr(table_ref, 'num_rows') else None
            
            # Try a sample query
            try:
                sample_query = f"SELECT * FROM `{full_table_path}` LIMIT 1"
                sample_df = client.query(sample_query).to_dataframe()
                result['sample_query'] = {
                    'success': True,
                    'rows': len(sample_df),
                    'columns': list(sample_df.columns),
                    'sample_data': sample_df.head(1).to_dict('records') if not sample_df.empty else None
                }
                logger.info(f"  ✅ Sample query successful: {len(sample_df)} rows, {len(sample_df.columns)} columns")
            except Exception as e:
                result['sample_query'] = {
                    'success': False,
                    'error': str(e)
                }
                logger.warning(f"  ⚠️  Sample query failed: {e}")
        
    except Exception as e:
        result['accessible'] = False
        result['error'] = str(e)
        logger.error(f"  ❌ Not accessible: {e}")
    
    return result

def get_dataset_schema(dataset_id: str, table_id: str) -> Optional[Dict]:
    """
    Get full schema for a specific table.
    """
    try:
        table_ref = client.get_table(f"{dataset_id}.{table_id}")
        schema = [
            {
                'name': field.name,
                'type': field.field_type,
                'mode': field.mode,
                'description': field.description
            }
            for field in table_ref.schema
        ]
        
        return {
            'dataset_id': dataset_id,
            'table_id': table_id,
            'num_rows': table_ref.num_rows,
            'num_bytes': table_ref.num_bytes,
            'created': str(table_ref.created) if hasattr(table_ref, 'created') else None,
            'modified': str(table_ref.modified) if hasattr(table_ref, 'modified') else None,
            'schema': schema
        }
    except Exception as e:
        logger.error(f"Error getting schema for {dataset_id}.{table_id}: {e}")
        return None

def test_specific_datasets() -> Dict:
    """
    Test access to the specific datasets mentioned by user.
    """
    logger.info("="*80)
    logger.info("TESTING SPECIFIC TARGET DATASETS")
    logger.info("="*80)
    
    results = {}
    
    for category, datasets in TARGET_DATASETS.items():
        logger.info(f"\nTesting {category} datasets...")
        results[category] = {}
        
        for dataset_id in datasets:
            test_result = test_dataset_access(dataset_id)
            results[category][dataset_id] = test_result
            
            # If accessible, get detailed schema for first table
            if test_result['accessible'] and test_result['tables']:
                first_table = test_result['tables'][0]
                schema = get_dataset_schema(dataset_id, first_table)
                if schema:
                    results[category][dataset_id]['detailed_schema'] = schema
    
    return results

def discover_all_relevant_datasets() -> Dict:
    """
    Discover ALL datasets that might be relevant to our use case.
    """
    logger.info("="*80)
    logger.info("DISCOVERING ALL RELEVANT DATASETS")
    logger.info("="*80)
    
    # Keywords to search for
    keywords = [
        'weather', 'climate', 'noaa', 'temperature', 'precipitation',
        'economic', 'fred', 'bls', 'cpi', 'unemployment', 'gdp',
        'trade', 'export', 'import', 'commodity', 'agriculture',
        'soybean', 'corn', 'wheat', 'oil', 'energy', 'biofuel',
        'political', 'election', 'campaign', 'fec',
        'events', 'gdelt', 'news', 'sentiment'
    ]
    
    discovered = {}
    
    # Test known public projects
    public_projects = {
        'bigquery-public-data': 'Google Public Datasets',
        'noaa-public': 'NOAA Public Data',
        'bls-public-data': 'Bureau of Labor Statistics',
        'federal-election-commission': 'FEC Campaign Finance',
        'gdelt-bq': 'GDELT Events',
    }
    
    # Test known relevant datasets directly (cross-project listing is limited)
    known_relevant = [
        'noaa-public.ghcn-d',
        'bigquery-public-data.noaa_gsod',
        'bigquery-public-data.noaa_global_forecast_system',
        'bigquery-public-data.gdelt_bq.events',
        'gdelt-bq.gdeltv2.events',
        'bls-public-data.cpi_unemployment',
        'bigquery-public-data.federal_reserve_economic_data',
        'federal-election-commission.fec_2024',
        'bigquery-public-data.international_trade.comtrade_exports',
        'bigquery-public-data.usda_nass',
        'bigquery-public-data.covid19_open_data',
    ]
    
    for dataset_id in known_relevant:
        # Extract project from dataset_id
        project_id = dataset_id.split('.')[0]
        description = public_projects.get(project_id, 'Unknown')
        
        # Check if relevant by keyword matching
        is_relevant = any(keyword.lower() in dataset_id.lower() for keyword in keywords)
        
        if is_relevant:
            logger.info(f"\nTesting {dataset_id} ({description})...")
            try:
                test_result = test_dataset_access(dataset_id)
                discovered[dataset_id] = {
                    'description': description,
                    'test_result': test_result
                }
            except Exception as e:
                logger.warning(f"Could not test {dataset_id}: {e}")
    
    return discovered

def generate_comprehensive_report() -> Dict:
    """
    Generate comprehensive report of all available datasets.
    """
    logger.info("="*80)
    logger.info("GENERATING COMPREHENSIVE DATASET REPORT")
    logger.info("="*80)
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'target_datasets': {},
        'discovered_datasets': {},
        'recommendations': []
    }
    
    # Test target datasets
    target_results = test_specific_datasets()
    report['target_datasets'] = target_results
    
    # Discover additional datasets
    discovered = discover_all_relevant_datasets()
    report['discovered_datasets'] = discovered
    
    # Generate recommendations
    accessible_count = 0
    total_count = 0
    
    for category, datasets in target_results.items():
        for dataset_id, result in datasets.items():
            total_count += 1
            if result['accessible']:
                accessible_count += 1
                report['recommendations'].append({
                    'dataset_id': dataset_id,
                    'category': category,
                    'status': 'READY',
                    'tables': result['tables'],
                    'recommendation': f"Use {dataset_id} - {len(result['tables'])} tables available"
                })
            else:
                report['recommendations'].append({
                    'dataset_id': dataset_id,
                    'category': category,
                    'status': 'NOT_ACCESSIBLE',
                    'error': result.get('error'),
                    'recommendation': f"Find alternative for {dataset_id}"
                })
    
    report['summary'] = {
        'accessible': accessible_count,
        'total': total_count,
        'success_rate': f"{(accessible_count/total_count*100):.1f}%" if total_count > 0 else "0%"
    }
    
    return report

def main():
    """
    Main execution: Discover and test all Google Marketplace datasets.
    """
    logger.info("="*80)
    logger.info("GOOGLE CLOUD MARKETPLACE DATASET DISCOVERY")
    logger.info("="*80)
    logger.info("This script will:")
    logger.info("1. Test access to target datasets")
    logger.info("2. Discover additional relevant datasets")
    logger.info("3. Document schemas and availability")
    logger.info("4. Generate comprehensive report")
    logger.info("="*80)
    
    # Generate comprehensive report
    report = generate_comprehensive_report()
    
    # Save report
    report_file = OUTPUT_DIR / f"marketplace_datasets_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"\n✅ Report saved to: {report_file}")
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY")
    logger.info("="*80)
    logger.info(f"Accessible datasets: {report['summary']['accessible']}/{report['summary']['total']}")
    logger.info(f"Success rate: {report['summary']['success_rate']}")
    logger.info("\nReady to use:")
    for rec in report['recommendations']:
        if rec['status'] == 'READY':
            logger.info(f"  ✅ {rec['dataset_id']}: {rec['recommendation']}")
    
    logger.info("\nNot accessible:")
    for rec in report['recommendations']:
        if rec['status'] == 'NOT_ACCESSIBLE':
            logger.info(f"  ❌ {rec['dataset_id']}: {rec.get('error', 'Unknown error')}")
    
    logger.info("="*80)
    
    return report

if __name__ == "__main__":
    main()
