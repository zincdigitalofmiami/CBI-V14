# TABLE SCHEMA MAPPING - CRITICAL REFERENCE

## ⚠️ WARNING: SCHEMAS ARE DIFFERENT FOR SPECIFIC REASONS!

### Price Tables - Different Schemas

#### 1. soybean_oil_prices
- **Time Column**: `time` (TIMESTAMP)
- **Price Column**: `close` (FLOAT)
- **Other Columns**: open, high, low, volume, symbol
- **Source**: ZL futures data from yfinance/ingestion

#### 2. crude_oil_prices
- **Time Column**: `date` (DATE)
- **Price Column**: `close_price` (FLOAT)
- **Other Columns**: open_price, high_price, low_price, volume, symbol
- **Source**: Crude oil futures data

#### 3. usd_index_prices
- **Time Column**: `date` (DATE)
- **Price Column**: `close_price` (FLOAT)
- **Other Columns**: open_price, high_price, low_price, volume, symbol
- **Source**: DXY/USD index data

#### 4. palm_oil_prices
- **Time Column**: `time` (TIMESTAMP)
- **Price Column**: `close_price` (FLOAT)
- **Other Columns**: open_price, high_price, low_price, volume, symbol
- **Source**: Palm oil futures data

#### 5. vix_daily
- **Time Column**: `date` (DATE)
- **Price Column**: `close` (FLOAT)
- **Other Columns**: open, high, low, volume
- **Source**: VIX volatility index

### Social Intelligence Tables

#### comprehensive_social_intelligence
- **Time Column**: `created_at` (TIMESTAMP)
- **Content Column**: `content` (STRING)
- **Other Columns**: platform, author, engagement_score

### Weather Tables

#### weather_data
- **Time Column**: `date` (DATE)
- **Key Columns**: station_id, precipitation_mm, temperature_c
- **Location**: Identified by station_id prefix (BR=Brazil, AR=Argentina)

### Economic Tables

#### economic_indicators
- **Time Column**: `time` (TIMESTAMP)
- **Value Column**: `value` (FLOAT)
- **Other Columns**: indicator, source

## CRITICAL RULES:

1. **NEVER ASSUME** column names - ALWAYS CHECK the specific table
2. **DATE vs TIMESTAMP** - Some use DATE, some use TIMESTAMP for specific reasons
3. **close vs close_price** - Different naming conventions per data source
4. **JOIN CAREFULLY** - When joining tables, handle DATE/TIMESTAMP conversions
5. **NO PLACEHOLDERS** - If data doesn't exist, FAIL rather than use fallback

## SQL JOIN EXAMPLES:

```sql
-- Joining soybean_oil_prices (TIMESTAMP) with crude_oil_prices (DATE)
FROM soybean_oil_prices s
JOIN crude_oil_prices c ON DATE(s.time) = c.date

-- Joining palm_oil_prices (TIMESTAMP) with usd_index_prices (DATE)  
FROM palm_oil_prices p
JOIN usd_index_prices u ON DATE(p.time) = u.date
```

## NEVER USE THESE PLACEHOLDERS:
- ❌ base_price = 51.05
- ❌ 0.6 as correlation
- ❌ 0.5 as default_value
- ❌ COALESCE(value, 0.75) -- NO FALLBACKS!

## ALWAYS DO THIS:
- ✅ Check actual table schema first
- ✅ Use real column names
- ✅ Handle NULL values explicitly
- ✅ Fail if data is missing rather than use defaults
