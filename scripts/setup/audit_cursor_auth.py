#!/usr/bin/env python3
"""
Comprehensive Cursor Authentication Audit
Identifies why "Bad User API key" error occurs
"""

import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
import sys

SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"
STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
CURSOR_DIR = Path.home() / "Library/Application Support/Cursor"

def audit_cursor_auth():
    """Comprehensive audit of Cursor authentication."""
    
    print("="*80)
    print("CURSOR AUTHENTICATION COMPREHENSIVE AUDIT")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues = []
    warnings = []
    info = []
    
    # 1. Check Cursor directory
    print("1. CURSOR INSTALLATION")
    print("-" * 60)
    if CURSOR_DIR.exists():
        info.append("Cursor directory exists")
        print("   ✅ Cursor directory found")
    else:
        issues.append("Cursor directory not found")
        print("   ❌ Cursor directory NOT FOUND")
    print()
    
    # 2. Check settings file
    print("2. SETTINGS FILE")
    print("-" * 60)
    if SETTINGS_FILE.exists():
        info.append("Settings file exists")
        print("   ✅ Settings file found")
        
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
            
            # Check for required keys
            gemini_key = settings.get("geminicodeassist.apiKey")
            if gemini_key:
                info.append(f"Gemini API key configured: {gemini_key[:20]}...")
                print(f"   ✅ Gemini API key: {gemini_key[:20]}...")
            else:
                warnings.append("Gemini API key not in settings")
                print("   ⚠️  Gemini API key NOT in settings")
            
        except json.JSONDecodeError as e:
            issues.append(f"Settings file has invalid JSON: {e}")
            print(f"   ❌ Invalid JSON: {e}")
    else:
        issues.append("Settings file not found")
        print("   ❌ Settings file NOT FOUND")
    print()
    
    # 3. Check database
    print("3. CURSOR DATABASE")
    print("-" * 60)
    if STATE_DB.exists():
        info.append("Database exists")
        print(f"   ✅ Database found: {STATE_DB.stat().st_size / 1024:.1f} KB")
        
        try:
            conn = sqlite3.connect(STATE_DB)
            cursor = conn.cursor()
            
            # Check access token
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/accessToken' LIMIT 1")
            token_result = cursor.fetchone()
            
            if token_result and token_result[0] and len(token_result[0]) > 10:
                token = token_result[0]
                info.append(f"Access token found: {len(token)} chars")
                print(f"   ✅ Access token: {len(token)} characters")
                
                # Check if token looks valid
                if token.count('.') == 2:
                    print("   ✅ Token format: JWT (valid format)")
                else:
                    warnings.append("Access token format unusual (not JWT)")
                    print("   ⚠️  Token format: Not JWT (unusual)")
            else:
                issues.append("Access token missing or invalid")
                print("   ❌ Access token: MISSING or INVALID")
            
            # Check refresh token
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/refreshToken' LIMIT 1")
            refresh_result = cursor.fetchone()
            
            if refresh_result and refresh_result[0] and len(refresh_result[0]) > 10:
                info.append("Refresh token found")
                print(f"   ✅ Refresh token: {len(refresh_result[0])} characters")
            else:
                warnings.append("Refresh token missing")
                print("   ⚠️  Refresh token: MISSING")
            
            # Check subscription
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeMembershipType' LIMIT 1")
            membership = cursor.fetchone()
            if membership:
                print(f"   ✅ Membership: {membership[0]}")
                info.append(f"Membership: {membership[0]}")
            else:
                warnings.append("Membership type not found")
                print("   ⚠️  Membership: NOT FOUND")
            
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeSubscriptionStatus' LIMIT 1")
            status = cursor.fetchone()
            if status:
                print(f"   ✅ Status: {status[0]}")
                info.append(f"Status: {status[0]}")
            else:
                warnings.append("Subscription status not found")
                print("   ⚠️  Status: NOT FOUND")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"Database error: {e}")
            print(f"   ❌ Database error: {e}")
    else:
        issues.append("Database not found")
        print("   ❌ Database NOT FOUND")
    print()
    
    # 4. Test API keys
    print("4. API KEY FUNCTIONALITY")
    print("-" * 60)
    
    # Gemini
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            gemini_key = settings.get("geminicodeassist.apiKey")
            if gemini_key:
                try:
                    result = subprocess.run([
                        "curl", "-s", "--max-time", "5",
                        f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        if "error" not in result.stdout.lower():
                            print("   ✅ Gemini API key: WORKING")
                            info.append("Gemini API key works")
                        else:
                            print("   ❌ Gemini API key: API ERROR")
                            issues.append("Gemini API key returns error")
                    else:
                        print("   ❌ Gemini API key: REQUEST FAILED")
                        issues.append("Gemini API key request failed")
                except Exception as e:
                    print(f"   ⚠️  Gemini API key: Could not test ({e})")
                    warnings.append(f"Could not test Gemini key: {e}")
    
    # OpenAI
    if STATE_DB.exists():
        try:
            conn = sqlite3.connect(STATE_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                openai_key = result[0]
                try:
                    test_result = subprocess.run([
                        "curl", "-s", "--max-time", "5",
                        "https://api.openai.com/v1/models",
                        "-H", f"Authorization: Bearer {openai_key}"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if test_result.returncode == 0:
                        if "error" not in test_result.stdout.lower():
                            print("   ✅ OpenAI API key: WORKING")
                            info.append("OpenAI API key works")
                        else:
                            print("   ❌ OpenAI API key: API ERROR")
                            issues.append("OpenAI API key returns error")
                    else:
                        print("   ❌ OpenAI API key: REQUEST FAILED")
                        issues.append("OpenAI API key request failed")
                except Exception as e:
                    print(f"   ⚠️  OpenAI API key: Could not test ({e})")
                    warnings.append(f"Could not test OpenAI key: {e}")
            else:
                warnings.append("OpenAI key not in database")
                print("   ⚠️  OpenAI API key: NOT FOUND in database")
        except Exception as e:
            warnings.append(f"Could not check OpenAI key: {e}")
    print()
    
    # 5. Summary
    print("="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    print()
    
    if issues:
        print("🔴 CRITICAL ISSUES:")
        for issue in issues:
            print(f"   ❌ {issue}")
        print()
    
    if warnings:
        print("🟡 WARNINGS:")
        for warning in warnings:
            print(f"   ⚠️  {warning}")
        print()
    
    if info:
        print("✅ INFORMATION:")
        for item in info[:10]:  # Limit output
            print(f"   ✅ {item}")
        print()
    
    # 6. Recommendations
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()
    
    if "Access token missing or invalid" in str(issues):
        print("🔧 FIX: Re-authenticate with Cursor")
        print("   1. Cursor → Settings → Account")
        print("   2. Sign out and sign back in")
        print("   3. This will refresh access token")
        print()
    
    if "Access token format unusual" in str(warnings):
        print("🔧 FIX: Token may be expired")
        print("   1. Sign out of Cursor")
        print("   2. Sign back in")
        print("   3. This will generate new tokens")
        print()
    
    if not issues and not warnings:
        print("✅ All checks passed!")
        print("   If you're still getting 'Bad User API key' error:")
        print("   1. Restart Cursor (Cmd + Q)")
        print("   2. Check Cursor → Settings → Account")
        print("   3. Verify subscription is active")
        print()
    
    return len(issues), len(warnings)

if __name__ == "__main__":
    issues, warnings = audit_cursor_auth()
    sys.exit(1 if issues > 0 else 0)

