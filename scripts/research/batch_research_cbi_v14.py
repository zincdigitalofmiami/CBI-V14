#!/usr/bin/env python3
"""
Batch Research for CBI-V14
Run multiple research tasks in sequence for comprehensive analysis
"""

import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.deep_research import DeepResearcher


def run_batch_research():
    """Run a batch of research tasks for CBI-V14."""
    
    print("="*80)
    print("CBI-V14 BATCH RESEARCH")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    researcher = DeepResearcher(model="o4-mini-deep-research")
    results_dir = "results/research"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    
    # Research Task 1: Market Regimes
    print("1. Researching Market Regimes...")
    try:
        response = researcher.research_market_regimes(
            asset="ZL",
            date_range="2000-2025",
            focus="Fed policy and trade wars",
        )
        output_file = f"{results_dir}/batch_regimes_{timestamp}.json"
        result = {
            "task": "Market Regimes",
            "asset": "ZL",
            "date_range": "2000-2025",
            "output": response.output_text,
            "response_id": getattr(response, 'id', None),
            "timestamp": timestamp,
        }
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        results.append(result)
        print(f"   ✅ Saved to: {output_file}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Research Task 2: Feature Engineering
    print("2. Researching Feature Engineering Best Practices...")
    try:
        response = researcher.research_feature_engineering(
            asset="ZL",
            indicator_type="momentum and volatility",
        )
        output_file = f"{results_dir}/batch_features_{timestamp}.json"
        result = {
            "task": "Feature Engineering",
            "asset": "ZL",
            "indicator_type": "momentum and volatility",
            "output": response.output_text,
            "response_id": getattr(response, 'id', None),
            "timestamp": timestamp,
        }
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        results.append(result)
        print(f"   ✅ Saved to: {output_file}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Research Task 3: Economic Impact - Fed Policy
    print("3. Researching Fed Policy Impact...")
    try:
        response = researcher.research_economic_impact(
            topic="Federal Reserve interest rate changes",
            asset="ZL",
            date_range="2000-2025",
        )
        output_file = f"{results_dir}/batch_fed_impact_{timestamp}.json"
        result = {
            "task": "Economic Impact - Fed Policy",
            "topic": "Federal Reserve interest rate changes",
            "asset": "ZL",
            "output": response.output_text,
            "response_id": getattr(response, 'id', None),
            "timestamp": timestamp,
        }
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        results.append(result)
        print(f"   ✅ Saved to: {output_file}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Research Task 4: Economic Impact - Trade Wars
    print("4. Researching Trade War Impact...")
    try:
        response = researcher.research_economic_impact(
            topic="US-China trade wars",
            asset="ZL",
            date_range="2018-2025",
        )
        output_file = f"{results_dir}/batch_trade_war_{timestamp}.json"
        result = {
            "task": "Economic Impact - Trade Wars",
            "topic": "US-China trade wars",
            "asset": "ZL",
            "output": response.output_text,
            "response_id": getattr(response, 'id', None),
            "timestamp": timestamp,
        }
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        results.append(result)
        print(f"   ✅ Saved to: {output_file}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Summary
    print("="*80)
    print("BATCH RESEARCH COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    print(f"✅ Completed {len(results)} research tasks")
    print(f"📁 Results saved to: {results_dir}/")
    print()
    print("Next steps:")
    print("  - Review research results")
    print("  - Extract key findings")
    print("  - Integrate into feature engineering")
    print("  - Update regime detection logic")
    print()
    
    # Save summary
    summary_file = f"{results_dir}/batch_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "tasks_completed": len(results),
            "results": results,
        }, f, indent=2)
    print(f"📋 Summary saved to: {summary_file}")


if __name__ == "__main__":
    run_batch_research()

