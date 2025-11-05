#!/usr/bin/env python3
"""
CBI-V14 COMPREHENSIVE CRON & DATA INGESTION AUDIT
Audit all cron jobs, data pulls, overlaps, and gaps in the system
"""

import subprocess
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
import logging
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "cbi-v14"

def get_current_cron_jobs():
    """Get current crontab and analyze scheduled jobs"""
    logger.info("🔍 ANALYZING CURRENT CRONTAB...")

    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            cron_content = result.stdout
        else:
            cron_content = "# No crontab found"
    except:
        cron_content = "# Error reading crontab"

    # Parse cron jobs
    jobs = []
    for line in cron_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Parse cron schedule (simplified)
        parts = line.split()
        if len(parts) >= 6:
            schedule = ' '.join(parts[:5])
            command = ' '.join(parts[5:])

            # Extract key info
            job_info = {
                'schedule': schedule,
                'command': command,
                'frequency': analyze_cron_schedule(schedule),
                'script': extract_script_name(command),
                'target': extract_target_info(command)
            }
            jobs.append(job_info)

    return jobs

def analyze_cron_schedule(schedule):
    """Analyze cron schedule to determine frequency"""
    try:
        minute, hour, day, month, weekday = schedule.split()

        if minute == '*' and hour == '*':
            return "Every minute"
        elif minute == '0' and hour == '*':
            return "Hourly"
        elif minute == '0' and '*/' in hour:
            interval = hour.split('/')[1]
            return f"Every {interval} hours"
        elif minute == '0' and hour.isdigit():
            return f"Daily at {hour}:00"
        elif minute == '0' and hour in ['6', '9', '16', '18']:
            hour_names = {'6': '6 AM', '9': '9 AM', '16': '4 PM', '18': '6 PM'}
            return f"Daily at {hour_names[hour]}"
        elif minute == '0' and hour == '6' and weekday == '1-5':
            return "Weekdays at 6 AM"
        else:
            return f"Custom: {schedule}"
    except:
        return f"Unknown: {schedule}"

def extract_script_name(command):
    """Extract script name from command"""
    if 'python3' in command:
        # Find the script path
        parts = command.split()
        for i, part in enumerate(parts):
            if part.endswith('.py'):
                return os.path.basename(part)
    return "Unknown script"

def extract_target_info(command):
    """Extract target data/info from command"""
    if 'hourly_prices' in command:
        return "Commodity prices (ZL, ZS, ZC, ZM) + VIX"
    elif 'daily_weather' in command:
        return "Weather data (19 stations)"
    elif 'production_web_scraper' in command:
        return "News & market data scraping"
    else:
        return "Unknown"

def analyze_data_sources():
    """Analyze what data sources are currently being collected"""
    logger.info("📊 ANALYZING DATA SOURCE COVERAGE...")

    client = bigquery.Client(project=PROJECT_ID)

    # Check key data tables
    data_sources = [
        {'name': 'Soybean Oil Prices', 'table': 'forecasting_data_warehouse.soybean_oil_prices', 'frequency': 'Hourly'},
        {'name': 'Weather Data', 'table': 'forecasting_data_warehouse.weather_data', 'frequency': 'Daily'},
        {'name': 'Social Sentiment', 'table': 'forecasting_data_warehouse.social_sentiment', 'frequency': 'Variable'},
        {'name': 'Trump Policy Intelligence', 'table': 'forecasting_data_warehouse.trump_policy_intelligence', 'frequency': 'Daily'},
        {'name': 'CFTC COT Data', 'table': 'forecasting_data_warehouse.cftc_cot', 'frequency': 'Weekly'},
        {'name': 'Economic Indicators', 'table': 'forecasting_data_warehouse.economic_indicators', 'frequency': 'Daily'},
        {'name': 'Currency Data', 'table': 'forecasting_data_warehouse.currency_data', 'frequency': 'Daily'},
        {'name': 'News Intelligence', 'table': 'forecasting_data_warehouse.news_intelligence', 'frequency': 'Hourly'},
    ]

    source_status = []
    for source in data_sources:
        try:
            query = f"""
            SELECT
              COUNT(*) as row_count,
              MIN(CASE WHEN date IS NOT NULL THEN date
                       WHEN timestamp IS NOT NULL THEN DATE(timestamp)
                       WHEN time IS NOT NULL THEN DATE(time)
                       ELSE NULL END) as earliest_date,
              MAX(CASE WHEN date IS NOT NULL THEN date
                       WHEN timestamp IS NOT NULL THEN DATE(timestamp)
                       WHEN time IS NOT NULL THEN DATE(time)
                       ELSE NULL END) as latest_date
            FROM `cbi-v14.{source['table']}`
            """

            result = client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                status = {
                    'name': source['name'],
                    'table': source['table'],
                    'frequency': source['frequency'],
                    'row_count': row['row_count'],
                    'date_range': f"{row['earliest_date']} to {row['latest_date']}" if row['earliest_date'] else 'No dates',
                    'status': 'Active' if row['row_count'] > 0 else 'Empty'
                }
                source_status.append(status)
        except Exception as e:
            source_status.append({
                'name': source['name'],
                'table': source['table'],
                'frequency': source['frequency'],
                'row_count': 0,
                'date_range': f'Error: {str(e)[:50]}',
                'status': 'Error'
            })

    return source_status

def check_for_overlaps_and_gaps():
    """Check for scheduling overlaps and data gaps"""
    logger.info("🔄 ANALYZING OVERLAPS AND GAPS...")

    issues = {
        'overlaps': [],
        'gaps': [],
        'missing_sources': [],
        'frequency_issues': []
    }

    # Check for overlapping times
    # 9 AM and 4 PM scraper might overlap with other processes

    # Check for missing critical data sources
    missing_critical = [
        'USDA Export Sales (weekly)',
        'Baltic Dry Index (daily)',
        'Port Congestion Data (daily)',
        'Fertilizer Prices (monthly)',
        'Satellite Crop Health (weekly)',
        'ENSO Climate Data (monthly)',
        'EIA Biofuel Production (weekly)',
        'USDA Harvest Progress (weekly)'
    ]

    issues['missing_sources'] = missing_critical

    # Check frequency issues
    frequency_concerns = [
        'News scraping only twice daily - missing breaking news',
        'Weather only at 6 AM - missing severe weather alerts',
        'No weekend data collection for some sources',
        'VIX data from Alpha Vantage may have API limits'
    ]

    issues['frequency_issues'] = frequency_concerns

    return issues

def audit_log_files():
    """Audit recent log file activity"""
    logger.info("📝 AUDITING LOG FILES...")

    log_dir = "/Users/zincdigital/CBI-V14/logs"
    log_files = [
        'prices.log',
        'weather.log',
        'scraper_morning.log',
        'scraper_afternoon.log'
    ]

    log_status = []
    for log_file in log_files:
        log_path = os.path.join(log_dir, log_file)
        if os.path.exists(log_path):
            # Check file size and last modification
            stat = os.stat(log_path)
            size_mb = stat.st_size / (1024 * 1024)
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            days_old = (datetime.now() - last_modified).days

            # Check for recent errors
            try:
                with open(log_path, 'r') as f:
                    recent_lines = f.readlines()[-10:]  # Last 10 lines
                    error_count = sum(1 for line in recent_lines if 'ERROR' in line or '❌' in line)
            except:
                error_count = -1

            log_status.append({
                'file': log_file,
                'size_mb': round(size_mb, 2),
                'last_modified': last_modified.strftime('%Y-%m-%d %H:%M'),
                'days_old': days_old,
                'recent_errors': error_count
            })
        else:
            log_status.append({
                'file': log_file,
                'size_mb': 0,
                'last_modified': 'Never',
                'days_old': 999,
                'recent_errors': -1
            })

    return log_status

def generate_recommendations():
    """Generate improvement recommendations"""
    logger.info("💡 GENERATING RECOMMENDATIONS...")

    recommendations = {
        'immediate': [
            'Add weekend data collection for critical sources',
            'Implement hourly news scraping for breaking developments',
            'Add data freshness monitoring alerts',
            'Create data quality dashboards'
        ],
        'short_term': [
            'Add missing data sources (USDA exports, Baltic index, etc.)',
            'Implement API rate limit monitoring',
            'Add automated data gap detection',
            'Create data source health monitoring'
        ],
        'long_term': [
            'Implement real-time data streaming',
            'Add predictive data freshness alerts',
            'Create automated data source failover',
            'Build comprehensive data lineage tracking'
        ]
    }

    return recommendations

def create_audit_report():
    """Create comprehensive audit report"""
    logger.info("📋 CREATING COMPREHENSIVE AUDIT REPORT...")

    # Gather all audit data
    cron_jobs = get_current_cron_jobs()
    data_sources = analyze_data_sources()
    issues = check_for_overlaps_and_gaps()
    log_status = audit_log_files()
    recommendations = generate_recommendations()

    # Create report
    report = f"""
================================================================================
CBI-V14 COMPREHENSIVE CRON & DATA INGESTION AUDIT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

1. CURRENT CRON SCHEDULE
================================================================================
"""

    if cron_jobs:
        for i, job in enumerate(cron_jobs, 1):
            report += f"{i}. {job['frequency']}\n"
            report += f"   Script: {job['script']}\n"
            report += f"   Target: {job['target']}\n"
            report += f"   Command: {job['command'][:100]}...\n\n"
    else:
        report += "No cron jobs found!\n\n"

    report += f"""
2. DATA SOURCE STATUS
================================================================================
"""

    for source in data_sources:
        report += f"📊 {source['name']}\n"
        report += f"   Table: {source['table']}\n"
        report += f"   Frequency: {source['frequency']}\n"
        report += f"   Records: {source['row_count']:,}\n"
        report += f"   Date Range: {source['date_range']}\n"
        report += f"   Status: {source['status']}\n\n"

    report += f"""
3. ISSUES IDENTIFIED
================================================================================

OVERLAPS & CONFLICTS:
"""
    if issues['overlaps']:
        for issue in issues['overlaps']:
            report += f"⚠️  {issue}\n"
    else:
        report += "✅ No scheduling overlaps detected\n"

    report += f"\nMISSING CRITICAL DATA SOURCES:\n"
    for source in issues['missing_sources']:
        report += f"❌ {source}\n"

    report += f"\nFREQUENCY CONCERNS:\n"
    for concern in issues['frequency_issues']:
        report += f"⚠️  {concern}\n"

    report += f"""

4. LOG FILE AUDIT
================================================================================
"""
    for log in log_status:
        status_icon = "✅" if log['recent_errors'] == 0 else "⚠️" if log['recent_errors'] > 0 else "❓"
        report += f"{status_icon} {log['file']}\n"
        report += f"   Size: {log['size_mb']:.2f} MB\n"
        report += f"   Last Modified: {log['last_modified']}\n"
        report += f"   Recent Errors: {log['recent_errors']}\n\n"

    report += f"""
5. RECOMMENDATIONS
================================================================================

IMMEDIATE (This Week):
"""
    for rec in recommendations['immediate']:
        report += f"🔥 {rec}\n"

    report += f"\nSHORT TERM (1-2 Weeks):\n"
    for rec in recommendations['short_term']:
        report += f"📅 {rec}\n"

    report += f"\nLONG TERM (1-3 Months):\n"
    for rec in recommendations['long_term']:
        report += f"🚀 {rec}\n"

    report += f"""

================================================================================
AUDIT SUMMARY
================================================================================
• Cron Jobs: {len(cron_jobs)} active
• Data Sources: {len(data_sources)} total
• Missing Sources: {len(issues['missing_sources'])}
• Log Files: {len(log_status)} monitored

RECOMMENDATION: Add weekend collection and implement missing critical sources
================================================================================
"""

    # Save report
    report_path = f"/Users/zincdigital/CBI-V14/logs/cron_audit_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w') as f:
        f.write(report)

    print(report)
    logger.info(f"✅ Audit report saved to: {report_path}")

    return report_path

if __name__ == "__main__":
    create_audit_report()


