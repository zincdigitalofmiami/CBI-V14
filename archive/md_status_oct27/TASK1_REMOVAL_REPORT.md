# TASK 1 REMOVAL REPORT

**Date:** 2025-10-23 19:51:05

## Summary

- Original features: 189
- Final features: 155
- Removed: 34 features

## Sparse Features Removed (<10% coverage)

Total: 14

- `china_posts_7d_ma`: Only 7.0% coverage

- `event_impact_level`: Only 5.9% coverage

- `cftc_commercial_long`: Only 5.7% coverage

- `cftc_commercial_short`: Only 5.7% coverage

- `cftc_commercial_net`: Only 5.7% coverage

- `cftc_open_interest`: Only 5.7% coverage

- `news_total_count_enhanced`: Only 0.6% coverage

- `tariff_total_mentions`: Only 0.3% coverage

- `china_total_mentions`: Only 0.3% coverage

- `brazil_article_count`: Only 0.4% coverage

- `brazil_harvest_signals`: Only 0.2% coverage

- `policy_total_mentions`: Only 0.4% coverage

- `policy_momentum`: Only 0.2% coverage

- `weather_article_count`: Only 0.4% coverage

## Constant Features Removed (1 unique value)

Total: 3

- `ice_mentions`: Constant - provides zero information

- `reddit_sentiment`: Constant - provides zero information

- `ice_enforcement_count`: Constant - provides zero information

## High-NaN Features Removed (>95% NaN)

Total: 17

- `tariff_sentiment`: 99.6% NaN

- `trump_sentiment`: 99.5% NaN

- `china_sentiment_policy`: 98.8% NaN

- `avg_ag_impact`: 96.0% NaN

- `max_ag_impact`: 96.0% NaN

- `avg_soy_relevance`: 96.0% NaN

- `tariff_mentions_tariff`: 96.0% NaN

- `china_mentions_tariff`: 96.0% NaN

- `trade_mentions`: 96.0% NaN

- `high_priority_events`: 96.0% NaN

- `policy_events`: 96.0% NaN

- `tariff_mentions_lag1`: 96.0% NaN

- `tariff_mentions_lag7`: 96.4% NaN

- `china_mentions_lag1`: 96.0% NaN

- `tariff_mentions_7d`: 96.0% NaN

- `china_mentions_7d`: 96.0% NaN

- `sentiment_std`: 99.8% NaN