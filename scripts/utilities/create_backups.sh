#!/bin/bash
# Create backups before integration

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

echo "Creating backups with timestamp: $BACKUP_DATE"
echo ""

# Backup 1: production_training_data_1w
echo "Backing up production_training_data_1w..."
bq cp \
  cbi-v14:models_v4.production_training_data_1w \
  cbi-v14:models_v4.production_training_data_1w_backup_$BACKUP_DATE

echo "✅ production_training_data_1w backed up"
echo ""

# Backup 2: production_training_data_1m
echo "Backing up production_training_data_1m..."
bq cp \
  cbi-v14:models_v4.production_training_data_1m \
  cbi-v14:models_v4.production_training_data_1m_backup_$BACKUP_DATE

echo "✅ production_training_data_1m backed up"
echo ""

# Backup 3: soybean_oil_prices
echo "Backing up soybean_oil_prices..."
bq cp \
  cbi-v14:forecasting_data_warehouse.soybean_oil_prices \
  cbi-v14:forecasting_data_warehouse.soybean_oil_prices_backup_$BACKUP_DATE

echo "✅ soybean_oil_prices backed up"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   BACKUPS COMPLETE                                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Backup timestamp: $BACKUP_DATE"
echo ""
echo "Rollback command (if needed):"
echo "  ./scripts/rollback_integration.sh"
echo "  (Use timestamp: $BACKUP_DATE)"
echo ""

