-- 📋 BEST PRACTICES: See `.cursorrules` and `docs/reference/BEST_PRACTICES_DRAFT.md` for mandatory best practices:
--    - No fake data, always check before creating, always audit after work
--    - us-central1 only, no costly resources without approval
--    - Research best practices, research quant finance modeling
--    - Always validate data quality, test queries, verify results

-- ============================================================================
-- UTILS DATASET - UDFs for Technical Indicators
-- ============================================================================

-- Create utils dataset if it doesn't exist
CREATE SCHEMA IF NOT EXISTS utils
OPTIONS (location='us-central1', description='Utility functions and UDFs');

-- ============================================================================
-- UDF 1: EMA (Exponential Moving Average) - JavaScript UDF
-- ============================================================================

CREATE OR REPLACE FUNCTION utils.ema(values ARRAY<FLOAT64>, period INT64)
RETURNS FLOAT64
LANGUAGE js AS """
  if (!values || values.length === 0 || period <= 0) return null;
  
  // EMA calculation: EMA = (Close - EMA_prev) * multiplier + EMA_prev
  // multiplier = 2 / (period + 1)
  const multiplier = 2 / (period + 1);
  let ema = null;
  
  for (let i = 0; i < values.length; i++) {
    if (values[i] === null || values[i] === undefined) continue;
    
    if (ema === null) {
      // Initialize with first value
      ema = values[i];
    } else if (i < period) {
      // Use SMA for first period values
      let sum = 0;
      let count = 0;
      for (let j = 0; j <= i; j++) {
        if (values[j] !== null && values[j] !== undefined) {
          sum += values[j];
          count++;
        }
      }
      ema = sum / count;
    } else {
      // Apply EMA formula
      ema = (values[i] - ema) * multiplier + ema;
    }
  }
  
  return ema;
""";

-- ============================================================================
-- UDF 2: MACD Full (12-26-9) - JavaScript UDF
-- ============================================================================

CREATE OR REPLACE FUNCTION utils.macd_full(
  values ARRAY<FLOAT64>,
  fast_period INT64,
  slow_period INT64,
  signal_period INT64
)
RETURNS STRUCT<
  macd_line FLOAT64,
  signal_line FLOAT64,
  histogram FLOAT64,
  ema_fast FLOAT64,
  ema_slow FLOAT64
>
LANGUAGE js AS """
  if (!values || values.length === 0) {
    return {
      macd_line: null,
      signal_line: null,
      histogram: null,
      ema_fast: null,
      ema_slow: null
    };
  }
  
  // Helper function to calculate EMA
  function calculateEMA(arr, period) {
    if (arr.length === 0 || period <= 0) return null;
    const multiplier = 2 / (period + 1);
    let ema = null;
    
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] === null || arr[i] === undefined) continue;
      
      if (ema === null) {
        ema = arr[i];
      } else if (i < period) {
        let sum = 0;
        let count = 0;
        for (let j = 0; j <= i; j++) {
          if (arr[j] !== null && arr[j] !== undefined) {
            sum += arr[j];
            count++;
          }
        }
        ema = sum / count;
      } else {
        ema = (arr[i] - ema) * multiplier + ema;
      }
    }
    return ema;
  }
  
  // Calculate fast and slow EMAs
  const ema_fast = calculateEMA(values, fast_period);
  const ema_slow = calculateEMA(values, slow_period);
  
  if (ema_fast === null || ema_slow === null) {
    return {
      macd_line: null,
      signal_line: null,
      histogram: null,
      ema_fast: ema_fast,
      ema_slow: ema_slow
    };
  }
  
  // MACD line = EMA_fast - EMA_slow
  const macd_line = ema_fast - ema_slow;
  
  // For signal line, we need MACD values over time
  // Since we only have the final MACD line value, we'll approximate
  // In practice, this should be calculated with window functions in SQL
  const signal_line = null; // Will be calculated in SQL using window functions
  const histogram = macd_line - (signal_line || 0);
  
  return {
    macd_line: macd_line,
    signal_line: signal_line,
    histogram: histogram,
    ema_fast: ema_fast,
    ema_slow: ema_slow
  };
""";

