CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.

---

# Day 1 Execution Packet — November 21, 2025
Status: 🟢 AUTHORIZED TO EXECUTE (Option A: Full Denormalized Architecture)
Owners: Kirk (executor), Codex/Sonnet (support), Gemini (validated)

## Scope (Day 1, 4–6 hours)
- Regime split → canonical sources updated
- Create denormalized table
- Handshake test (producer ↔ schema)
- Documentation touch-ups

## 1) Regime Updates (canonical source)
Edit `registry/regime_weights.yaml`:
```
trump_return_2024_2025:  # ❌ REMOVE
  ...

trump_anticipation_2024:
  start_date: '2023-11-01'
  end_date: '2025-01-19'
  weight: 400
  description: Trump 2.0 anticipation - market pricing expected tariff/trade policies

trump_second_term:
  start_date: '2025-01-20'
  end_date: '2029-01-20'
  weight: 600
  description: Trump second presidential term - active tariff/trade/biofuel policy regime
```

## 2) Regime calendar (BigQuery)
Insert/replace rows in `training.regime_calendar`:
```
INSERT INTO training.regime_calendar (regime, weight, start_date, end_date, description) VALUES
('trump_anticipation_2024', 400, DATE '2023-11-01', DATE '2025-01-19', 'Trump 2.0 anticipation'),
('trump_second_term',       600, DATE '2025-01-20', DATE '2029-01-20', 'Trump second term');
```

Gap-check SQL (expect gap_days = 1):
```
SELECT regime, start_date, end_date,
       LEAD(start_date) OVER (ORDER BY start_date) AS next_start,
       DATE_DIFF(LEAD(start_date) OVER (ORDER BY start_date), end_date, DAY) AS gap_days
FROM training.regime_calendar
WHERE regime LIKE 'trump_%'
ORDER BY start_date;
```

## 3) Create denormalized table (run DDL)
```
CREATE TABLE IF NOT EXISTS features.daily_ml_matrix (
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
    distance_to_nearest FLOAT64,
    weekly_P_distance FLOAT64,
    is_above_P BOOL
  >,

  policy STRUCT<
    trump_action_prob FLOAT64,
    trump_score FLOAT64,
    trump_sentiment_7d FLOAT64,
    trump_tariff_intensity FLOAT64,
    is_shock_regime BOOL
  >,

  golden_zone STRUCT<
    state INT64,             -- 0=out, 1=in zone, 2=deep
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
CLUSTER BY symbol, regime.name
OPTIONS (description = 'Master ML Feature Matrix. Denormalized. 1-Hour Micro-Batch. Phase 1.');
```

## 4) Producer ↔ schema handshake (pivots)
- Ensure `cloud_function_pivot_calculator.py` outputs exactly:
  `P, R1, R2, S1, S2, distance_to_P, distance_to_nearest, weekly_P_distance, is_above_P`
- 1-row test (pseudo):
```
sample = producer_output_one_row()
schema_keys = {"P","R1","R2","S1","S2","distance_to_P","distance_to_nearest","weekly_P_distance","is_above_P"}
assert set(sample.keys()) == schema_keys
```

## 5) Verify partitioning/clustering
- Confirm table options: PARTITION BY data_date; CLUSTER BY symbol, regime.name.

## 6) Documentation
- Note Day 1 completion in QUAD_CHECK and schema notes (brief).

## Completion checklist (Day 1)
- [ ] regime_weights.yaml updated
- [ ] training.regime_calendar updated
- [ ] Gap-check SQL = gap_days 1
- [ ] features.daily_ml_matrix created (partition/cluster verified)
- [ ] Pivot producer outputs match STRUCT keys (1-row test pass)
- [ ] Docs touched (noting Day 1 complete)

End of Day 1 Packet.
