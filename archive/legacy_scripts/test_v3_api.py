#!/usr/bin/env python3
"""
Test V3 Model API Endpoints
Verifies that models are properly wired and returning predictions
"""

import requests
import json
from datetime import datetime
from tabulate import tabulate

# API base URL (adjust if running on different port)
BASE_URL = "http://localhost:8000/api/v3"

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*60)
    print("TESTING MODEL INFO ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/model-info")
        if response.status_code == 200:
            data = response.json()
            print("✓ Model info retrieved successfully")
            print(f"\nTotal models: {data['summary']['total_models']}")
            print(f"Best overall: {data['summary']['best_overall']}")
            print(f"Best MAE: {data['summary']['best_mae']}")
            
            # Display model performance
            print("\nModel Performance:")
            for horizon, info in data['best_models'].items():
                print(f"  {horizon}: MAE={info['mae']:.2f}, R²={info['r2']:.3f} ({info['type']})")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_single_forecast(horizon="1w"):
    """Test single forecast endpoint"""
    print(f"\n" + "="*60)
    print(f"TESTING SINGLE FORECAST: {horizon}")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/forecast/{horizon}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Forecast retrieved successfully")
            
            # Display prediction
            print(f"\nModel: {data['model_name']}")
            print(f"Current Price: ${data['current_price']:.2f}")
            print(f"Prediction: ${data['prediction']:.2f}")
            print(f"Change: ${data['predicted_change']:.2f} ({data['predicted_change_pct']:.1f}%)")
            print(f"MAE: {data['confidence_metrics']['mae']:.2f}")
            print(f"R²: {data['confidence_metrics']['r2']:.3f}")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            if response.text:
                print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_all_forecasts():
    """Test all forecasts endpoint"""
    print("\n" + "="*60)
    print("TESTING ALL FORECASTS")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/forecast/all")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Retrieved {len(data)} forecasts")
            
            # Create comparison table
            table_data = []
            for forecast in data:
                table_data.append([
                    forecast['horizon'],
                    f"${forecast['current_price']:.2f}",
                    f"${forecast['prediction']:.2f}",
                    f"${forecast['predicted_change']:.2f}",
                    f"{forecast['predicted_change_pct']:.1f}%",
                    f"{forecast['confidence_metrics']['mae']:.2f}"
                ])
            
            headers = ["Horizon", "Current", "Prediction", "Change", "Change %", "MAE"]
            print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_model_comparison(horizon="1w"):
    """Test model comparison endpoint"""
    print(f"\n" + "="*60)
    print(f"TESTING MODEL COMPARISON: {horizon}")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/compare/{horizon}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Comparison retrieved successfully")
            
            print(f"\nCurrent Price: ${data['current_price']:.2f}")
            print(f"Boosted Tree: ${data['boosted_tree_prediction']:.2f}")
            print(f"Linear Baseline: ${data['linear_baseline_prediction']:.2f}")
            print(f"Difference: ${data['difference']:.2f}")
            
            # Determine which is more bullish
            if data['boosted_tree_prediction'] > data['linear_baseline_prediction']:
                print("→ Boosted Tree is more bullish")
            else:
                print("→ Linear model is more bullish")
            return True
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TESTING HEALTH CHECK")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {data['status']}")
            print(f"Models available: {data.get('models_available', 'N/A')}")
            return data['status'] == 'healthy'
        else:
            print(f"✗ Failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("V3 MODEL API TEST SUITE")
    print("="*80)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("\n⚠️  API may not be running. Start it with:")
            print("   cd forecast && uvicorn main:app --reload")
            return
    except:
        print("\n⚠️  Cannot connect to API. Start it with:")
        print("   cd forecast && uvicorn main:app --reload")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Model Info", test_model_info),
        ("Single Forecast (1w)", lambda: test_single_forecast("1w")),
        ("All Forecasts", test_all_forecasts),
        ("Model Comparison", lambda: test_model_comparison("1w"))
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, "✓ PASS" if success else "✗ FAIL"))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        print(f"{test_name:.<30} {result}")
    
    passed = sum(1 for _, r in results if "PASS" in r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! V3 models are ready for dashboard deployment!")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
