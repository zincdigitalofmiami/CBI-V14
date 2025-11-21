#!/usr/bin/env python3
"""
Get current billing charges for the project.
Uses gcloud commands to query billing data.
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta

PROJECT = "cbi-v14"
BILLING_ACCOUNT = "015605-20A96F-2AD992"


def get_billing_account():
    """Get billing account ID."""
    try:
        result = subprocess.run(
            ["gcloud", "billing", "projects", "describe", PROJECT,
             "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        billing_account = data.get("billingAccountName", "").split("/")[-1]
        return billing_account
    except Exception as e:
        print(f"⚠️  Could not get billing account: {e}")
        return BILLING_ACCOUNT


def get_current_month_cost():
    """Try to get current month cost using gcloud."""
    print("="*80)
    print("CURRENT MONTH BILLING")
    print("="*80)
    
    billing_account = get_billing_account()
    print(f"Billing Account: {billing_account}\n")
    
    # Get current date range
    today = datetime.now()
    first_day = today.replace(day=1)
    
    print(f"Current Period: {first_day.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")
    print(f"Days in period: {(today - first_day).days + 1}\n")
    
    print("💡 To get exact current charges, you need to:")
    print("   1. Go to: https://console.cloud.google.com/billing")
    print(f"   2. Select billing account: {billing_account}")
    print("   3. Click 'Reports'")
    print(f"   4. Filter by project: {PROJECT}")
    print("   5. Set date range: Current month")
    print("\n   Or use BigQuery billing export (if enabled):")
    print("   SELECT SUM(cost) as total_cost")
    print("   FROM `billing_export.gcp_billing_export_v1_XXXXX`")
    print(f"   WHERE project.id = '{PROJECT}'")
    print(f"     AND usage_start_time >= '{first_day.strftime('%Y-%m-%d')}'")
    
    return None


def estimate_from_bill():
    """Estimate current charges based on your bill."""
    print("\n" + "="*80)
    print("ESTIMATED CURRENT CHARGES (Based on Your Bill)")
    print("="*80)
    
    # Your bill shows these monthly costs
    monthly_costs = {
        "Cloud SQL": 139.87,
        "Cloud Workstations": 91.40,
        "Compute Engine": 33.26,
        "Vertex AI": 24.80,
        "Networking": 17.38,
        "Dataplex": 1.31,
        "BigQuery": 0.28,
        "Artifact Registry": 0.05,
    }
    
    today = datetime.now()
    first_day = today.replace(day=1)
    days_in_month = today.day
    total_days = (today - first_day).days + 1
    
    print(f"\nCurrent Date: {today.strftime('%Y-%m-%d')}")
    print(f"Days into month: {days_in_month}")
    print(f"Days in period: {total_days}\n")
    
    print("If resources ran for FULL MONTH:")
    print("-" * 80)
    total_full_month = sum(monthly_costs.values())
    print(f"Total (full month): ${total_full_month:.2f}")
    
    print("\nIf resources were DELETED MID-MONTH:")
    print("-" * 80)
    # Estimate: if deleted 10 days ago
    days_ran = max(1, days_in_month - 10)
    prorated_total = sum(cost * (days_ran / 30) for cost in monthly_costs.values())
    print(f"Estimated (ran for ~{days_ran} days): ${prorated_total:.2f}")
    
    print("\nIf resources were DELETED RECENTLY (last few days):")
    print("-" * 80)
    # Estimate: if deleted 3 days ago
    days_ran_recent = max(1, days_in_month - 3)
    prorated_recent = sum(cost * (days_ran_recent / 30) for cost in monthly_costs.values())
    print(f"Estimated (ran for ~{days_ran_recent} days): ${prorated_recent:.2f}")
    
    print("\n" + "="*80)
    print("BREAKDOWN BY SERVICE")
    print("="*80)
    for service, cost in monthly_costs.items():
        prorated = cost * (days_ran / 30)
        print(f"{service:25} ${cost:8.2f}/month → ~${prorated:8.2f} (est. {days_ran} days)")
    
    print("\n" + "="*80)
    print("⚠️  IMPORTANT")
    print("="*80)
    print("These are ESTIMATES based on your bill.")
    print("Actual charges depend on:")
    print("  1. Exact dates resources were created/deleted")
    print("  2. Partial hour charges")
    print("  3. Billing lag (24-48 hours)")
    print("\nFor EXACT charges, check GCP Console Billing:")
    print(f"  https://console.cloud.google.com/billing/{BILLING_ACCOUNT}/reports")


def main():
    print("="*80)
    print("CURRENT BILLING ANALYSIS")
    print(f"Project: {PROJECT}")
    print("="*80)
    
    get_current_month_cost()
    estimate_from_bill()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Check GCP Console for exact charges")
    print("2. Set up billing alerts (see setup_billing_alerts.py)")
    print("3. Monitor next billing cycle")


if __name__ == "__main__":
    main()









