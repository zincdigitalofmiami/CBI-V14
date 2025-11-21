#!/usr/bin/env python3
"""
Research Economic Impact on Asset Prices for CBI-V14
Uses OpenAI Deep Research to analyze economic factors affecting futures prices
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.deep_research import DeepResearcher
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Research economic impact on asset prices")
    parser.add_argument("topic", help="Economic topic (e.g., 'Fed rate changes', 'trade wars', 'biofuel policy')")
    parser.add_argument("--asset", default="ZL", help="Asset symbol (default: ZL)")
    parser.add_argument("--date-range", default="2000-2025", help="Date range (default: 2000-2025)")
    parser.add_argument("--model", default="o4-mini-deep-research",
                       choices=["o3-deep-research", "o4-mini-deep-research"],
                       help="Model to use")
    parser.add_argument("--output", help="Output file path (JSON)")
    
    args = parser.parse_args()
    
    print("="*80)
    print(f"RESEARCHING ECONOMIC IMPACT: {args.topic}")
    print(f"Asset: {args.asset}")
    print(f"Date Range: {args.date_range}")
    print("="*80)
    print()
    
    researcher = DeepResearcher(model=args.model)
    
    try:
        response = researcher.research_economic_impact(
            topic=args.topic,
            asset=args.asset,
            date_range=args.date_range,
        )
        
        print("\n" + "="*80)
        print("RESEARCH RESULTS")
        print("="*80)
        print(response.output_text)
        print("\n" + "="*80)
        
        if args.output:
            result = {
                "topic": args.topic,
                "asset": args.asset,
                "date_range": args.date_range,
                "model": args.model,
                "output": response.output_text,
                "response_id": getattr(response, 'id', None),
            }
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✅ Results saved to: {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()



