# Deduplication Rules

**Date**: November 13, 2025  
**Project**: CBI-V14 Soybean Oil Forecasting Platform  
**Version**: 1.0

## Overview

This document defines rules for handling duplicate data across multiple sources during the BigQuery warehouse rebuild. It establishes source precedence, conflict resolution procedures, and audit logging requirements.

## Source Precedence Order

When the same metric appears in multiple sources, use this priority order:

### Price Data

1. **Primary**: `soybean_oil_raw_daily` (validated, multi-source aggregated)
2. **Fallback 1**: `yahoo_normalized` (Yahoo Finance normalized data)
3. **Fallback 2**: `biofuel_components_canonical` (canonical biofuel data)
4. **Fallback 3**: `yahoo_finance_complete_enterprise` (comprehensive Yahoo data)

**Rationale**: Validated multi-source data is most reliable. Yahoo Finance is widely used and normalized. Biofuel components provide specialized commodity data.

### Sentiment Data

1. **Primary**: `social_sentiment_unified` (unified social sentiment)
2. **Fallback 1**: `news_advanced` (advanced news sentiment)
3. **Fallback 2**: `news_intelligence` (general news intelligence)
4. **Fallback 3**: `social_sentiment` (raw social sentiment)

**Rationale**: Unified sentiment provides consistent scoring. News sources provide additional context.

### Weather Data

1. **Primary**: `weather_data` (aggregated weather data)
2. **Fallback 1**: `weather_brazil_clean` (cleaned Brazil weather)
3. **Fallback 2**: `weather_us_midwest_clean` (cleaned US Midwest weather)
4. **Fallback 3**: `weather_argentina_daily` (Argentina weather)

**Rationale**: Aggregated data provides comprehensive coverage. Cleaned regional data is more reliable than raw.

### Policy Data

1. **Primary**: `trump_policy_intelligence` (validated Trump policy data)
2. **Fallback 1**: `ice_trump_intelligence` (ICE enforcement intelligence)
3. **Fallback 2**: `policy_events_federalregister` (Federal Register events)

**Rationale**: Validated policy intelligence is most accurate. ICE and Federal Register provide official sources.

### CFTC Data

1. **Primary**: `cftc_daily_filled` (filled CFTC data with imputation)
2. **Fallback 1**: `cftc_cot` (raw CFTC COT data)
3. **Fallback 2**: `vw_cftc_soybean_oil_weekly` (CFTC view)

**Rationale**: Filled data provides complete time series. Raw COT data is authoritative but may have gaps.

## Conflict Resolution Procedures

### Step 1: Compare Values

When two sources have values for the same date:

```sql
-- Example conflict detection
SELECT 
  date,
  source_primary,
  value_primary,
  source_secondary,
  value_secondary,
  ABS(value_primary - value_secondary) / value_primary * 100 as pct_diff
FROM (
  SELECT 
    date,
    'source_1' as source_primary,
    value_1 as value_primary,
    'source_2' as source_secondary,
    value_2 as value_secondary
  FROM conflict_check
)
WHERE value_primary IS NOT NULL 
  AND value_secondary IS NOT NULL
```

### Step 2: Apply Resolution Rules

#### Rule 1: Within 2% Difference

If `ABS(value_primary - value_secondary) / value_primary * 100 <= 2.0`:

- **Action**: Use primary source value
- **Log**: Record difference in `monitoring.dedup_conflicts` with `resolution = 'primary_source'`
- **Reason**: Differences within 2% are likely due to rounding or timing differences

#### Rule 2: Between 2% and 10% Difference

If `2.0 < ABS(value_primary - value_secondary) / value_primary * 100 <= 10.0`:

- **Action**: Use primary source value, flag for review
- **Log**: Record in `monitoring.dedup_conflicts` with `resolution = 'primary_source_flagged'` and `review_required = TRUE`
- **Reason**: Moderate differences may indicate data quality issues

#### Rule 3: Greater than 10% Difference

If `ABS(value_primary - value_secondary) / value_primary * 100 > 10.0`:

- **Action**: Store both values, flag as anomaly
- **Log**: Record in `monitoring.dedup_conflicts` with `resolution = 'conflict_manual_review'` and `review_required = TRUE`
- **Reason**: Large differences require manual investigation

### Step 3: Manual Review Process

For conflicts flagged for review:

1. **Data Team Review**: Review conflict within 48 hours
2. **Source Verification**: Verify which source is correct
3. **Resolution**: Update `monitoring.dedup_conflicts` with final resolution
4. **Data Correction**: If needed, update the feature table with correct value

## Column Consolidation Rules

### Sentiment Columns

**Current State**: 97+ sentiment-related columns across multiple tables

**Target State**: Canonical sentiment columns

| Current Columns | Canonical Column | Transformation |
|----------------|------------------|----------------|
| `china_sentiment`, `sentiment_china`, `china_sentiment_score` | `sentiment_score` | Weighted average, prefer `social_sentiment_unified` |
| `positive_ratio`, `pos_ratio`, `positive_sentiment_ratio` | `positive_ratio` | Use primary source, fallback to calculated |
| `negative_ratio`, `neg_ratio`, `negative_sentiment_ratio` | `negative_ratio` | Use primary source, fallback to calculated |
| `neutral_ratio`, `neutral_sentiment_ratio` | `neutral_ratio` | Use primary source, fallback to calculated |
| `sentiment_volatility`, `sentiment_std`, `sentiment_variance` | `sentiment_volatility` | Standard deviation of sentiment scores |

**Mapping Logic**:
```python
def consolidate_sentiment_columns(df):
    """Consolidate 97 sentiment columns into canonical set."""
    # Primary source: social_sentiment_unified
    if 'social_sentiment_unified' in df.columns:
        df['sentiment_score'] = df['social_sentiment_unified']
    elif 'news_advanced' in df.columns:
        df['sentiment_score'] = df['news_advanced']
    else:
        # Weighted average of available sources
        sentiment_cols = [c for c in df.columns if 'sentiment' in c.lower()]
        df['sentiment_score'] = df[sentiment_cols].mean(axis=1)
    
    return df
```

### Price Columns

**Current State**: Multiple price columns (close, close_price, price, value)

**Target State**: Canonical price columns

| Current Columns | Canonical Column | Transformation |
|----------------|------------------|----------------|
| `close`, `close_price`, `price`, `value` | `close_price` | Use primary source, prefer validated multi-source |
| `open`, `open_price` | `open_price` | Use primary source |
| `high`, `high_price` | `high_price` | Use primary source |
| `low`, `low_price` | `low_price` | Use primary source |
| `volume`, `vol`, `trading_volume` | `volume` | Use primary source |

### Weather Columns

**Current State**: Multiple weather columns with different naming conventions

**Target State**: Canonical weather columns

| Current Columns | Canonical Column | Transformation |
|----------------|------------------|----------------|
| `temp`, `temperature`, `temp_c`, `temperature_c` | `temperature_c` | Use primary source, convert to Celsius if needed |
| `precip`, `precipitation`, `precip_mm`, `precipitation_mm` | `precipitation_mm` | Use primary source, convert to mm if needed |
| `humidity`, `humidity_pct`, `relative_humidity` | `humidity_pct` | Use primary source, convert to percentage if needed |

## Audit Table Schema

### `monitoring.dedup_conflicts`

```sql
CREATE OR REPLACE TABLE `cbi-v14.monitoring.dedup_conflicts` (
  conflict_id STRING NOT NULL,
  table_name STRING NOT NULL,
  date DATE NOT NULL,
  column_name STRING NOT NULL,
  source_primary STRING NOT NULL,
  source_secondary STRING NOT NULL,
  value_primary FLOAT64,
  value_secondary FLOAT64,
  delta FLOAT64,
  pct_diff FLOAT64,
  resolution STRING,
  resolution_timestamp TIMESTAMP,
  review_required BOOL,
  reviewed_by STRING,
  review_notes STRING,
  created_timestamp TIMESTAMP NOT NULL
)
PARTITION BY date
CLUSTER BY table_name, column_name
OPTIONS (
  description = 'Audit log of deduplication conflicts and resolutions'
);
```

**Resolution Values**:
- `primary_source` – Used primary source (difference < 2%)
- `primary_source_flagged` – Used primary source but flagged (difference 2-10%)
- `conflict_manual_review` – Requires manual review (difference > 10%)
- `manual_override` – Manual resolution applied
- `data_corrected` – Data corrected after review

## Deduplication Script

### Python Example

```python
def deduplicate_table(
    primary_source: str,
    secondary_sources: List[str],
    date_column: str = 'date',
    value_column: str = 'value',
    conflict_threshold: float = 0.02
) -> pd.DataFrame:
    """
    Deduplicate data from multiple sources.
    
    Args:
        primary_source: Primary source table name
        secondary_sources: List of secondary source table names
        date_column: Name of date column
        value_column: Name of value column
        conflict_threshold: Percentage difference threshold (0.02 = 2%)
    
    Returns:
        Deduplicated DataFrame
    """
    # Load primary source
    df_primary = load_table(primary_source)
    
    # Load secondary sources
    dfs_secondary = [load_table(source) for source in secondary_sources]
    
    # Merge on date
    df_merged = df_primary.copy()
    for i, df_sec in enumerate(dfs_secondary):
        df_merged = df_merged.merge(
            df_sec[[date_column, value_column]],
            on=date_column,
            how='left',
            suffixes=('', f'_sec_{i}')
        )
    
    # Resolve conflicts
    conflicts = []
    for col in df_merged.columns:
        if col.endswith('_sec_0'):
            primary_col = value_column
            secondary_col = col
            
            # Calculate differences
            df_merged['pct_diff'] = (
                abs(df_merged[primary_col] - df_merged[secondary_col]) 
                / df_merged[primary_col] * 100
            )
            
            # Apply resolution rules
            mask_small = df_merged['pct_diff'] <= conflict_threshold * 100
            mask_medium = (df_merged['pct_diff'] > conflict_threshold * 100) & (df_merged['pct_diff'] <= 10.0)
            mask_large = df_merged['pct_diff'] > 10.0
            
            # Use primary for small differences
            df_merged.loc[mask_small, value_column] = df_merged.loc[mask_small, primary_col]
            
            # Flag medium differences
            if mask_medium.any():
                conflicts.extend(
                    df_merged.loc[mask_medium, [date_column, primary_col, secondary_col, 'pct_diff']]
                    .to_dict('records')
                )
            
            # Flag large differences for manual review
            if mask_large.any():
                conflicts.extend(
                    df_merged.loc[mask_large, [date_column, primary_col, secondary_col, 'pct_diff']]
                    .to_dict('records')
                )
    
    # Log conflicts
    if conflicts:
        log_conflicts_to_bigquery(conflicts, primary_source)
    
    return df_merged[[date_column, value_column]]
```

## Documentation Requirements

For each deduplication rule, document:

1. **Rule Name**: Descriptive name
2. **Sources Involved**: List of source tables
3. **Precedence Order**: Priority order
4. **Conflict Threshold**: Percentage difference thresholds
5. **Resolution Logic**: How conflicts are resolved
6. **Example**: Example conflict and resolution

## References

- See `DATA_LINEAGE_MAP.md` for source relationships
- See `VALIDATION_CHECKLIST.md` for deduplication validation tests

