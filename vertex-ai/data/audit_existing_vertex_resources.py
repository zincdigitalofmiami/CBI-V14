#!/usr/bin/env python3
"""
audit_existing_vertex_resources.py
Audit existing Vertex AI datasets, models, and endpoints to understand what's already created.
Helps identify what to keep, clean up, or reference for new work.
"""

import os
import subprocess
import json
from datetime import datetime

PROJECT = os.getenv("PROJECT", "cbi-v14")
REGION = os.getenv("REGION", "us-central1")

def run_gcloud_command(cmd):
    """Run gcloud command and return JSON output."""
    try:
        result = subprocess.run(
            cmd + ["--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return []
    except json.JSONDecodeError:
        return []

def audit_datasets():
    """Audit existing Vertex AI datasets."""
    print("=== EXISTING VERTEX AI DATASETS ===\n")
    
    cmd = ["gcloud", "ai", "datasets", "list", "--region", REGION, "--project", PROJECT]
    datasets = run_gcloud_command(cmd)
    
    if not datasets:
        print("No datasets found or error accessing datasets.")
        return
    
    print(f"Found {len(datasets)} dataset(s):\n")
    
    for ds in datasets:
        name = ds.get("name", "N/A")
        display_name = ds.get("displayName", "N/A")
        create_time = ds.get("createTime", "N/A")
        metadata_schema_uri = ds.get("metadataSchemaUri", "N/A")
        
        print(f"Name: {name}")
        print(f"Display Name: {display_name}")
        print(f"Created: {create_time}")
        print(f"Schema: {metadata_schema_uri}")
        print("-" * 60)

def audit_models():
    """Audit existing Vertex AI models."""
    print("\n=== EXISTING VERTEX AI MODELS ===\n")
    
    cmd = ["gcloud", "ai", "models", "list", "--region", REGION, "--project", PROJECT]
    models = run_gcloud_command(cmd)
    
    if not models:
        print("No models found or error accessing models.")
        return
    
    print(f"Found {len(models)} model(s):\n")
    
    for model in models:
        name = model.get("name", "N/A")
        display_name = model.get("displayName", "N/A")
        create_time = model.get("createTime", "N/A")
        model_id = name.split("/")[-1] if "/" in name else name
        
        print(f"Model ID: {model_id}")
        print(f"Display Name: {display_name}")
        print(f"Created: {create_time}")
        print(f"Full Name: {name}")
        print("-" * 60)

def audit_endpoints():
    """Audit existing Vertex AI endpoints."""
    print("\n=== EXISTING VERTEX AI ENDPOINTS ===\n")
    
    cmd = ["gcloud", "ai", "endpoints", "list", "--region", REGION, "--project", PROJECT]
    endpoints = run_gcloud_command(cmd)
    
    if not endpoints:
        print("No endpoints found or error accessing endpoints.")
        return
    
    print(f"Found {len(endpoints)} endpoint(s):\n")
    
    for ep in endpoints:
        name = ep.get("name", "N/A")
        display_name = ep.get("displayName", "N/A")
        create_time = ep.get("createTime", "N/A")
        endpoint_id = name.split("/")[-1] if "/" in name else name
        
        print(f"Endpoint ID: {endpoint_id}")
        print(f"Display Name: {display_name}")
        print(f"Created: {create_time}")
        print(f"Full Name: {name}")
        print("-" * 60)

def check_naming_compliance():
    """Check if existing resources follow our naming conventions."""
    print("\n=== NAMING CONVENTION COMPLIANCE ===\n")
    
    expected_patterns = [
        "CBI V14 Vertex",
        "cbi-v14-vertex",
        "training_1m",
        "training_3m",
        "training_6m",
        "training_12m"
    ]
    
    print("Expected naming patterns:")
    for pattern in expected_patterns:
        print(f"  - {pattern}")
    print("\nNote: Existing resources may not follow new naming conventions.")
    print("New resources will follow strict naming conventions from CLEAN_WORKSPACE_ORGANIZATION_PLAN.md")

def main():
    """Run all audits."""
    print(f"Vertex AI Existing Resources Audit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("=" * 60 + "\n")
    print(f"Project: {PROJECT}")
    print(f"Region: {REGION}\n")
    print("=" * 60 + "\n")
    
    audit_datasets()
    audit_models()
    audit_endpoints()
    check_naming_compliance()
    
    print("\n" + "=" * 60)
    print("Audit complete.")
    print("\nRecommendations:")
    print("1. Document existing resources for reference")
    print("2. New resources will follow clean workspace naming conventions")
    print("3. Consider archiving old datasets/models if not in use")

if __name__ == "__main__":
    main()

