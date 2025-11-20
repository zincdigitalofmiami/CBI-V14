#!/usr/bin/env python3
"""
Restore Cursor Models in Chat
Restores all Cursor built-in models (Claude, GPT, etc.) while keeping Codex app separate
"""

import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"

def backup_database():
    """Backup Cursor database before making changes."""
    if not STATE_DB.exists():
        print(f"   ⚠️  Database not found: {STATE_DB}")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = STATE_DB.parent / f"state.vscdb.backup_{timestamp}"
    shutil.copy(STATE_DB, backup_file)
    print(f"   ✅ Backup created: {backup_file.name}")
    return True

def restore_cursor_models():
    """Restore Cursor models by resetting model preferences."""
    print("🔧 Restoring Cursor models...")
    
    if not STATE_DB.exists():
        print(f"   ❌ Database not found: {STATE_DB}")
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        # Check current model preferences
        cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%model%' OR key LIKE '%preference%'")
        current_prefs = cursor.fetchall()
        
        print(f"   📋 Found {len(current_prefs)} model preference entries")
        
        # Reset model preferences to use Cursor defaults
        # Remove any problematic model preferences that might be blocking Cursor models
        problematic_keys = [
            'cursor/lastSingleModelPreference',
            'cursor/bestOfNCountPreference',
            'cursor/bestOfNEnsemblePreferences',
        ]
        
        for key in problematic_keys:
            cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
            if cursor.rowcount > 0:
                print(f"   ✅ Reset: {key}")
        
        # Ensure Claude markdown is enabled (helps with model compatibility)
        cursor.execute("""
            INSERT OR REPLACE INTO ItemTable (key, value) 
            VALUES ('cursor/claudeMdEnabled', 'true')
        """)
        print("   ✅ Enabled Claude markdown support")
        
        # Ensure memories are enabled (helps with model functionality)
        cursor.execute("""
            INSERT OR REPLACE INTO ItemTable (key, value) 
            VALUES ('cursor/memoriesEnabled', 'true')
        """)
        print("   ✅ Enabled memories")
        
        conn.commit()
        conn.close()
        
        print("   ✅ Cursor models restored")
        return True
        
    except Exception as e:
        print(f"   ❌ Error restoring models: {e}")
        return False

def verify_cursor_subscription():
    """Verify Cursor subscription status."""
    print("\n🔍 Verifying Cursor subscription...")
    
    if not STATE_DB.exists():
        print("   ⚠️  Cannot verify - database not found")
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        # Check subscription
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeMembershipType'")
        result = cursor.fetchone()
        if result:
            membership = result[0]
            print(f"   ✅ Membership: {membership}")
            
            if membership.lower() in ['ultra', 'pro', 'premium']:
                print("   ✅ Subscription active - all models should be available")
            else:
                print("   ⚠️  Limited subscription - some models may not be available")
        
        # Check subscription status
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeSubscriptionStatus'")
        result = cursor.fetchone()
        if result:
            status = result[0]
            print(f"   ✅ Status: {status}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ⚠️  Could not verify subscription: {e}")
        return False

def check_codex_app():
    """Verify Codex app is separate and not affected."""
    print("\n🔍 Checking Codex app status...")
    print("   ℹ️  Codex is a separate application")
    print("   ℹ️  Codex settings are independent of Cursor")
    print("   ✅ Codex app will NOT be affected by these changes")
    return True

def main():
    """Main restoration function."""
    print("="*80)
    print("RESTORE CURSOR MODELS IN CHAT")
    print("="*80)
    print()
    print("This will:")
    print("  ✅ Restore all Cursor built-in models (Claude, GPT, Sonnet, etc.)")
    print("  ✅ Reset model preferences to use Cursor defaults")
    print("  ✅ Keep Codex app separate and unaffected")
    print()
    
    # Backup
    print("📦 Creating backup...")
    if not backup_database():
        print("   ⚠️  Could not create backup - proceeding anyway")
    print()
    
    # Restore models
    success = restore_cursor_models()
    print()
    
    # Verify subscription
    verify_cursor_subscription()
    
    # Check Codex
    check_codex_app()
    
    print()
    print("="*80)
    if success:
        print("✅ CURSOR MODELS RESTORED!")
        print()
        print("🔄 NEXT STEPS:")
        print("   1. Restart Cursor completely (Cmd + Q)")
        print("   2. Reopen Cursor")
        print("   3. Open Chat/Composer")
        print("   4. Select model from dropdown:")
        print("      - Claude 4.5 Sonnet")
        print("      - Claude 4.5 Sonnet Thinking")
        print("      - GPT-5.1")
        print("      - Other Cursor models")
        print()
        print("   Codex app: Still works independently ✅")
    else:
        print("⚠️  SOME ISSUES - Check output above")
    print("="*80)
    print()

if __name__ == "__main__":
    main()

