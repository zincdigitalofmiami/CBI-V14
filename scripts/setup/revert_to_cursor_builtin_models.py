#!/usr/bin/env python3
"""
Revert Cursor IDE to Built-In Models Only
Removes all custom provider/baseUrl settings to ensure Cursor uses its own models
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

SETTINGS_FILE = Path.home() / "Library/Application Support/Cursor/User/settings.json"

def backup_settings():
    """Backup settings before making changes."""
    if not SETTINGS_FILE.exists():
        print("   ⚠️  Settings file not found")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = SETTINGS_FILE.parent / f"settings.json.backup_builtin_{timestamp}"
    shutil.copy(SETTINGS_FILE, backup_file)
    print(f"   ✅ Backup created: {backup_file.name}")
    return True

def remove_custom_provider_settings():
    """Remove custom provider/baseUrl settings from settings.json."""
    print("🔧 Removing custom provider settings...")
    
    if not SETTINGS_FILE.exists():
        print("   ⚠️  Settings file not found")
        return False
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        
        # Keys to remove (custom provider settings)
        keys_to_remove = [
            # OpenAI custom settings
            'cursor.openAI.baseUrl',
            'cursor.openAI.apiKey',
            'cursor.copilot.openai.baseUrl',
            'cursor.copilot.openai.apiKey',
            'openai.baseUrl',
            'openai.apiKey',
            
            # Provider settings
            'cursor.ai.provider',
            'cursor.languageModel.provider',
            'cursor.model.provider',
            'cursor.provider',
            
            # Custom baseUrl
            'cursor.baseUrl',
            'cursor.ai.baseUrl',
            'cursor.model.baseUrl',
            'cursor.languageModel.baseUrl',
            
            # Extra parameters
            'cursor.extraParameters',
            'cursor.model.extraParameters',
            'cursor.ai.extraParameters',
            'cursor.top_k',
            'cursor.model.top_k',
            
            # Gemini custom settings (keep only extension key)
            'cursor.gemini.baseUrl',
            'cursor.gemini.model',
            'cursor.languageModel.model',
            'cursor.model.model',
            'geminicodeassist.project',  # Causes license checks and parameter issues
            
            # Custom model provider
            'cursor.customModelProvider',
            'cursor.customModelProvider.baseUrl',
            'cursor.customModelProvider.apiKey',
        ]
        
        removed = []
        for key in keys_to_remove:
            if key in settings:
                del settings[key]
                removed.append(key)
                print(f"   ✅ Removed: {key}")
        
        # Also check for any keys containing baseUrl, provider, or generativelanguage
        keys_to_check = list(settings.keys())
        for key in keys_to_check:
            # Check if key contains problematic terms
            if any(term in key.lower() for term in ['baseurl', 'provider', 'generativelanguage', 'top_k', 'extraparam']):
                # But keep geminicodeassist.apiKey (for extension)
                if 'geminicodeassist.apiKey' not in key:
                    del settings[key]
                    if key not in removed:
                        removed.append(key)
                        print(f"   ✅ Removed: {key}")
        
        # Save settings
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        
        if removed:
            print(f"   ✅ Removed {len(removed)} custom provider settings")
        else:
            print("   ℹ️  No custom provider settings found (already clean)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def verify_settings():
    """Verify settings are clean."""
    print("\n🔍 Verifying settings...")
    
    if not SETTINGS_FILE.exists():
        print("   ⚠️  Settings file not found")
        return False
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        
        # Check for problematic settings
        problematic = []
        for key in settings.keys():
            if any(term in key.lower() for term in ['baseurl', 'provider', 'generativelanguage', 'top_k', 'extraparam']):
                # But allow geminicodeassist.apiKey (for extension)
                if 'geminicodeassist.apiKey' not in key:
                    problematic.append(key)
        
        if problematic:
            print(f"   ⚠️  Found {len(problematic)} potentially problematic settings:")
            for key in problematic:
                print(f"      - {key}")
        else:
            print("   ✅ No custom provider settings found")
            print("   ✅ Settings are clean")
        
        # Show current settings
        print("\n   📋 Current settings:")
        for key in sorted(settings.keys()):
            if 'gemini' in key.lower() or 'cloudcode' in key.lower() or 'cursor' in key.lower() or 'window' in key.lower() or 'workbench' in key.lower() or 'update' in key.lower():
                value = settings[key]
                if isinstance(value, str) and len(value) > 30:
                    value = value[:30] + "..."
                print(f"      - {key}: {value}")
        
        return len(problematic) == 0
        
    except Exception as e:
        print(f"   ⚠️  Error verifying: {e}")
        return False

def main():
    """Main function."""
    print("="*80)
    print("REVERT CURSOR TO BUILT-IN MODELS ONLY")
    print("="*80)
    print()
    print("This will:")
    print("  ✅ Remove custom provider settings")
    print("  ✅ Remove custom baseUrl settings")
    print("  ✅ Remove extra parameters (like top_k)")
    print("  ✅ Ensure Cursor uses only its built-in models")
    print("  ✅ Keep Gemini extension API key (for extension use)")
    print()
    
    # Backup
    print("📦 Creating backup...")
    backup_settings()
    print()
    
    # Remove custom settings
    success = remove_custom_provider_settings()
    print()
    
    # Verify
    verify_settings()
    
    print()
    print("="*80)
    if success:
        print("✅ CURSOR REVERTED TO BUILT-IN MODELS!")
        print()
        print("🔄 NEXT STEPS:")
        print("   1. Restart Cursor completely (Cmd + Q)")
        print("   2. Reopen Cursor")
        print("   3. Open Chat/Composer")
        print("   4. In model dropdown, select Cursor models:")
        print("      - Claude 4.5 Sonnet")
        print("      - Claude 4.5 Sonnet Thinking")
        print("      - GPT-5.1 (Cursor)")
        print("      - Sonnet 4.5")
        print("      - Composer 1")
        print()
        print("   ⚠️  DO NOT select models that require external APIs")
        print("   ✅ Use only Cursor's built-in models")
        print()
        print("   🚨 CRITICAL: DO NOT select Gemini from Cursor's dropdown!")
        print("      - Cursor's built-in Gemini has a bug (top_k error)")
        print("      - Use Gemini extension instead: Cmd+Shift+P → 'Gemini: Open Chat'")
        print()
        print("   Codex CLI: Still works independently ✅")
    else:
        print("⚠️  SOME ISSUES - Check output above")
    print("="*80)
    print()

if __name__ == "__main__":
    main()

