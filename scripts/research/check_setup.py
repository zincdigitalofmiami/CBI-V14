#!/usr/bin/env python3
"""
Check Deep Research Setup
Verifies all components are configured correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def check_keychain_key():
    """Check if OpenAI API key is in Keychain."""
    try:
        from src.utils.keychain_manager import get_api_key
        key = get_api_key('OPENAI_API_KEY')
        if key:
            print("✅ OpenAI API key found in Keychain")
            print(f"   Key starts with: {key[:7]}...")
            return True
        else:
            print("❌ OpenAI API key NOT found in Keychain")
            print()
            print("   To fix, run:")
            print("   security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w 'sk-...' -U")
            return False
    except Exception as e:
        print(f"❌ Error checking Keychain: {e}")
        return False

def check_imports():
    """Check if required modules can be imported."""
    try:
        from src.utils.deep_research import DeepResearcher
        print("✅ DeepResearcher class can be imported")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_scripts():
    """Check if research scripts exist and are executable."""
    scripts = [
        'research_market_regimes.py',
        'research_feature_engineering.py',
        'research_economic_impact.py',
        'batch_research_cbi_v14.py',
        'test_deep_research.py',
    ]
    
    script_dir = os.path.dirname(__file__)
    all_exist = True
    
    for script in scripts:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            if os.access(script_path, os.X_OK):
                print(f"✅ {script} exists and is executable")
            else:
                print(f"⚠️  {script} exists but is not executable")
                all_exist = False
        else:
            print(f"❌ {script} not found")
            all_exist = False
    
    return all_exist

def check_results_dir():
    """Check if results directory exists."""
    results_dir = os.path.join(os.path.dirname(__file__), '../../results/research')
    if os.path.exists(results_dir):
        print(f"✅ Results directory exists: {results_dir}")
        return True
    else:
        print(f"⚠️  Results directory not found: {results_dir}")
        print("   Creating it...")
        os.makedirs(results_dir, exist_ok=True)
        print("   ✅ Created")
        return True

def check_openai_sdk():
    """Check if OpenAI SDK is installed."""
    try:
        import openai
        print(f"✅ OpenAI SDK installed (version: {openai.__version__})")
        return True
    except ImportError:
        print("❌ OpenAI SDK not installed")
        print()
        print("   To fix, run:")
        print("   pip install openai")
        return False

def main():
    """Run all checks."""
    print("="*80)
    print("DEEP RESEARCH SETUP CHECK")
    print("="*80)
    print()
    
    checks = {
        "OpenAI SDK": check_openai_sdk,
        "Keychain API Key": check_keychain_key,
        "DeepResearcher Import": check_imports,
        "Research Scripts": check_scripts,
        "Results Directory": check_results_dir,
    }
    
    results = {}
    for name, check_func in checks.items():
        print(f"\n{name}:")
        results[name] = check_func()
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("✅ All checks passed! Deep Research is ready to use.")
        print()
        print("Next steps:")
        print("  python3 scripts/research/test_deep_research.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        failed = [name for name, passed in results.items() if not passed]
        print(f"Failed checks: {', '.join(failed)}")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())



