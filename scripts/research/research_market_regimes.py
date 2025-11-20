#!/usr/bin/env python3
"""
Research Market Regimes for CBI-V14
Uses OpenAI Deep Research to analyze market regimes and transitions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.deep_research import DeepResearcher
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="Research market regimes")
    parser.add_argument("--asset", default="ZL", help="Asset symbol (default: ZL)")
    parser.add_argument("--date-range", default="2000-2025", help="Date range (default: 2000-2025)")
    parser.add_argument("--focus", help="Focus area (e.g., 'Fed policy', 'trade wars')")
    parser.add_argument("--model", default="o4-mini-deep-research",
                       choices=["o3-deep-research", "o4-mini-deep-research"],
                       help="Model to use")
    parser.add_argument("--output", help="Output file path (JSON)")
    
    args = parser.parse_args()
    
    print("="*80)
    print(f"RESEARCHING MARKET REGIMES: {args.asset}")
    print(f"Date Range: {args.date_range}")
    if args.focus:
        print(f"Focus: {args.focus}")
    print("="*80)
    print()
    
    researcher = DeepResearcher(model=args.model)
    
    try:
        response = researcher.research_market_regimes(
            asset=args.asset,
            date_range=args.date_range,
            focus=args.focus,
        )
        
        print("\n" + "="*80)
        print("RESEARCH RESULTS")
        print("="*80)
        print(response.output_text)
        print("\n" + "="*80)
        
        if args.output:
            result = {
                "asset": args.asset,
                "date_range": args.date_range,
                "focus": args.focus,
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


