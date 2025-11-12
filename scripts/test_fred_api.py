#!/usr/bin/env python3
"""
Test FRED API key by making a simple API call
"""
import os
import requests
import sys

PROJECT_ID = "cbi-v14"
FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Try to get API key from multiple sources
FRED_API_KEY = os.getenv('FRED_API_KEY')

# Try Secret Manager if available
if not FRED_API_KEY:
    try:
        from google.cloud import secretmanager
        client_secret = secretmanager.SecretManagerServiceClient()
        name = f'projects/{PROJECT_ID}/secrets/forecasting-data-keys/versions/latest'
        response = client_secret.access_secret_version(request={'name': name})
        secret_data = response.payload.data.decode('UTF-8')
        import json
        keys = json.loads(secret_data)
        FRED_API_KEY = keys.get('FRED_API_KEY') or keys.get('fred_api_key')
        print("✅ Found FRED API key in Secret Manager")
    except Exception as e:
        print(f"⚠️  Could not retrieve from Secret Manager: {str(e)[:100]}")

# Fallback to hardcoded key (if found in codebase)
if not FRED_API_KEY:
    print("⚠️  Trying hardcoded key from codebase...")
    FRED_API_KEY = "dc195c8658c46ee1df83bcd4fd8a690b"

if not FRED_API_KEY:
    print("❌ ERROR: No FRED API key found!")
    print("   Set FRED_API_KEY environment variable or add to Secret Manager")
    sys.exit(1)

print(f"\n🔑 Testing FRED API key: {FRED_API_KEY[:8]}...{FRED_API_KEY[-4:]}")
print("="*80)

# Test 1: Simple series info request (GDPC1 - Real GDP)
print("\n📊 Test 1: Fetching series info for GDPC1 (Real GDP)...")
try:
    url = f"{FRED_BASE_URL}/series"
    params = {
        'series_id': 'GDPC1',
        'api_key': FRED_API_KEY,
        'file_type': 'json'
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'seriess' in data and len(data['seriess']) > 0:
        series = data['seriess'][0]
        print(f"   ✅ Series info retrieved successfully!")
        print(f"   Title: {series.get('title', 'N/A')}")
        print(f"   Units: {series.get('units', 'N/A')}")
        print(f"   Frequency: {series.get('frequency', 'N/A')}")
    else:
        print(f"   ⚠️  Unexpected response format")
        print(f"   Response: {str(data)[:200]}")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        print(f"   ❌ Authentication failed (403 Forbidden)")
        print(f"   The API key may be invalid or expired")
    elif e.response.status_code == 400:
        print(f"   ❌ Bad request (400)")
        print(f"   Response: {e.response.text[:200]}")
    else:
        print(f"   ❌ HTTP Error {e.response.status_code}: {e.response.text[:200]}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    sys.exit(1)

# Test 2: Fetch recent observations
print("\n📈 Test 2: Fetching recent observations for GDPC1...")
try:
    url = f"{FRED_BASE_URL}/series/observations"
    params = {
        'series_id': 'GDPC1',
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': 5,
        'sort_order': 'desc'
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'observations' in data and len(data['observations']) > 0:
        print(f"   ✅ Retrieved {len(data['observations'])} observations")
        print(f"   Most recent observations:")
        for obs in data['observations'][:3]:
            print(f"     - {obs.get('date', 'N/A')}: {obs.get('value', 'N/A')}")
    else:
        print(f"   ⚠️  No observations found")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    sys.exit(1)

# Test 3: Check rate limits/status
print("\n⏱️  Test 3: Checking API status...")
try:
    # Try a simple categories request to verify API is responsive
    url = f"{FRED_BASE_URL}/categories"
    params = {
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'limit': 1
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    print(f"   ✅ API is responsive (status: {response.status_code})")
except Exception as e:
    print(f"   ⚠️  Status check failed: {str(e)[:100]}")

print("\n" + "="*80)
print("✅ FRED API KEY TEST COMPLETE")
print("="*80)
print(f"\n✅ API Key is VALID and working!")
print(f"   Key: {FRED_API_KEY[:8]}...{FRED_API_KEY[-4:]}")
print(f"   You can use this key for FRED API calls.\n")









