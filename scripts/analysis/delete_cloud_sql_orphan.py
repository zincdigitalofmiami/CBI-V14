#!/usr/bin/env python3
"""
Attempt to find and delete orphaned Cloud SQL instances that might be charging.
Sometimes instances in certain states don't show up in normal list.
"""

import subprocess
import json
import sys

PROJECT = "cbi-v14"


def check_all_cloud_sql_states():
    """Check for Cloud SQL instances in all possible states."""
    print("="*80)
    print("SEARCHING FOR CLOUD SQL INSTANCES (ALL STATES)")
    print("="*80)
    
    # Try different filters
    filters = [
        "",  # No filter
        "state:RUNNABLE",
        "state:FAILED",
        "state:SUSPENDED",
        "state:PENDING_CREATE",
        "state:MAINTENANCE",
        "state:UNKNOWN_STATE",
    ]
    
    all_instances = []
    
    for filter_str in filters:
        cmd = ["gcloud", "sql", "instances", "list", "--project", PROJECT, "--format=json"]
        if filter_str:
            cmd.extend(["--filter", filter_str])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            if data:
                print(f"\n✅ Found {len(data)} instance(s) with filter: {filter_str or 'none'}")
                for inst in data:
                    print(f"   - {inst.get('name')}: {inst.get('state')} ({inst.get('tier')})")
                    if inst not in all_instances:
                        all_instances.append(inst)
        except Exception as e:
            pass
    
    if not all_instances:
        print("\n❌ No Cloud SQL instances found in any state")
        print("\n💡 This suggests:")
        print("   1. Instance was already deleted")
        print("   2. Charges are from previous billing period (billing lag)")
        print("   3. Instance exists in a different project")
        print("   4. Permissions issue (check with: gcloud projects get-iam-policy cbi-v14)")
    
    return all_instances


def check_billing_api():
    """Try to use billing API to find what's charging."""
    print("\n" + "="*80)
    print("CHECKING BILLING API")
    print("="*80)
    
    print("💡 To see what's actually charging, you need to:")
    print("   1. Go to: https://console.cloud.google.com/billing")
    print("   2. Select billing account: 015605-20A96F-2AD992")
    print("   3. Click 'Reports'")
    print("   4. Filter by:")
    print("      - Project: cbi-v14")
    print("      - Service: Cloud SQL")
    print("      - SKU: Cloud SQL for PostgreSQL: Regional - Enterprise Plus")
    print("   5. Check the 'Resource' column to see instance name")
    
    print("\n💡 Alternative: Use BigQuery billing export (if enabled)")
    print("   SELECT * FROM `billing_export.gcp_billing_export_v1_XXXXX`")
    print("   WHERE project.id = 'cbi-v14'")
    print("   AND service.description = 'Cloud SQL'")
    print("   ORDER BY usage_start_time DESC")


def try_find_by_name_patterns():
    """Try common Cloud SQL instance name patterns."""
    print("\n" + "="*80)
    print("TRYING COMMON INSTANCE NAMES")
    print("="*80)
    
    common_names = [
        "cbi-v14-db",
        "cbi-v14-sql",
        "cbi-v14-postgres",
        "postgres",
        "database",
        "db-instance",
        "cbi-db",
    ]
    
    found = False
    for name in common_names:
        try:
            result = subprocess.run(
                ["gcloud", "sql", "instances", "describe", name,
                 "--project", PROJECT,
                 "--format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                print(f"✅ Found instance: {name}")
                print(f"   State: {data.get('state')}")
                print(f"   Tier: {data.get('settings', {}).get('tier', 'UNKNOWN')}")
                print(f"   Region: {data.get('region', 'UNKNOWN')}")
                found = True
        except:
            pass
    
    if not found:
        print("❌ No instances found with common names")


def main():
    print("="*80)
    print("CLOUD SQL ORPHAN HUNT")
    print(f"Project: {PROJECT}")
    print("="*80)
    print("\n⚠️  Your bill shows $139.87/month for Cloud SQL")
    print("   But no instances are showing up in normal list.")
    print("   This script tries to find hidden/orphaned instances.\n")
    
    instances = check_all_cloud_sql_states()
    try_find_by_name_patterns()
    check_billing_api()
    
    if instances:
        print("\n" + "="*80)
        print("FOUND INSTANCES - DELETE THEM!")
        print("="*80)
        for inst in instances:
            name = inst.get('name')
            state = inst.get('state')
            tier = inst.get('tier', inst.get('settings', {}).get('tier', 'UNKNOWN'))
            
            print(f"\n🗑️  Instance: {name}")
            print(f"   State: {state}")
            print(f"   Tier: {tier}")
            print(f"   Cost: ~$139.87/month")
            print(f"\n   To delete:")
            print(f"   gcloud sql instances delete {name} --project={PROJECT}")
            print(f"\n   ⚠️  WARNING: This will DELETE all data!")
    else:
        print("\n" + "="*80)
        print("RECOMMENDATION")
        print("="*80)
        print("\nSince no instances are found, the charges are likely:")
        print("1. From a previous billing period (billing lag)")
        print("2. From an instance that was deleted but charges are still showing")
        print("\n💡 Action: Check GCP Console Billing directly:")
        print("   https://console.cloud.google.com/billing/015605-20A96F-2AD992/reports")
        print("\n   Look for:")
        print("   - Resource name in billing details")
        print("   - Date range of charges")
        print("   - Whether charges are from current or previous period")


if __name__ == "__main__":
    main()









