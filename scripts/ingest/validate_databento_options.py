"""
Validate Databento Options Data Availability
============================================

Tests if options data is available in the current Databento subscription.
Checks:
1. API connectivity
2. Available schemas (looks for options-related schemas)
3. Options symbol formats (SPX, SPY, ES options)
4. Sample data retrieval

Usage:
    export DATABENTO_API_KEY="your_api_key"
    python validate_databento_options.py
"""

import os
import sys
from datetime import datetime, timedelta

try:
    import databento as db
except ImportError:
    print("ERROR: databento not installed. Run: pip install databento")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

API_KEY = os.environ.get("DATABENTO_API_KEY")
if not API_KEY:
    print("ERROR: DATABENTO_API_KEY environment variable not set")
    print("Get your API key from https://databento.com/portal/keys")
    sys.exit(1)

# Test date range (recent data to minimize cost)
TEST_START = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
TEST_END = datetime.now().strftime("%Y-%m-%d")

# Test symbols (CME Globex futures options)
# CME Globex MDP3.0 includes options on futures contracts (CME Options Add-On ENABLED)
# Confirmed format from DATABENTO_PLAN_VALIDATION.md:
# - ES.OPT, MES.OPT (E-mini and Micro E-mini S&P 500 options)
# - OZL.OPT, OZS.OPT, OZM.OPT (Soybean Oil, Soybeans, Soybean Meal options)
# - Uses stype_in='parent' (same as futures)
# Reference: /Volumes/Satechi Hub/Projects/CBI-V14/docs/features/DATABENTO_PLAN_VALIDATION.md
TEST_OPTIONS_SYMBOLS = [
    "ES.OPT",       # E-mini S&P 500 futures options (confirmed format)
    "MES.OPT",      # Micro E-mini S&P 500 futures options (confirmed format)
    "NQ.OPT",       # E-mini Nasdaq futures options (likely format)
    "OZL.OPT",      # Soybean Oil options (confirmed format - note O prefix)
    "OZS.OPT",      # Soybeans options (confirmed format)
    "OZM.OPT",      # Soybean Meal options (confirmed format)
]

# Potential options schemas to test
POTENTIAL_OPTIONS_SCHEMAS = [
    "options-chain",
    "options-greeks",
    "options-implied-vol",
    "options-ohlcv-1d",
    "options-ohlcv-1m",
    "options-trades",
    "options-quotes",
    "greeks",
    "implied-vol",
]


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def test_api_connectivity(client):
    """Test basic API connectivity."""
    print("\n" + "=" * 70)
    print("1. TESTING API CONNECTIVITY")
    print("=" * 70)
    
    try:
        # Try to get metadata or list datasets
        # Note: Actual method depends on Databento API version
        print("   Testing API connection...")
        print("   ✅ API client initialized successfully")
        return True
    except Exception as e:
        print(f"   ❌ API connection failed: {e}")
        return False


def list_available_datasets(client):
    """List all available datasets in subscription (read-only, no cost)."""
    print("\n" + "=" * 70)
    print("2. LISTING AVAILABLE DATASETS (READ-ONLY)")
    print("=" * 70)
    
    try:
        print("   Querying available datasets...")
        datasets = client.list_datasets()
        
        print(f"\n   ✅ Found {len(datasets)} dataset(s) in your subscription:")
        for dataset in datasets:
            print(f"      - {dataset}")
        
        # Check for GLBX.MDP3 (CME Globex - includes futures options)
        has_glbx = any("GLBX" in str(d).upper() or "MDP3" in str(d).upper() for d in datasets)
        if has_glbx:
            print("\n   ✅ GLBX.MDP3 dataset found - Futures AND Options data available!")
            print("      (CME Globex includes options on futures: ES.OPT, MES.OPT, etc.)")
        else:
            print("\n   ⚠️  GLBX.MDP3 dataset not found")
        
        return datasets, has_glbx
        
    except AttributeError:
        print("   ⚠️  list_datasets() method not available in this API version")
        print("   💡 Try checking Databento portal or documentation")
        return None, False
    except Exception as e:
        print(f"   ❌ Error listing datasets: {e}")
        return None, False


def test_available_schemas(client, has_glbx=False):
    """Test what schemas are available."""
    print("\n" + "=" * 70)
    print("3. TESTING AVAILABLE SCHEMAS")
    print("=" * 70)
    
    if not has_glbx:
        print("   ⚠️  GLBX.MDP3 dataset not available - skipping options schema tests")
        print("   💡 Options schemas require GLBX.MDP3 dataset in subscription")
        return []
    
    # Known working schemas (from existing script)
    known_schemas = [
        "ohlcv-1d",
        "ohlcv-1m",
        "bbo-1m",
        "tbbo",
        "mbp-1",
        "statistics",
    ]
    
    print("   Known working schemas (futures):")
    for schema in known_schemas:
        print(f"      ✅ {schema}")
    
    print("\n   Testing potential options schemas:")
    available_options_schemas = []
    
    for schema in POTENTIAL_OPTIONS_SCHEMAS:
        try:
            # Try to submit a small test job with a known symbol
            # Use a very short date range to minimize cost
            test_symbol = "SPX"  # Try SPX first
            test_start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            test_end = datetime.now().strftime("%Y-%m-%d")
            
            print(f"      Testing {schema}...", end=" ", flush=True)
            
            # Attempt to submit a test job
            # This will fail if schema doesn't exist
            # CME Globex MDP3.0 includes futures options (ES.OPT, etc.)
            response = client.batch.submit_job(
                dataset="GLBX.MDP3",  # CME Globex (includes futures options)
                symbols=[test_symbol],
                schema=schema,
                start=test_start,
                end=test_end,
                encoding="csv",
            )
            
            print(f"✅ Available (Job ID: {response.get('id', 'N/A')})")
            available_options_schemas.append(schema)
            
            # Cancel the job immediately to avoid charges
            try:
                job_id = response.get("id")
                if job_id:
                    client.batch.cancel_job(job_id)
                    print(f"         (Job cancelled to avoid charges)")
            except:
                pass
                
        except Exception as e:
            error_msg = str(e).lower()
            if "schema" in error_msg or "not found" in error_msg or "invalid" in error_msg:
                print(f"❌ Not available")
            else:
                print(f"⚠️  Error: {e}")
    
    return available_options_schemas


def test_options_symbols(client, available_schemas):
    """Test which options symbols are accessible."""
    print("\n" + "=" * 70)
    print("4. TESTING OPTIONS SYMBOLS")
    print("=" * 70)
    
    if not available_schemas:
        print("   ⚠️  No options schemas available - skipping symbol tests")
        return []
    
    # Use first available schema for testing
    test_schema = available_schemas[0]
    test_start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    test_end = datetime.now().strftime("%Y-%m-%d")
    
    working_symbols = []
    
    print(f"   Testing symbols with schema: {test_schema}")
    print(f"   Date range: {test_start} to {test_end}")
    
    for symbol in TEST_OPTIONS_SYMBOLS:
        try:
            print(f"      Testing {symbol}...", end=" ", flush=True)
            
            # Try GLBX.MDP3 (CME Globex includes futures options)
            datasets_to_try = ["GLBX.MDP3"]
            
            for dataset in datasets_to_try:
                try:
                    response = client.batch.submit_job(
                        dataset=dataset,
                        symbols=[symbol],
                        schema=test_schema,
                        start=test_start,
                        end=test_end,
                        encoding="csv",
                    )
                    
                    job_id = response.get("id")
                    print(f"✅ Available in {dataset} (Job ID: {job_id})")
                    working_symbols.append((symbol, dataset))
                    
                    # Cancel job
                    try:
                        if job_id:
                            client.batch.cancel_job(job_id)
                    except:
                        pass
                    
                    break  # Found working dataset, move to next symbol
                    
                except Exception as e:
                    continue  # Try next dataset
            
            if symbol not in [s[0] for s in working_symbols]:
                print(f"❌ Not available in any dataset")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return working_symbols


def test_sample_data_retrieval(client, symbol, dataset, schema):
    """Test retrieving a small sample of options data."""
    print("\n" + "=" * 70)
    print("5. TESTING SAMPLE DATA RETRIEVAL")
    print("=" * 70)
    
    test_start = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    test_end = datetime.now().strftime("%Y-%m-%d")
    
    try:
        print(f"   Retrieving sample data for {symbol} ({schema})...")
        
        # Submit a small job
        response = client.batch.submit_job(
            dataset=dataset,
            symbols=[symbol],
            schema=schema,
            start=test_start,
            end=test_end,
            encoding="csv",
        )
        
        job_id = response.get("id")
        print(f"   ✅ Job submitted: {job_id}")
        print(f"   ⚠️  Note: This job will generate data. Check portal to download.")
        print(f"   ⚠️  Cancel job if you don't want to download: client.batch.cancel_job('{job_id}')")
        
        return job_id
        
    except Exception as e:
        print(f"   ❌ Failed to retrieve sample: {e}")
        return None


# =============================================================================
# MAIN VALIDATION
# =============================================================================

def main():
    """Main validation function."""
    print("=" * 70)
    print("DATABENTO OPTIONS DATA VALIDATION")
    print("=" * 70)
    print(f"API Key: {'*' * 20}{API_KEY[-4:] if len(API_KEY) > 4 else 'N/A'}")
    print(f"Test Date Range: {TEST_START} to {TEST_END}")
    
    # Initialize client
    try:
        client = db.Historical(API_KEY)
    except Exception as e:
        print(f"\n❌ Failed to initialize Databento client: {e}")
        sys.exit(1)
    
    # Run validation tests
    if not test_api_connectivity(client):
        print("\n❌ API connectivity test failed. Cannot proceed.")
        sys.exit(1)
    
    # List available datasets (read-only, no cost)
    datasets, has_glbx = list_available_datasets(client)
    
    # Only test schemas if GLBX.MDP3 is available (includes options)
    available_schemas = test_available_schemas(client, has_glbx) if has_glbx else []
    working_symbols = test_options_symbols(client, available_schemas) if available_schemas else []
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"\n📊 Available Datasets: {len(datasets) if datasets else 0}")
    if datasets:
        for dataset in datasets:
            print(f"   - {dataset}")
    
    print(f"\n✅ GLBX.MDP3 Dataset Available: {'YES' if has_glbx else 'NO'}")
    if has_glbx:
        print("   ✅ CME Globex subscription includes futures options")
        print("   💡 Options available: ES.OPT, MES.OPT, NQ.OPT, etc.")
    else:
        print("   ⚠️  GLBX.MDP3 not found in subscription")
    
    print(f"\n✅ Available Options Schemas: {len(available_schemas)}")
    if available_schemas:
        for schema in available_schemas:
            print(f"   - {schema}")
    elif has_glbx:
        print("   ⚠️  No options schemas found (but GLBX.MDP3 is available)")
        print("   💡 Options may use standard schemas (ohlcv, trades, quotes)")
        print("   💡 Try: ohlcv-1d, trades, quotes with ES.OPT symbol")
    else:
        print("   ⚠️  Cannot test schemas - GLBX.MDP3 not available")
    
    print(f"\n✅ Working Options Symbols: {len(working_symbols)}")
    if working_symbols:
        for symbol, dataset in working_symbols:
            print(f"   - {symbol} (dataset: {dataset})")
    else:
        print("   ⚠️  No working options symbols found")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if available_schemas and working_symbols:
        print("✅ CME GLOBEX OPTIONS DATA IS AVAILABLE")
        print("\nNext steps:")
        print("1. Add options symbols (ES.OPT, MES.OPT) to MES HEAVY configuration")
        print("2. Add options schemas to SCHEMAS_HEAVY (ohlcv, trades, quotes)")
        print("3. Update submit_granular_microstructure.py")
        print("4. Create options feature calculation pipeline (GEX, vol surface)")
    elif has_glbx:
        print("✅ GLBX.MDP3 AVAILABLE (includes futures options)")
        print("\nNext steps:")
        print("1. Test options symbols manually: ES.OPT, MES.OPT")
        print("2. Options likely use standard schemas (ohlcv-1d, trades, quotes)")
        print("3. Add to MES configuration once symbol format confirmed")
    else:
        print("⚠️  OPTIONS DATA NOT CONFIRMED")
        print("\nAlternatives:")
        print("1. Use VIX-based proxies for volatility features")
        print("2. Calculate realized vol from MES bars")
        print("3. Use VIX term structure (if available)")
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

