# Master Feature Set Schema (models.vw_master_feature_set_v1)

**Purpose:** Single, purpose-built view for ML training containing all features needed for soybean oil price forecasting.

## Schema Definition

```sql
CREATE OR REPLACE VIEW `cbi-v14.models.vw_master_feature_set_v1` AS
SELECT 
    -- Primary key and time
    DATE(price.time) as feature_date,
    
    -- Target variable (ZL price)
    price.close as zl_price,
    
    -- Price features
    price.open as zl_open,
    price.high as zl_high,
    price.low as zl_low,
    price.volume as zl_volume,
    
    -- Price-derived features
    (price.close - LAG(price.close, 1) OVER (ORDER BY DATE(price.time))) / LAG(price.close, 1) OVER (ORDER BY DATE(price.time)) as zl_return_1d,
    (price.close - LAG(price.close, 7) OVER (ORDER BY DATE(price.time))) / LAG(price.close, 7) OVER (ORDER BY DATE(price.time)) as zl_return_7d,
    STDDEV(price.close) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as zl_volatility_30d,
    
    -- Weather features (aggregated)
    weather_us.precip_mm as us_precip,
    weather_us.temp_max as us_temp_max,
    weather_us.temp_min as us_temp_min,
    weather_br.precip_mm as brazil_precip,
    weather_br.temp_max as brazil_temp_max,
    weather_br.temp_min as brazil_temp_min,
    
    -- Weather-derived features
    AVG(weather_us.precip_mm) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as us_precip_7d_avg,
    AVG(weather_us.precip_mm) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as us_precip_30d_avg,
    AVG(weather_br.precip_mm) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as brazil_precip_7d_avg,
    AVG(weather_br.precip_mm) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as brazil_precip_30d_avg,
    
    -- Economic features
    econ.usd_brl as usd_brl_rate,
    econ.fed_funds_rate as fed_funds_rate,
    econ.crude_oil_wti as crude_oil_price,
    econ.vix as vix_index,
    
    -- Economic-derived features
    (econ.usd_brl - LAG(econ.usd_brl, 1) OVER (ORDER BY DATE(price.time))) / LAG(econ.usd_brl, 1) OVER (ORDER BY DATE(price.time)) as usd_brl_change_1d,
    (econ.crude_oil_wti - LAG(econ.crude_oil_wti, 1) OVER (ORDER BY DATE(price.time))) / LAG(econ.crude_oil_wti, 1) OVER (ORDER BY DATE(price.time)) as crude_oil_change_1d,
    
    -- Social intelligence features
    trump.sentiment_score as trump_sentiment,
    trump.ice_mention_count as ice_mentions,
    
    -- Social-derived features
    AVG(trump.sentiment_score) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as trump_sentiment_7d_avg,
    SUM(trump.ice_mention_count) OVER (ORDER BY DATE(price.time) ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ice_mentions_7d_sum,
    
    -- Metadata
    price.source_name,
    price.confidence_score,
    price.ingest_timestamp_utc,
    price.provenance_uuid

FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices` price
LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_data` weather_us 
    ON DATE(price.time) = weather_us.date AND weather_us.region = 'US'
LEFT JOIN `cbi-v14.forecasting_data_warehouse.weather_data` weather_br 
    ON DATE(price.time) = weather_br.date AND weather_br.region = 'Brazil'
LEFT JOIN `cbi-v14.forecasting_data_warehouse.economic_indicators` econ 
    ON DATE(price.time) = econ.date
LEFT JOIN `cbi-v14.forecasting_data_warehouse.ice_trump_intelligence` trump 
    ON DATE(price.time) = DATE(trump.timestamp)
WHERE price.symbol = 'ZL'
ORDER BY feature_date DESC
```

## Feature Categories

### 1. Price Features (5)
- `zl_price` - Target variable (close price)
- `zl_open`, `zl_high`, `zl_low` - OHLC components
- `zl_volume` - Trading volume

### 2. Price-Derived Features (3)
- `zl_return_1d` - 1-day price return
- `zl_return_7d` - 7-day price return
- `zl_volatility_30d` - 30-day rolling volatility

### 3. Weather Features (6)
- `us_precip`, `us_temp_max`, `us_temp_min` - US weather
- `brazil_precip`, `brazil_temp_max`, `brazil_temp_min` - Brazil weather

### 4. Weather-Derived Features (4)
- `us_precip_7d_avg`, `us_precip_30d_avg` - US precipitation averages
- `brazil_precip_7d_avg`, `brazil_precip_30d_avg` - Brazil precipitation averages

### 5. Economic Features (4)
- `usd_brl_rate` - USD/BRL exchange rate
- `fed_funds_rate` - Federal funds rate
- `crude_oil_price` - WTI crude oil price
- `vix_index` - VIX volatility index

### 6. Economic-Derived Features (2)
- `usd_brl_change_1d` - 1-day USD/BRL change
- `crude_oil_change_1d` - 1-day crude oil change

### 7. Social Intelligence Features (2)
- `trump_sentiment` - Trump sentiment score
- `ice_mentions` - ICE mention count

### 8. Social-Derived Features (2)
- `trump_sentiment_7d_avg` - 7-day Trump sentiment average
- `ice_mentions_7d_sum` - 7-day ICE mentions sum

### 9. Metadata (4)
- `source_name`, `confidence_score`, `ingest_timestamp_utc`, `provenance_uuid`

## Total Features: 32

## Data Quality Requirements

### Completeness
- Target variable (`zl_price`): 100% non-null required
- Core features (price, weather, economic): ≥95% non-null for training period
- Social features: ≥80% non-null (sparse data expected)

### Freshness
- Price data: ≤15 minutes lag
- Weather data: ≤24 hours lag
- Economic data: ≤same day lag
- Social data: ≤4 hours lag

### Validation Rules
- Price returns: Within ±50% (outlier detection)
- Weather data: Temperature within -50°C to +60°C
- Economic data: Exchange rates > 0, rates ≥ 0
- Social sentiment: Between -1 and +1

## Usage Notes

### Training Data Window
- Start date: 2023-01-01 (sufficient history for derived features)
- End date: Current date - 1 day (avoid look-ahead bias)
- Minimum training period: 365 days

### Feature Engineering Pipeline
1. Raw data ingestion → staging tables
2. Feature calculation → derived features
3. Quality validation → outlier detection
4. Feature store materialization → this view
5. Model training → use this view as input

### Model Compatibility
- BigQuery ML: Compatible with all feature types
- LightGBM/XGBoost: Requires feature scaling
- Neural networks: Requires normalization
- ARIMA: Use price features only

## Next Steps
1. Create the view in BigQuery
2. Validate data quality and completeness
3. Test with sample ML training queries
4. Document feature importance analysis
5. Set up automated feature validation
