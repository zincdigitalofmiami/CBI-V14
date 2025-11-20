#!/usr/bin/env python3
"""
Check Cursor AI agent configurations and API keys.
Helps diagnose GPT and Gemini key issues.
"""

import json
import os
import subprocess
from pathlib import Path

def check_cursor_settings():
    """Check Cursor settings files for AI agent configs."""
    print("="*80)
    print("CURSOR AI AGENT CONFIGURATION CHECK")
    print("="*80)
    
    # Common Cursor settings locations
    settings_paths = [
        Path.home() / "Library/Application Support/Cursor/User/settings.json",
        Path.home() / ".cursor/ide_state.json",
        Path.home() / ".cursor/mcp.json",
    ]
    
    print("\n1. CHECKING CURSOR SETTINGS FILES")
    print("-" * 80)
    
    for path in settings_paths:
        if path.exists():
            print(f"\n✅ Found: {path}")
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Search for AI-related keys
                    data_str = json.dumps(data, indent=2).lower()
                    if any(keyword in data_str for keyword in ['openai', 'gemini', 'gpt', 'api', 'key', 'model']):
                        print(f"   Contains AI-related settings")
                        # Print relevant sections
                        if isinstance(data, dict):
                            for key in data.keys():
                                if any(kw in key.lower() for kw in ['openai', 'gemini', 'gpt', 'api', 'model', 'lm', 'language']):
                                    print(f"   - {key}: {str(data[key])[:100]}")
                    else:
                        print(f"   No AI-related settings found")
            except Exception as e:
                print(f"   ⚠️  Error reading: {e}")
        else:
            print(f"\n❌ Not found: {path}")
    
    print("\n2. CHECKING ENVIRONMENT VARIABLES")
    print("-" * 80)
    
    env_vars = [
        'OPENAI_API_KEY',
        'GEMINI_API_KEY',
        'GOOGLE_API_KEY',
        'CURSOR_OPENAI_API_KEY',
        'CURSOR_GEMINI_API_KEY',
    ]
    
    found_keys = []
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask the key (show first 4 and last 4 chars)
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"✅ {var}: {masked}")
            found_keys.append(var)
        else:
            print(f"❌ {var}: Not set")
    
    if not found_keys:
        print("\n⚠️  No API keys found in environment variables")
    
    print("\n3. CHECKING MCP CONFIGURATION")
    print("-" * 80)
    
    mcp_path = Path.home() / ".cursor/mcp.json"
    if mcp_path.exists():
        try:
            with open(mcp_path, 'r') as f:
                mcp_data = json.load(f)
                print(f"✅ MCP config found: {mcp_path}")
                if mcp_data.get("mcpServers"):
                    print(f"   Configured servers: {list(mcp_data['mcpServers'].keys())}")
                    for server_name, server_config in mcp_data.get("mcpServers", {}).items():
                        print(f"\n   Server: {server_name}")
                        print(f"   Type: {server_config.get('command', 'unknown')}")
                        if 'env' in server_config:
                            print(f"   Environment variables: {list(server_config['env'].keys())}")
                else:
                    print("   ⚠️  No MCP servers configured")
        except Exception as e:
            print(f"   ⚠️  Error reading MCP config: {e}")
    else:
        print(f"❌ MCP config not found: {mcp_path}")
    
    print("\n4. CHECKING CURSOR DEFAULT SETTINGS")
    print("-" * 80)
    
    try:
        result = subprocess.run(
            ["defaults", "read", "com.todesktop.230313mzl4w4u92"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout.lower()
            if any(keyword in output for keyword in ['openai', 'gemini', 'gpt', 'api']):
                print("✅ Found AI-related settings in Cursor defaults")
                # Extract relevant lines
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if any(kw in line.lower() for kw in ['openai', 'gemini', 'gpt', 'api', 'key']):
                        print(f"   {line[:100]}")
            else:
                print("❌ No AI-related settings in Cursor defaults")
        else:
            print("⚠️  Could not read Cursor defaults (may not be installed)")
    except Exception as e:
        print(f"⚠️  Error checking defaults: {e}")
    
    print("\n5. RECOMMENDATIONS")
    print("-" * 80)
    
    print("\nTo configure GPT/OpenAI in Cursor:")
    print("1. Open Cursor Settings (Cmd+,)")
    print("2. Search for 'OpenAI' or 'API'")
    print("3. Look for:")
    print("   - 'Cursor: OpenAI API Key'")
    print("   - 'Cursor: Custom Model Provider'")
    print("   - Language Model settings")
    print("\nTo configure Gemini in Cursor:")
    print("1. Open Cursor Settings (Cmd+,)")
    print("2. Search for 'Gemini' or 'Google'")
    print("3. Look for:")
    print("   - 'Cursor: Gemini API Key'")
    print("   - 'Cursor: Google API Key'")
    print("   - Language Model settings")
    print("\nAlternative: Check Cursor's Settings UI:")
    print("  - Cursor → Settings → Features → AI")
    print("  - Or: Cursor → Settings → Extensions → Language Models")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nIf GPT key is not working:")
    print("  1. Verify key is set in Cursor Settings UI")
    print("  2. Check if key has proper permissions/credits")
    print("  3. Verify key format (should start with 'sk-...')")
    print("  4. Check Cursor logs for error messages")
    print("\nIf Gemini is not showing up:")
    print("  1. Verify key is set in Cursor Settings UI")
    print("  2. Check if Gemini is enabled in Cursor")
    print("  3. Verify key format (should be valid Google API key)")
    print("  4. Check Cursor logs for error messages")


if __name__ == "__main__":
    check_cursor_settings()

