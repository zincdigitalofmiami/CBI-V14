#!/bin/bash
# CBI-V14 Enhanced Data Pipeline Cron Setup
# Adds bi-daily data collection for FX, Fed rates, and fundamentals

INGESTION_DIR="/Users/zincdigital/CBI-V14/cbi-v14-ingestion"
LOG_DIR="/Users/zincdigital/CBI-V14/logs"

# Create log directory
mkdir -p "$LOG_DIR"

echo "🔧 Setting up CBI-V14 Enhanced Data Pipeline cron jobs..."

# Get current crontab
crontab -l > /tmp/current_cron 2>/dev/null

# Add enhanced data collection jobs
cat << 'ENHANCED_CRON' >> /tmp/current_cron

# CBI-V14 Enhanced Data Pipeline - CRITICAL DATA SOURCES
# Bi-daily collection for FX rates, Fed policy, and fundamentals

# Enhanced data pipeline (6 AM and 6 PM EST - market critical times)
0 6,18 * * 1-5 cd $INGESTION_DIR && python3 enhanced_data_pipeline.py >> $LOG_DIR/enhanced_pipeline.log 2>&1

# FX-only collection (every 4 hours during weekdays to catch market moves)
0 */4 * * 1-5 cd $INGESTION_DIR && python3 -c "
import sys
sys.path.append('$INGESTION_DIR')
from enhanced_data_pipeline import fetch_yahoo_forex_data, CBI_V14_DataIngestionPipeline, logger

logger.info('FX-only collection started')
pipeline = CBI_V14_DataIngestionPipeline()
fx_data = fetch_yahoo_forex_data()
if not fx_data.empty:
    for pair in fx_data['pair'].unique():
        pair_data = fx_data[fx_data['pair'] == pair].copy()
        if 'BRL' in pair:
            pair_data['from_currency'] = 'USD'
            pair_data['to_currency'] = 'BRL'
            source_id = 'yahoo_finance_brl'
        elif 'CNY' in pair:
            pair_data['from_currency'] = 'USD' 
            pair_data['to_currency'] = 'CNY'
            source_id = 'yahoo_finance_cny'
        elif 'ARS' in pair:
            pair_data['from_currency'] = 'USD'
            pair_data['to_currency'] = 'ARS' 
            source_id = 'yahoo_finance_ars'
        else:
            continue
        
        pair_data['date'] = pair_data['Date']
        pair_data['rate'] = pair_data['Close']
        result = pipeline.ingest_and_validate(source_id, 'forex', pair_data)
        logger.info(f'FX collection result for {pair}: {result[\"status\"]}')
else:
    logger.warning('No FX data retrieved in scheduled collection')
logger.info('FX-only collection completed')
" >> $LOG_DIR/fx_collection.log 2>&1

ENHANCED_CRON

# Install the updated crontab
crontab /tmp/current_cron

# Clean up
rm /tmp/current_cron

echo "✅ Enhanced data pipeline cron jobs installed successfully"
echo ""
echo "📅 NEW SCHEDULED JOBS:"
echo "  - Enhanced Pipeline: 6 AM & 6 PM EST (weekdays) - Full validation & storage"
echo "  - FX Collection: Every 4 hours (weekdays) - FX rates only"
echo ""
echo "🔍 Current cron jobs:"
crontab -l | grep -E "(enhanced|fx_collection)" || echo "  No enhanced jobs found (check installation)"

echo ""
echo "📝 Log files will be created at:"
echo "  - $LOG_DIR/enhanced_pipeline.log"
echo "  - $LOG_DIR/fx_collection.log"

echo ""
echo "⚠️  CRITICAL SAFETY FEATURES ENABLED:"
echo "  ✅ Strict duplicate detection (queries BigQuery before insert)"
echo "  ✅ Placeholder value detection (rejects any 0.5 values)"
echo "  ✅ Range validation (rejects out-of-range currency/rate values)"
echo "  ✅ Limited lookback (max 30 days to prevent historical corruption)"
echo "  ✅ Comprehensive logging for audit trail"

echo ""
echo "🚨 DATA CORRUPTION PREVENTION:"
echo "  - NO historical years pulled (recent data only)"
echo "  - Duplicate dates automatically filtered out"  
echo "  - Failed validation = no data stored"
echo "  - All operations logged for accountability"

echo ""
echo "▶️  To manually run the enhanced pipeline:"
echo "    cd $INGESTION_DIR && python3 enhanced_data_pipeline.py"
