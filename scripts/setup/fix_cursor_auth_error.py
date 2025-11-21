#!/usr/bin/env python3
"""
Fix Cursor Authentication Error (ERROR_BAD_USER_API_KEY)
Re-authenticates with Cursor to refresh expired tokens
"""

import sqlite3
import shutil
import json
from pathlib import Path
from datetime import datetime

STATE_DB = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"

def backup_database():
    """Backup Cursor database before making changes."""
    if not STATE_DB.exists():
        print(f"   ⚠️  Database not found: {STATE_DB}")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = STATE_DB.parent / f"state.vscdb.backup_auth_{timestamp}"
    shutil.copy(STATE_DB, backup_file)
    print(f"   ✅ Backup created: {backup_file.name}")
    return True

def check_auth_status():
    """Check current authentication status."""
    print("🔍 Checking authentication status...")
    
    if not STATE_DB.exists():
        print(f"   ❌ Database not found: {STATE_DB}")
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        # Check access token
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/accessToken' LIMIT 1")
        access_token = cursor.fetchone()
        if access_token:
            token = access_token[0]
            print(f"   ✅ Access token exists: {len(token)} chars")
            # Check if token is JWT format (3 parts separated by dots)
            parts = token.split('.')
            if len(parts) == 3:
                print(f"   ✅ Token format: Valid JWT")
            else:
                print(f"   ⚠️  Token format: Invalid (not JWT)")
        else:
            print(f"   ❌ Access token: NOT FOUND")
        
        # Check refresh token
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/refreshToken' LIMIT 1")
        refresh_token = cursor.fetchone()
        if refresh_token:
            print(f"   ✅ Refresh token exists: {len(refresh_token[0])} chars")
        else:
            print(f"   ❌ Refresh token: NOT FOUND")
        
        # Check subscription
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeMembershipType' LIMIT 1")
        membership = cursor.fetchone()
        if membership:
            print(f"   ✅ Membership: {membership[0]}")
        
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/stripeSubscriptionStatus' LIMIT 1")
        status = cursor.fetchone()
        if status:
            print(f"   ✅ Subscription status: {status[0]}")
        
        # Check email
        cursor.execute("SELECT value FROM ItemTable WHERE key = 'cursorAuth/cachedEmail' LIMIT 1")
        email = cursor.fetchone()
        if email:
            print(f"   ✅ Account email: {email[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking auth: {e}")
        return False

def clear_auth_tokens():
    """Clear authentication tokens to force re-authentication."""
    print("\n🔧 Clearing authentication tokens...")
    
    if not STATE_DB.exists():
        print(f"   ❌ Database not found: {STATE_DB}")
        return False
    
    try:
        conn = sqlite3.connect(STATE_DB)
        cursor = conn.cursor()
        
        # Clear auth tokens (keeps subscription info)
        auth_keys = [
            'cursorAuth/accessToken',
            'cursorAuth/refreshToken',
        ]
        
        for key in auth_keys:
            cursor.execute("DELETE FROM ItemTable WHERE key = ?", (key,))
            if cursor.rowcount > 0:
                print(f"   ✅ Cleared: {key}")
        
        conn.commit()
        conn.close()
        
        print("   ✅ Authentication tokens cleared")
        print("   ℹ️  Cursor will prompt you to sign in again")
        return True
        
    except Exception as e:
        print(f"   ❌ Error clearing tokens: {e}")
        return False

def main():
    """Main fix function."""
    print("="*80)
    print("FIX CURSOR AUTHENTICATION ERROR (ERROR_BAD_USER_API_KEY)")
    print("="*80)
    print()
    print("This error means Cursor's authentication tokens are expired or invalid.")
    print("We'll clear the tokens so Cursor will prompt you to sign in again.")
    print()
    
    # Check current status
    check_auth_status()
    
    # Backup
    print("\n📦 Creating backup...")
    if not backup_database():
        print("   ⚠️  Could not create backup - proceeding anyway")
    
    # Clear tokens
    print()
    success = clear_auth_tokens()
    
    print()
    print("="*80)
    if success:
        print("✅ AUTHENTICATION TOKENS CLEARED!")
        print()
        print("🔄 NEXT STEPS:")
        print("   1. Restart Cursor completely (Cmd + Q)")
        print("   2. Reopen Cursor")
        print("   3. Cursor will prompt you to sign in")
        print("   4. Sign in with your Cursor account:")
        print("      - Email: zincmiami@gmail.com")
        print("      - Or use GitHub authentication")
        print("   5. After signing in, tokens will be refreshed")
        print("   6. Error should be resolved")
        print()
        print("   ⚠️  You MUST sign in again for this to work!")
    else:
        print("⚠️  SOME ISSUES - Check output above")
    print("="*80)
    print()

if __name__ == "__main__":
    main()


