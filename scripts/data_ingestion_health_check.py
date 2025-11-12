#!/usr/bin/env python3
"""
CBI-V14 Data Ingestion Health Check
Monitors data collection quality and completeness
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import logging
import os
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

class DataIngestionHealthCheck:
    """Monitor data ingestion health and completeness"""

    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.report_data = {}

    def check_data_freshness(self):
        """Check how fresh all data sources are"""
        logger.info("📅 Checking data freshness...")

        data_sources = [
            ('soybean_oil_prices', 'forecasting_data_warehouse', 'time'),
            ('currency_data', 'forecasting_data_warehouse', 'date'),
            ('economic_indicators', 'forecasting_data_warehouse', 'time'),
            ('cftc_cot', 'forecasting_data_warehouse', 'report_date'),
            ('weather_data', 'forecasting_data_warehouse', 'date'),
            ('social_sentiment', 'forecasting_data_warehouse', 'timestamp'),
            ('news_intelligence', 'forecasting_data_warehouse', 'published_at'),
            ('trump_policy_intelligence', 'staging', 'timestamp'),
        ]

        freshness_report = []

        for table_name, dataset, date_col in data_sources:
            try:
                query = f"""
                SELECT
                  COUNT(*) as record_count,
                  MAX({date_col}) as latest_date,
                  MIN({date_col}) as earliest_date
                FROM `{PROJECT_ID}.{dataset}.{table_name}`
                WHERE {date_col} IS NOT NULL
                """

                result = self.client.query(query).to_dataframe()

                if not result.empty:
                    row = result.iloc[0]
                    latest = row['latest_date']

                    # Calculate days old
                    if hasattr(latest, 'to_pydatetime'):
                        latest_dt = latest.to_pydatetime()
                    else:
                        latest_dt = pd.to_datetime(latest)

                    days_old = (datetime.now() - latest_dt.replace(tzinfo=None)).days

                    # Determine status
                    if days_old <= 1:
                        status = "🟢 FRESH"
                    elif days_old <= 7:
                        status = "🟡 RECENT"
                    elif days_old <= 30:
                        status = "🟠 STALE"
                    else:
                        status = "🔴 OUTDATED"

                    freshness_report.append({
                        'table': f"{dataset}.{table_name}",
                        'records': row['record_count'],
                        'latest': latest.strftime('%Y-%m-%d') if hasattr(latest, 'strftime') else str(latest),
                        'days_old': days_old,
                        'status': status
                    })
                else:
                    freshness_report.append({
                        'table': f"{dataset}.{table_name}",
                        'records': 0,
                        'latest': 'No data',
                        'days_old': 999,
                        'status': "❌ EMPTY"
                    })

            except Exception as e:
                freshness_report.append({
                    'table': f"{dataset}.{table_name}",
                    'records': 0,
                    'latest': f'Error: {str(e)[:30]}',
                    'days_old': 999,
                    'status': "❌ ERROR"
                })

        self.report_data['freshness'] = freshness_report
        return freshness_report

    def check_cron_job_activity(self):
        """Check recent cron job activity via log files"""
        logger.info("📋 Checking cron job activity...")

        log_dir = "/Users/zincdigital/CBI-V14/logs"
        expected_logs = [
            'prices.log',
            'weather.log',
            'social_intel.log',
            'trump_policy.log',
            'economic_data.log',
            'cftc_data.log',
            'usda_exports.log',
            'biofuel_data.log',
            'scraper_morning.log',
            'scraper_afternoon.log'
        ]

        log_status = []

        for log_file in expected_logs:
            log_path = os.path.join(log_dir, log_file)

            if os.path.exists(log_path):
                # Check file modification time
                mtime = os.path.getmtime(log_path)
                last_modified = datetime.fromtimestamp(mtime)
                hours_old = (datetime.now() - last_modified).total_seconds() / 3600

                # Check for recent activity (last 24 hours)
                if hours_old <= 24:
                    status = "🟢 ACTIVE"
                elif hours_old <= 168:  # 7 days
                    status = "🟡 RECENT"
                else:
                    status = "🟠 INACTIVE"

                # Get file size
                size_mb = os.path.getsize(log_path) / (1024 * 1024)

                log_status.append({
                    'log_file': log_file,
                    'status': status,
                    'last_activity': last_modified.strftime('%Y-%m-%d %H:%M'),
                    'hours_old': round(hours_old, 1),
                    'size_mb': round(size_mb, 2)
                })
            else:
                log_status.append({
                    'log_file': log_file,
                    'status': "❌ MISSING",
                    'last_activity': 'Never',
                    'hours_old': 999,
                    'size_mb': 0
                })

        self.report_data['cron_activity'] = log_status
        return log_status

    def check_data_quality_metrics(self):
        """Check data quality metrics across sources"""
        logger.info("📊 Checking data quality metrics...")

        quality_checks = []

        # Check for duplicate records in key tables
        tables_to_check = [
            ('soybean_oil_prices', 'forecasting_data_warehouse'),
            ('currency_data', 'forecasting_data_warehouse'),
            ('economic_indicators', 'forecasting_data_warehouse'),
        ]

        for table_name, dataset in tables_to_check:
            try:
                # Check for duplicates in last 30 days
                query = f"""
                SELECT
                  COUNT(*) as total_records,
                  COUNT(DISTINCT date) as unique_dates,
                  (COUNT(*) - COUNT(DISTINCT date)) as duplicates
                FROM `{PROJECT_ID}.{dataset}.{table_name}`
                WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                """

                result = self.client.query(query).to_dataframe()

                if not result.empty:
                    row = result.iloc[0]
                    dup_rate = (row['duplicates'] / row['total_records'] * 100) if row['total_records'] > 0 else 0

                    if dup_rate < 1:
                        status = "🟢 GOOD"
                    elif dup_rate < 5:
                        status = "🟡 ACCEPTABLE"
                    else:
                        status = "🟠 HIGH DUPLICATES"

                    quality_checks.append({
                        'table': f"{dataset}.{table_name}",
                        'total_records': row['total_records'],
                        'duplicates': row['duplicates'],
                        'duplicate_rate': round(dup_rate, 2),
                        'status': status
                    })

            except Exception as e:
                quality_checks.append({
                    'table': f"{dataset}.{table_name}",
                    'total_records': 0,
                    'duplicates': 0,
                    'duplicate_rate': 0,
                    'status': f"❌ ERROR: {str(e)[:30]}"
                })

        self.report_data['quality'] = quality_checks
        return quality_checks

    def generate_health_report(self):
        """Generate comprehensive health report"""
        logger.info("📋 Generating comprehensive health report...")

        # Run all checks
        freshness = self.check_data_freshness()
        cron_activity = self.check_cron_job_activity()
        quality = self.check_data_quality_metrics()

        # Calculate overall health score
        fresh_score = sum(1 for item in freshness if 'FRESH' in item['status'] or 'RECENT' in item['status'])
        cron_score = sum(1 for item in cron_activity if 'ACTIVE' in item['status'] or 'RECENT' in item['status'])
        quality_score = sum(1 for item in quality if 'GOOD' in item['status'] or 'ACCEPTABLE' in item['status'])

        total_checks = len(freshness) + len(cron_activity) + len(quality)
        overall_score = (fresh_score + cron_score + quality_score) / total_checks * 100

        # Generate report
        report = f"""
================================================================================
CBI-V14 DATA INGESTION HEALTH REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

OVERALL HEALTH SCORE: {overall_score:.1f}%

1. DATA FRESHNESS ({fresh_score}/{len(freshness)} sources fresh)
================================================================================
"""

        for item in sorted(freshness, key=lambda x: x['days_old']):
            report += "6"
            report += f"{item['status']}\n"

        report += f"""

2. CRON JOB ACTIVITY ({cron_score}/{len(cron_activity)} logs active)
================================================================================
"""

        for item in sorted(cron_activity, key=lambda x: x['hours_old']):
            report += "12"
            report += f"{item['status']}\n"

        report += f"""

3. DATA QUALITY ({quality_score}/{len(quality)} tables good)
================================================================================
"""

        for item in sorted(quality, key=lambda x: x['duplicate_rate'], reverse=True):
            report += "20"
            report += f"{item['status']}\n"

        # Add recommendations
        report += f"""

4. RECOMMENDATIONS
================================================================================
"""

        issues = []

        # Freshness issues
        stale_sources = [item for item in freshness if item['days_old'] > 7]
        if stale_sources:
            issues.append(f"• {len(stale_sources)} data sources are stale (>7 days old)")

        # Cron issues
        inactive_crons = [item for item in cron_activity if 'INACTIVE' in item['status'] or 'MISSING' in item['status']]
        if inactive_crons:
            issues.append(f"• {len(inactive_crons)} cron jobs are not running")

        # Quality issues
        quality_problems = [item for item in quality if 'HIGH' in item['status'] or 'ERROR' in item['status']]
        if quality_problems:
            issues.append(f"• {len(quality_problems)} tables have quality issues")

        if issues:
            report += "Issues requiring attention:\n"
            for issue in issues:
                report += f"{issue}\n"
        else:
            report += "✅ All systems operating normally\n"

        report += f"""
CRITICAL MISSING DATA SOURCES (from audit):
• Baltic Dry Index (shipping costs)
• Port congestion data (supply chain)
• Fertilizer prices (production costs)
• ENSO climate data (weather forecasts)
• Satellite crop health (yield estimates)

================================================================================
END OF HEALTH REPORT
================================================================================
"""

        # Save report
        report_path = f"/Users/zincdigital/CBI-V14/logs/health_check_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            f.write(report)

        print(report)
        logger.info(f"✅ Health report saved to: {report_path}")

        return report_path

if __name__ == "__main__":
    checker = DataIngestionHealthCheck()
    report_path = checker.generate_health_report()
    print(f"\n📋 Full report saved to: {report_path}")








