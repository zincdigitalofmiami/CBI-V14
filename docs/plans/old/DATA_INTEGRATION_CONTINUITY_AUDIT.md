# DATA INTEGRATION CONTINUITY AUDIT

**Date**: 2025-01-XX  
**Purpose**: Reverse engineer all data integration areas for continuity verification

## EXECUTIVE SUMMARY

This audit documents all data sources, intermediate tables, and final training dataset connections to ensure complete continuity across the CBI-V14 forecasting pipeline.

---

## 1. SOURCE DATA INVENTORY

### 1.1 Source Tables (forecasting_data_warehouse)

| Source Table | Records | Unique Dates | Date Range | Status |
|-------------|---------|--------------|------------|--------|
| `news_intelligence` | 2,705 | 17 | 2025-10-04 to 2025-10-30 | ⚠️ Limited (recent only) |
| `cftc_cot` | 72 | 60 | 2024-08-06 to 2025-09-23 | ⚠️ Limited (recent only) |
| `social_sentiment` | 653 | ~653 | Various | ✅ Active |
| `trump_policy_intelligence` | 215 | ~215 | Various | ✅ Active |
| `usda_export_sales` | Unknown | Weekly | Various | ✅ Active |
| `currency_data` | Unknown | Daily | Various | ✅ Active |
| `palm_oil_prices` | 1,278 | Daily | Various | ✅ Active |
| `yahoo_finance_enhanced` | Unknown | Daily | 2020-01-02+ | ✅ Active |

### 1.2 Key Column Mappings

**News Intelligence:**
- Source: `published` (TIMESTAMP) → Target: `date` (DATE)
- Source: `intelligence_score` → Target: `news_avg_score`
- Source: `title`, `content` → Target: `china_news_count`, `biofuel_news_count`, etc.

**CFTC:**
- Source: `report_date` → Target: `date` (DATE)
- Source: `commercial_long`, `commercial_short` → Target: `cftc_commercial_long`, `cftc_commercial_short`
- Source: `managed_money_long`, `managed_money_short` → Target: `cftc_managed_long`, `cftc_managed_short`
- Forward-fill: Weekly → Daily using `LAST_VALUE() OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`

**Palm Oil:**
- Primary: `yahoo_finance_enhanced` WHERE `symbol = 'FCPO=F'`
- Fallback: `palm_oil_prices` table (uses `time` column, converted to DATE)
- Target: `palm_price`, `palm_volume` (if exists)

**Currency:**
- Source: `currency_data` with `from_currency` and `to_currency`
- Normalization: USD/CNY, USD/BRL, USD/ARS, USD/MYR
- Target: `usd_cny_rate`, `usd_brl_rate`, `usd_ars_rate`, `usd_myr_rate`

---

## 2. INTERMEDIATE TABLES (models_v4)

### 2.1 Daily Aggregation Tables

| Table Name | Purpose | Records | Date Range | Status |
|-----------|---------|---------|------------|--------|
| `news_intelligence_daily` | Daily news aggregation | 17 | 2025-10-04 to 2025-10-30 | ✅ Created |
| `cftc_daily_filled` | CFTC weekly → daily forward-fill | 2,043 | 2020-01-02 to 2025-11-03 | ✅ Created |
| `palm_oil_complete` | Palm oil with forward-fill | ~1,400+ | 2020-01-02+ | ✅ Created |
| `social_sentiment_daily` | Social sentiment daily aggregation | ~653 | Various | ✅ Created |
| `trump_policy_daily` | Trump policy daily aggregation | ~215 | Various | ✅ Created |
| `usda_export_daily` | USDA export weekly → daily | Unknown | Various | ✅ Created |
| `currency_complete` | Currency pairs normalized | Unknown | Various | ✅ Created |

### 2.2 Intermediate Table Schema Verification

**news_intelligence_daily:**
- `date` (DATE)
- `news_article_count` (INT64)
- `news_avg_score` (FLOAT64)
- `news_sentiment_avg` (FLOAT64)
- `china_news_count`, `biofuel_news_count`, `tariff_news_count`, `weather_news_count` (INT64)
- `news_intelligence_7d`, `news_volume_7d` (FLOAT64, INT64)

**cftc_daily_filled:**
- `date` (DATE)
- `cftc_commercial_long`, `cftc_commercial_short` (FLOAT64)
- `cftc_managed_long`, `cftc_managed_short` (FLOAT64)
- `cftc_open_interest` (FLOAT64)
- `cftc_commercial_net`, `cftc_managed_net` (FLOAT64)
- `cftc_commercial_extreme`, `cftc_spec_extreme` (FLOAT64)

**palm_oil_complete:**
- `date` (DATE)
- `palm_price_filled` (FLOAT64)
- `palm_volume_filled` (FLOAT64, nullable)
- `palm_source` (STRING)

---

## 3. TRAINING DATASET INTEGRATION

### 3.1 MERGE Operations

**MERGE Statement Pattern:**
```sql
MERGE `cbi-v14.models_v4.training_dataset_super_enriched` AS target
USING (SELECT ... FROM intermediate_table) AS source
ON target.date = source.date
WHEN MATCHED THEN UPDATE SET
  column_name = COALESCE(target.column_name, source.column_name)
```

**Completed MERGEs:**
1. ✅ News Intelligence → `news_article_count`, `news_avg_score`
2. ✅ CFTC Data → `cftc_commercial_long`, `cftc_commercial_short`, `cftc_managed_long`, `cftc_managed_short`, `cftc_open_interest`, `cftc_commercial_net`, `cftc_managed_net`
3. ✅ Palm Oil → `palm_price` (palm_volume column doesn't exist in target)
4. ✅ Currency → `usd_cny_rate`, `usd_brl_rate`, `usd_ars_rate`, `usd_myr_rate`

### 3.2 Training Dataset Coverage

| Column | Total Rows | Non-NULL Rows | Coverage % | Status |
|--------|------------|---------------|------------|--------|
| `news_article_count` | 1,448 | 4 | 0.3% | ⚠️ Limited (date range mismatch) |
| `cftc_commercial_long` | 1,448 | 298 | 20.6% | ⚠️ Limited (data starts Aug 2024) |
| `palm_price` | 1,448 | 1,433 | 99.0% | ✅ Excellent |
| `usd_cny_rate` | 1,448 | 1,448 | 100.0% | ✅ Complete |
| `usd_brl_rate` | 1,448 | 1,448 | 100.0% | ✅ Complete |
| `usd_ars_rate` | 1,448 | Unknown | Unknown | ⚠️ Needs verification |
| `usd_myr_rate` | 1,448 | Unknown | Unknown | ⚠️ Needs verification |

---

## 4. CONTINUITY GAPS IDENTIFIED

### 4.1 Date Range Mismatches

**Issue 1: News Intelligence Limited Coverage**
- **Source Data**: 2025-10-04 to 2025-10-30 (17 dates)
- **Training Data**: 2020-01-02 to 2025-10-13 (1,448 dates)
- **Overlap**: Only 4 dates (Oct 4-7, 2025)
- **Impact**: 0.3% coverage (4/1,448 rows)
- **Root Cause**: News data ingestion started very recently (Oct 2025)
- **Solution**: Historical news data needed for full coverage

**Issue 2: CFTC Data Limited Coverage**
- **Source Data**: 2024-08-06 to 2025-09-23 (60 weekly reports)
- **Training Data**: 2020-01-02 to 2025-10-13 (1,448 dates)
- **Forward-Fill Coverage**: 455 rows filled (20.6%)
- **Impact**: Data exists for Aug 2024+ but forward-fill cannot go backwards
- **Root Cause**: CFTC data ingestion started Aug 2024
- **Solution**: Historical CFTC data needed for full coverage

### 4.2 Missing Column Mappings

**Columns Created but Not Merged:**
- `social_sentiment_avg`, `social_sentiment_volatility`, `social_post_count`, `bullish_ratio`, `bearish_ratio`, `social_sentiment_7d`, `social_volume_7d` (from `social_sentiment_daily`)
- `trump_policy_events`, `trump_policy_impact_avg`, `trump_policy_impact_max`, `trade_policy_events`, `china_policy_events`, `ag_policy_events`, `trump_policy_7d`, `trump_events_7d` (from `trump_policy_daily`)
- `soybean_weekly_sales`, `soybean_oil_weekly_sales`, `soybean_meal_weekly_sales`, `china_soybean_sales` (from `usda_export_daily`)
- `news_sentiment_avg`, `china_news_count`, `biofuel_news_count`, `tariff_news_count`, `weather_news_count`, `news_intelligence_7d`, `news_volume_7d` (from `news_intelligence_daily`)
- `cftc_commercial_extreme`, `cftc_spec_extreme` (from `cftc_daily_filled`)

**Reason**: These columns may not exist in `training_dataset_super_enriched` schema, or MERGE was simplified to only update existing columns.

---

## 5. DATA PIPELINE FLOW

### 5.1 Complete Data Flow Diagram

```
SOURCE TABLES (forecasting_data_warehouse)
  │
  ├─→ news_intelligence
  │     │
  │     └─→ news_intelligence_daily (daily aggregation)
  │           │
  │           └─→ MERGE → training_dataset_super_enriched
  │
  ├─→ cftc_cot
  │     │
  │     └─→ cftc_daily_filled (weekly → daily forward-fill)
  │           │
  │           └─→ MERGE → training_dataset_super_enriched
  │
  ├─→ yahoo_finance_enhanced (FCPO=F)
  │     │
  ├─→ palm_oil_prices
  │     │
  │     └─→ palm_oil_complete (combined sources + forward-fill)
  │           │
  │           └─→ MERGE → training_dataset_super_enriched
  │
  ├─→ currency_data
  │     │
  │     └─→ currency_complete (normalized pairs)
  │           │
  │           └─→ MERGE → training_dataset_super_enriched
  │
  ├─→ social_sentiment
  │     │
  │     └─→ social_sentiment_daily (daily aggregation)
  │           │
  │           └─→ [NOT MERGED - columns may not exist]
  │
  ├─→ trump_policy_intelligence
  │     │
  │     └─→ trump_policy_daily (daily aggregation)
  │           │
  │           └─→ [NOT MERGED - columns may not exist]
  │
  └─→ usda_export_sales
        │
        └─→ usda_export_daily (weekly → daily)
              │
              └─→ [NOT MERGED - columns may not exist]
```

### 5.2 Pipeline Integrity

**✅ Verified:**
- Source tables exist and have data
- Intermediate tables created successfully
- MERGE operations completed without errors
- Date joins work correctly (ON target.date = source.date)

**⚠️ Needs Verification:**
- Social sentiment columns in training dataset
- Trump policy columns in training dataset
- USDA export columns in training dataset
- All news intelligence derived columns
- CFTC percentile columns

---

## 6. RECOMMENDATIONS

### 6.1 Immediate Actions

1. **Verify Column Existence**
   - Check if social sentiment, Trump policy, and USDA columns exist in `training_dataset_super_enriched`
   - If they exist, complete the MERGE operations
   - If they don't exist, add them to the schema first

2. **Complete Missing MERGEs**
   - Merge `social_sentiment_daily` → training dataset
   - Merge `trump_policy_daily` → training dataset
   - Merge `usda_export_daily` → training dataset
   - Merge all news intelligence derived columns
   - Merge CFTC percentile columns

3. **Historical Data Backfill**
   - Fetch historical news data (2020-2025)
   - Fetch historical CFTC data (2020-2024)
   - This will dramatically improve coverage

### 6.2 Long-Term Improvements

1. **Automated Pipeline**
   - Create scheduled jobs to update intermediate tables daily
   - Automate MERGE operations after data ingestion
   - Add monitoring/alerting for data quality issues

2. **Data Quality Checks**
   - Add validation queries to ensure continuity
   - Monitor coverage percentages over time
   - Alert when coverage drops below thresholds

3. **Documentation**
   - Maintain this continuity audit document
   - Document all schema changes
   - Track all MERGE operations

---

## 7. CONTINUITY VERIFICATION QUERIES

### 7.1 Source → Intermediate Verification

```sql
-- Verify news_intelligence_daily has all expected dates
SELECT COUNT(*) as records, MIN(date) as earliest, MAX(date) as latest
FROM `cbi-v14.models_v4.news_intelligence_daily`;

-- Verify cftc_daily_filled forward-fill worked
SELECT date, cftc_commercial_long, 
       LAG(cftc_commercial_long) OVER (ORDER BY date) as prev_value
FROM `cbi-v14.models_v4.cftc_daily_filled`
WHERE date BETWEEN '2024-08-06' AND '2024-08-13'
ORDER BY date;
```

### 7.2 Intermediate → Training Verification

```sql
-- Verify MERGE worked for CFTC
SELECT COUNT(*) as total_rows,
       COUNTIF(cftc_commercial_long IS NOT NULL) as cftc_filled,
       ROUND(COUNTIF(cftc_commercial_long IS NOT NULL) / COUNT(*) * 100, 1) as coverage_pct
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL;

-- Verify date continuity
SELECT date, 
       news_article_count, cftc_commercial_long, palm_price,
       CASE WHEN news_article_count IS NULL AND cftc_commercial_long IS NULL AND palm_price IS NULL 
            THEN 'ALL_MISSING' 
            WHEN news_article_count IS NULL OR cftc_commercial_long IS NULL OR palm_price IS NULL
            THEN 'PARTIAL'
            ELSE 'COMPLETE' END as data_status
FROM `cbi-v14.models_v4.training_dataset_super_enriched`
WHERE target_1w IS NOT NULL
ORDER BY date DESC
LIMIT 20;
```

---

## 8. CONCLUSION

**Current Status**: Partial Integration Complete
- ✅ Pipeline structure created
- ✅ Core data sources integrated (CFTC, Palm Oil, Currency)
- ⚠️ Limited coverage due to recent data ingestion start dates
- ⚠️ Some intermediate tables not yet merged to training dataset

**Next Steps**: Complete missing MERGEs and backfill historical data for full coverage.


