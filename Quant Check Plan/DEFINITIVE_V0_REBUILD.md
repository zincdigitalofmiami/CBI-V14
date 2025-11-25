# 🔧 DEFINITIVE v0 REBUILD
**Date:** November 24, 2025  
**Author:** Claude (ignoring all conflicting docs)  
**Status:** 🟢 READY FOR EXECUTION

---

## 🎯 WHAT WE'RE BUILDING

**One thing:** A working ZL baseline that proves the pipeline works.

**Nothing else matters until this works.**

---

## 📊 WHAT WE HAVE (VERIFIED)

```
BigQuery Project: cbi-v14

POPULATED:
├── market_data.databento_futures_ohlcv_1d
│   ├── ZL: 3,998 rows (2010-06-06 → 2025-11-14)
│   └── MES: 2,036 rows (2019-05-05 → 2025-11-16)
│   └── Schema: date (DATE), symbol (STRING), open, high, low, close, volume, ...

EMPTY (but schema exists):
├── features.daily_ml_matrix (denormalized, STRUCTs)
├── training.regime_weights
├── training.regime_calendar
└── everything else
```

---

## 🔗 DATAFORM HANDSHAKE REQUIREMENTS

### Date Type Consistency
- **Source:** `market_data.databento_futures_ohlcv_1d.date` → `DATE` type
- **Target:** All tables use `DATE` type (NOT DATETIME, NOT TIMESTAMP for partition key)
- **Partition:** Use `DATE(column)` syntax for partitioning

### Declaration Pattern (Dataform)
```javascript
// definitions/01_declarations/databento_ohlcv.sqlx
config {
  type: "declaration",
  database: "cbi-v14",                    // GCP Project
  schema: "market_data",                  // Dataset
  name: "databento_futures_ohlcv_1d"      // Table
}
// No SQL body for declarations
```

### Incremental Pattern (Dataform)
```javascript
// definitions/02_features/zl_daily_v1.sqlx
config {
  type: "incremental",
  schema: "features",
  bigquery: {
    partitionBy: "trade_date",           // DATE column
    clusterBy: ["symbol", "regime_name"]
  },
  uniqueKey: ["trade_date", "symbol"],   // MERGE key
  tags: ["features", "zl", "v1"]
}

SELECT
  CAST(date AS DATE) AS trade_date,      // Explicit cast for safety
  symbol,
  ...
FROM ${ref("databento_futures_ohlcv_1d")}
WHERE symbol = 'ZL'
```

### Reference Pattern (Dataform)
```javascript
// Use ref() for dependencies - enables lineage
FROM ${ref("databento_futures_ohlcv_1d")}  // ✅ Correct
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`  // ❌ Breaks lineage
```

---

## 🏗️ THE BUILD

### Step 1: Create Regime Lookup Table

**Table:** `training.regime_lookup` (NEW - simple, clean)

**Dataform Definition:**
```javascript
// definitions/00_reference/regime_lookup.sqlx
config {
  type: "table",
  schema: "training",
  description: "Regime definitions with date ranges and training weights",
  tags: ["reference", "regime"]
}

SELECT 
  regime_name,
  CAST(start_date AS DATE) AS start_date,
  CAST(end_date AS DATE) AS end_date,
  weight,
  description
FROM UNNEST([
  STRUCT('pre_trade_war' AS regime_name, DATE '2010-01-01' AS start_date, DATE '2018-02-28' AS end_date, 100 AS weight, 'Normal pre-trade war' AS description),
  STRUCT('trade_war', DATE '2018-03-01', DATE '2019-12-31', 300, 'US-China trade war'),
  STRUCT('covid_crash', DATE '2020-01-01', DATE '2020-05-31', 200, 'COVID crash'),
  STRUCT('covid_recovery', DATE '2020-06-01', DATE '2020-12-31', 200, 'COVID recovery'),
  STRUCT('inflation', DATE '2021-01-01', DATE '2022-12-31', 300, 'High inflation'),
  STRUCT('trump_anticipation', DATE '2023-01-01', DATE '2025-01-19', 400, 'Trump 2.0 anticipation'),
  STRUCT('trump_term', DATE '2025-01-20', DATE '2029-12-31', 600, 'Trump second term')
])
```

**Direct SQL (if not using Dataform):**
```sql
CREATE OR REPLACE TABLE `cbi-v14.training.regime_lookup` (
    regime_name STRING NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    weight INT64 NOT NULL,
    description STRING
);

INSERT INTO `cbi-v14.training.regime_lookup` VALUES
    ('pre_trade_war', DATE '2010-01-01', DATE '2018-02-28', 100, 'Normal pre-trade war'),
    ('trade_war', DATE '2018-03-01', DATE '2019-12-31', 300, 'US-China trade war'),
    ('covid_crash', DATE '2020-01-01', DATE '2020-05-31', 200, 'COVID crash'),
    ('covid_recovery', DATE '2020-06-01', DATE '2020-12-31', 200, 'COVID recovery'),
    ('inflation', DATE '2021-01-01', DATE '2022-12-31', 300, 'High inflation'),
    ('trump_anticipation', DATE '2023-01-01', DATE '2025-01-19', 400, 'Trump 2.0 anticipation'),
    ('trump_term', DATE '2025-01-20', DATE '2029-12-31', 600, 'Trump second term');
```

**Why this design:**
- NO daily rows (avoids partition limits)
- Simple date range lookup
- Uses `DATE` type consistently (not strings)
- Python does the matching at ingestion time
- Easy to modify

---

### Step 2: Create Clean Feature Table

**Table:** `features.zl_daily_v1` (NEW - clean slate)

**Dataform Definition:**
```javascript
// definitions/02_features/zl_daily_v1.sqlx
config {
  type: "table",  // Use "table" for initial creation, "incremental" for updates
  schema: "features",
  bigquery: {
    partitionBy: "trade_date",
    clusterBy: ["symbol", "regime_name"]
  },
  description: "ZL daily features v1 - minimal baseline for first model",
  tags: ["features", "zl", "v1", "baseline"]
}

-- This is the SCHEMA definition
-- Actual data loaded via Python ingestion (not Dataform SQL)
SELECT
  CAST(NULL AS DATE) AS trade_date,
  CAST(NULL AS STRING) AS symbol,
  CAST(NULL AS FLOAT64) AS open,
  CAST(NULL AS FLOAT64) AS high,
  CAST(NULL AS FLOAT64) AS low,
  CAST(NULL AS FLOAT64) AS close,
  CAST(NULL AS INT64) AS volume,
  CAST(NULL AS FLOAT64) AS return_1d,
  CAST(NULL AS FLOAT64) AS return_5d,
  CAST(NULL AS FLOAT64) AS return_21d,
  CAST(NULL AS FLOAT64) AS ma_5,
  CAST(NULL AS FLOAT64) AS ma_21,
  CAST(NULL AS FLOAT64) AS ma_63,
  CAST(NULL AS FLOAT64) AS volatility_21d,
  CAST(NULL AS FLOAT64) AS rsi_14,
  CAST(NULL AS STRING) AS regime_name,
  CAST(NULL AS INT64) AS regime_weight,
  CURRENT_TIMESTAMP() AS ingestion_ts
WHERE FALSE  -- Schema-only, no rows
```

**Direct SQL (if not using Dataform):**
```sql
CREATE OR REPLACE TABLE `cbi-v14.features.zl_daily_v1` (
    -- Identity (DATE type for partition compatibility)
    trade_date DATE NOT NULL,
    symbol STRING NOT NULL,
    
    -- Raw OHLCV (from Databento)
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    
    -- Basic TA (calculated in Python)
    return_1d FLOAT64,
    return_5d FLOAT64,
    return_21d FLOAT64,
    ma_5 FLOAT64,
    ma_21 FLOAT64,
    ma_63 FLOAT64,
    volatility_21d FLOAT64,
    rsi_14 FLOAT64,
    
    -- Regime (stamped at ingestion)
    regime_name STRING,
    regime_weight INT64,
    
    -- Metadata
    ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY trade_date
CLUSTER BY symbol, regime_name
OPTIONS(
    description='ZL daily features v1 - minimal baseline'
);
```

**Why this design:**
- FLAT columns (no STRUCTs for v0 - simpler)
- `DATE` type for partition key (not DATETIME)
- Only what we need for baseline
- Easy to query, easy to debug
- Can migrate to STRUCTs in v2 if needed

---

### Step 3: Python Ingestion Script

**File:** `scripts/ingest_zl_v1.py`

**Key Date Handling:**
- Source `date` column is `DATE` type in BigQuery
- Pandas reads it as `datetime64[ns]` or `object` (date)
- Must ensure proper type conversion for BQ load

```python
"""
ZL v1 Ingestion - Minimal Baseline
Reads Databento OHLCV, calculates basic TA, stamps regime, loads to BQ.

DATE HANDLING:
- BigQuery source: DATE type
- Pandas: datetime64[ns] or date object
- BigQuery target: DATE type (for partitioning)
- Ensure: pd.to_datetime() then .dt.date for DATE columns
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, date

# Config
PROJECT = 'cbi-v14'
SOURCE_TABLE = f'{PROJECT}.market_data.databento_futures_ohlcv_1d'
TARGET_TABLE = f'{PROJECT}.features.zl_daily_v1'
REGIME_TABLE = f'{PROJECT}.training.regime_lookup'

# Regime definitions with proper date objects
REGIMES = [
    ('pre_trade_war', date(2010, 1, 1), date(2018, 2, 28), 100),
    ('trade_war', date(2018, 3, 1), date(2019, 12, 31), 300),
    ('covid_crash', date(2020, 1, 1), date(2020, 5, 31), 200),
    ('covid_recovery', date(2020, 6, 1), date(2020, 12, 31), 200),
    ('inflation', date(2021, 1, 1), date(2022, 12, 31), 300),
    ('trump_anticipation', date(2023, 1, 1), date(2025, 1, 19), 400),
    ('trump_term', date(2025, 1, 20), date(2029, 12, 31), 600),
]

def get_regime(d):
    """
    Lookup regime for a given date.
    
    Args:
        d: Can be datetime64, Timestamp, date, or string
    Returns:
        (regime_name, weight) tuple
    """
    # Normalize to date object for comparison
    if isinstance(d, pd.Timestamp):
        d = d.date()
    elif isinstance(d, str):
        d = datetime.strptime(d, '%Y-%m-%d').date()
    elif hasattr(d, 'date'):
        d = d.date()
    
    for name, start, end, weight in REGIMES:
        if start <= d <= end:
            return name, weight
    return 'unknown', 100

def calculate_ta(df):
    """Calculate basic technical indicators."""
    df = df.sort_values('date').copy()
    
    # Returns
    df['return_1d'] = df['close'].pct_change(1)
    df['return_5d'] = df['close'].pct_change(5)
    df['return_21d'] = df['close'].pct_change(21)
    
    # Moving averages
    df['ma_5'] = df['close'].rolling(5).mean()
    df['ma_21'] = df['close'].rolling(21).mean()
    df['ma_63'] = df['close'].rolling(63).mean()
    
    # Volatility (21-day realized)
    df['volatility_21d'] = df['return_1d'].rolling(21).std() * np.sqrt(252)
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    return df

def main():
    client = bigquery.Client(project=PROJECT)
    
    # 1. Read Databento ZL data
    print("Reading Databento ZL data...")
    query = f"""
        SELECT date, open, high, low, close, volume
        FROM `{SOURCE_TABLE}`
        WHERE symbol = 'ZL'
        ORDER BY date
    """
    df = client.query(query).to_dataframe()
    print(f"  Loaded {len(df)} rows")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Date dtype: {df['date'].dtype}")
    
    # 2. Ensure date column is proper datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # 3. Calculate TA
    print("Calculating technical indicators...")
    df = calculate_ta(df)
    
    # 4. Stamp regime (vectorized for speed)
    print("Stamping regimes...")
    regime_data = df['date'].apply(get_regime)
    df['regime_name'] = regime_data.apply(lambda x: x[0])
    df['regime_weight'] = regime_data.apply(lambda x: x[1])
    
    # 5. Rename and prepare for BQ
    df = df.rename(columns={'date': 'trade_date'})
    df['symbol'] = 'ZL'
    df['ingestion_ts'] = datetime.utcnow()
    
    # 6. Convert trade_date to DATE type for BQ partitioning
    # BigQuery expects date objects, not datetime64
    df['trade_date'] = df['trade_date'].dt.date
    
    # 7. Select only columns we need (in correct order)
    cols = [
        'trade_date', 'symbol', 'open', 'high', 'low', 'close', 'volume',
        'return_1d', 'return_5d', 'return_21d',
        'ma_5', 'ma_21', 'ma_63',
        'volatility_21d', 'rsi_14',
        'regime_name', 'regime_weight', 'ingestion_ts'
    ]
    df = df[cols]
    
    # 8. Drop rows with NaN in critical columns (first ~63 rows)
    before = len(df)
    df = df.dropna(subset=['ma_63', 'volatility_21d', 'rsi_14'])
    print(f"  Dropped {before - len(df)} rows with NaN (warmup period)")
    print(f"  Final row count: {len(df)}")
    
    # 9. Validate before load
    print("\nValidation:")
    print(f"  NULL regime_name: {df['regime_name'].isna().sum()}")
    print(f"  NULL close: {df['close'].isna().sum()}")
    print(f"  Regime distribution:")
    print(df['regime_name'].value_counts())
    
    # 10. Load to BigQuery
    print(f"\nLoading {len(df)} rows to {TARGET_TABLE}...")
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',  # Replace for v0
        # Schema is auto-detected, but we ensure types are correct
    )
    job = client.load_table_from_dataframe(df, TARGET_TABLE, job_config=job_config)
    job.result()
    print("  Done!")
    
    # 11. Verify
    result = client.query(f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNTIF(regime_name IS NULL) as null_regimes,
            COUNTIF(close IS NULL) as null_prices,
            MIN(trade_date) as min_date,
            MAX(trade_date) as max_date
        FROM `{TARGET_TABLE}`
    """).to_dataframe()
    print(f"\nVerification:")
    print(f"  Total rows: {result['total_rows'].iloc[0]}")
    print(f"  NULL regimes: {result['null_regimes'].iloc[0]}")
    print(f"  NULL prices: {result['null_prices'].iloc[0]}")
    print(f"  Date range: {result['min_date'].iloc[0]} to {result['max_date'].iloc[0]}")

if __name__ == '__main__':
    main()
```

**Date Type Summary:**
| Layer | Column | Type | Notes |
|-------|--------|------|-------|
| BQ Source | `date` | `DATE` | Native BQ date |
| Pandas | `date` | `datetime64[ns]` | After pd.to_datetime() |
| Pandas (final) | `trade_date` | `date` | After .dt.date |
| BQ Target | `trade_date` | `DATE` | For partitioning |

---

### Step 4: Training View

**View:** `training.vw_zl_1m_v1`

**Dataform Definition:**
```javascript
// definitions/03_training/vw_zl_1m_v1.sqlx
config {
  type: "view",
  schema: "training",
  description: "ZL 1-month training view - flattened, with targets and splits",
  tags: ["training", "zl", "1m", "v1"]
}

SELECT
    trade_date,
    close,
    return_1d,
    return_5d,
    return_21d,
    ma_5,
    ma_21,
    ma_63,
    volatility_21d,
    rsi_14,
    regime_name,
    regime_weight AS sample_weight,
    
    -- Target: 21 trading days forward return
    SAFE_DIVIDE(
        LEAD(close, 21) OVER (ORDER BY trade_date) - close,
        close
    ) AS target_1m,
    
    -- Direction target
    CASE 
        WHEN LEAD(close, 21) OVER (ORDER BY trade_date) > close THEN 1
        ELSE 0
    END AS target_direction,
    
    -- Simple time split (using DATE comparisons)
    CASE
        WHEN trade_date < DATE '2023-01-01' THEN 'train'
        WHEN trade_date < DATE '2024-01-01' THEN 'val'
        ELSE 'test'
    END AS split

FROM ${ref("zl_daily_v1")}
WHERE 
    -- Exclude last 21 days (no target available)
    trade_date <= DATE_SUB(
        (SELECT MAX(trade_date) FROM ${ref("zl_daily_v1")}),
        INTERVAL 21 DAY
    )
ORDER BY trade_date
```

**Direct SQL (if not using Dataform):**
```sql
CREATE OR REPLACE VIEW `cbi-v14.training.vw_zl_1m_v1` AS
SELECT
    trade_date,
    close,
    return_1d,
    return_5d,
    return_21d,
    ma_5,
    ma_21,
    ma_63,
    volatility_21d,
    rsi_14,
    regime_name,
    regime_weight AS sample_weight,
    
    -- Target: 21 trading days forward return
    SAFE_DIVIDE(
        LEAD(close, 21) OVER (ORDER BY trade_date) - close,
        close
    ) AS target_1m,
    
    -- Direction target
    CASE 
        WHEN LEAD(close, 21) OVER (ORDER BY trade_date) > close THEN 1
        ELSE 0
    END AS target_direction,
    
    -- Simple time split (explicit DATE literals)
    CASE
        WHEN trade_date < DATE '2023-01-01' THEN 'train'
        WHEN trade_date < DATE '2024-01-01' THEN 'val'
        ELSE 'test'
    END AS split

FROM `cbi-v14.features.zl_daily_v1`
WHERE 
    -- Exclude last 21 days (no target available)
    trade_date <= DATE_SUB(
        (SELECT MAX(trade_date) FROM `cbi-v14.features.zl_daily_v1`),
        INTERVAL 21 DAY
    )
ORDER BY trade_date;
```

---

### Step 5: Dataform Assertions (Data Quality Gates)

**Critical:** Run these BEFORE exporting to catch data issues early.

**Dataform Assertion Files:**

```javascript
// definitions/04_assertions/assert_zl_not_null_keys.sqlx
config {
  type: "assertion",
  schema: "features",
  description: "Verify no NULL keys in ZL feature table",
  tags: ["assertion", "critical", "zl"]
}

SELECT trade_date, symbol
FROM ${ref("zl_daily_v1")}
WHERE trade_date IS NULL 
   OR symbol IS NULL
   OR close IS NULL
   OR regime_name IS NULL
```

```javascript
// definitions/04_assertions/assert_zl_unique_key.sqlx
config {
  type: "assertion",
  schema: "features",
  description: "Verify no duplicate (trade_date, symbol) pairs",
  tags: ["assertion", "critical", "zl"]
}

SELECT trade_date, symbol, COUNT(*) as cnt
FROM ${ref("zl_daily_v1")}
GROUP BY 1, 2
HAVING COUNT(*) > 1
```

```javascript
// definitions/04_assertions/assert_zl_row_count.sqlx
config {
  type: "assertion",
  schema: "features",
  description: "Verify minimum row count (should be ~3700+)",
  tags: ["assertion", "critical", "zl"]
}

SELECT 1
WHERE (SELECT COUNT(*) FROM ${ref("zl_daily_v1")}) < 3500
```

```javascript
// definitions/04_assertions/assert_zl_price_sanity.sqlx
config {
  type: "assertion",
  schema: "features",
  description: "Verify price values are sane (ZL trades ~20-80 cents/lb)",
  tags: ["assertion", "sanity", "zl"]
}

SELECT trade_date, close
FROM ${ref("zl_daily_v1")}
WHERE close <= 0 
   OR close > 150  -- ZL never traded above 100 cents/lb historically
```

```javascript
// definitions/04_assertions/assert_zl_rsi_range.sqlx
config {
  type: "assertion",
  schema: "features",
  description: "Verify RSI is in valid range [0, 100]",
  tags: ["assertion", "sanity", "zl"]
}

SELECT trade_date, rsi_14
FROM ${ref("zl_daily_v1")}
WHERE rsi_14 < 0 
   OR rsi_14 > 100
```

```javascript
// definitions/04_assertions/assert_regime_coverage.sqlx
config {
  type: "assertion",
  schema: "training",
  description: "Verify all dates have regime coverage (no gaps)",
  tags: ["assertion", "critical", "regime"]
}

WITH date_range AS (
  SELECT MIN(trade_date) AS min_date, MAX(trade_date) AS max_date
  FROM ${ref("zl_daily_v1")}
),
expected_regimes AS (
  SELECT r.regime_name, r.start_date, r.end_date
  FROM ${ref("regime_lookup")} r, date_range d
  WHERE r.start_date <= d.max_date AND r.end_date >= d.min_date
)
SELECT trade_date
FROM ${ref("zl_daily_v1")} f
WHERE NOT EXISTS (
  SELECT 1 FROM expected_regimes r
  WHERE f.trade_date BETWEEN r.start_date AND r.end_date
)
```

**Run Assertions:**
```bash
# Dataform CLI
dataform test --tags assertion

# Or run all
dataform run --include-deps --tags assertion
```

---

### Step 5b: Direct SQL Assertions (if not using Dataform)

**Run these before exporting:**

```sql
-- Assertion 1: Row count
SELECT 'row_count' AS check, COUNT(*) AS value 
FROM `cbi-v14.features.zl_daily_v1`
WHERE value >= 3700;  -- Should be ~3,935 (3,998 - 63 warmup)

-- Assertion 2: No NULL regimes
SELECT 'null_regimes' AS check, COUNTIF(regime_name IS NULL) AS value 
FROM `cbi-v14.features.zl_daily_v1`
WHERE value = 0;

-- Assertion 3: No NULL prices
SELECT 'null_prices' AS check, COUNTIF(close IS NULL) AS value 
FROM `cbi-v14.features.zl_daily_v1`
WHERE value = 0;

-- Assertion 4: Price sanity
SELECT 'price_range' AS check, 
       MIN(close) AS min_price, 
       MAX(close) AS max_price
FROM `cbi-v14.features.zl_daily_v1`
WHERE min_price > 0 AND max_price < 100;  -- ZL trades in cents/lb

-- Assertion 5: RSI sanity
SELECT 'rsi_range' AS check,
       MIN(rsi_14) AS min_rsi,
       MAX(rsi_14) AS max_rsi
FROM `cbi-v14.features.zl_daily_v1`
WHERE min_rsi >= 0 AND max_rsi <= 100;

-- Assertion 6: Training view has targets
SELECT 'training_rows' AS check, COUNT(*) AS value
FROM `cbi-v14.training.vw_zl_1m_v1`
WHERE target_1m IS NOT NULL;  -- Should be ~3,600+
```

---

### Step 6: Export & Train

**Export:**
```bash
bq extract \
    --destination_format=CSV \
    --field_delimiter=',' \
    'cbi-v14:training.vw_zl_1m_v1' \
    gs://cbi-v14-exports/zl_training_1m_v1.csv
```

**Or direct Python export:**
```python
query = "SELECT * FROM `cbi-v14.training.vw_zl_1m_v1`"
df = client.query(query).to_dataframe()
df.to_csv('zl_training_1m_v1.csv', index=False)
```

**Train:**
```python
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit

# Load
df = pd.read_csv('zl_training_1m_v1.csv')
df = df[df['split'] == 'train']

# Features
features = [
    'return_1d', 'return_5d', 'return_21d',
    'ma_5', 'ma_21', 'ma_63',
    'volatility_21d', 'rsi_14'
]
X = df[features]
y = df['target_1m']
weights = df['sample_weight']

# Train with time series CV
tscv = TimeSeriesSplit(n_splits=5)
params = {
    'objective': 'regression',
    'metric': 'mae',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'verbose': -1
}

for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    w_train = weights.iloc[train_idx]
    
    train_data = lgb.Dataset(X_train, label=y_train, weight=w_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, val_data],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
    )
    
    print(f"Fold {fold+1}: MAE = {model.best_score['valid_1']['l1']:.4f}")

# Feature importance
print("\nFeature Importance:")
for name, imp in sorted(zip(features, model.feature_importance()), key=lambda x: -x[1]):
    print(f"  {name}: {imp}")
```

---

## 📁 DATAFORM PROJECT STRUCTURE

```
dataform/
├── dataform.json                    # Project config
├── definitions/
│   ├── 00_declarations/
│   │   └── databento_ohlcv.sqlx     # Source declaration
│   ├── 01_reference/
│   │   └── regime_lookup.sqlx       # Regime definitions
│   ├── 02_features/
│   │   └── zl_daily_v1.sqlx         # Feature table (schema only)
│   ├── 03_training/
│   │   └── vw_zl_1m_v1.sqlx         # Training view
│   └── 04_assertions/
│       ├── assert_zl_not_null.sqlx
│       ├── assert_zl_unique.sqlx
│       ├── assert_zl_row_count.sqlx
│       ├── assert_zl_price_sanity.sqlx
│       ├── assert_zl_rsi_range.sqlx
│       └── assert_regime_coverage.sqlx
├── includes/
│   └── constants.js                  # Shared constants
└── package.json
```

**dataform.json:**
```json
{
  "warehouse": "bigquery",
  "defaultSchema": "features",
  "defaultDatabase": "cbi-v14",
  "defaultLocation": "us-central1",
  "vars": {
    "market_data": "market_data",
    "features": "features",
    "training": "training",
    "reference": "training"
  }
}
```

**includes/constants.js:**
```javascript
const REGIMES = [
  { name: 'pre_trade_war', start: '2010-01-01', end: '2018-02-28', weight: 100 },
  { name: 'trade_war', start: '2018-03-01', end: '2019-12-31', weight: 300 },
  { name: 'covid_crash', start: '2020-01-01', end: '2020-05-31', weight: 200 },
  { name: 'covid_recovery', start: '2020-06-01', end: '2020-12-31', weight: 200 },
  { name: 'inflation', start: '2021-01-01', end: '2022-12-31', weight: 300 },
  { name: 'trump_anticipation', start: '2023-01-01', end: '2025-01-19', weight: 400 },
  { name: 'trump_term', start: '2025-01-20', end: '2029-12-31', weight: 600 },
];

module.exports = { REGIMES };
```

---

## 📋 EXECUTION ORDER

### Option A: Using Dataform

```bash
# 1. Initialize Dataform (if not exists)
cd /Users/zincdigital/CBI-V14/dataform
dataform init

# 2. Run reference tables first
dataform run --tags reference

# 3. Run feature schema creation
dataform run --tags features

# 4. Run Python ingestion (outside Dataform)
python scripts/ingest_zl_v1.py

# 5. Run assertions
dataform test

# 6. Run training views
dataform run --tags training

# 7. Export and train (Mac)
python scripts/export_and_train.py
```

### Option B: Direct SQL (No Dataform)

```
1. Create regime_lookup table (5 min)
   └── bq query --use_legacy_sql=false < sql/create_regime_lookup.sql

2. Create zl_daily_v1 table (5 min)
   └── bq query --use_legacy_sql=false < sql/create_zl_daily_v1.sql

3. Run Python ingestion (10 min)
   └── python scripts/ingest_zl_v1.py

4. Run assertions (5 min)
   └── bq query --use_legacy_sql=false < sql/assertions.sql

5. Create training view (5 min)
   └── bq query --use_legacy_sql=false < sql/create_training_view.sql

6. Export to CSV (5 min)
   └── Python or bq extract

7. Train baseline (30 min)
   └── python scripts/train_baseline.py

TOTAL: ~1 hour
```

---

## ✅ SUCCESS CRITERIA

| Check | Target |
|-------|--------|
| `features.zl_daily_v1` rows | ≥ 3,700 |
| NULL regime_name | 0 |
| NULL close | 0 |
| Training view rows with target | ≥ 3,600 |
| LightGBM trains without error | ✅ |
| CV folds don't blow up | ✅ |
| Feature importances sensible | ✅ |

---

## 🚫 WHAT WE'RE NOT DOING

- ❌ Using existing `features.daily_ml_matrix` (too complex)
- ❌ Using STRUCTs (v2)
- ❌ Using `training.regime_calendar` (partition issues)
- ❌ Adding VIX (v1.5)
- ❌ Adding FRED (v2)
- ❌ Adding weather (v2.5)
- ❌ Adding Trump features (v3)
- ❌ Adding MES (v4)
- ❌ Caring about MAE (v0 is about pipeline, not performance)

---

## 🔄 UPGRADE PATH

| Version | What to Add | How |
|---------|-------------|-----|
| v1 | Pivots | Add columns, update Python |
| v1.5 | VIX | Load to raw_intelligence, join in Python |
| v2 | FRED macro | Same pattern |
| v2.5 | Weather | Same pattern |
| v3 | Trump features | Same pattern |
| v4 | MES | Duplicate pipeline for MES |
| v5 | STRUCTs | Migrate to daily_ml_matrix if needed |

Each version:
1. Add columns to `features.zl_daily_v1`
2. Update Python ingestion
3. Update training view
4. Retrain
5. Measure impact

---

## 🎯 THIS IS THE WAY

No more docs. No more conflicts. Just:

1. **One regime table** (simple date ranges)
2. **One feature table** (flat, clean)
3. **One training view** (zero joins)
4. **One Python script** (does everything)
5. **One baseline model** (proves it works)

**Execute this, then iterate.**

