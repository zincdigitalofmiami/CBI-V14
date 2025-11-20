#!/bin/bash
# Store API Keys in macOS Keychain
# Run this script to securely store all required API keys

set -e

KEYCHAIN_SERVICE="cbi-v14"
ACCOUNT="default"

echo "=========================================="
echo "CBI-V14 API Key Storage in macOS Keychain"
echo "=========================================="
echo ""
echo "This script will store API keys securely in macOS Keychain."
echo "You will be prompted for each key value."
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Function to store a key
store_key() {
    local key_name=$1
    local description=$2
    
    echo ""
    echo "----------------------------------------"
    echo "$description"
    echo "Key name: $key_name"
    echo ""
    read -sp "Enter the API key value (hidden): " key_value
    echo ""
    
    if [ -z "$key_value" ]; then
        echo "⚠️  Skipping $key_name (empty value)"
        return
    fi
    
    # Delete existing key if it exists
    security delete-generic-password -a "$ACCOUNT" -s "${KEYCHAIN_SERVICE}.${key_name}" 2>/dev/null || true
    
    # Add new key
    security add-generic-password \
        -a "$ACCOUNT" \
        -s "${KEYCHAIN_SERVICE}.${key_name}" \
        -w "$key_value" \
        -U
    
    if [ $? -eq 0 ]; then
        echo "✅ Stored $key_name in Keychain"
    else
        echo "❌ Failed to store $key_name"
    fi
}

# Store required keys
store_key "FRED_API_KEY" "Federal Reserve Economic Data API Key"
store_key "NEWSAPI_KEY" "NewsAPI Key (for sentiment analysis)"
store_key "SCRAPE_CREATORS_API_KEY" "ScrapeCreators API Key (for social media scraping)"

echo ""
echo "=========================================="
echo "Key Storage Complete"
echo "=========================================="
echo ""
echo "To verify keys were stored:"
echo "  security find-generic-password -a default -s cbi-v14.FRED_API_KEY -w"
echo ""
echo "To list all CBI-V14 keys:"
echo "  security dump-keychain | grep cbi-v14"
echo ""
echo "To use keys in Python:"
echo "  from src.utils.keychain_manager import get_api_key"
echo "  key = get_api_key('FRED_API_KEY')"
echo ""







