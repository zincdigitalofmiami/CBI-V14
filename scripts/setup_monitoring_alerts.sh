#!/bin/bash
#
# Setup Cloud Monitoring and BigQuery Budget Alerts
# Part of cron optimization plan implementation
#

set -e

PROJECT="cbi-v14"
REGION="us-central1"

echo "================================================================================"
echo "SETTING UP MONITORING & ALERTS FOR CBI-V14"
echo "================================================================================"
echo "Project: $PROJECT"
echo "Region: $REGION"
echo "================================================================================"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo "❌ Error: Not authenticated with gcloud"
    echo "   Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT

echo ""
echo "📊 Setting up BigQuery Budget Alerts..."
echo ""

# Create BigQuery budget alert policy
BUDGET_ALERT_POLICY='{
  "displayName": "BigQuery Cost Alert - 80%",
  "conditions": [
    {
      "displayName": "BigQuery costs exceed 80% of budget",
      "conditionThreshold": {
        "filter": "resource.type=\"billing_account\" AND metric.type=\"billing.googleapis.com/billing/billing_account_cost\"",
        "comparison": "COMPARISON_GT",
        "thresholdValue": 80,
        "duration": "0s"
      }
    }
  ],
  "notificationChannels": [],
  "alertStrategy": {
    "notificationRateLimit": {
      "period": "300s"
    }
  }
}'

echo "⚠️  Note: Budget alerts require manual setup in Google Cloud Console"
echo "   Go to: https://console.cloud.google.com/billing/budgets"
echo "   Create budget: \$100/month for BigQuery"
echo "   Set alerts at 80% (\$80) and 100% (\$100)"
echo ""

echo ""
echo "📈 Setting up Cloud Monitoring alerts..."
echo ""

# Check if monitoring API is enabled
if ! gcloud services list --enabled --filter="name:monitoring.googleapis.com" | grep -q monitoring; then
    echo "Enabling Cloud Monitoring API..."
    gcloud services enable monitoring.googleapis.com --project=$PROJECT
fi

echo ""
echo "Creating alert policies..."
echo ""

# Alert 1: BigQuery Job Failures
echo "  1. BigQuery Job Failures Alert..."
echo "     Note: Create manually in Cloud Console:"
echo "     - Go to: https://console.cloud.google.com/monitoring/alerting"
echo "     - Create policy for: BigQuery job failures"
echo "     - Filter: resource.type=\"bigquery_project\" AND metric.type=\"bigquery.googleapis.com/job/job_failed\""
echo ""

# Alert 2: Data Freshness (if tables are stale)
echo "  2. Data Freshness Alert..."
echo "     Note: Requires custom metric - create monitoring script"
echo ""

# Alert 3: Cloud Scheduler Job Failures
echo "  3. Cloud Scheduler Job Failures..."
SCHEDULER_ALERT_POLICY_NAME="cbi-v14-scheduler-failures"
echo "     Checking for existing alert policy..."

if gcloud alpha monitoring policies list --filter="displayName:$SCHEDULER_ALERT_POLICY_NAME" --format="value(name)" 2>/dev/null | grep -q .; then
    echo "     ✅ Alert policy already exists"
else
    echo "     ⚠️  Create manually in Cloud Console:"
    echo "        - Go to: https://console.cloud.google.com/monitoring/alerting"
    echo "        - Create policy for: Cloud Scheduler job failures"
    echo "        - Filter: resource.type=\"cloud_scheduler_job\" AND metric.type=\"cloudscheduler.googleapis.com/job/attempt_count\""
fi

echo ""
echo "📝 Creating job execution tracking table in BigQuery..."
echo ""

# Create job execution tracking table
JOB_TRACKING_TABLE="cbi-v14:forecasting_data_warehouse.job_execution_tracking"

bq query --use_legacy_sql=false << EOF
CREATE TABLE IF NOT EXISTS \`${JOB_TRACKING_TABLE}\` (
  job_name STRING NOT NULL,
  execution_time TIMESTAMP NOT NULL,
  status STRING NOT NULL,
  rows_processed INT64,
  duration_seconds FLOAT64,
  error_message STRING,
  cost_estimate_usd FLOAT64
)
PARTITION BY DATE(execution_time)
CLUSTER BY job_name, status
OPTIONS(
  description="Tracks execution of all cron jobs and scheduled tasks",
  labels=[("purpose", "monitoring"), ("component", "cron")]
)
EOF

if [ $? -eq 0 ]; then
    echo "✅ Job execution tracking table created"
else
    echo "⚠️  Error creating table (may already exist)"
fi

echo ""
echo "📋 Creating monitoring helper script..."
echo ""

# Create monitoring helper script
cat > /Users/zincdigital/CBI-V14/scripts/log_job_execution.py << 'PYEOF'
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
        'execution_time': datetime.now(),
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
PYEOF

chmod +x /Users/zincdigital/CBI-V14/scripts/log_job_execution.py

echo "✅ Monitoring helper script created: scripts/log_job_execution.py"

echo ""
echo "================================================================================"
echo "✅ MONITORING SETUP COMPLETE"
echo "================================================================================"
echo ""
echo "📋 Summary:"
echo "  ✅ Job execution tracking table created in BigQuery"
echo "  ✅ Monitoring helper script created"
echo ""
echo "⚠️  Manual Steps Required:"
echo ""
echo "1. BigQuery Budget Alerts:"
echo "   - Go to: https://console.cloud.google.com/billing/budgets"
echo "   - Create budget: \$100/month for BigQuery"
echo "   - Set alerts at 80% (\$80) and 100% (\$100)"
echo ""
echo "2. Cloud Monitoring Alerts:"
echo "   - Go to: https://console.cloud.google.com/monitoring/alerting"
echo "   - Create alerts for:"
echo "     • BigQuery job failures"
echo "     • Cloud Scheduler job failures"
echo "     • Data freshness (custom metric)"
echo ""
echo "3. Integrate Job Tracking:"
echo "   - Update cron jobs to call log_job_execution.py"
echo "   - Example: python3 scripts/log_job_execution.py hourly_prices success --rows 10 --duration 5.2"
echo ""
echo "📊 View job execution tracking:"
echo "   bq query --use_legacy_sql=false 'SELECT * FROM \`cbi-v14.forecasting_data_warehouse.job_execution_tracking\` ORDER BY execution_time DESC LIMIT 100'"
echo ""

