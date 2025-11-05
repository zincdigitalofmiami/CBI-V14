#!/usr/bin/env python3
"""
Helper script to log job execution to BigQuery tracking table
Usage: Call this from cron jobs to track execution
"""

import sys
from google.cloud import bigquery
from datetime import datetime
import time

def log_job_execution(job_name, status, rows_processed=0, duration_seconds=0, error_message=None, cost_estimate_usd=0):
    """Log job execution to BigQuery tracking table"""
    client = bigquery.Client(project='cbi-v14')
    table_id = 'cbi-v14.forecasting_data_warehouse.job_execution_tracking'
    
    row = {
        'job_name': job_name,
        'execution_time': datetime.now().isoformat(),
        'status': status,
        'rows_processed': rows_processed,
        'duration_seconds': duration_seconds,
        'error_message': error_message,
        'cost_estimate_usd': cost_estimate_usd
    }
    
    try:
        errors = client.insert_rows_json(table_id, [row])
        if errors:
            print(f"Error logging execution: {errors}", file=sys.stderr)
        else:
            print(f"✅ Logged execution: {job_name} - {status}")
    except Exception as e:
        print(f"Error logging execution: {e}", file=sys.stderr)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Log job execution to BigQuery')
    parser.add_argument('job_name', help='Name of the job')
    parser.add_argument('status', choices=['success', 'failure'], help='Job status')
    parser.add_argument('--rows', type=int, default=0, help='Rows processed')
    parser.add_argument('--duration', type=float, default=0, help='Duration in seconds')
    parser.add_argument('--error', help='Error message if failed')
    parser.add_argument('--cost', type=float, default=0, help='Estimated cost in USD')
    
    args = parser.parse_args()
    log_job_execution(args.job_name, args.status, args.rows, args.duration, args.error, args.cost)

