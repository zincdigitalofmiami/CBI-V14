#!/bin/bash
# Rollback Script - Yahoo Finance Integration
# Run this if integration fails or causes issues

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ROLLBACK: Yahoo Finance Integration                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get backup timestamp
echo "📋 Available backups:"
bq ls cbi-v14:models_v4 | grep "backup_2025"
echo ""

read -p "Enter backup timestamp (YYYYMMDD_HHMMSS): " BACKUP_DATE

echo ""
echo "⚠️  WARNING: This will RESTORE from backups and DELETE integration changes"
echo "⚠️  This action CANNOT be undone"
echo ""

read -p "Are you sure you want to rollback? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 0
fi

echo ""
echo "🔄 Starting rollback process..."
echo ""

# Step 1: Drop views created during integration
echo "Step 1: Removing integration views..."

bq rm -f -t cbi-v14:forecasting_data_warehouse.yahoo_finance_historical && echo "  ✅ Dropped yahoo_finance_historical view" || echo "  ⚠️  View not found (skipping)"

bq rm -f -t cbi-v14:forecasting_data_warehouse.soybean_oil_prices_historical_view && echo "  ✅ Dropped soybean_oil_prices_historical_view" || echo "  ⚠️  View not found (skipping)"

bq rm -f -t cbi-v14:forecasting_data_warehouse.biofuel_components_historical_view && echo "  ✅ Dropped biofuel_components_historical_view" || echo "  ⚠️  View not found (skipping)"

bq rm -f -t cbi-v14:forecasting_data_warehouse.all_symbols_20yr_view && echo "  ✅ Dropped all_symbols_20yr_view" || echo "  ⚠️  View not found (skipping)"

echo ""

# Step 2: Drop regime tables created during integration
echo "Step 2: Removing regime tables..."

bq rm -f -t cbi-v14:models_v4.trade_war_2017_2019_historical && echo "  ✅ Dropped trade_war_2017_2019_historical" || echo "  ⚠️  Table not found (skipping)"

bq rm -f -t cbi-v14:models_v4.crisis_2008_historical && echo "  ✅ Dropped crisis_2008_historical" || echo "  ⚠️  Table not found (skipping)"

bq rm -f -t cbi-v14:models_v4.pre_crisis_2000_2007_historical && echo "  ✅ Dropped pre_crisis_2000_2007_historical" || echo "  ⚠️  Table not found (skipping)"

bq rm -f -t cbi-v14:models_v4.recovery_2010_2016_historical && echo "  ✅ Dropped recovery_2010_2016_historical" || echo "  ⚠️  Table not found (skipping)"

echo ""

# Step 3: Restore soybean_oil_prices from backup (if backfill was executed)
echo "Step 3: Restoring soybean_oil_prices (if modified)..."

read -p "Was soybean_oil_prices backfilled? (yes/no): " backfilled

if [ "$backfilled" = "yes" ]; then
    echo "  🔄 Restoring soybean_oil_prices from backup..."
    
    # Delete current table
    bq rm -f -t cbi-v14:forecasting_data_warehouse.soybean_oil_prices
    
    # Restore from backup
    bq cp \
        cbi-v14:forecasting_data_warehouse.soybean_oil_prices_backup_$BACKUP_DATE \
        cbi-v14:forecasting_data_warehouse.soybean_oil_prices
    
    echo "  ✅ soybean_oil_prices restored"
else
    echo "  ⚠️  Skipping soybean_oil_prices restore (not modified)"
fi

echo ""

# Step 4: Restore production training tables (if rebuilt)
echo "Step 4: Restoring production training tables (if modified)..."

read -p "Were production_training_data_* tables rebuilt? (yes/no): " rebuilt

if [ "$rebuilt" = "yes" ]; then
    echo "  🔄 Restoring production training tables..."
    
    # Restore 1w
    bq rm -f -t cbi-v14:models_v4.production_training_data_1w
    bq cp \
        cbi-v14:models_v4.production_training_data_1w_backup_$BACKUP_DATE \
        cbi-v14:models_v4.production_training_data_1w
    echo "  ✅ production_training_data_1w restored"
    
    # Restore 1m
    bq rm -f -t cbi-v14:models_v4.production_training_data_1m
    bq cp \
        cbi-v14:models_v4.production_training_data_1m_backup_$BACKUP_DATE \
        cbi-v14:models_v4.production_training_data_1m
    echo "  ✅ production_training_data_1m restored"
    
    # Add other horizons if backed up
    echo "  ⚠️  Note: Restore other horizons manually if needed"
else
    echo "  ⚠️  Skipping training table restore (not modified)"
fi

echo ""

# Step 5: Verification
echo "Step 5: Verification..."

echo "  Checking soybean_oil_prices row count..."
SOYBEAN_ROWS=$(bq query --nouse_legacy_sql --format=csv "SELECT COUNT(*) FROM \`cbi-v14.forecasting_data_warehouse.soybean_oil_prices\`" | tail -n 1)
echo "  Current rows: $SOYBEAN_ROWS"

echo "  Checking production_training_data_1m row count..."
TRAINING_ROWS=$(bq query --nouse_legacy_sql --format=csv "SELECT COUNT(*) FROM \`cbi-v14.models_v4.production_training_data_1m\`" | tail -n 1)
echo "  Current rows: $TRAINING_ROWS"

echo ""

# Final summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ROLLBACK COMPLETE                                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "✅ Rollback completed successfully"
echo ""
echo "📋 What was rolled back:"
echo "   - Integration views removed"
echo "   - Regime tables removed"
if [ "$backfilled" = "yes" ]; then
    echo "   - soybean_oil_prices restored from backup"
fi
if [ "$rebuilt" = "yes" ]; then
    echo "   - production_training_data_* restored from backup"
fi
echo ""

echo "📋 Backup tables retained (can be deleted if no longer needed):"
echo "   - cbi-v14:forecasting_data_warehouse.soybean_oil_prices_backup_$BACKUP_DATE"
echo "   - cbi-v14:models_v4.production_training_data_1w_backup_$BACKUP_DATE"
echo "   - cbi-v14:models_v4.production_training_data_1m_backup_$BACKUP_DATE"
echo ""

echo "⚠️  Next steps:"
echo "   1. Review what went wrong (check logs)"
echo "   2. Fix issues in integration plan"
echo "   3. Re-run pre-integration audit"
echo "   4. Retry integration when ready"
echo ""

