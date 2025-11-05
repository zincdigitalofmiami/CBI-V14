# CBI-V14 Asset Classification System

## Overview
Proper classification of financial assets is critical for accurate modeling and analysis. This system ensures commodities are never conceptually mixed with currencies or other asset classes.

## Asset Type Definitions

### 1. Commodity Futures (`commodity_future`)
**Definition**: Exchange-traded futures contracts for physical commodities
**Examples**:
- `ZL=F`: Soybean Oil Futures
- `ZS=F`: Soybean Futures
- `ZC=F`: Corn Futures
- `ZM=F`: Soybean Meal Futures
- `ZW=F`: Wheat Futures
- `CL=F`: Crude Oil Futures
- `GC=F`: Gold Futures

**Characteristics**:
- Tradable contracts with expiration dates
- Price reflects supply/demand for physical commodity
- Trading volume and open interest data available
- Used for hedging and speculation

### 2. Currency Indices (`currency_index`)
**Definition**: Indices measuring currency strength/weakness
**Examples**:
- `DX-Y.NYB`: US Dollar Index (DXY) - measures USD vs basket of currencies
- `EURUSD=X`: Euro vs US Dollar (future implementation)
- `USDJPY=X`: US Dollar vs Japanese Yen (future implementation)

**Characteristics**:
- Not tradable assets themselves
- Index values reflect currency market sentiment
- Critical for commodity pricing (strong USD = lower commodity prices)
- No trading volume (synthetic index)

### 3. Volatility Indices (`volatility_index`)
**Definition**: Measures of market fear/uncertainty
**Examples**:
- `^VIX`: CBOE Volatility Index - measures expected S&P 500 volatility
- Other VIX variants (future implementation)

**Characteristics**:
- Not prices or tradable assets
- Higher values = more market fear
- Calculated from options pricing
- Key indicator for risk sentiment

### 4. Economic Indicators (`economic_indicator`)
**Definition**: Macroeconomic data points
**Examples**:
- Fed Funds Rate
- GDP Growth
- Inflation (CPI)
- Treasury Yields
- Unemployment Rate

**Characteristics**:
- Policy and economic data
- Released by government agencies
- Influences all asset classes
- Not directly tradable

## Classification Rules

### NEVER Mix These Categories:
1. **Commodities ≠ Currencies**: Soybeans are not "dollars" - DXY belongs in currency_indices
2. **Prices ≠ Indices**: VIX is not a "price" - it's a volatility measure
3. **Futures ≠ Spot**: Futures prices vs cash prices should be distinguished
4. **Trading ≠ Economic**: Currency trading rates ≠ economic indicators

### Implementation Rules:
- Asset type is stored in `asset_type` column
- Symbol naming conventions maintained
- Separate data flows for different asset classes
- Clear metadata for each classification

## Data Flow Architecture

```
Yahoo Finance API
├── Commodity Futures (ZL=F, ZS=F, etc.)
├── Currency Indices (DX-Y.NYB)
└── Volatility Indices (^VIX)

Economic Data APIs
├── Interest Rates (Fed Funds, Treasury Yields)
├── Economic Indicators (GDP, Inflation)
└── Currency Rates (USD/BRL, USD/CNY, etc.)

Web Scraping
├── News & Sentiment Data
└── Alternative Data Sources
```

## Quality Assurance

### Validation Rules:
- Commodity futures must have volume data
- Currency indices have no volume (set to 0)
- Volatility indices have no volume (set to 0)
- Economic indicators stored separately from prices

### Error Prevention:
- Automatic classification based on symbol patterns
- Validation checks prevent misclassification
- Separate storage tables for different asset types
- Metadata tracking for audit trails

## Usage in Modeling

### Feature Engineering:
- Commodity futures: Price momentum, volatility, correlations
- Currency indices: USD strength impact on commodities
- Volatility indices: Market fear correlation with commodity prices
- Economic indicators: Macro environment context

### Correlation Analysis:
- Commodities correlate with each other (supply/demand)
- Commodities correlate inversely with strong USD
- Commodities correlate with volatility during uncertainty
- Economic indicators influence all asset classes

## Maintenance

### Adding New Assets:
1. Determine correct asset_type
2. Add to SYMBOLS configuration
3. Update classification logic
4. Test data collection
5. Validate in database

### Monitoring:
- Regular classification audits
- Data quality checks
- Performance monitoring
- Error alerting

## Historical Context

**Issue Identified**: USD currency data was conceptually mixed with soybean commodity data, leading to confusion between currencies and commodities.

**Resolution**: Implemented strict asset classification system that properly separates:
- Commodity futures (physical goods)
- Currency indices (monetary values)
- Volatility indices (risk measures)
- Economic indicators (policy data)

This ensures clean, logical data organization for accurate financial modeling.


