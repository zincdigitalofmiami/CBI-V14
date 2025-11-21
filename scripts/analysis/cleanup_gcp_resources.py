#!/usr/bin/env python3
"""
Cleanup script to shut down expensive GCP resources.
WARNING: This will shut down resources that are incurring costs.
"""

import subprocess
import sys
import argparse
from typing import List

PROJECT = "cbi-v14"
REGION = "us-central1"


def confirm_action(message: str) -> bool:
    """Ask for user confirmation."""
    response = input(f"{message} (yes/no): ").strip().lower()
    return response in ["yes", "y"]


def stop_compute_instance(instance_name: str, zone: str):
    """Stop a Compute Engine instance."""
    print(f"\n🛑 Stopping Compute Engine instance: {instance_name}")
    try:
        subprocess.run(
            ["gcloud", "compute", "instances", "stop", instance_name,
             "--zone", zone, "--project", PROJECT],
            check=True
        )
        print(f"✅ Stopped {instance_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error stopping {instance_name}: {e}")


def delete_cloud_sql_instance(instance_name: str):
    """Delete a Cloud SQL instance."""
    print(f"\n🗑️  Deleting Cloud SQL instance: {instance_name}")
    print("   ⚠️  WARNING: This will DELETE all data in the database!")
    
    if not confirm_action(f"   Are you sure you want to delete {instance_name}?"):
        print("   ❌ Cancelled")
        return
    
    try:
        subprocess.run(
            ["gcloud", "sql", "instances", "delete", instance_name,
             "--project", PROJECT, "--quiet"],
            check=True
        )
        print(f"✅ Deleted {instance_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error deleting {instance_name}: {e}")


def stop_cloud_workstation(workstation_name: str, config: str):
    """Stop a Cloud Workstation."""
    print(f"\n🛑 Stopping Cloud Workstation: {workstation_name}")
    try:
        subprocess.run(
            ["gcloud", "workstations", "stop", workstation_name,
             "--config", config,
             "--region", REGION,
             "--project", PROJECT],
            check=True
        )
        print(f"✅ Stopped {workstation_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error stopping {workstation_name}: {e}")


def delete_cloud_workstation(workstation_name: str, config: str):
    """Delete a Cloud Workstation."""
    print(f"\n🗑️  Deleting Cloud Workstation: {workstation_name}")
    
    if not confirm_action(f"   Are you sure you want to delete {workstation_name}?"):
        print("   ❌ Cancelled")
        return
    
    try:
        subprocess.run(
            ["gcloud", "workstations", "delete", workstation_name,
             "--config", config,
             "--region", REGION,
             "--project", PROJECT, "--quiet"],
            check=True
        )
        print(f"✅ Deleted {workstation_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error deleting {workstation_name}: {e}")


def undeploy_vertex_endpoint(endpoint_name: str):
    """Undeploy all models from a Vertex AI endpoint."""
    print(f"\n🛑 Undeploying models from endpoint: {endpoint_name}")
    
    if not confirm_action(f"   Undeploy all models from {endpoint_name}?"):
        print("   ❌ Cancelled")
        return
    
    try:
        # Get deployed models first
        result = subprocess.run(
            ["gcloud", "ai", "endpoints", "describe", endpoint_name,
             "--region", REGION,
             "--project", PROJECT,
             "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        import json
        endpoint = json.loads(result.stdout)
        deployed_models = endpoint.get("deployedModels", [])
        
        if not deployed_models:
            print("   ✅ No models deployed")
            return
        
        # Undeploy each model
        for model in deployed_models:
            model_id = model.get("id", "")
            print(f"   Undeploying model: {model_id}")
            subprocess.run(
                ["gcloud", "ai", "endpoints", "undeploy-model", endpoint_name,
                 "--deployed-model-id", model_id,
                 "--region", REGION,
                 "--project", PROJECT, "--quiet"],
                check=True
            )
        
        print(f"✅ Undeployed all models from {endpoint_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error undeploying from {endpoint_name}: {e}")


def delete_unattached_disk(disk_name: str, zone: str):
    """Delete an unattached persistent disk."""
    print(f"\n🗑️  Deleting unattached disk: {disk_name}")
    
    if not confirm_action(f"   Delete disk {disk_name}?"):
        print("   ❌ Cancelled")
        return
    
    try:
        subprocess.run(
            ["gcloud", "compute", "disks", "delete", disk_name,
             "--zone", zone,
             "--project", PROJECT, "--quiet"],
            check=True
        )
        print(f"✅ Deleted {disk_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error deleting {disk_name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup expensive GCP resources"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    parser.add_argument(
        "--auto-yes",
        action="store_true",
        help="Automatically confirm all actions (dangerous!)"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("GCP RESOURCE CLEANUP")
    print(f"Project: {PROJECT}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    print("="*80)
    
    # Check authentication
    try:
        subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        print("❌ Error: Not authenticated with gcloud")
        print("   Run: gcloud auth login")
        sys.exit(1)
    
    print("\n⚠️  WARNING: This script will shut down/delete resources!")
    print("   Run 'python3 scripts/analysis/check_gcp_resources.py' first")
    print("   to see what resources exist.\n")
    
    if not args.auto_yes:
        if not confirm_action("Continue with cleanup?"):
            print("❌ Cancelled")
            sys.exit(0)
    
    # Run the check script first to see what exists
    print("\n📋 Checking current resources...")
    subprocess.run(
        ["python3", "scripts/analysis/check_gcp_resources.py"],
        check=False
    )
    
    print("\n" + "="*80)
    print("CLEANUP OPTIONS")
    print("="*80)
    print("\nThis script requires manual selection of resources to clean up.")
    print("For safety, please run the check script first, then manually:")
    print("\n1. Stop Compute Engine instances:")
    print("   gcloud compute instances stop INSTANCE_NAME --zone=ZONE")
    print("\n2. Delete Cloud SQL instances:")
    print("   gcloud sql instances delete INSTANCE_NAME")
    print("\n3. Stop/Delete Cloud Workstations:")
    print("   gcloud workstations stop WORKSTATION_NAME --config=CONFIG --region=us-central1")
    print("   gcloud workstations delete WORKSTATION_NAME --config=CONFIG --region=us-central1")
    print("\n4. Undeploy Vertex AI endpoints:")
    print("   gcloud ai endpoints undeploy-model ENDPOINT_NAME --deployed-model-id=MODEL_ID --region=us-central1")
    print("\n5. Delete unattached disks:")
    print("   gcloud compute disks delete DISK_NAME --zone=ZONE")


if __name__ == "__main__":
    main()









