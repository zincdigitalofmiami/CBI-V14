#!/usr/bin/env python3
"""
Populate Vegas tables with sample data for testing
TEMPORARY SOLUTION until Glide API is fixed
This creates realistic sample data based on your restaurant structure
"""

import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import random

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

def create_sample_customers():
    """Create sample customer data"""
    customers = [
        {
            'customer_id': 'MGM-001',
            'customer_name': 'MGM Resorts',
            'account_type': 'Enterprise',
            'relationship_score': 85,
            'current_volume_gal': 5000,
            'last_order_date': (datetime.now() - timedelta(days=5)).date(),
            'growth_potential': 'High',
            'next_action': 'F1 Event Upsell',
            'account_manager': 'Chris Stacy',
            'contract_end_date': (datetime.now() + timedelta(days=365)).date(),
            'ingested_at': datetime.now()
        },
        {
            'customer_id': 'CAESARS-001',
            'customer_name': 'Caesars Entertainment',
            'account_type': 'Enterprise',
            'relationship_score': 92,
            'current_volume_gal': 7500,
            'last_order_date': (datetime.now() - timedelta(days=3)).date(),
            'growth_potential': 'Medium',
            'next_action': 'Contract Renewal',
            'account_manager': 'Chris Stacy',
            'contract_end_date': (datetime.now() + timedelta(days=180)).date(),
            'ingested_at': datetime.now()
        },
        {
            'customer_id': 'WYNN-001',
            'customer_name': 'Wynn Resorts',
            'account_type': 'Premium',
            'relationship_score': 78,
            'current_volume_gal': 3500,
            'last_order_date': (datetime.now() - timedelta(days=10)).date(),
            'growth_potential': 'High',
            'next_action': 'Quarterly Review',
            'account_manager': 'Chris Stacy',
            'contract_end_date': (datetime.now() + timedelta(days=270)).date(),
            'ingested_at': datetime.now()
        }
    ]
    return pd.DataFrame(customers)

def create_sample_events():
    """Create sample event data - matches existing BigQuery schema"""
    events = [
        {
            'event_id': 'F1-2025',
            'event_name': 'F1 Las Vegas Grand Prix',
            'event_type': 'F1 Race',
            'event_date': (datetime.now() + timedelta(days=30)).date(),
            'location': 'Las Vegas Strip',
            'expected_attendance': 350000,
            'base_daily_traffic': 50000,
            'cuisine_intensity_factor': 1.8,
            'volume_multiplier': 3.4,
            'event_duration_days': 3,
            'revenue_opportunity': 145000.0,
            'urgency': 'IMMEDIATE ACTION',
            'ingested_at': datetime.now()
        },
        {
            'event_id': 'NYE-2025',
            'event_name': 'New Years Eve 2025',
            'event_type': 'Holiday Weekend',
            'event_date': (datetime.now() + timedelta(days=60)).date(),
            'location': 'Las Vegas Strip',
            'expected_attendance': 400000,
            'base_daily_traffic': 50000,
            'cuisine_intensity_factor': 1.5,
            'volume_multiplier': 2.8,
            'event_duration_days': 2,
            'revenue_opportunity': 95000.0,
            'urgency': 'HIGH PRIORITY',
            'ingested_at': datetime.now()
        },
        {
            'event_id': 'UFC-300',
            'event_name': 'UFC 300',
            'event_type': 'Major Fight',
            'event_date': (datetime.now() + timedelta(days=15)).date(),
            'location': 'T-Mobile Arena',
            'expected_attendance': 18000,
            'base_daily_traffic': 50000,
            'cuisine_intensity_factor': 1.3,
            'volume_multiplier': 2.2,
            'event_duration_days': 1,
            'revenue_opportunity': 32000.0,
            'urgency': 'MONITOR',
            'ingested_at': datetime.now()
        }
    ]
    return pd.DataFrame(events)

def create_sample_margin_alerts():
    """Create sample margin alert data"""
    alerts = [
        {
            'alert_id': 'ALERT-001',
            'customer_name': 'MGM Resorts - Bellagio',
            'alert_type': 'Price Increase Risk',
            'severity': 'HIGH',
            'current_margin_pct': 12.5,
            'risk_amount_usd': 15000,
            'recommended_action': 'Lock in forward contract for 90 days',
            'urgency': 'Immediate Action Required',
            'created_at': datetime.now() - timedelta(hours=2),
            'ingested_at': datetime.now()
        },
        {
            'alert_id': 'ALERT-002',
            'customer_name': 'Caesars - Caesars Palace',
            'alert_type': 'Volume Commitment Gap',
            'severity': 'MEDIUM',
            'current_margin_pct': 15.2,
            'risk_amount_usd': 8500,
            'recommended_action': 'Discuss event volume forecast',
            'urgency': 'Review Within 7 Days',
            'created_at': datetime.now() - timedelta(hours=24),
            'ingested_at': datetime.now()
        }
    ]
    return pd.DataFrame(alerts)

def create_sample_upsell_opportunities():
    """Create sample upsell opportunities - mapped directly to what dashboard expects"""
    opportunities = [
        {
            'id': 'OPP-001',
            'venue_name': 'MGM Grand',
            'event_name': 'F1 Las Vegas Grand Prix',
            'event_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'event_duration_days': 3,
            'expected_attendance': 350000,
            'oil_demand_surge_gal': 2800,
            'revenue_opportunity': 48000,
            'urgency': 'IMMEDIATE ACTION',
            'messaging_strategy_target': 'Gordon Ramsay Steak, Wolfgang Puck Bar & Grill, all high-end dining',
            'messaging_strategy_monthly_forecast': '3.4x normal volume = 2,800 additional gallons',
            'messaging_strategy_message': '"With F1 bringing 350K affluent visitors over 3 days, we anticipate a 3.4x surge in your oil needs. We can lock your rate now and ensure supply during the rush."',
            'messaging_strategy_timing': '45 days before event (optimal pricing window)',
            'messaging_strategy_value_prop': 'Rate lock + guaranteed delivery during peak demand',
            'ingested_at': datetime.now()
        },
        {
            'id': 'OPP-002',
            'venue_name': 'Caesars Palace',
            'event_name': 'New Years Eve 2025',
            'event_date': (datetime.now() + timedelta(days=60)).isoformat(),
            'event_duration_days': 2,
            'expected_attendance': 400000,
            'oil_demand_surge_gal': 3200,
            'revenue_opportunity': 52000,
            'urgency': 'HIGH PRIORITY',
            'messaging_strategy_target': 'All Caesars dining outlets',
            'messaging_strategy_monthly_forecast': '2.8x normal volume = 3,200 additional gallons',
            'messaging_strategy_message': '"NYE typically brings a 2.8x surge. We can secure your supply now at current rates before holiday pricing kicks in."',
            'messaging_strategy_timing': '60 days before event',
            'messaging_strategy_value_prop': 'Pre-holiday pricing + priority delivery',
            'ingested_at': datetime.now()
        },
        {
            'id': 'OPP-003',
            'venue_name': 'T-Mobile Arena',
            'event_name': 'UFC 300',
            'event_date': (datetime.now() + timedelta(days=15)).isoformat(),
            'event_duration_days': 1,
            'expected_attendance': 18000,
            'oil_demand_surge_gal': 450,
            'revenue_opportunity': 12000,
            'urgency': 'MONITOR',
            'messaging_strategy_target': 'Arena concessions',
            'messaging_strategy_monthly_forecast': '2.2x normal volume = 450 additional gallons',
            'messaging_strategy_message': '"UFC events drive 18K fight fans. Stock up early to avoid shortages during fight weekend."',
            'messaging_strategy_timing': '14 days before event',
            'messaging_strategy_value_prop': 'Guaranteed supply + same-day delivery',
            'ingested_at': datetime.now()
        }
    ]
    return pd.DataFrame(opportunities)

def populate_tables():
    """Populate all Vegas tables with sample data"""
    client = bigquery.Client(project=PROJECT_ID)
    
    print("=" * 60)
    print("POPULATING VEGAS TABLES WITH SAMPLE DATA")
    print("=" * 60)
    
    # Create sample data
    customers_df = create_sample_customers()
    events_df = create_sample_events()
    alerts_df = create_sample_margin_alerts()
    opportunities_df = create_sample_upsell_opportunities()
    
    # Save to BigQuery
    tables = {
        'vegas_customers': customers_df,
        'vegas_events': events_df,
        'vegas_margin_alerts': alerts_df,
        'vegas_upsell_opportunities': opportunities_df
    }
    
    for table_name, df in tables.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            autodetect=True
        )
        
        try:
            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()
            print(f"✅ Loaded {len(df)} rows to {table_name}")
        except Exception as e:
            print(f"❌ Error loading {table_name}: {e}")
    
    print("=" * 60)
    print("✅ SAMPLE DATA POPULATION COMPLETE")
    print("=" * 60)
    print("\n📊 Dashboard should now show data at:")
    print("https://cbi-dashboard.vercel.app/vegas")

if __name__ == "__main__":
    populate_tables()

