#!/usr/bin/env python3
"""
Remove OpenAI API Key from Cursor
Keeps Codex working (separate app)
Uses Cursor's built-in models instead
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
import sys

STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"

def remove_openai_from_cursor():
    """Remove OpenAI API key from Cursor database."""
    
    print("="*80)
    print("REMOVING OPENAI CONNECTIONS FROM CURSOR")
    print("="*80)
    print()
    print("This will:")
    print("  ✅ Remove OpenAI API key from Cursor database")
    print("  ✅ Keep Codex app working (separate)")
    print("  ✅ Use Cursor's built-in models instead")
    print()
    
    if not STATE_DB.exists():
        print("❌ Cursor database not found")
        return False
    
    # Backup database
    backup_file = STATE_DB.with_suffix(f'.vscdb.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copy2(STATE_DB, backup_file)
    print(f"✅ Backup created: {backup_file.name}")
    print()
    
    # Remove OpenAI key
    print("Removing OpenAI API key from database...")
    conn = sqlite3.connect(STATE_DB)
    cursor = conn.cursor()
    
    # Find OpenAI key
    cursor.execute("SELECT key FROM ItemTable WHERE key = 'cursorAuth/openAIKey' LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        # Delete OpenAI key
        cursor.execute("DELETE FROM ItemTable WHERE key = 'cursorAuth/openAIKey'")
        conn.commit()
        print("   ✅ Removed cursorAuth/openAIKey")
    else:
        print("   ℹ️  OpenAI key not found (already removed?)")
    
    # Check for other OpenAI-related entries (but don't delete everything)
    cursor.execute("""
        SELECT key FROM ItemTable 
        WHERE key LIKE '%openai%' OR key LIKE '%OpenAI%'
        ORDER BY key
    """)
    
    other_keys = cursor.fetchall()
    if other_keys:
        print(f"\n   Found {len(other_keys)} other OpenAI-related entries:")
        for (key,) in other_keys:
            print(f"   - {key} (keeping - may be needed)")
    
    conn.close()
    
    print()
    print("="*80)
    print("✅ OPENAI REMOVED FROM CURSOR")
    print("="*80)
    print()
    print("📋 WHAT CHANGED:")
    print("   ✅ OpenAI API key removed from Cursor database")
    print("   ✅ Cursor will use its built-in models")
    print("   ✅ Codex app still works (separate)")
    print()
    print("🔄 RESTART CURSOR:")
    print("   Cmd + Q → Quit → Reopen Cursor")
    print()
    print("📝 TO USE CURSOR MODELS:")
    print("   - Select models from Cursor's dropdown")
    print("   - Use GPT-5.1, Sonnet 4.5, Composer 1, etc.")
    print("   - These are Cursor's models (no OpenAI key needed)")
    print()
    
    return True

if __name__ == "__main__":
    success = remove_openai_from_cursor()
    sys.exit(0 if success else 1)

