-- Updated signals.vw_sentiment_price_correlation
-- Updated: 2025-11-17 17:57:50

WITH daily_sentiment AS (
    SELECT 
        date, 
        platform, 
        avg_sentiment
    FROM `cbi-v14.signals.vw_social_sentiment_aggregates_daily`
    WHERE avg_sentiment IS NOT NULL
), 
daily_prices AS (
    SELECT 
        DATE(time) as date, 
        yahoo_close as zl_price, 
        (yahoo_close - LAG(close, 1) OVER (ORDER BY time)) / LAG(close, 1) OVER (ORDER BY time) as zl_return 
    FROM `cbi-v14.forecasting_data_warehouse.yahoo_historical_prefixed`
    WHERE yahoo_close IS NOT NULL
), 
combined_data AS (
    SELECT 
        s.date, 
        s.platform, 
        s.avg_sentiment, 
        p.zl_return 
    FROM daily_sentiment s 
    JOIN daily_prices p ON s.date = p.date
) 
SELECT 
    date, 
    platform, 
    avg_sentiment, 
    zl_return, 
    CORR(avg_sentiment, zl_return) OVER (
        PARTITION BY platform 
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) as sentiment_zl_corr_30d 
FROM combined_data