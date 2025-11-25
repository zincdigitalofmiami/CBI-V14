# 🚀 EXECUTION START - November 24, 2025
**Status:** IN PROGRESS  
**Current Phase:** 0 - Foundation Setup

---

## 📊 CURRENT STATE

### BigQuery Data Present:
| Table | Rows | Date Range |
|-------|------|------------|
| `market_data.databento_futures_ohlcv_1d` | **6,034** | 2010-06-06 → 2025-11-16 |
| - ZL (Soybean Oil) | 3,998 | 2010-06-06 → 2025-11-14 |
| - MES (Micro E-mini) | 2,036 | 2019-05-05 → 2025-11-16 |

### Tables Created (Empty):
- ✅ 19 training tables (ZL + MES horizons)
- ✅ `regime_calendar` (0 rows - **NEEDS POPULATION**)
- ✅ `regime_weights` (0 rows - **NEEDS POPULATION**)

### Scripts Available:
- ✅ `cloud_function_pivot_calculator.py`
- ✅ `build_all_features.py`
- ✅ `ingest_features_hybrid.py`
- ✅ `fetch_fred_economic_data.py`

---

## 🎯 EXECUTION PHASES

### Phase 0: Foundation (NOW) ⬅️ CURRENT
1. **Populate `regime_calendar`** - Define market regimes with dates
2. **Populate `regime_weights`** - Training weights per regime
3. **Verify reference tables**

### Phase 1: Core Data (Today/Tomorrow)
1. Pull FRED data (VIX proxies, rates, BDI)
2. Calculate basic technicals from Databento
3. Run pivot calculator
4. Build `features.daily_ml_matrix`

### Phase 2: Training Tables (Day 2-3)
1. Populate ZL training tables
2. Export to Mac for baseline training
3. Train LightGBM baseline

### Phase 3: Advanced Features (Day 4+)
1. Add remaining Databento symbols (ZS, ZM, CL, HO, FX)
2. Cross-asset correlations
3. Policy/sentiment features

---

## 📋 PHASE 0 EXECUTION

### Step 1: Populate regime_calendar

```sql
-- Insert regime definitions
INSERT INTO `cbi-v14.training.regime_calendar` (date, regime_name, start_date, end_date)
WITH date_spine AS (
    SELECT date
    FROM UNNEST(GENERATE_DATE_ARRAY('2010-01-01', '2029-12-31')) AS date
),
regime_definitions AS (
    SELECT 'pre_crisis_2010_2011' AS regime_name, DATE '2010-01-01' AS start_date, DATE '2011-12-31' AS end_date UNION ALL
    SELECT 'post_crisis_2012_2013', DATE '2012-01-01', DATE '2013-12-31' UNION ALL
    SELECT 'normal_2014_2016', DATE '2014-01-01', DATE '2016-12-31' UNION ALL
    SELECT 'pre_tradewar_2017', DATE '2017-01-01', DATE '2017-12-31' UNION ALL
    SELECT 'tradewar_escalation_2018_2019', DATE '2018-01-01', DATE '2019-12-31' UNION ALL
    SELECT 'covid_shock_2020', DATE '2020-01-01', DATE '2020-12-31' UNION ALL
    SELECT 'recovery_inflation_2021_2022', DATE '2021-01-01', DATE '2022-12-31' UNION ALL
    SELECT 'trump_anticipation_2024', DATE '2023-11-01', DATE '2025-01-19' UNION ALL
    SELECT 'trump_second_term', DATE '2025-01-20', DATE '2029-01-20'
)
SELECT 
    d.date,
    r.regime_name,
    r.start_date,
    r.end_date
FROM date_spine d
JOIN regime_definitions r
    ON d.date BETWEEN r.start_date AND r.end_date
ORDER BY d.date;
```

### Step 2: Populate regime_weights

```sql
-- Insert regime weights
INSERT INTO `cbi-v14.training.regime_weights` (regime_name, training_weight, gating_weight)
VALUES
    ('pre_crisis_2010_2011', 100, 0.5),
    ('post_crisis_2012_2013', 150, 0.6),
    ('normal_2014_2016', 200, 0.7),
    ('pre_tradewar_2017', 250, 0.8),
    ('tradewar_escalation_2018_2019', 400, 1.0),
    ('covid_shock_2020', 350, 0.9),
    ('recovery_inflation_2021_2022', 450, 1.1),
    ('trump_anticipation_2024', 400, 1.0),
    ('trump_second_term', 600, 1.2);
```

---

## ⏰ TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Foundation | 1-2 hours | 🟡 IN PROGRESS |
| Phase 1: Core Data | 4-6 hours | ⏸️ Pending |
| Phase 2: Training Tables | 2-3 hours | ⏸️ Pending |
| Phase 3: Advanced | 1-2 days | ⏸️ Pending |

---

**Next Action:** Run regime_calendar population SQL


