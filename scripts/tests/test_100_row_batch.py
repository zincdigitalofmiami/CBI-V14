#!/usr/bin/env python3
"""
Day 2 Integration Test - 100 Row Batch Load
Validates end-to-end pipeline before production

Tests:
1. Schema handshake (producer → DDL)
2. Regime materialization (no NULL regime.name)
3. All STRUCT fields populated
4. Load succeeds to BigQuery
5. Query-back verification
"""

import sys
import logging
from datetime import datetime, date
from google.cloud import bigquery
import pandas as pd

# Import ingestion logic
sys.path.insert(0, '/Users/kirkmusick/Documents/GitHub/CBI-V14')
from scripts.ingestion.ingest_features_hybrid import (
    get_current_regime,
    calculate_features_mock,
    validate_batch,
    load_with_retry,
    test_schema_handshake
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("INTEGRATION_TEST")

PROJECT_ID = "cbi-v14"
DESTINATION = f"{PROJECT_ID}.features.daily_ml_matrix_test"  # Use test table

def create_test_table(client: bigquery.Client):
    """Create test table (copy of production schema)"""
    
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {DESTINATION} (
      symbol STRING NOT NULL,
      data_date DATE NOT NULL,
      timestamp TIMESTAMP,

      market_data STRUCT<
        open FLOAT64, high FLOAT64, low FLOAT64, close FLOAT64,
        volume INT64, vwap FLOAT64, realized_vol_1h FLOAT64
      >,

      pivots STRUCT<
        P FLOAT64, R1 FLOAT64, R2 FLOAT64, S1 FLOAT64, S2 FLOAT64,
        distance_to_P FLOAT64,
        distance_to_nearest_pivot FLOAT64,
        weekly_pivot_distance FLOAT64,
        price_above_P BOOL
      >,

      policy STRUCT<
        trump_action_prob FLOAT64,
        trump_expected_zl_move FLOAT64,
        trump_score FLOAT64,
        trump_score_signed FLOAT64,
        trump_confidence FLOAT64,
        trump_sentiment_7d FLOAT64,
        trump_tariff_intensity FLOAT64,
        trump_procurement_alert BOOL,
        trump_mentions INT64,
        trumpxi_china_mentions INT64,
        trumpxi_sentiment_volatility FLOAT64,
        trumpxi_policy_impact FLOAT64,
        trumpxi_volatility_30d_ma FLOAT64,
        trump_soybean_sentiment_7d FLOAT64,
        policy_trump_topic_multiplier FLOAT64,
        policy_trump_recency_decay FLOAT64
      >,

      golden_zone STRUCT<
        state INT64,
        swing_high FLOAT64,
        swing_low FLOAT64,
        fib_50 FLOAT64,
        fib_618 FLOAT64,
        vol_decay_slope FLOAT64,
        qualified_trigger BOOL
      >,

      regime STRUCT<
        name STRING,
        weight INT64,
        vol_percentile FLOAT64,
        k_vol FLOAT64
      >,

      ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    )
    PARTITION BY data_date
    CLUSTER BY symbol, regime.name;
    """
    
    client.query(ddl).result()
    logger.info(f"✅ Test table created: {DESTINATION}")

def cleanup_test_table(client: bigquery.Client):
    """Drop test table after test"""
    try:
        client.delete_table(DESTINATION)
        logger.info(f"✅ Test table cleaned up: {DESTINATION}")
    except Exception as e:
        logger.warning(f"⚠️ Could not cleanup test table: {e}")

def test_100_row_batch():
    """
    Main test: Generate 100 rows, load to BigQuery, verify
    """
    
    logger.info("🧪 Starting 100-Row Batch Integration Test")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    try:
        # Step 1: Create test table
        create_test_table(client)
        
        # Step 2: Run schema handshake test
        if not test_schema_handshake():
            logger.error("❌ TEST FAILED: Schema handshake failed")
            return False
        
        # Step 3: Generate 100 rows (50 ZL + 50 MES)
        now = datetime.now()
        today = date.today()
        current_regime = get_current_regime(client, str(today))
        
        rows = []
        for i in range(50):
            for symbol in ["ZL", "MES"]:
                mkt, piv, pol, gz = calculate_features_mock(symbol, now)
                
                row = {
                    "symbol": symbol,
                    "data_date": today,
                    "timestamp": now,
                    "market_data": mkt,
                    "pivots": piv,
                    "policy": pol,
                    "golden_zone": gz,
                    "regime": current_regime,
                    "ingestion_ts": now
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        logger.info(f"✅ Generated {len(df)} rows")
        
        # Step 4: Validate batch
        validate_batch(df)
        
        # Step 5: Load to BigQuery
        load_with_retry(client, df, DESTINATION, max_retries=3)
        
        # Step 6: Query back and verify
        verify_query = f"""
        SELECT 
            symbol,
            COUNT(*) as row_count,
            COUNT(DISTINCT regime.name) as unique_regimes,
            SUM(CASE WHEN pivots.distance_to_nearest_pivot IS NULL THEN 1 ELSE 0 END) as null_pivots,
            SUM(CASE WHEN policy.trump_mentions IS NULL THEN 1 ELSE 0 END) as null_policy,
            SUM(CASE WHEN regime.name IS NULL THEN 1 ELSE 0 END) as null_regime
        FROM `{DESTINATION}`
        WHERE data_date = '{today}'
        GROUP BY symbol
        ORDER BY symbol
        """
        
        result_df = client.query(verify_query).to_dataframe()
        
        logger.info("📊 Query-Back Results:")
        logger.info(f"\n{result_df.to_string()}")
        
        # Step 7: Validate results
        errors = []
        
        for _, row in result_df.iterrows():
            if row['row_count'] != 50:
                errors.append(f"{row['symbol']}: Expected 50 rows, got {row['row_count']}")
            
            if row['null_pivots'] > 0:
                errors.append(f"{row['symbol']}: {row['null_pivots']} NULL pivots detected")
            
            if row['null_policy'] > 0:
                errors.append(f"{row['symbol']}: {row['null_policy']} NULL policy fields detected")
            
            if row['null_regime'] > 0:
                errors.append(f"{row['symbol']}: {row['null_regime']} NULL regime.name detected")
            
            if row['unique_regimes'] != 1:
                errors.append(f"{row['symbol']}: Expected 1 unique regime, got {row['unique_regimes']}")
        
        if errors:
            logger.error("❌ TEST FAILED: Validation errors:")
            for error in errors:
                logger.error(f"  - {error}")
            return False
        
        logger.info("✅ All validations passed!")
        logger.info("🎉 100-ROW BATCH INTEGRATION TEST: PASSED")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup test table
        cleanup_test_table(client)

if __name__ == "__main__":
    success = test_100_row_batch()
    sys.exit(0 if success else 1)

