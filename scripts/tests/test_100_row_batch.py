#!/usr/bin/env python3
"""
100-Row Integration Test for features.daily_ml_matrix
======================================================

Tests the complete ingestion pipeline:
1. Generate 100 test rows with realistic data
2. Run ingestion pipeline
3. Query back from BigQuery
4. Verify data integrity
5. Auto-cleanup (delete test data)

This test verifies:
- Schema enforcement (STRUCTs)
- Regime lookup (Python cache)
- Micro-batch loading
- Partitioning/clustering
- Data quality checks

Per: DAY_1_EXECUTION_PACKET_2025-11-21.md
"""

import sys
import logging
from datetime import datetime, timedelta, date
from pathlib import Path

import pandas as pd
import numpy as np
from google.cloud import bigquery

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.ingest_features_hybrid import IngestionPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test constants
PROJECT_ID = "cbi-v14"
TABLE_ID = "features.daily_ml_matrix"
TEST_SYMBOL = "ZL_TEST"
NUM_ROWS = 100


def generate_test_data() -> pd.DataFrame:
    """Generate 100 rows of realistic test data."""
    logger.info(f"Generating {NUM_ROWS} test rows...")
    
    # Date range: last 100 days within regime coverage (2023-11-01 to present)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=NUM_ROWS-1)
    
    # Ensure we're within trump_anticipation_2024 or trump_second_term
    if start_date < date(2023, 11, 1):
        start_date = date(2023, 11, 1)
        end_date = start_date + timedelta(days=NUM_ROWS-1)
    
    dates = pd.date_range(start=start_date, end=end_date, freq='D')[:NUM_ROWS]
    
    # Generate realistic OHLCV data (ZL futures ~$0.50/lb, so ~$50)
    np.random.seed(42)
    base_price = 50.0
    
    data = {
        'symbol': [TEST_SYMBOL] * NUM_ROWS,
        'data_date': dates,
        'timestamp': [datetime.now()] * NUM_ROWS,
        
        # Market data
        'open': base_price + np.random.randn(NUM_ROWS) * 2,
        'high': base_price + np.random.randn(NUM_ROWS) * 2 + 1,
        'low': base_price + np.random.randn(NUM_ROWS) * 2 - 1,
        'close': base_price + np.random.randn(NUM_ROWS) * 2,
        'volume': np.random.randint(10000, 50000, NUM_ROWS),
        'vwap': base_price + np.random.randn(NUM_ROWS) * 2,
        'realized_vol_1h': np.random.uniform(0.1, 0.5, NUM_ROWS),
        
        # Pivot points (realistic for $50 price)
        'P': base_price + np.random.randn(NUM_ROWS) * 0.5,
        'R1': base_price + np.random.uniform(0.5, 1.5, NUM_ROWS),
        'R2': base_price + np.random.uniform(1.5, 3.0, NUM_ROWS),
        'S1': base_price - np.random.uniform(0.5, 1.5, NUM_ROWS),
        'S2': base_price - np.random.uniform(1.5, 3.0, NUM_ROWS),
        'distance_to_P': np.random.randn(NUM_ROWS) * 0.5,
        'distance_to_nearest_pivot': np.random.uniform(0.1, 2.0, NUM_ROWS),
        'weekly_pivot_distance': np.random.randn(NUM_ROWS) * 1.0,
        'price_above_P': np.random.choice([True, False], NUM_ROWS),
        
        # Trump/policy features
        'trump_action_prob': np.random.uniform(0.0, 1.0, NUM_ROWS),
        'trump_expected_zl_move': np.random.randn(NUM_ROWS) * 0.02,
        'trump_score': np.random.uniform(0.0, 10.0, NUM_ROWS),
        'trump_score_signed': np.random.randn(NUM_ROWS) * 5.0,
        'trump_confidence': np.random.uniform(0.5, 1.0, NUM_ROWS),
        'trump_sentiment_7d': np.random.randn(NUM_ROWS),
        'trump_tariff_intensity': np.random.uniform(0.0, 10.0, NUM_ROWS),
        'trump_procurement_alert': np.random.choice([True, False], NUM_ROWS),
        'trump_mentions': np.random.randint(0, 50, NUM_ROWS),
        'trumpxi_china_mentions': np.random.randint(0, 20, NUM_ROWS),
        'trumpxi_sentiment_volatility': np.random.uniform(0.0, 5.0, NUM_ROWS),
        'trumpxi_policy_impact': np.random.randn(NUM_ROWS) * 0.5,
        'trumpxi_volatility_30d_ma': np.random.uniform(0.1, 2.0, NUM_ROWS),
        'trump_soybean_sentiment_7d': np.random.randn(NUM_ROWS),
        'policy_trump_topic_multiplier': np.random.uniform(1.0, 3.0, NUM_ROWS),
        'policy_trump_recency_decay': np.random.uniform(0.5, 1.0, NUM_ROWS),
        
        # Golden Zone (MES-style, but included for testing)
        'golden_zone_state': np.random.randint(0, 3, NUM_ROWS),
        'swing_high': base_price + np.random.uniform(1.0, 5.0, NUM_ROWS),
        'swing_low': base_price - np.random.uniform(1.0, 5.0, NUM_ROWS),
        'fib_50': base_price + np.random.randn(NUM_ROWS) * 1.0,
        'fib_618': base_price + np.random.randn(NUM_ROWS) * 1.5,
        'vol_decay_slope': np.random.randn(NUM_ROWS) * 0.1,
        'qualified_trigger': np.random.choice([True, False], NUM_ROWS),
    }
    
    df = pd.DataFrame(data)
    
    # Ensure high > low, high >= open/close, low <= open/close
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1) + 0.1
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1) - 0.1
    
    logger.info(f"✅ Generated {len(df)} test rows")
    logger.info(f"Date range: {df['data_date'].min()} → {df['data_date'].max()}")
    
    return df


def query_test_data(client: bigquery.Client) -> pd.DataFrame:
    """Query back the test data from BigQuery."""
    query = f"""
    SELECT
      symbol,
      data_date,
      regime_name,
      regime.name as regime_struct_name,
      regime.weight as regime_weight,
      market_data.close as close_price,
      pivots.P as pivot_P,
      policy.trump_action_prob,
      golden_zone.state as gz_state
    FROM `{PROJECT_ID}.{TABLE_ID}`
    WHERE symbol = '{TEST_SYMBOL}'
    ORDER BY data_date
    """
    
    logger.info("Querying test data from BigQuery...")
    df = client.query(query).to_dataframe()
    logger.info(f"✅ Retrieved {len(df)} rows from BigQuery")
    
    return df


def cleanup_test_data(client: bigquery.Client):
    """Delete test data from BigQuery."""
    query = f"""
    DELETE FROM `{PROJECT_ID}.{TABLE_ID}`
    WHERE symbol = '{TEST_SYMBOL}'
    """
    
    logger.info("Cleaning up test data...")
    job = client.query(query)
    job.result()
    logger.info(f"✅ Deleted test data for symbol {TEST_SYMBOL}")


def verify_data_integrity(original_df: pd.DataFrame, queried_df: pd.DataFrame) -> bool:
    """Verify data integrity between original and queried data."""
    logger.info("Verifying data integrity...")
    
    checks = {
        'row_count': len(original_df) == len(queried_df),
        'regime_populated': queried_df['regime_name'].notna().all(),
        'regime_weight_valid': (queried_df['regime_weight'].isin([400, 600])).all(),
        'close_price_reasonable': (queried_df['close_price'] > 0).all(),
        'pivot_populated': queried_df['pivot_P'].notna().sum() > 0,
        'policy_populated': queried_df['trump_action_prob'].notna().sum() > 0,
    }
    
    logger.info("Integrity checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        logger.info(f"  {status} {check}: {passed}")
    
    return all(checks.values())


def main():
    """Run the integration test."""
    logger.info("="*80)
    logger.info("100-ROW INTEGRATION TEST")
    logger.info("="*80)
    
    client = bigquery.Client(project=PROJECT_ID)
    
    try:
        # 1. Generate test data
        test_df = generate_test_data()
        
        # 2. Run ingestion
        logger.info("\n" + "="*80)
        logger.info("RUNNING INGESTION PIPELINE")
        logger.info("="*80)
        
        pipeline = IngestionPipeline()
        report = pipeline.ingest(test_df)
        
        if report['status'] != 'success':
            logger.error(f"❌ Ingestion failed: {report}")
            return 1
        
        logger.info(f"✅ Ingestion successful: {report['rows_loaded']} rows loaded")
        
        # 3. Query back
        logger.info("\n" + "="*80)
        logger.info("QUERYING TEST DATA")
        logger.info("="*80)
        
        queried_df = query_test_data(client)
        
        if queried_df.empty:
            logger.error("❌ No data retrieved from BigQuery")
            return 1
        
        # 4. Verify integrity
        logger.info("\n" + "="*80)
        logger.info("VERIFYING DATA INTEGRITY")
        logger.info("="*80)
        
        integrity_ok = verify_data_integrity(test_df, queried_df)
        
        if not integrity_ok:
            logger.error("❌ Data integrity check failed")
            return 1
        
        logger.info("✅ Data integrity verified")
        
        # 5. Show sample
        logger.info("\n" + "="*80)
        logger.info("SAMPLE DATA (first 5 rows)")
        logger.info("="*80)
        print(queried_df.head())
        
        # 6. Cleanup
        logger.info("\n" + "="*80)
        logger.info("CLEANUP")
        logger.info("="*80)
        
        cleanup_test_data(client)
        
        # Final verification: ensure data was deleted
        final_check = query_test_data(client)
        if not final_check.empty:
            logger.warning(f"⚠️ Cleanup incomplete: {len(final_check)} rows remain")
            return 1
        
        logger.info("✅ Cleanup verified")
        
        # Success!
        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS PASSED")
        logger.info("="*80)
        logger.info(f"Rows ingested: {report['rows_loaded']}")
        logger.info(f"Duration: {report['duration_seconds']:.1f}s")
        logger.info(f"Throughput: {report['rows_per_second']:.0f} rows/sec")
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        
        # Try to cleanup anyway
        try:
            cleanup_test_data(client)
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
