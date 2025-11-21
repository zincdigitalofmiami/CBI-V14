#!/usr/bin/env python3
"""
Check GCP billing details to identify what's actually being charged.
Requires billing API to be enabled.
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta

PROJECT = "cbi-v14"


def check_billing_account():
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
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting billing account: {e.stderr}")
        return None


def check_all_regions():
    """Check resources in all regions."""
    print("\n" + "="*80)
    print("CHECKING ALL REGIONS")
    print("="*80)
    
    # Common regions
    regions = [
        "us-central1", "us-east1", "us-west1", "us-west2", "us-west3", "us-west4",
        "europe-west1", "europe-west2", "europe-west3", "europe-west4",
        "asia-east1", "asia-southeast1", "asia-northeast1"
    ]
    
    found_resources = False
    
    for region in regions:
        # Check Compute Engine
        instances = subprocess.run(
            ["gcloud", "compute", "instances", "list",
             "--project", PROJECT,
             "--filter", f"zone:{region}*",
             "--format=json"],
            capture_output=True,
            text=True
        )
        if instances.returncode == 0:
            data = json.loads(instances.stdout)
            if data:
                print(f"\n📍 Region: {region}")
                print(f"   Compute Engine instances: {len(data)}")
                for inst in data:
                    print(f"      - {inst.get('name')} ({inst.get('status')})")
                found_resources = True
        
        # Check Cloud SQL (global, but check anyway)
        if region == "us-central1":  # Only check once
            sql_instances = subprocess.run(
                ["gcloud", "sql", "instances", "list",
                 "--project", PROJECT,
                 "--format=json"],
                capture_output=True,
                text=True
            )
            if sql_instances.returncode == 0:
                data = json.loads(sql_instances.stdout)
                if data:
                    print(f"\n📍 Cloud SQL instances (global):")
                    for inst in data:
                        print(f"      - {inst.get('name')} ({inst.get('state')})")
                    found_resources = True
    
    if not found_resources:
        print("✅ No resources found in any region")
    
    return found_resources


def check_workstations_all_regions():
    """Check Cloud Workstations in all regions."""
    print("\n" + "="*80)
    print("CHECKING CLOUD WORKSTATIONS (ALL REGIONS)")
    print("="*80)
    
    regions = ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"]
    
    found = False
    for region in regions:
        try:
            configs = subprocess.run(
                ["gcloud", "workstations", "configs", "list",
                 "--project", PROJECT,
                 "--region", region,
                 "--format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if configs.returncode == 0:
                data = json.loads(configs.stdout)
                if data:
                    print(f"\n📍 Region: {region}")
                    for config in data:
                        print(f"   Config: {config.get('name')}")
                    found = True
        except:
            pass
    
    if not found:
        print("✅ No Cloud Workstation configs found in any region")
    
    return found


def check_vertex_ai_all_regions():
    """Check Vertex AI endpoints in all regions."""
    print("\n" + "="*80)
    print("CHECKING VERTEX AI ENDPOINTS (ALL REGIONS)")
    print("="*80)
    
    regions = ["us-central1", "us-east1", "us-west1", "europe-west1", "asia-east1"]
    
    found = False
    for region in regions:
        try:
            endpoints = subprocess.run(
                ["gcloud", "ai", "endpoints", "list",
                 "--project", PROJECT,
                 "--region", region,
                 "--format=json"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if endpoints.returncode == 0:
                data = json.loads(endpoints.stdout)
                if data:
                    print(f"\n📍 Region: {region}")
                    for endpoint in data:
                        deployed = len(endpoint.get("deployedModels", []))
                        print(f"   Endpoint: {endpoint.get('displayName')} ({deployed} models deployed)")
                    found = True
        except:
            pass
    
    if not found:
        print("✅ No Vertex AI endpoints found in any region")
    
    return found


def check_billing_export():
    """Try to check billing export (if enabled)."""
    print("\n" + "="*80)
    print("BILLING INFORMATION")
    print("="*80)
    
    billing_account = check_billing_account()
    if billing_account:
        print(f"✅ Billing Account: {billing_account}")
        print("\n💡 To see detailed billing:")
        print("   1. Go to: https://console.cloud.google.com/billing")
        print("   2. Select your billing account")
        print("   3. Click 'Reports' to see cost breakdown")
        print("   4. Filter by project: cbi-v14")
        print("\n💡 To see current month costs:")
        print("   gcloud billing accounts get-iam-policy BILLING_ACCOUNT_ID")
    else:
        print("❌ Could not get billing account")
        print("   Check: https://console.cloud.google.com/billing")


def main():
    print("="*80)
    print("COMPREHENSIVE GCP RESOURCE CHECK")
    print(f"Project: {PROJECT}")
    print("="*80)
    
    # Check all regions
    check_all_regions()
    check_workstations_all_regions()
    check_vertex_ai_all_regions()
    check_billing_export()
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print("\n1. Check GCP Console Billing directly:")
    print("   https://console.cloud.google.com/billing")
    print("\n2. Look for charges from:")
    print("   - Previous billing periods (charges may be delayed)")
    print("   - Other projects (if you have multiple)")
    print("   - Resources that were deleted but still show charges")
    print("\n3. Check for orphaned resources:")
    print("   - Unattached disks (we found 1: 50 GB)")
    print("   - Old snapshots")
    print("   - Old images")
    print("\n4. If resources were recently deleted:")
    print("   - Charges may appear for partial month")
    print("   - Wait 24-48 hours for billing to update")


if __name__ == "__main__":
    main()









