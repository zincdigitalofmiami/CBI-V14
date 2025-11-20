#!/usr/bin/env python3
"""
macOS Keychain Manager for API Keys
====================================

All API keys MUST be stored in macOS Keychain, not in code or environment variables.

Usage:
    from src.utils.keychain_manager import get_api_key
    
    fred_key = get_api_key('FRED_API_KEY')
    if not fred_key:
        raise RuntimeError("FRED_API_KEY not found in Keychain")

To store a key in Keychain:
    security add-generic-password -a "cbi-v14" -s "FRED_API_KEY" -w "your_key_here" -U
"""

import subprocess
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Keychain service name for all CBI-V14 keys
KEYCHAIN_SERVICE = "cbi-v14"


def get_api_key(key_name: str, account: str = "default") -> Optional[str]:
    """
    Retrieve an API key from macOS Keychain.
    
    Args:
        key_name: The name of the API key (e.g., 'FRED_API_KEY', 'NEWSAPI_KEY')
        account: The account name (default: 'default')
    
    Returns:
        The API key string if found, None otherwise
    
    Raises:
        RuntimeError: If not running on macOS
    """
    if sys.platform != 'darwin':
        raise RuntimeError("Keychain access is only available on macOS")
    
    try:
        # Use security command to retrieve password from Keychain
        # -a: account name
        # -s: service name (KEYCHAIN_SERVICE)
        # -w: write password to stdout
        cmd = [
            'security',
            'find-generic-password',
            '-a', account,
            '-s', f"{KEYCHAIN_SERVICE}.{key_name}",
            '-w'  # Write password to stdout
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        
        key = result.stdout.strip()
        if key:
            logger.debug(f"Retrieved {key_name} from Keychain")
            return key
        else:
            logger.warning(f"{key_name} found in Keychain but is empty")
            return None
            
    except subprocess.CalledProcessError as e:
        if e.returncode == 44:  # Item not found
            logger.warning(f"{key_name} not found in Keychain")
            return None
        else:
            logger.error(f"Error retrieving {key_name} from Keychain: {e.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout retrieving {key_name} from Keychain")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving {key_name} from Keychain: {e}")
        return None


def set_api_key(key_name: str, key_value: str, account: str = "default") -> bool:
    """
    Store an API key in macOS Keychain.
    
    Args:
        key_name: The name of the API key (e.g., 'FRED_API_KEY')
        key_value: The API key value to store
        account: The account name (default: 'default')
    
    Returns:
        True if successful, False otherwise
    
    Raises:
        RuntimeError: If not running on macOS
    """
    if sys.platform != 'darwin':
        raise RuntimeError("Keychain access is only available on macOS")
    
    try:
        # First, try to delete existing key if it exists
        subprocess.run(
            ['security', 'delete-generic-password',
             '-a', account,
             '-s', f"{KEYCHAIN_SERVICE}.{key_name}"],
            capture_output=True,
            check=False  # Don't fail if it doesn't exist
        )
        
        # Add the new key
        cmd = [
            'security',
            'add-generic-password',
            '-a', account,
            '-s', f"{KEYCHAIN_SERVICE}.{key_name}",
            '-w', key_value,
            '-U'  # Update if exists
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        
        logger.info(f"Stored {key_name} in Keychain")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error storing {key_name} in Keychain: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error storing {key_name} in Keychain: {e}")
        return False


def list_stored_keys() -> list[str]:
    """
    List all CBI-V14 API keys stored in Keychain.
    
    Returns:
        List of key names stored in Keychain
    """
    if sys.platform != 'darwin':
        return []
    
    try:
        cmd = [
            'security',
            'dump-keychain',
            '-d'  # Dump all items
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        
        # Parse output to find CBI-V14 keys
        keys = []
        for line in result.stdout.split('\n'):
            if KEYCHAIN_SERVICE in line:
                # Extract key name from service name
                if f"{KEYCHAIN_SERVICE}." in line:
                    key_name = line.split(f"{KEYCHAIN_SERVICE}.")[-1].strip()
                    if key_name:
                        keys.append(key_name)
        
        return list(set(keys))  # Remove duplicates
        
    except Exception as e:
        logger.error(f"Error listing keys from Keychain: {e}")
        return []


# Convenience function that matches os.getenv() interface for easy migration
def get_key(key_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get API key from Keychain with fallback to environment variable (for migration).
    
    This function provides backward compatibility during migration.
    Once all keys are in Keychain, this will only use Keychain.
    
    Args:
        key_name: The name of the API key
        default: Optional default value (not recommended for production)
    
    Returns:
        The API key if found, default if provided, None otherwise
    """
    import os
    
    # First try Keychain
    key = get_api_key(key_name)
    if key:
        return key
    
    # Fallback to environment variable (for migration period only)
    env_key = os.getenv(key_name)
    if env_key:
        logger.warning(f"Using {key_name} from environment variable. "
                      f"Please migrate to Keychain using: "
                      f"security add-generic-password -a default -s cbi-v14.{key_name} -w <key> -U")
        return env_key
    
    # Return default if provided
    if default is not None:
        logger.warning(f"Using default value for {key_name}. "
                      f"Please store in Keychain for production use.")
        return default
    
    return None







