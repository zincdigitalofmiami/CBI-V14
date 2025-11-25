# ✅ DATAFORM HANDSHAKE CHECKLIST
**Date:** November 24, 2025  
**Purpose:** Quick reference for date types and Dataform patterns

---

## 📅 DATE TYPE RULES

### BigQuery Types
| Type | Use For | Partition? | Notes |
|------|---------|------------|-------|
| `DATE` | Trade dates, calendar dates | ✅ YES | Preferred for daily data |
| `DATETIME` | Timestamps without timezone | ❌ Avoid | Use TIMESTAMP instead |
| `TIMESTAMP` | Exact moments (ingestion_ts) | ✅ YES | With timezone |

### Our Schema
| Table | Column | Type | Partition Key? |
|-------|--------|------|----------------|
| `databento_futures_ohlcv_1d` | `date` | `DATE` | ✅ |
| `features.zl_daily_v1` | `trade_date` | `DATE` | ✅ |
| `training.regime_lookup` | `start_date`, `end_date` | `DATE` | ❌ |
| `training.vw_zl_1m_v1` | `trade_date` | `DATE` | N/A (view) |

### Python → BigQuery Date Handling
```python
# Source: datetime64[ns] from BQ query
df['date'] = pd.to_datetime(df['date'])

# Target: date object for BQ DATE column
df['trade_date'] = df['date'].dt.date

# DO NOT: Keep as datetime64 for DATE partition columns
# df['trade_date'] = df['date']  # ❌ May cause type mismatch
```

---

## 🔗 DATAFORM PATTERNS

### 1. Declaration (Source Tables)
```javascript
config {
  type: "declaration",
  database: "cbi-v14",           // GCP Project (NOT dataset!)
  schema: "market_data",         // Dataset
  name: "databento_futures_ohlcv_1d"
}
// NO SQL body
```

### 2. Table with Partitioning
```javascript
config {
  type: "table",
  schema: "features",
  bigquery: {
    partitionBy: "trade_date",   // Column name, DATE type
    clusterBy: ["symbol", "regime_name"]
  },
  tags: ["features"]
}
```

### 3. Incremental with MERGE
```javascript
config {
  type: "incremental",
  schema: "features",
  uniqueKey: ["trade_date", "symbol"],  // MERGE key
  bigquery: {
    partitionBy: "trade_date",
    clusterBy: ["symbol"]
  }
}

SELECT ...
FROM ${ref("source_table")}
// NO WHERE clause needed - MERGE handles updates
```

### 4. View
```javascript
config {
  type: "view",
  schema: "training",
  tags: ["training"]
}

SELECT ...
FROM ${ref("zl_daily_v1")}  // Use ref() for lineage
```

### 5. Assertion
```javascript
config {
  type: "assertion",
  schema: "features",
  tags: ["assertion", "critical"]
}

// Return rows that FAIL the assertion
SELECT trade_date, symbol
FROM ${ref("zl_daily_v1")}
WHERE trade_date IS NULL  // These rows are BAD
```

---

## ⚠️ COMMON MISTAKES

### ❌ Wrong: database/schema swapped
```javascript
config {
  database: "market_data",  // ❌ This is the dataset!
  schema: "cbi-v14",        // ❌ This is the project!
}
```

### ✅ Correct: database = project, schema = dataset
```javascript
config {
  database: "cbi-v14",      // ✅ GCP Project
  schema: "market_data",    // ✅ Dataset
}
```

### ❌ Wrong: Hardcoded table reference
```javascript
FROM `cbi-v14.market_data.databento_futures_ohlcv_1d`  // ❌ Breaks lineage
```

### ✅ Correct: Use ref()
```javascript
FROM ${ref("databento_futures_ohlcv_1d")}  // ✅ Enables lineage
```

### ❌ Wrong: MAX(date) for incremental
```javascript
WHERE date > (SELECT MAX(date) FROM ${self()})  // ❌ Misses late data
```

### ✅ Correct: uniqueKey for MERGE
```javascript
config {
  uniqueKey: ["date", "symbol"]  // ✅ Handles late/repair data
}
// No WHERE clause needed
```

### ❌ Wrong: DATETIME for partition key
```javascript
partitionBy: "DATETIME(trade_date)"  // ❌ Use DATE
```

### ✅ Correct: DATE for partition key
```javascript
partitionBy: "trade_date"  // ✅ Assumes DATE type column
```

---

## 🧪 DATE COMPARISON IN SQL

### ✅ Correct: DATE literals
```sql
WHERE trade_date < DATE '2023-01-01'
WHERE trade_date BETWEEN DATE '2020-01-01' AND DATE '2020-12-31'
```

### ❌ Wrong: String comparison (works but risky)
```sql
WHERE trade_date < '2023-01-01'  -- Implicit cast, may fail
```

### ✅ Correct: DATE functions
```sql
WHERE trade_date <= DATE_SUB(CURRENT_DATE(), INTERVAL 21 DAY)
WHERE trade_date >= DATE_ADD(start_date, INTERVAL 1 MONTH)
```

---

## 📋 PRE-EXECUTION CHECKLIST

Before running Dataform:

- [ ] All `DATE` columns are `DATE` type (not DATETIME)
- [ ] Declarations use `database: "cbi-v14"` (project)
- [ ] Declarations use `schema: "dataset_name"` (dataset)
- [ ] All table references use `${ref("table_name")}`
- [ ] Incremental tables have `uniqueKey` defined
- [ ] Partition columns are `DATE` type
- [ ] Python ingestion converts to `.dt.date` before load
- [ ] Date literals use `DATE 'YYYY-MM-DD'` syntax
- [ ] Assertions return failing rows (not passing)

---

## 🔄 REGIME LOOKUP PATTERN

### In Dataform (regime_lookup table)
```sql
SELECT 
  regime_name,
  CAST(start_date AS DATE) AS start_date,
  CAST(end_date AS DATE) AS end_date,
  weight
FROM UNNEST([
  STRUCT('pre_trade_war' AS regime_name, DATE '2010-01-01' AS start_date, ...)
])
```

### In Python (stamping regime)
```python
from datetime import date

REGIMES = [
    ('pre_trade_war', date(2010, 1, 1), date(2018, 2, 28), 100),
    ...
]

def get_regime(d):
    if isinstance(d, pd.Timestamp):
        d = d.date()
    for name, start, end, weight in REGIMES:
        if start <= d <= end:
            return name, weight
    return 'unknown', 100
```

### Joining (if needed in SQL)
```sql
SELECT f.*, r.regime_name, r.weight
FROM features.zl_daily_v1 f
LEFT JOIN training.regime_lookup r
  ON f.trade_date BETWEEN r.start_date AND r.end_date
```

**But we stamp at ingestion, so this join is NOT needed at query time.**

---

**This checklist ensures all handshakes are correct before execution.**

