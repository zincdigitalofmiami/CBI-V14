#!/usr/bin/env python3
"""
Check all GCP resources that might be incurring costs.
Identifies Cloud SQL, Cloud Workstations, Compute Engine, Vertex AI endpoints, etc.
"""

import subprocess
import json
import sys
from typing import Dict, List, Any

PROJECT = "cbi-v14"
REGION = "us-central1"


def run_gcloud_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a gcloud command and return JSON output."""
    try:
        result = subprocess.run(
            ["gcloud"] + cmd + ["--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running: {' '.join(cmd)}")
        print(f"   {e.stderr}")
        return []
    except json.JSONDecodeError:
        return []


def check_compute_instances():
    """Check all Compute Engine instances."""
    print("\n" + "="*80)
    print("COMPUTE ENGINE INSTANCES")
    print("="*80)
    
    instances = run_gcloud_command([
        "compute", "instances", "list",
        "--project", PROJECT
    ])
    
    if not instances:
        print("✅ No Compute Engine instances found")
        return []
    
    total_cost = 0
    for instance in instances:
        zone = instance.get("zone", "").split("/")[-1]
        machine_type = instance.get("machineType", "").split("/")[-1]
        status = instance.get("status", "UNKNOWN")
        
        print(f"\n📦 Instance: {instance.get('name', 'UNKNOWN')}")
        print(f"   Zone: {zone}")
        print(f"   Machine Type: {machine_type}")
        print(f"   Status: {status}")
        print(f"   Creation: {instance.get('creationTimestamp', 'UNKNOWN')}")
        
        if status == "RUNNING":
            print(f"   ⚠️  RUNNING - This is incurring costs!")
            # Rough cost estimate
            if "e2-micro" in machine_type:
                print(f"   💰 Estimated cost: ~$6/month")
            elif "n1-standard" in machine_type:
                print(f"   💰 Estimated cost: ~$50-150/month")
            else:
                print(f"   💰 Check pricing for {machine_type}")
    
    return instances


def check_cloud_sql():
    """Check all Cloud SQL instances."""
    print("\n" + "="*80)
    print("CLOUD SQL INSTANCES")
    print("="*80)
    
    instances = run_gcloud_command([
        "sql", "instances", "list",
        "--project", PROJECT
    ])
    
    if not instances:
        print("✅ No Cloud SQL instances found")
        return []
    
    for instance in instances:
        name = instance.get("name", "UNKNOWN")
        region = instance.get("region", "UNKNOWN")
        tier = instance.get("settings", {}).get("tier", "UNKNOWN")
        state = instance.get("state", "UNKNOWN")
        
        print(f"\n🗄️  Instance: {name}")
        print(f"   Region: {region}")
        print(f"   Tier: {tier}")
        print(f"   State: {state}")
        
        if state == "RUNNABLE":
            print(f"   ⚠️  RUNNING - This is incurring costs!")
            print(f"   💰 Estimated cost: $50-200/month (depending on tier)")
            print(f"   💰 Your bill shows: $139.87/month")
    
    return instances


def check_cloud_workstations():
    """Check all Cloud Workstations."""
    print("\n" + "="*80)
    print("CLOUD WORKSTATIONS")
    print("="*80)
    
    # Check for workstation configs
    configs = run_gcloud_command([
        "workstations", "configs", "list",
        "--project", PROJECT,
        "--region", REGION
    ])
    
    if not configs:
        print("✅ No Cloud Workstation configs found")
    else:
        print(f"📝 Found {len(configs)} workstation config(s)")
        for config in configs:
            print(f"   Config: {config.get('name', 'UNKNOWN')}")
    
    # Check for active workstations
    workstations = run_gcloud_command([
        "workstations", "list",
        "--project", PROJECT,
        "--region", REGION
    ])
    
    if not workstations:
        print("✅ No active Cloud Workstations found")
    else:
        print(f"\n⚠️  Found {len(workstations)} active workstation(s):")
        for ws in workstations:
            name = ws.get("name", "UNKNOWN")
            state = ws.get("state", "UNKNOWN")
            print(f"   Workstation: {name}")
            print(f"   State: {state}")
            if state == "RUNNING":
                print(f"   ⚠️  RUNNING - Control plane fee: ~$91/month")
    
    return workstations or []


def check_vertex_ai_endpoints():
    """Check all Vertex AI endpoints."""
    print("\n" + "="*80)
    print("VERTEX AI ENDPOINTS")
    print("="*80)
    
    endpoints = run_gcloud_command([
        "ai", "endpoints", "list",
        "--project", PROJECT,
        "--region", REGION
    ])
    
    if not endpoints:
        print("✅ No Vertex AI endpoints found")
        return []
    
    for endpoint in endpoints:
        name = endpoint.get("displayName", endpoint.get("name", "UNKNOWN"))
        deployed_models = endpoint.get("deployedModels", [])
        
        print(f"\n🎯 Endpoint: {name}")
        print(f"   Resource: {endpoint.get('name', 'UNKNOWN')}")
        print(f"   Deployed Models: {len(deployed_models)}")
        
        if deployed_models:
            print(f"   ⚠️  HAS DEPLOYED MODELS - This is incurring costs!")
            for model in deployed_models:
                machine_type = model.get("dedicatedResources", {}).get("machineSpec", {}).get("machineType", "UNKNOWN")
                min_replicas = model.get("dedicatedResources", {}).get("minReplicaCount", 0)
                print(f"      Model: {model.get('displayName', 'UNKNOWN')}")
                print(f"      Machine Type: {machine_type}")
                print(f"      Min Replicas: {min_replicas}")
                print(f"      💰 Estimated cost: ~$50-200/month per replica")
    
    return endpoints


def check_vertex_ai_models():
    """Check Vertex AI models (storage costs)."""
    print("\n" + "="*80)
    print("VERTEX AI MODELS (Storage)")
    print("="*80)
    
    models = run_gcloud_command([
        "ai", "models", "list",
        "--project", PROJECT,
        "--region", REGION
    ])
    
    if not models:
        print("✅ No Vertex AI models found")
        return []
    
    print(f"📦 Found {len(models)} model(s)")
    total_size = 0
    for model in models:
        name = model.get("displayName", model.get("name", "UNKNOWN"))
        create_time = model.get("createTime", "UNKNOWN")
        print(f"   Model: {name}")
        print(f"   Created: {create_time}")
        # Note: Model storage is usually minimal cost
    
    return models


def check_cloud_functions():
    """Check Cloud Functions."""
    print("\n" + "="*80)
    print("CLOUD FUNCTIONS")
    print("="*80)
    
    functions = run_gcloud_command([
        "functions", "list",
        "--project", PROJECT,
        "--gen2"
    ])
    
    if not functions:
        print("✅ No Cloud Functions found")
        return []
    
    for func in functions:
        name = func.get("name", "UNKNOWN")
        state = func.get("state", "UNKNOWN")
        print(f"   Function: {name}")
        print(f"   State: {state}")
        # Cloud Functions only cost when invoked
    
    return functions


def check_disks():
    """Check persistent disks."""
    print("\n" + "="*80)
    print("PERSISTENT DISKS")
    print("="*80)
    
    disks = run_gcloud_command([
        "compute", "disks", "list",
        "--project", PROJECT
    ])
    
    if not disks:
        print("✅ No persistent disks found")
        return []
    
    total_size = 0
    for disk in disks:
        name = disk.get("name", "UNKNOWN")
        size_gb = int(disk.get("sizeGb", 0))
        status = disk.get("status", "UNKNOWN")
        users = disk.get("users", [])
        
        print(f"\n💾 Disk: {name}")
        print(f"   Size: {size_gb} GB")
        print(f"   Status: {status}")
        if users:
            print(f"   Attached to: {', '.join(users)}")
        else:
            print(f"   ⚠️  NOT ATTACHED - Still incurring storage costs!")
            print(f"   💰 Cost: ~${size_gb * 0.17}/month")
        
        total_size += size_gb
    
    print(f"\n📊 Total disk size: {total_size} GB")
    if total_size > 30:
        print(f"   ⚠️  Exceeds free tier (30 GB)")
        print(f"   💰 Cost for excess: ~${(total_size - 30) * 0.17}/month")
    
    return disks


def main():
    print("="*80)
    print("GCP RESOURCE AUDIT - Cost Analysis")
    print(f"Project: {PROJECT}")
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
    
    # Run all checks
    compute_instances = check_compute_instances()
    cloud_sql = check_cloud_sql()
    workstations = check_cloud_workstations()
    endpoints = check_vertex_ai_endpoints()
    models = check_vertex_ai_models()
    functions = check_cloud_functions()
    disks = check_disks()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    issues = []
    
    if compute_instances:
        running = [i for i in compute_instances if i.get("status") == "RUNNING"]
        if running:
            issues.append(f"⚠️  {len(running)} Compute Engine instance(s) running")
    
    if cloud_sql:
        running = [i for i in cloud_sql if i.get("state") == "RUNNABLE"]
        if running:
            issues.append(f"⚠️  {len(running)} Cloud SQL instance(s) running ($139.87/month)")
    
    if workstations:
        running = [w for w in workstations if w.get("state") == "RUNNING"]
        if running:
            issues.append(f"⚠️  {len(running)} Cloud Workstation(s) running ($91/month)")
    
    if endpoints:
        with_models = [e for e in endpoints if e.get("deployedModels")]
        if with_models:
            issues.append(f"⚠️  {len(with_models)} Vertex AI endpoint(s) with deployed models")
    
    if not issues:
        print("✅ No obvious cost issues found")
        print("   (Check BigQuery usage separately)")
    else:
        print("⚠️  COST ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Run cleanup script to shut down unnecessary resources:")
        print("   python3 scripts/analysis/cleanup_gcp_resources.py")


if __name__ == "__main__":
    main()









