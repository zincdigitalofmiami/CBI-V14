#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script to troubleshoot gcloud and BigQuery connection issues.
Tests authentication, permissions, and connectivity.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        stdout = result.stdout if capture_output else ""
        stderr = result.stderr if capture_output else ""
        return result.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def check_gcloud_auth() -> Dict[str, any]:
    """Check gcloud authentication status."""
    print("\n" + "="*80)
    print("1. GCLOUD AUTHENTICATION CHECK")
    print("="*80)
    
    results = {}
    
    # Check active account
    exit_code, stdout, stderr = run_command(["gcloud", "auth", "list"])
    results["auth_list"] = {
        "status": "✅ PASS" if exit_code == 0 else "❌ FAIL",
        "output": stdout,
        "error": stderr
    }
    print(f"   Auth List: {results['auth_list']['status']}")
    if stdout:
        print(f"   {stdout.strip()}")
    
    # Check current project
    exit_code, stdout, stderr = run_command(["gcloud", "config", "get-value", "project"])
    results["project"] = {
        "status": "✅ PASS" if exit_code == 0 and stdout.strip() else "❌ FAIL",
        "value": stdout.strip() if exit_code == 0 else None,
        "error": stderr
    }
    print(f"   Active Project: {results['project']['value']}")
    
    # Check access token
    exit_code, stdout, stderr = run_command(["gcloud", "auth", "print-access-token"])
    results["access_token"] = {
        "status": "✅ PASS" if exit_code == 0 and len(stdout.strip()) > 0 else "❌ FAIL",
        "has_token": len(stdout.strip()) > 0 if exit_code == 0 else False,
        "error": stderr
    }
    print(f"   Access Token: {results['access_token']['status']}")
    
    # Check ADC
    adc_path = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    results["adc_file"] = {
        "status": "✅ EXISTS" if adc_path.exists() else "❌ MISSING",
        "path": str(adc_path),
        "readable": adc_path.exists() and os.access(adc_path, os.R_OK)
    }
    print(f"   ADC File: {results['adc_file']['status']}")
    if adc_path.exists():
        print(f"   Path: {results['adc_file']['path']}")
    
    # Check ADC token
    exit_code, stdout, stderr = run_command(["gcloud", "auth", "application-default", "print-access-token"])
    results["adc_token"] = {
        "status": "✅ PASS" if exit_code == 0 and len(stdout.strip()) > 0 else "❌ FAIL",
        "has_token": len(stdout.strip()) > 0 if exit_code == 0 else False,
        "error": stderr
    }
    print(f"   ADC Token: {results['adc_token']['status']}")
    
    return results

def check_iam_permissions() -> Dict[str, any]:
    """Check IAM permissions for current user."""
    print("\n" + "="*80)
    print("2. IAM PERMISSIONS CHECK")
    print("="*80)
    
    results = {}
    
    # Get current account
    exit_code, account_stdout, _ = run_command(["gcloud", "config", "get-value", "account"])
    if exit_code != 0:
        print("   ❌ Could not get current account")
        return results
    
    account = account_stdout.strip()
    print(f"   Checking permissions for: {account}")
    
    # Get project
    exit_code, project_stdout, _ = run_command(["gcloud", "config", "get-value", "project"])
    if exit_code != 0:
        print("   ❌ Could not get project")
        return results
    
    project = project_stdout.strip()
    
    # Get IAM policy
    exit_code, stdout, stderr = run_command([
        "gcloud", "projects", "get-iam-policy", project,
        "--flatten", "bindings[].members",
        "--format", "json"
    ])
    
    if exit_code == 0:
        try:
            bindings = json.loads(stdout)
            user_roles = []
            for binding in bindings:
                if account in binding.get("members", []):
                    user_roles.append(binding.get("role", ""))
            
            results["roles"] = user_roles
            results["status"] = "✅ PASS"
            print(f"   Found {len(user_roles)} roles:")
            for role in user_roles[:10]:  # Show first 10
                print(f"     - {role}")
            if len(user_roles) > 10:
                print(f"     ... and {len(user_roles) - 10} more")
        except json.JSONDecodeError:
            results["status"] = "❌ FAIL"
            results["error"] = "Could not parse IAM policy"
            print("   ❌ Could not parse IAM policy")
    else:
        results["status"] = "❌ FAIL"
        results["error"] = stderr
        print(f"   ❌ Failed to get IAM policy: {stderr}")
    
    return results

def check_bigquery_connection() -> Dict[str, any]:
    """Check BigQuery connection and permissions."""
    print("\n" + "="*80)
    print("3. BIGQUERY CONNECTION CHECK")
    print("="*80)
    
    results = {}
    
    try:
        from google.cloud import bigquery
    except ImportError:
        results["status"] = "❌ FAIL"
        results["error"] = "google-cloud-bigquery not installed"
        print("   ❌ google-cloud-bigquery not installed")
        print("   Install with: pip install google-cloud-bigquery")
        return results
    
    try:
        # Get project
        exit_code, project_stdout, _ = run_command(["gcloud", "config", "get-value", "project"])
        project = project_stdout.strip() if exit_code == 0 else "cbi-v14"
        
        # Create client
        client = bigquery.Client(project=project)
        results["client_creation"] = "✅ PASS"
        print(f"   Client created for project: {project}")
        
        # Test read query
        try:
            query = "SELECT 1 as test"
            result = client.query(query).result()
            rows = list(result)
            results["read_query"] = "✅ PASS"
            print(f"   Read Query: ✅ PASS")
        except Exception as e:
            results["read_query"] = "❌ FAIL"
            results["read_error"] = str(e)
            print(f"   Read Query: ❌ FAIL - {e}")
        
        # List datasets
        try:
            datasets = list(client.list_datasets())
            results["list_datasets"] = "✅ PASS"
            results["dataset_count"] = len(datasets)
            print(f"   List Datasets: ✅ PASS ({len(datasets)} datasets)")
            for ds in datasets[:5]:
                print(f"     - {ds.dataset_id}")
            if len(datasets) > 5:
                print(f"     ... and {len(datasets) - 5} more")
        except Exception as e:
            results["list_datasets"] = "❌ FAIL"
            results["list_error"] = str(e)
            print(f"   List Datasets: ❌ FAIL - {e}")
        
        # Test write (create a temp view in a test dataset)
        try:
            test_query = """
            CREATE OR REPLACE VIEW `{}.ops.test_write_permission` AS
            SELECT CURRENT_TIMESTAMP() as test_time, 'write_test' as test_value
            """.format(project)
            job = client.query(test_query)
            job.result()
            results["write_query"] = "✅ PASS"
            print(f"   Write Query: ✅ PASS")
            
            # Clean up
            try:
                client.delete_table(f"{project}.ops.test_write_permission")
            except:
                pass
        except Exception as e:
            results["write_query"] = "❌ FAIL"
            results["write_error"] = str(e)
            print(f"   Write Query: ❌ FAIL - {e}")
        
        results["status"] = "✅ PASS"
        
    except Exception as e:
        results["status"] = "❌ FAIL"
        results["error"] = str(e)
        print(f"   ❌ Connection failed: {e}")
    
    return results

def check_environment_variables() -> Dict[str, any]:
    """Check relevant environment variables."""
    print("\n" + "="*80)
    print("4. ENVIRONMENT VARIABLES CHECK")
    print("="*80)
    
    results = {}
    
    env_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GCP_PROJECT_ID",
        "GOOGLE_CLOUD_PROJECT",
        "GCLOUD_PROJECT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        results[var] = {
            "set": value is not None,
            "value": value if value else None,
            "exists": Path(value).exists() if value and var == "GOOGLE_APPLICATION_CREDENTIALS" else None
        }
        status = "✅ SET" if value else "⚠️  NOT SET"
        print(f"   {var}: {status}")
        if value:
            print(f"      Value: {value}")
            if var == "GOOGLE_APPLICATION_CREDENTIALS" and Path(value).exists():
                print(f"      File exists: ✅")
            elif var == "GOOGLE_APPLICATION_CREDENTIALS":
                print(f"      File exists: ❌")
    
    return results

def main():
    """Run all diagnostic checks."""
    print("\n" + "="*80)
    print("GCP CONNECTION DIAGNOSTIC TOOL")
    print("="*80)
    print("\nThis script will check:")
    print("  1. gcloud authentication")
    print("  2. IAM permissions")
    print("  3. BigQuery connection")
    print("  4. Environment variables")
    
    all_results = {}
    
    # Run checks
    all_results["gcloud_auth"] = check_gcloud_auth()
    all_results["iam_permissions"] = check_iam_permissions()
    all_results["bigquery"] = check_bigquery_connection()
    all_results["environment"] = check_environment_variables()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    issues = []
    
    if all_results["gcloud_auth"]["access_token"]["status"] != "✅ PASS":
        issues.append("❌ gcloud access token not working")
    
    if all_results["bigquery"].get("read_query") != "✅ PASS":
        issues.append("❌ BigQuery read access not working")
    
    if all_results["bigquery"].get("write_query") != "✅ PASS":
        issues.append("⚠️  BigQuery write access may be limited (read-only mode)")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ All checks passed!")
    
    print("\n" + "="*80)
    print("For detailed results, check the output above.")
    print("="*80 + "\n")
    
    return 0 if not issues else 1

if __name__ == "__main__":
    sys.exit(main())




