-- ============================================
-- STEP 1: CREATE ULTRA-CLEAN TRAINING TABLE
-- All features COALESCED - NO NULLS POSSIBLE
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.ultimate_clean_training` AS
WITH validated_data AS (
  SELECT 
    date,
    target_1m,
    
    -- CORE FEATURES (ALL COALESCED - NO NULLS POSSIBLE)
    COALESCE(zl_f_close, 45.0) AS f01_zl_close,
    COALESCE((zl_f_close - zs_f_close - zm_f_close), 0.0) AS f02_crush_margin,
    COALESCE(china_soybean_imports_mt, 0.0) AS f03_china_imports,
    COALESCE(vix_close, 20.0) AS f04_vix,
    COALESCE(LAG(vix_close, 3) OVER (ORDER BY date), 20.0) AS f05_vix_lag3d,
    COALESCE(CASE WHEN vix_close > 25 THEN 1 ELSE 0 END, 0) AS f06_vix_spike,
    COALESCE(dxy_close, 100.0) AS f07_dxy,
    COALESCE(rin_d4_price, 1.5) AS f08_rin_d4,
    COALESCE(brazil_export_premium, 0.0) AS f09_brazil_premium,
    COALESCE(argentina_export_tax, 30.0) AS f10_argentina_tax,
    
    -- TRUMP FEATURES (FROM trump_policy_intelligence)
    COALESCE(trump_agricultural_impact, 0.0) AS f11_trump_ag_impact,
    COALESCE(trump_soybean_relevance, 0.0) AS f12_trump_soy_relevance,
    COALESCE(trump_agricultural_impact * trump_confidence, 0.0) AS f13_trump_weighted,
    COALESCE(AVG(trump_agricultural_impact) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 0.0) AS f14_trump_ma7d,
    
    -- BIG EIGHT SIGNALS
    COALESCE(feature_vix_stress, 0.3) AS f15_vix_stress,
    COALESCE(feature_china_relations, 0.2) AS f16_china_relations,
    COALESCE(feature_tariff_threat, 0.2) AS f17_tariff_threat,
    COALESCE(feature_biofuel_cascade, 1.2) AS f18_biofuel_cascade,
    COALESCE(big8_composite_score, 0.45) AS f19_big8_composite,
    COALESCE(CASE WHEN market_regime = 'STRESSED' THEN 1 WHEN market_regime = 'EXTREME' THEN 2 ELSE 0 END, 0) AS f20_market_stress,
    
    -- CFTC POSITIONING
    COALESCE(cftc_net_position, 0.0) AS f21_cftc_net,
    COALESCE(cftc_position_change, 0.0) AS f22_cftc_change,
    
    -- SOCIAL SENTIMENT
    COALESCE(social_sentiment_avg, 0.0) AS f23_social_avg,
    COALESCE(social_sentiment_extreme, 0.0) AS f24_social_extreme,
    
    -- TECHNICALS
    COALESCE(zl_f_rsi_14, 50.0) AS f25_zl_rsi,
    COALESCE(zl_f_macd_hist, 0.0) AS f26_zl_macd,
    COALESCE(zl_f_open_int, 100000) AS f27_zl_open_int,
    COALESCE(adm_close, 50.0) AS f28_adm_close,
    COALESCE(bg_close, 40.0) AS f29_bg_close,
    COALESCE(dar_close, 35.0) AS f30_dar_close,
    
    -- VIX INTERACTIONS (MULTIPLIERS)
    COALESCE(vix_close * trump_agricultural_impact, 0.0) AS f31_vix_x_trump,
    COALESCE(vix_close * feature_china_relations, 0.0) AS f32_vix_x_china,
    COALESCE(feature_vix_stress * big8_composite_score, 0.0) AS f33_vix_x_big8,
    COALESCE(CASE WHEN vix_close > 25 THEN trump_agricultural_impact * 2 ELSE trump_agricultural_impact END, 0.0) AS f34_trump_amplified,
    
    -- ADDITIONAL KEY FEATURES
    COALESCE(zl_f_volume, 50000) AS f35_zl_volume,
    COALESCE(cl_f_close, 75.0) AS f36_crude_oil,
    COALESCE(zc_f_close, 4.5) AS f37_corn_price,
    COALESCE(zw_f_close, 5.5) AS f38_wheat_price,
    COALESCE(zs_f_close, 11.0) AS f39_soybean_price,
    COALESCE(palm_oil_spot_price, 900.0) AS f40_palm_oil,
    
    -- FX PAIRS (Using available columns)
    COALESCE(dxy_close, 100.0) AS f41_usd_index,
    COALESCE(brazil_export_premium/argentina_export_tax, 0.0) AS f42_brazil_arg_ratio,
    COALESCE(china_soybean_imports_mt/100000, 0.0) AS f43_china_norm,
    COALESCE(eur_usd_close, 1.05) AS f44_eur_usd,
    
    -- BIOFUEL
    COALESCE(biodiesel_price, 4.0) AS f45_biodiesel,
    COALESCE(ethanol_price, 2.5) AS f46_ethanol,
    COALESCE(rin_d5_price, 1.2) AS f47_rin_d5,
    
    -- CALCULATED FEATURES
    COALESCE(zl_f_close - LAG(zl_f_close, 7) OVER (ORDER BY date), 0.0) AS f48_zl_change_7d,
    COALESCE(vix_close - LAG(vix_close, 1) OVER (ORDER BY date), 0.0) AS f49_vix_daily_change,
    
    -- FINAL KEY FEATURES
    COALESCE(fed_funds_rate, 5.5) AS f50_fed_funds,
    COALESCE(us_employment_change_000s, 200) AS f51_employment,
    COALESCE(inflation_expectation_5y, 2.5) AS f52_inflation_exp,
    COALESCE(credit_spread_basis, 100) AS f53_credit_spread,
    COALESCE(term_spread_2_10, 0.0) AS f54_term_spread,
    COALESCE(china_cancellation_flag, 0) AS f55_china_cancel,
    COALESCE(us_export_sales_weekly, 100000) AS f56_us_exports,
    COALESCE(brazil_export_premium - argentina_export_tax, 0.0) AS f57_brazil_arg_spread,
    COALESCE(trump_post_count, 0) AS f58_trump_posts,
    COALESCE(trump_confidence, 0.7) AS f59_trump_confidence,
    COALESCE(rin_d4_price / NULLIF(zl_f_close, 0), 0.0) AS f60_rin_zl_ratio
    
  FROM `cbi-v14.models_v4.trump_rich_2023_2025` t
  LEFT JOIN `cbi-v14.neural.vw_big_eight_signals` b8 ON t.date = b8.date
  WHERE target_1m IS NOT NULL
    AND t.date >= '2023-01-01'
    AND t.date <= CURRENT_DATE()
)
SELECT * FROM validated_data
ORDER BY date;

