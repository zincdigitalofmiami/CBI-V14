#!/usr/bin/env python3
"""
Set up GCP billing alerts to prevent future cost surprises.
Creates budget alerts at $5, $10, and $20/month thresholds.
"""

import subprocess
import json
import sys

PROJECT = "cbi-v14"
BILLING_ACCOUNT = "015605-20A96F-2AD992"


def check_billing_account():
    """Verify billing account is accessible."""
    try:
        result = subprocess.run(
            ["gcloud", "billing", "accounts", "describe", BILLING_ACCOUNT,
             "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        print(f"✅ Billing Account: {data.get('displayName', BILLING_ACCOUNT)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error accessing billing account: {e.stderr}")
        return False


def create_budget(budget_name: str, amount: float, thresholds: list):
    """Create a billing budget with alerts."""
    print(f"\n📊 Creating budget: {budget_name}")
    print(f"   Amount: ${amount}/month")
    print(f"   Thresholds: {thresholds}")
    
    try:
        # Create budget
        cmd = [
            "gcloud", "billing", "budgets", "create",
            f"--billing-account={BILLING_ACCOUNT}",
            f"--display-name={budget_name}",
            f"--budget-amount={amount}USD",
            f"--filter-projects=projects/{PROJECT}",
        ]
        
        # Add threshold rules (correct syntax: percent=50, not threshold=50)
        for threshold in thresholds:
            cmd.append(f"--threshold-rule=percent={threshold}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Budget created successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr.lower():
            print(f"⚠️  Budget '{budget_name}' already exists")
            return True
        else:
            print(f"❌ Error creating budget: {e.stderr}")
            return False


def list_existing_budgets():
    """List existing budgets."""
    print("\n" + "="*80)
    print("EXISTING BUDGETS")
    print("="*80)
    
    try:
        result = subprocess.run(
            ["gcloud", "billing", "budgets", "list",
             f"--billing-account={BILLING_ACCOUNT}",
             "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        budgets = json.loads(result.stdout)
        
        if budgets:
            print(f"\nFound {len(budgets)} existing budget(s):")
            for budget in budgets:
                name = budget.get("displayName", "Unknown")
                amount = budget.get("budgetAmount", {}).get("specifiedAmount", {}).get("currencyCode", "USD")
                amount_value = budget.get("budgetAmount", {}).get("specifiedAmount", {}).get("units", "0")
                print(f"  - {name}: ${amount_value} {amount}")
        else:
            print("No existing budgets found")
        
        return budgets
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not list budgets: {e.stderr}")
        return []


def setup_email_notifications():
    """Instructions for setting up email notifications."""
    print("\n" + "="*80)
    print("EMAIL NOTIFICATIONS")
    print("="*80)
    print("\nTo receive email alerts when budgets are exceeded:")
    print("1. Go to: https://console.cloud.google.com/billing")
    print(f"2. Select billing account: {BILLING_ACCOUNT}")
    print("3. Click 'Budgets & alerts'")
    print("4. Click on each budget")
    print("5. Click 'Edit notifications'")
    print("6. Add your email address")
    print("7. Save")
    print("\nYou'll receive emails at:")
    print("  - 50% of budget")
    print("  - 90% of budget")
    print("  - 100% of budget")


def main():
    print("="*80)
    print("SETTING UP BILLING ALERTS")
    print(f"Project: {PROJECT}")
    print(f"Billing Account: {BILLING_ACCOUNT}")
    print("="*80)
    
    # Check billing account
    if not check_billing_account():
        print("\n❌ Cannot proceed without billing account access")
        sys.exit(1)
    
    # List existing budgets
    existing = list_existing_budgets()
    
    # Create budgets
    budgets_to_create = [
        {
            "name": "CBI-V14 Critical Alert ($5)",
            "amount": 5.0,
            "thresholds": [50, 90, 100]
        },
        {
            "name": "CBI-V14 Warning Alert ($10)",
            "amount": 10.0,
            "thresholds": [90, 100]
        },
        {
            "name": "CBI-V14 Emergency Alert ($20)",
            "amount": 20.0,
            "thresholds": [100]
        }
    ]
    
    print("\n" + "="*80)
    print("CREATING BUDGETS")
    print("="*80)
    
    created = 0
    for budget in budgets_to_create:
        # Check if budget already exists
        exists = any(
            b.get("displayName") == budget["name"]
            for b in existing
        )
        
        if exists:
            print(f"\n⏭️  Skipping '{budget['name']}' (already exists)")
        else:
            if create_budget(
                budget["name"],
                budget["amount"],
                budget["thresholds"]
            ):
                created += 1
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✅ Created {created} new budget(s)")
    print(f"⏭️  Skipped {len(budgets_to_create) - created} existing budget(s)")
    
    setup_email_notifications()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. Set up email notifications (see instructions above)")
    print("2. Verify budgets in GCP Console:")
    print(f"   https://console.cloud.google.com/billing/{BILLING_ACCOUNT}/budgets")
    print("3. Test by checking budget alerts")
    print("\n✅ Billing alerts are now active!")
    print("   You'll be notified at $2.50, $4.50, $5.00, $9.00, $10.00, and $20.00")


if __name__ == "__main__":
    main()

