#!/usr/bin/env python3
"""
Verify Cursor Gemini and OpenAI API Configuration
Comprehensive verification script
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"
STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"

def check_keychain(service: str) -> bool:
    """Check if key exists in Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", "default", "-s", f"cbi-v14.{service}", "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False

def verify_gemini():
    """Verify Gemini configuration."""
    print("🔍 Verifying Gemini...")
    
    if not SETTINGS_FILE.exists():
        print("   ❌ Settings file not found")
        return False
    
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    
    # Check API key
    gemini_key = settings.get("geminicodeassist.apiKey")
    if not gemini_key:
        print("   ❌ Gemini API key NOT SET in settings.json")
        return False
    
    if len(gemini_key) < 20:
        print("   ⚠️  Gemini API key seems too short")
        return False
    
    print(f"   ✅ API Key: {gemini_key[:20]}...")
    
    # Check project setting (should NOT exist)
    if "geminicodeassist.project" in settings:
        print(f"   ⚠️  WARNING: geminicodeassist.project is set!")
        print(f"      This may cause license errors")
        print(f"      Value: {settings['geminicodeassist.project']}")
        return False
    else:
        print("   ✅ No project setting (prevents license errors)")
    
    # Check Keychain
    if check_keychain("GEMINI_API_KEY"):
        print("   ✅ Key in Keychain")
    else:
        print("   ⚠️  Key not in Keychain (but OK if in settings)")
    
    return True

def verify_openai():
    """Verify OpenAI configuration."""
    print("🔍 Verifying OpenAI...")
    
    if not STATE_DB.exists():
        print("   ❌ Cursor database not found")
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        # Check OpenAI key
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("   ❌ OpenAI key NOT FOUND in Cursor database")
            conn.close()
            return False
        
        openai_key = result[0]
        if not openai_key or len(openai_key) < 20:
            print("   ❌ OpenAI key is invalid or too short")
            conn.close()
            return False
        
        if not openai_key.startswith("sk-"):
            print("   ⚠️  OpenAI key doesn't start with 'sk-' (may be invalid)")
            conn.close()
            return False
        
        print(f"   ✅ API Key: {openai_key[:20]}...")
        print(f"   ✅ Key length: {len(openai_key)} characters")
        
        # Check Keychain
        if check_keychain("OPENAI_API_KEY"):
            print("   ✅ Key in Keychain")
        else:
            print("   ⚠️  Key not in Keychain (but OK if in database)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return False

def main():
    """Main verification function."""
    print("="*80)
    print("VERIFYING CURSOR GEMINI & OPENAI CONFIGURATION")
    print("="*80)
    print()
    
    gemini_ok = verify_gemini()
    print()
    openai_ok = verify_openai()
    print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    if gemini_ok and openai_ok:
        print("✅ BOTH GEMINI AND OPENAI ARE PROPERLY CONFIGURED!")
        print()
        print("🔄 NEXT STEP: Restart Cursor")
        print("   Cmd + Q → Quit → Reopen Cursor")
        return 0
    elif gemini_ok:
        print("✅ GEMINI: OK")
        print("❌ OPENAI: NEEDS FIXING")
        return 1
    elif openai_ok:
        print("✅ OPENAI: OK")
        print("❌ GEMINI: NEEDS FIXING")
        return 1
    else:
        print("❌ BOTH NEED FIXING")
        print()
        print("Run: python3 scripts/setup/fix_cursor_apis.py")
        return 1

if __name__ == "__main__":
    exit(main())



