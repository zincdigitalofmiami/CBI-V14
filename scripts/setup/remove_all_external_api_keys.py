#!/usr/bin/env python3
"""
Remove All External API Keys from Cursor
Forces Cursor to use its built-in models instead of external APIs
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime

STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"

def backup_files():
    """Backup database and settings before making changes."""
    print("📦 Creating backups...")
    
    if STATE_DB.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_db = STATE_DB.parent / f"state.vscdb.backup_external_apis_{timestamp}"
        shutil.copy(STATE_DB, backup_db)
        print(f"   ✅ Database backup: {backup_db.name}")
    
    if SETTINGS_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_settings = SETTINGS_FILE.parent / f"settings.json.backup_external_apis_{timestamp}"
        shutil.copy(SETTINGS_FILE, backup_settings)
        print(f"   ✅ Settings backup: {backup_settings.name}")
    
    print()

def remove_external_api_keys_from_db():
    """Remove external API keys from Cursor database."""
    print("🔧 Removing external API keys from database...")
    
    if not STATE_DB.exists():
        print("   ⚠️  Database not found")
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        # Keys to remove (external API providers)
        keys_to_remove = [
            'cursorAuth/openAIKey',  # OpenAI
            'cursorAuth/xAIKey',     # xAI (if exists)
            'cursorAuth/xaiKey',     # xAI (alternate)
            'cursorAuth/anthropicKey',  # Anthropic (if exists)
        ]
        
        removed = []
        for key in keys_to_remove:
            cursor.execute("SELECT key FROM ItemTable WHERE key = ? LIMIT 1", (key,))
            if cursor.fetchone():
                cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
                removed.append(key)
                print(f"   ✅ Removed: {key}")
        
        # Also search for any keys containing "xai" or "x.ai"
        cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%xai%' OR key LIKE '%x.ai%'")
        xai_keys = cursor.fetchall()
        for (key,) in xai_keys:
            if key not in removed:
                cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
                print(f"   ✅ Removed: {key}")
        
        conn.commit()
        conn.close()
        
        if removed or xai_keys:
            print("   ✅ External API keys removed from database")
        else:
            print("   ℹ️  No external API keys found in database")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def remove_external_api_keys_from_settings():
    """Remove external API keys from settings.json."""
    print("\n🔧 Checking settings.json...")
    
    if not SETTINGS_FILE.exists():
        print("   ℹ️  Settings file not found")
        return True
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        
        # Keys to check/remove
        keys_to_check = [
            'cursor.openAI.apiKey',
            'cursor.xAI.apiKey',
            'cursor.xai.apiKey',
            'cursor.anthropic.apiKey',
        ]
        
        removed = []
        for key in keys_to_check:
            if key in settings:
                del settings[key]
                removed.append(key)
                print(f"   ✅ Removed from settings: {key}")
        
        # Also check for any xAI-related settings
        xai_settings = [k for k in settings.keys() if 'xai' in k.lower() or 'x.ai' in k.lower()]
        for key in xai_settings:
            if key not in removed:
                del settings[key]
                print(f"   ✅ Removed from settings: {key}")
        
        if removed or xai_settings:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            print("   ✅ Settings updated")
        else:
            print("   ℹ️  No external API keys found in settings")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Error reading settings: {e}")
        return False

def verify_cursor_subscription():
    """Verify Cursor subscription is active."""
    print("\n🔍 Verifying Cursor subscription...")
    
    if not STATE_DB.exists():
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeMembershipType' LIMIT 1")
        membership = cursor.fetchone()
        if membership:
            print(f"   ✅ Membership: {membership[0]}")
        
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeSubscriptionStatus' LIMIT 1")
        status = cursor.fetchone()
        if status:
            print(f"   ✅ Status: {status[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}")
        return False

def main():
    """Main function."""
    print("="*80)
    print("REMOVE ALL EXTERNAL API KEYS FROM CURSOR")
    print("="*80)
    print()
    print("This will:")
    print("  ✅ Remove OpenAI API keys")
    print("  ✅ Remove xAI API keys")
    print("  ✅ Remove other external API keys")
    print("  ✅ Force Cursor to use built-in models")
    print("  ✅ Keep Codex app working (separate)")
    print()
    
    # Backup
    backup_files()
    
    # Remove from database
    db_success = remove_external_api_keys_from_db()
    
    # Remove from settings
    settings_success = remove_external_api_keys_from_settings()
    
    # Verify subscription
    verify_cursor_subscription()
    
    print()
    print("="*80)
    if db_success and settings_success:
        print("✅ EXTERNAL API KEYS REMOVED!")
        print()
        print("🔄 NEXT STEPS:")
        print("   1. Restart Cursor completely (Cmd + Q)")
        print("   2. Reopen Cursor")
        print("   3. Open Chat/Composer")
        print("   4. Select Cursor's built-in models:")
        print("      - Claude 4.5 Sonnet")
        print("      - Claude 4.5 Sonnet Thinking")
        print("      - GPT-5.1 (Cursor version)")
        print("      - Sonnet 4.5")
        print("      - Composer 1")
        print()
        print("   ⚠️  DO NOT select models that require external API keys")
        print("   ✅ Use only Cursor's built-in models")
        print()
        print("   Codex app: Still works independently ✅")
    else:
        print("⚠️  SOME ISSUES - Check output above")
    print("="*80)
    print()

if __name__ == "__main__":
    main()

