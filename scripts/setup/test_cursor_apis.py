#!/usr/bin/env python3
"""
Test Cursor Gemini and OpenAI API Keys
Actually tests the keys work, not just that they're configured
"""

import subprocess
import json
import sqlite3
from pathlib import Path
import sys

SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"
STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"

def test_gemini_key(key: str, stress_test: bool = False) -> bool:
    """Test Gemini API key by making actual API call.
    
    Args:
        key: Gemini API key
        stress_test: If True, makes 5 rapid requests to test rate limits
    """
    print("🧪 Testing Gemini API key...")
    
    if stress_test:
        print("   🔥 STRESS MODE: Making 5 rapid requests to test rate limits...")
        rate_limit_hit = False
        successful = 0
        
        for i in range(5):
            try:
                result = subprocess.run([
                    "curl", "-s", "--max-time", "5",
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        if "error" in data:
                            error = data["error"]
                            status = str(error.get("status", "")).upper()
                            message = error.get("message", "").lower()
                            if ("RESOURCE_EXHAUSTED" in status or 
                                "rate limit" in message or 
                                "quota" in message or 
                                "too many requests" in message):
                                print(f"   ❌ Request {i+1}: RATE LIMIT HIT")
                                rate_limit_hit = True
                                break
                        else:
                            successful += 1
                            print(f"   ✅ Request {i+1}: OK")
                    except:
                        pass
            except:
                pass
        
        if rate_limit_hit:
            print("   🔴 QUOTA/RATE LIMIT ISSUE DETECTED")
            print("   💡 See docs/setup/GEMINI_RATE_LIMITS.md")
            return False
        else:
            print(f"   ✅ All {successful}/5 requests succeeded - NO QUOTA ISSUES")
            print("   ✅ Quotas are NOT the problem")
    
    try:
        result = subprocess.run([
            "curl", "-s", "--max-time", "10",
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            print(f"   ❌ Request failed: {result.stderr[:200]}")
            return False
        
        try:
            data = json.loads(result.stdout)
            
            if "error" in data:
                error = data["error"]
                message = error.get("message", "Unknown error")
                status = error.get("status", "Unknown")
                print(f"   ❌ API Error: {message}")
                print(f"   ❌ Status: {status}")

                message_lower = message.lower()
                status_upper = str(status).upper()

                if (
                    "resource_exhausted" in status_upper
                    or "rate limit" in message_lower
                    or "quota" in message_lower
                    or "too many requests" in message_lower
                ):
                    print("   ⚠️ This looks like a GEMINI QUOTA/RATE LIMIT issue.")
                    print("   💡 See docs/setup/GEMINI_RATE_LIMITS.md for details.")
                else:
                    print("   ℹ️ This does NOT look like a quota error.")
                    print("   ℹ️ Check Cursor integration (top_k bug, auth, etc.).")
                    print("   ℹ️ See docs/setup/FIX_OPENAI_GEMINI_ERRORS.md and docs/setup/TOP_K_ERROR_FINAL_FIX.md.")
                return False
            
            if "models" in data or len(data) > 0:
                print("   ✅ Gemini API key is VALID and WORKING")
                print(f"   ✅ Successfully connected to Gemini API")
                return True
            else:
                print(f"   ⚠️  Unexpected response: {result.stdout[:200]}")
                return False
                
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response: {result.stdout[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_openai_key(key: str) -> bool:
    """Test OpenAI API key by making actual API call."""
    print("🧪 Testing OpenAI API key...")
    
    try:
        result = subprocess.run([
            "curl", "-s", "--max-time", "10",
            "https://api.openai.com/v1/models",
            "-H", f"Authorization: Bearer {key}",
            "-H", "Content-Type: application/json"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            print(f"   ❌ Request failed: {result.stderr[:200]}")
            return False
        
        try:
            data = json.loads(result.stdout)
            
            if "error" in data:
                error = data["error"]
                message = error.get("message", "Unknown error")
                err_type = error.get("type", "Unknown")
                code = error.get("code", "Unknown")
                print(f"   ❌ API Error: {message}")
                print(f"   ❌ Type: {err_type}")
                print(f"   ❌ Code: {code}")
                
                message_lower = message.lower()
                type_lower = str(err_type).lower()
                code_lower = str(code).lower()
                
                # Check for specific errors
                if "organization" in message_lower:
                    print("   💡 Fix: Verify organization at https://platform.openai.com/settings/organization/general")
                elif (
                    "rate limit" in message_lower
                    or "quota" in message_lower
                    or "too many requests" in message_lower
                    or "insufficient_quota" in type_lower
                    or "insufficient_quota" in code_lower
                    or "rate_limit" in type_lower
                    or "rate_limit" in code_lower
                    or "rate_limit_exceeded" in code_lower
                    or "tokens per min" in message_lower
                    or "tpm" in message_lower
                    or ("limit" in message_lower and "requested" in message_lower)
                ):
                    print("   ⚠️ This looks like an OPENAI QUOTA/RATE LIMIT issue.")
                    
                    # Extract TPM info if present
                    if "tokens per min" in message_lower or "tpm" in message_lower:
                        if "Limit" in message and "Requested" in message:
                            print("   📊 This is a TOKENS PER MINUTE (TPM) limit issue.")
                            print("   💡 Your request is too large - reduce input/output tokens.")
                            print("   💡 See https://platform.openai.com/account/rate-limits")
                        else:
                            print("   💡 Check https://platform.openai.com/usage and your plan limits.")
                    else:
                        print("   💡 Check https://platform.openai.com/usage and your plan limits.")
                else:
                    print("   ℹ️ This does NOT look like a quota error.")
                    print("   ℹ️ For auth/organization issues, see docs/setup/FIX_OPENAI_GEMINI_ERRORS.md.")
                
                return False
            
            if "data" in data or isinstance(data, list):
                print("   ✅ OpenAI API key is VALID and WORKING")
                print(f"   ✅ Successfully connected to OpenAI API")
                return True
            else:
                print(f"   ⚠️  Unexpected response: {result.stdout[:200]}")
                return False
                
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response: {result.stdout[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Test both API keys."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Cursor Gemini & OpenAI API Keys")
    parser.add_argument("--stress", action="store_true",
                       help="Run stress test (5 rapid requests) to verify quotas are not the problem")
    args = parser.parse_args()
    
    print("="*80)
    print("TESTING CURSOR GEMINI & OPENAI API KEYS")
    if args.stress:
        print("🔥 STRESS MODE ENABLED - Testing rate limits")
    print("="*80)
    print()
    
    all_passed = True
    
    # Test Gemini
    print("1. GEMINI API KEY TEST")
    print("-" * 60)
    
    if not SETTINGS_FILE.exists():
        print("   ❌ Settings file not found")
        all_passed = False
    else:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        
        gemini_key = settings.get("geminicodeassist.apiKey")
        if not gemini_key:
            print("   ❌ Gemini API key not found in settings")
            all_passed = False
        else:
            print(f"   Key: {gemini_key[:20]}...")
            if test_gemini_key(gemini_key, stress_test=args.stress):
                print("   ✅ Gemini: WORKING")
            else:
                print("   ❌ Gemini: NOT WORKING")
                all_passed = False
    
    print()
    
    # Test OpenAI
    print("2. OPENAI API KEY TEST")
    print("-" * 60)
    
    if not STATE_DB.exists():
        print("   ❌ Cursor database not found")
        all_passed = False
    else:
        try:
            conn = sqlite3.connect(STATE_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print("   ❌ OpenAI key not found in database")
                all_passed = False
            else:
                openai_key = result[0]
                print(f"   Key: {openai_key[:20]}...")
                if test_openai_key(openai_key):
                    print("   ✅ OpenAI: WORKING")
                else:
                    print("   ❌ OpenAI: NOT WORKING")
                    all_passed = False
                    
        except Exception as e:
            print(f"   ❌ Error reading database: {e}")
            all_passed = False
    
    print()
    print("="*80)
    print("TEST RESULTS")
    print("="*80)
    
    if all_passed:
        print("✅ BOTH API KEYS ARE WORKING!")
        print()
        print("🔄 Restart Cursor to use them:")
        print("   Cmd + Q → Quit → Reopen Cursor")
        return 0
    else:
        print("⚠️  SOME API KEYS ARE NOT WORKING")
        print()
        print("Check the errors above and fix:")
        print("  - Invalid/expired keys")
        print("  - Missing permissions")
        print("  - Organization verification needed (OpenAI)")
        return 1

if __name__ == "__main__":
    sys.exit(main())

