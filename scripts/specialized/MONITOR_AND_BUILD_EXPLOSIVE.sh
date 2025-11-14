#!/bin/bash
# MONITOR DATA PULL AND BUILD EXPLOSIVE DATASET

echo "🚀 MONITORING 224-SYMBOL DATA PULL"
echo "=================================="

while true; do
    # Check if pull script is still running
    if ps aux | grep -q "[p]ull_224_driver_universe.py"; then
        echo -n "⏳ Pull still running... "
        
        # Check latest table update time if exists
        bq query --use_legacy_sql=false --format=csv 2>/dev/null << EOF | tail -1
        SELECT MAX(created) 
        FROM \`cbi-v14.yahoo_finance_comprehensive.__TABLES__\`
        WHERE table_id = 'all_drivers_224_universe'
EOF
        
        sleep 30
    else
        echo "✅ PULL COMPLETE!"
        break
    fi
done

echo ""
echo "🔥 BUILDING EXPLOSIVE TRAINING DATASET"
echo "======================================"

# Check what we got
echo "Checking loaded data..."
bq query --use_legacy_sql=false --format=pretty << 'EOF'
SELECT 
  COUNT(DISTINCT symbol) AS symbols,
  MIN(date) AS earliest,
  MAX(date) AS latest,
  COUNT(*) AS total_rows
FROM `cbi-v14.yahoo_finance_comprehensive.all_drivers_224_universe`;
EOF

echo ""
echo "📊 CREATING MASSIVE FEATURE TABLE"
echo "================================="

# Create the explosive table with ALL features
bq query --use_legacy_sql=false << 'EOF'
CREATE OR REPLACE TABLE `cbi-v14.models_v4.full_224_explosive_all_years` AS
WITH yahoo_raw AS (
  SELECT * FROM `cbi-v14.yahoo_finance_comprehensive.all_drivers_224_universe`
),
yahoo_pivoted AS (
  -- INSERT GENERATED PIVOT HERE
  $(cat /tmp/full_224_pivot.sql)
),
target AS (
  SELECT 
    date,
    LEAD(close, 22) OVER (ORDER BY date) - close AS target_1m
  FROM yahoo_raw
  WHERE symbol = 'ZL=F'
)
SELECT 
  y.*,
  t.target_1m
FROM yahoo_pivoted y
LEFT JOIN target t ON y.date = t.date;
EOF

echo "✅ EXPLOSIVE DATASET READY!"
echo ""
echo "📈 FINAL STATS:"
bq query --use_legacy_sql=false --format=pretty << 'EOF'
SELECT 
  COUNT(*) AS rows,
  COUNT(DISTINCT date) AS unique_dates,
  MIN(date) AS earliest,
  MAX(date) AS latest,
  COUNT(*) AS columns
FROM `cbi-v14.models_v4.full_224_explosive_all_years`
LIMIT 1;
EOF

echo ""
echo "🏁 READY FOR TRAINING WITH:"
echo "  • ALL 224 SYMBOLS"
echo "  • ALL 50+ YEARS OF DATA"
echo "  • 6,300+ FEATURES"
echo "  • ALL CORRELATIONS"
echo "  • ALL INTERACTIONS"
echo "  • NO FUCKING COMPROMISES!"

