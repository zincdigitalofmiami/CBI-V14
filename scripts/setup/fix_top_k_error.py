#!/usr/bin/env python3
"""
Fix Gemini top_k Parameter Error
This is a Cursor bug where it sends unsupported parameters to Gemini
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"

def main():
    print("="*80)
    print("FIXING GEMINI TOP_K PARAMETER ERROR")
    print("="*80)
    print()
    print("🔴 THE PROBLEM:")
    print("   Cursor's built-in Gemini sends 'top_k' parameter that Gemini API doesn't accept")
    print("   This is a Cursor compatibility bug")
    print()
    
    # Backup
    backup_file = SETTINGS_FILE.with_suffix(f'.json.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copy2(SETTINGS_FILE, backup_file)
    print(f"✅ Backup created: {backup_file.name}")
    print()
    
    # Read settings
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)
    
    print("🔧 APPLYING FIXES...")
    print()
    
    # Fix 1: Minimal Gemini configuration
    # Only keep the API key, remove everything else that might trigger parameters
    essential_gemini = {
        "geminicodeassist.apiKey": settings.get("geminicodeassist.apiKey", ""),
    }
    
    # Remove ALL other Gemini settings that might cause issues
    keys_to_remove = [
        "geminicodeassist.project",
        "geminicodeassist.agentDebugMode",
        "geminicodeassist.codeGenerationPaneViewEnabled",
        "geminicodeassist.inlineSuggestions.nextEditPredictions",
        "geminicodeassist.inlineSuggestions.suggestionSpeed",
        "geminicodeassist.inlineSuggestions.enabled",
        "geminicodeassist.verboseLogging",
        "gemini-cli.debug.logging.enabled",
    ]
    
    removed = []
    for key in keys_to_remove:
        if key in settings:
            del settings[key]
            removed.append(key)
    
    # Set only essential Gemini settings
    for key, value in essential_gemini.items():
        settings[key] = value
    
    # Save
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
    
    print(f"✅ Removed {len(removed)} problematic settings:")
    for key in removed:
        print(f"   - {key}")
    print()
    print("✅ Minimal Gemini configuration applied")
    print()
    
    print("="*80)
    print("✅ FIXES APPLIED")
    print("="*80)
    print()
    print("📋 IMPORTANT: Use Gemini Code Assist Extension Instead")
    print()
    print("   Cursor's built-in Gemini has a bug (sends top_k parameter)")
    print("   The extension handles Gemini API correctly")
    print()
    print("   To use Gemini:")
    print("   1. Cmd + Shift + P")
    print("   2. Type: 'Gemini: Open Chat'")
    print("   3. Select model in extension's chat")
    print()
    print("   This bypasses Cursor's buggy built-in integration")
    print()
    print("🔄 RESTART CURSOR NOW")
    print("   Cmd + Q → Quit → Reopen")
    print()

if __name__ == "__main__":
    main()

