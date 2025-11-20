#!/usr/bin/env python3
"""
Test Deep Research Setup
Quick test to verify OpenAI Deep Research is configured correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.deep_research import DeepResearcher


def test_basic_research():
    """Test basic deep research functionality."""
    print("="*80)
    print("TESTING DEEP RESEARCH SETUP")
    print("="*80)
    print()
    
    try:
        # Initialize researcher
        print("1. Initializing DeepResearcher...")
        researcher = DeepResearcher(model="o4-mini-deep-research")
        print("   ✅ Initialized successfully")
        print()
        
        # Test a simple research query
        print("2. Testing basic research query...")
        print("   Query: 'What are the key factors affecting agricultural futures prices?'")
        print("   (This is a quick test - will use minimal tool calls)")
        print()
        
        response = researcher.research(
            query="What are the top 3 key factors affecting agricultural futures prices? Provide brief summary with citations.",
            max_tool_calls=5,  # Minimal for testing
            use_code_interpreter=False,  # Skip code interpreter for speed
        )
        
        print("   ✅ Research completed successfully")
        print()
        print("="*80)
        print("RESEARCH OUTPUT (First 500 chars):")
        print("="*80)
        print(response.output_text[:500] + "..." if len(response.output_text) > 500 else response.output_text)
        print()
        print("="*80)
        print("✅ DEEP RESEARCH IS WORKING!")
        print("="*80)
        print()
        print("Next steps:")
        print("  - Run: python3 scripts/research/research_market_regimes.py --asset ZL")
        print("  - Run: python3 scripts/research/research_feature_engineering.py --asset ZL")
        print("  - Run: python3 scripts/research/research_economic_impact.py 'Fed rate changes' --asset ZL")
        
        return True
        
    except RuntimeError as e:
        if "OPENAI_API_KEY" in str(e):
            print("   ❌ OpenAI API key not found in Keychain")
            print()
            print("   To fix, run:")
            print("   security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w 'sk-...' -U")
            return False
        else:
            raise
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
        print("   Check:")
        print("   - OpenAI API key is valid")
        print("   - You have OpenAI Pro plan access")
        print("   - Internet connection is working")
        return False


if __name__ == "__main__":
    success = test_basic_research()
    sys.exit(0 if success else 1)

