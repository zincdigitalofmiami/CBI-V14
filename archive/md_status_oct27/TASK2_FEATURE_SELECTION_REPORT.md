# TASK 2 FEATURE SELECTION REPORT

**Date:** 2025-10-23 19:52:33

## Summary

- Input features: 151
- Removed (high correlation): 48
- Features ranked: 103
- Selected features: 103

## Highly Correlated Features Removed

Total: 48

- `zl_price_lag1`: Corr=0.991 with zl_price_current

- `ma_7d`: Corr=0.989 with zl_price_current

- `monthly_zscore`: Corr=0.952 with zl_price_current

- `oil_price_per_cwt`: Corr=1.000 with zl_price_current

- `crush_margin`: Corr=1.000 with zl_price_current

- `crush_margin_7d_ma`: Corr=0.989 with zl_price_current

- `leadlag_zl_price`: Corr=1.000 with zl_price_current

- `zl_price_lag7`: Corr=0.963 with ma_7d

- `ma_30d`: Corr=0.954 with zl_price_lag7

- `crush_margin_30d_ma`: Corr=0.954 with zl_price_lag7

- `feature_geopolitical_volatility`: Corr=0.995 with feature_biofuel_ethanol

- `sentiment_volume_sent`: Corr=-0.973 with feature_geopolitical_volatility

- `feature_biofuel_ethanol`: Corr=-0.964 with sentiment_ma30

- `sentiment_volume`: Corr=1.000 with china_mentions

- `total_posts`: Corr=1.000 with china_mentions

- `import_demand_index`: Corr=-0.956 with tension_index

- `month`: Corr=1.000 with brazil_month

- `quarter`: Corr=0.971 with brazil_month

- `growing_degree_days`: Corr=0.950 with brazil_temperature_c

- `weather_brazil_temp`: Corr=1.000 with brazil_temperature_c

... and 28 more

## Top 20 Selected Features

1. `zl_price_current` - Score: 0.7511

2. `bean_price_per_bushel` - Score: 0.6749

3. `corn_price` - Score: 0.6594

4. `zl_volume` - Score: 0.6591

5. `zl_price_lag30` - Score: 0.6572

6. `wheat_price` - Score: 0.6500

7. `volatility_30d` - Score: 0.6486

8. `crude_price` - Score: 0.6260

9. `corr_zl_palm_365d` - Score: 0.5986

10. `corr_zl_crude_365d` - Score: 0.5963

11. `corr_zl_dxy_365d` - Score: 0.5898

12. `corr_zl_corn_365d` - Score: 0.5873

13. `fx_usd_brl` - Score: 0.5767

14. `meal_price_per_ton` - Score: 0.5693

15. `corr_zl_palm_180d` - Score: 0.5678

16. `fx_usd_cny_ma7` - Score: 0.5671

17. `corr_zl_vix_180d` - Score: 0.5584

18. `yoy_change` - Score: 0.5567

19. `corr_zl_vix_90d` - Score: 0.5565

20. `big8_composite_score` - Score: 0.5365

## Selected Features by Category

### Price (8 features)
- `zl_price_current`
- `bean_price_per_bushel`
- `corn_price`
- `zl_price_lag30`
- `wheat_price`
- `crude_price`
- `meal_price_per_ton`
- `palm_price`

### Currency/FX (17 features)
- `corr_zl_dxy_365d`
- `fx_usd_brl`
- `fx_usd_cny_ma7`
- `corr_zl_dxy_180d`
- `corr_zl_dxy_90d`
- `fx_usd_cny`
- `fx_usd_myr_ma7`
- `corr_zl_dxy_30d`
- `corr_zl_dxy_7d`
- `fx_usd_myr_pct_change`
- ... and 7 more

### Correlations (33 features)
- `corr_zl_palm_365d`
- `corr_zl_crude_365d`
- `corr_zl_dxy_365d`
- `corr_zl_corn_365d`
- `corr_zl_palm_180d`
- `corr_zl_vix_180d`
- `corr_zl_vix_90d`
- `corr_zl_crude_180d`
- `corr_zl_vix_30d`
- `corr_zl_palm_90d`
- ... and 23 more

### Weather (5 features)
- `brazil_temp_7d_ma`
- `weather_us_temp`
- `brazil_temperature_c`
- `weather_argentina_temp`
- `brazil_month`

### Sentiment (9 features)
- `sentiment_ma30`
- `sentiment_lag1`
- `sentiment_lag7`
- `max_sentiment`
- `avg_sentiment`
- `china_sentiment`
- `china_sentiment_30d_ma`
- `sentiment_change_1d`
- `sentiment_change_7d`

### Technical (8 features)
- `volatility_30d`
- `return_7d`
- `return_1d`
- `volatility_multiplier`
- `crude_momentum_2d`
- `dxy_momentum_3d`
- `palm_momentum_3d`
- `trumpxi_volatility_30d_ma`

### Seasonal (3 features)
- `seasonal_index`
- `export_seasonality_factor`
- `brazil_month`