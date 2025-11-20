#!/usr/bin/env python3
"""
Fix Cursor Gemini and OpenAI API Configuration
Comprehensive fix for both chat systems
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"
STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"

def get_keychain_key(service: str) -> str:
    """Get API key from Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", "default", "-s", f"cbi-v14.{service}", "-w"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def fix_gemini_settings():
    """Fix Gemini API settings."""
    print("🔧 Fixing Gemini settings...")
    
    # Get key from Keychain
    gemini_key = get_keychain_key("GEMINI_API_KEY")
    if not gemini_key:
        print("   ⚠️  Gemini key not in Keychain, using from settings")
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        gemini_key = settings.get("geminicodeassist.apiKey")
    
    if not gemini_key:
        print("   ❌ No Gemini key found!")
        return False
    
    # Update settings
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    
    settings["geminicodeassist.apiKey"] = gemini_key
    settings["geminicodeassist.agentDebugMode"] = True
    settings["geminicodeassist.codeGenerationPaneViewEnabled"] = True
    settings["geminicodeassist.inlineSuggestions.nextEditPredictions"] = True
    settings["geminicodeassist.inlineSuggestions.suggestionSpeed"] = "Slow"
    settings["geminicodeassist.verboseLogging"] = True
    
    # Remove project setting (causes license issues)
    if "geminicodeassist.project" in settings:
        del settings["geminicodeassist.project"]
        print("   ✅ Removed geminicodeassist.project (fixes license error)")
    
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
    
    print(f"   ✅ Gemini API key updated: {gemini_key[:20]}...")
    return True

def fix_openai_settings():
    """Fix OpenAI API settings."""
    print("🔧 Fixing OpenAI settings...")
    
    # Get key from Keychain
    openai_key = get_keychain_key("OPENAI_API_KEY")
    if not openai_key:
        print("   ⚠️  OpenAI key not in Keychain, checking Cursor database...")
        # Try to get from Cursor's internal database
        try:
            conn = sqlite3.connect(STATE_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1")
            result = cursor.fetchone()
            if result:
                openai_key = result[0]
                print("   ✅ Found OpenAI key in Cursor database")
            conn.close()
        except Exception as e:
            print(f"   ⚠️  Could not read Cursor database: {e}")
    
    if not openai_key:
        print("   ❌ No OpenAI key found!")
        return False
    
    # Store in Keychain if not already there
    if not get_keychain_key("OPENAI_API_KEY"):
        subprocess.run([
            "security", "add-generic-password",
            "-a", "default",
            "-s", "cbi-v14.OPENAI_API_KEY",
            "-w", openai_key,
            "-U"
        ], check=False)
        print("   ✅ Stored OpenAI key in Keychain")
    
    # Cursor uses internal database for OpenAI, but we can verify it exists
    print(f"   ✅ OpenAI key verified: {openai_key[:20]}...")
    return True

def verify_settings():
    """Verify all settings are correct."""
    print("\n🔍 Verifying settings...")
    
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    
    # Check Gemini
    gemini_key = settings.get("geminicodeassist.apiKey")
    if gemini_key:
        print(f"   ✅ Gemini: {gemini_key[:20]}...")
    else:
        print("   ❌ Gemini: NOT SET")
    
    # Check OpenAI (in database)
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1")
        result = cursor.fetchone()
        if result:
            openai_key = result[0]
            print(f"   ✅ OpenAI: {openai_key[:20]}...")
        else:
            print("   ❌ OpenAI: NOT SET in database")
        conn.close()
    except Exception as e:
        print(f"   ⚠️  Could not verify OpenAI: {e}")
    
    # Check Keychain
    gemini_kc = get_keychain_key("GEMINI_API_KEY")
    openai_kc = get_keychain_key("OPENAI_API_KEY")
    
    print(f"\n📦 Keychain:")
    print(f"   Gemini: {'✅' if gemini_kc else '❌'}")
    print(f"   OpenAI: {'✅' if openai_kc else '❌'}")

def main():
    """Main fix function."""
    print("="*80)
    print("FIXING CURSOR GEMINI & OPENAI CHAT CONFIGURATION")
    print("="*80)
    print()
    
    # Backup settings
    backup_file = f"{SETTINGS_FILE}.backup"
    if SETTINGS_FILE.exists():
        import shutil
        shutil.copy(SETTINGS_FILE, backup_file)
        print(f"✅ Backup created: {backup_file}")
        print()
    
    # Fix Gemini
    gemini_ok = fix_gemini_settings()
    print()
    
    # Fix OpenAI
    openai_ok = fix_openai_settings()
    print()
    
    # Verify
    verify_settings()
    print()
    
    print("="*80)
    if gemini_ok and openai_ok:
        print("✅ BOTH GEMINI AND OPENAI FIXED!")
    elif gemini_ok:
        print("✅ GEMINI FIXED (OpenAI needs attention)")
    elif openai_ok:
        print("✅ OPENAI FIXED (Gemini needs attention)")
    else:
        print("⚠️  SOME ISSUES REMAIN - Check output above")
    
    print("="*80)
    print()
    print("🔄 RESTART CURSOR NOW:")
    print("   Cmd + Q → Quit → Reopen Cursor")
    print()

if __name__ == "__main__":
    main()


