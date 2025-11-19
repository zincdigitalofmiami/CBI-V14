#!/usr/bin/env python3
"""
Get REAL BigQuery Costs - Direct from BigQuery
Queries actual usage: storage, queries, streaming, with projections for vast data growth
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from google.cloud import bigquery
from datetime import datetime, timedelta
import json

PROJECT_ID = 'cbi-v14'
LOCATION = 'us-central1'

def get_storage_costs(client):
    """Get actual storage costs from INFORMATION_SCHEMA"""
    print("=" * 80)
    print("STORAGE COSTS (Current)")
    print("=" * 80)
    
    # Query storage by dataset
    storage_query = f"""
    SELECT
      table_schema as dataset,
      SUM(total_logical_bytes) / POW(1024, 3) as logical_gb,
      SUM(total_physical_bytes) / POW(1024, 3) as physical_gb,
      COUNT(*) as table_count
    FROM `{PROJECT_ID}.region-{LOCATION}.INFORMATION_SCHEMA.TABLE_STORAGE`
    GROUP BY table_schema
    ORDER BY logical_gb DESC
    """
    
    try:
        job = client.query(storage_query, location=LOCATION)
        results = job.result()
        
        total_logical = 0
        total_physical = 0
        total_tables = 0
        
        print(f"\n{'Dataset':<40} {'Logical GB':<15} {'Physical GB':<15} {'Tables':<10}")
        print("-" * 80)
        
        for row in results:
            dataset = row.dataset
            logical_gb = row.logical_gb or 0
            physical_gb = row.physical_gb or 0
            table_count = row.table_count or 0
            
            total_logical += logical_gb
            total_physical += physical_gb
            total_tables += table_count
            
            print(f"{dataset:<40} {logical_gb:<15.3f} {physical_gb:<15.3f} {table_count:<10}")
        
        print("-" * 80)
        print(f"{'TOTAL':<40} {total_logical:<15.3f} {total_physical:<15.3f} {total_tables:<10}")
        
        # Calculate storage cost
        # Active storage: $0.020/GB/month (logical bytes)
        # Long-term storage (90+ days): $0.010/GB/month
        # For now, assume all active
        active_storage_cost = total_logical * 0.020
        long_term_storage_cost = total_physical * 0.010  # Physical is often long-term
        
        print(f"\nStorage Cost Calculation:")
        print(f"  Active storage ({total_logical:.3f} GB × $0.020): ${active_storage_cost:.4f}/month")
        print(f"  Long-term storage ({total_physical:.3f} GB × $0.010): ${long_term_storage_cost:.4f}/month")
        print(f"  Estimated cost: ${max(active_storage_cost, long_term_storage_cost):.4f}/month")
        
        return {
            'logical_gb': total_logical,
            'physical_gb': total_physical,
            'table_count': total_tables,
            'monthly_cost': max(active_storage_cost, long_term_storage_cost)
        }
        
    except Exception as e:
        print(f"Error querying storage: {e}")
        return None


def get_query_usage(client):
    """Get actual query usage from INFORMATION_SCHEMA.JOBS"""
    print("\n" + "=" * 80)
    print("QUERY USAGE (Last 30 Days)")
    print("=" * 80)
    
    # Query job statistics
    query_usage = f"""
    SELECT
      DATE(creation_time) as date,
      COUNT(*) as job_count,
      SUM(total_bytes_processed) / POW(1024, 3) as total_gb_scanned,
      SUM(total_slot_ms) / 1000 / 60 / 60 as total_slot_hours
    FROM `{PROJECT_ID}.region-{LOCATION}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      AND job_type = 'QUERY'
      AND state = 'DONE'
    GROUP BY date
    ORDER BY date DESC
    """
    
    try:
        job = client.query(query_usage, location=LOCATION)
        results = job.result()
        
        total_jobs = 0
        total_gb = 0
        total_slot_hours = 0
        
        print(f"\n{'Date':<15} {'Jobs':<10} {'GB Scanned':<15} {'Slot Hours':<15}")
        print("-" * 80)
        
        for row in results:
            date = row.date
            jobs = row.job_count or 0
            gb = row.total_gb_scanned or 0
            slot_hours = row.total_slot_hours or 0
            
            total_jobs += jobs
            total_gb += gb
            total_slot_hours += slot_hours
            
            print(f"{str(date):<15} {jobs:<10} {gb:<15.3f} {slot_hours:<15.3f}")
        
        print("-" * 80)
        print(f"{'TOTAL (30 days)':<15} {total_jobs:<10} {total_gb:<15.3f} {total_slot_hours:<15.3f}")
        
        # Calculate query cost
        # First 1 TB/month: FREE
        # After 1 TB: $5/TB
        free_tier_tb = 1.0
        query_cost = 0.0
        if total_gb / 1024 > free_tier_tb:
            excess_tb = (total_gb / 1024) - free_tier_tb
            query_cost = excess_tb * 5.0
        
        # Slot time cost (if using on-demand)
        # First 2,000 slot-hours/month: FREE
        # After: $0.04/slot-hour
        slot_cost = 0.0
        if total_slot_hours > 2000:
            excess_slots = total_slot_hours - 2000
            slot_cost = excess_slots * 0.04
        
        print(f"\nQuery Cost Calculation:")
        print(f"  Data scanned: {total_gb:.3f} GB ({total_gb/1024:.3f} TB)")
        print(f"  Free tier: 1 TB/month")
        if total_gb / 1024 <= free_tier_tb:
            print(f"  Query cost: $0.00 (under free tier)")
        else:
            print(f"  Query cost: ${query_cost:.4f}/month (excess: {excess_tb:.3f} TB)")
        
        print(f"  Slot hours: {total_slot_hours:.2f}")
        if total_slot_hours <= 2000:
            print(f"  Slot cost: $0.00 (under free tier)")
        else:
            print(f"  Slot cost: ${slot_cost:.4f}/month (excess: {excess_slots:.2f} hours)")
        
        return {
            'jobs_30d': total_jobs,
            'gb_scanned_30d': total_gb,
            'tb_scanned_30d': total_gb / 1024,
            'slot_hours_30d': total_slot_hours,
            'query_cost': query_cost,
            'slot_cost': slot_cost
        }
        
    except Exception as e:
        print(f"Error querying job usage: {e}")
        return None


def get_streaming_usage(client):
    """Get streaming insert usage"""
    print("\n" + "=" * 80)
    print("STREAMING INSERT USAGE (Last 30 Days)")
    print("=" * 80)
    
    # Query streaming insert jobs
    streaming_query = f"""
    SELECT
      DATE(creation_time) as date,
      COUNT(*) as insert_count,
      SUM(total_bytes_processed) / POW(1024, 3) as total_gb
    FROM `{PROJECT_ID}.region-{LOCATION}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
    WHERE
      creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      AND job_type = 'LOAD'
      AND destination_table IS NOT NULL
      AND state = 'DONE'
    GROUP BY date
    ORDER BY date DESC
    LIMIT 30
    """
    
    try:
        job = client.query(streaming_query, location=LOCATION)
        results = job.result()
        
        total_inserts = 0
        total_gb = 0
        
        print(f"\n{'Date':<15} {'Load Jobs':<15} {'GB Loaded':<15}")
        print("-" * 80)
        
        for row in results:
            date = row.date
            inserts = row.insert_count or 0
            gb = row.total_gb or 0
            
            total_inserts += inserts
            total_gb += gb
            
            print(f"{str(date):<15} {inserts:<15} {gb:<15.3f}")
        
        print("-" * 80)
        print(f"{'TOTAL (30 days)':<15} {total_inserts:<15} {total_gb:<15.3f}")
        
        # Streaming insert cost
        # Batch loads: FREE
        # Streaming inserts: First 2 TB/month FREE, then $0.05 per 200 MB
        streaming_cost = 0.0
        free_tier_tb = 2.0
        if total_gb / 1024 > free_tier_tb:
            excess_tb = (total_gb / 1024) - free_tier_tb
            # $0.05 per 200 MB = $0.25 per GB = $250 per TB
            streaming_cost = excess_tb * 250.0
        
        print(f"\nStreaming Cost Calculation:")
        print(f"  Data loaded: {total_gb:.3f} GB ({total_gb/1024:.3f} TB)")
        print(f"  Free tier: 2 TB/month (batch loads are always free)")
        if total_gb / 1024 <= free_tier_tb:
            print(f"  Streaming cost: $0.00 (under free tier)")
        else:
            print(f"  Streaming cost: ${streaming_cost:.4f}/month (excess: {excess_tb:.3f} TB)")
        
        return {
            'load_jobs_30d': total_inserts,
            'gb_loaded_30d': total_gb,
            'streaming_cost': streaming_cost
        }
        
    except Exception as e:
        print(f"Error querying streaming usage: {e}")
        return None


def project_costs_with_vast_data(storage_data, query_data, streaming_data):
    """Project costs with vast amounts more data"""
    print("\n" + "=" * 80)
    print("COST PROJECTIONS (With Vast Data Growth)")
    print("=" * 80)
    
    if not storage_data:
        print("Cannot project - missing storage data")
        return
    
    current_storage_gb = storage_data['logical_gb']
    current_cost = storage_data['monthly_cost']
    
    # Project scenarios
    scenarios = [
        ("Current", 1.0),
        ("10x Growth", 10.0),
        ("50x Growth", 50.0),
        ("100x Growth", 100.0),
        ("500x Growth", 500.0),
        ("1000x Growth", 1000.0),
    ]
    
    print(f"\nCurrent Storage: {current_storage_gb:.3f} GB")
    print(f"Current Cost: ${current_cost:.4f}/month\n")
    
    print(f"{'Scenario':<20} {'Storage (GB)':<20} {'Monthly Cost':<20} {'Yearly Cost':<20}")
    print("-" * 80)
    
    for scenario_name, multiplier in scenarios:
        projected_storage = current_storage_gb * multiplier
        projected_cost = projected_storage * 0.020  # Active storage rate
        yearly_cost = projected_cost * 12
        
        print(f"{scenario_name:<20} {projected_storage:<20.3f} ${projected_cost:<20.2f} ${yearly_cost:<20.2f}")
    
    # Query projections
    if query_data:
        current_gb = query_data['gb_scanned_30d']
        current_tb = query_data['tb_scanned_30d']
        
        print(f"\n\nQuery Usage Projections:")
        print(f"Current: {current_gb:.3f} GB/month ({current_tb:.3f} TB/month)")
        
        for scenario_name, multiplier in scenarios:
            projected_gb = current_gb * multiplier
            projected_tb = projected_gb / 1024
            
            if projected_tb <= 1.0:
                query_cost = 0.0
            else:
                excess_tb = projected_tb - 1.0
                query_cost = excess_tb * 5.0
            
            print(f"  {scenario_name}: {projected_gb:.3f} GB/month → ${query_cost:.2f}/month")


def main():
    """Main execution"""
    print("=" * 80)
    print("BIGQUERY REAL COST ANALYSIS")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize client
    try:
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    except Exception as e:
        print(f"Error initializing BigQuery client: {e}")
        return
    
    # Get actual costs
    storage_data = get_storage_costs(client)
    query_data = get_query_usage(client)
    streaming_data = get_streaming_usage(client)
    
    # Summary
    print("\n" + "=" * 80)
    print("CURRENT MONTHLY COST SUMMARY")
    print("=" * 80)
    
    total_cost = 0.0
    
    if storage_data:
        print(f"Storage: ${storage_data['monthly_cost']:.4f}/month")
        total_cost += storage_data['monthly_cost']
    
    if query_data:
        print(f"Queries: ${query_data['query_cost']:.4f}/month")
        print(f"Slots: ${query_data['slot_cost']:.4f}/month")
        total_cost += query_data['query_cost'] + query_data['slot_cost']
    
    if streaming_data:
        print(f"Streaming: ${streaming_data['streaming_cost']:.4f}/month")
        total_cost += streaming_data['streaming_cost']
    
    print("-" * 80)
    print(f"TOTAL CURRENT COST: ${total_cost:.4f}/month")
    print("=" * 80)
    
    # Projections
    if storage_data:
        project_costs_with_vast_data(storage_data, query_data, streaming_data)
    
    # Export to JSON
    output = {
        'timestamp': datetime.now().isoformat(),
        'project': PROJECT_ID,
        'location': LOCATION,
        'current_costs': {
            'storage': storage_data['monthly_cost'] if storage_data else 0,
            'queries': query_data['query_cost'] if query_data else 0,
            'slots': query_data['slot_cost'] if query_data else 0,
            'streaming': streaming_data['streaming_cost'] if streaming_data else 0,
            'total': total_cost
        },
        'current_usage': {
            'storage_gb': storage_data['logical_gb'] if storage_data else 0,
            'queries_gb_30d': query_data['gb_scanned_30d'] if query_data else 0,
            'streaming_gb_30d': streaming_data['gb_loaded_30d'] if streaming_data else 0,
        }
    }
    
    output_file = Path(__file__).parent.parent.parent / 'REAL_BQ_COSTS.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()

