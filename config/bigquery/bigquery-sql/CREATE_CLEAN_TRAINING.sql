-- ============================================
-- STEP 2: CREATE ULTRA-CLEAN TRAINING TABLE
-- All features COALESCED - NO NULLS POSSIBLE
-- Uses actual columns from trump_rich_2023_2025
-- ============================================

CREATE OR REPLACE TABLE `cbi-v14.models_v4.training_data_1m_clean` AS
WITH validated_data AS (
  SELECT 
    date,
    target_1m,
    
    -- CORE FEATURES (ALL COALESCED - NO NULLS POSSIBLE)
    COALESCE(zl_f_close, 45.0) AS f01_zl_close,
    COALESCE(crush_spread, 0.0) AS f02_crush_margin,
    COALESCE(china_us_imports_mt, 0.0) AS f03_china_imports,
    COALESCE(vix, 20.0) AS f04_vix,
    COALESCE(vix_lag_3d, 20.0) AS f05_vix_lag3d,
    COALESCE(vix_spike_flag, 0) AS f06_vix_spike,
    COALESCE(dxy, 100.0) AS f07_dxy,
    COALESCE(rin_d4_price, 1.5) AS f08_rin_d4,
    COALESCE(brazil_premium_usd, 0.0) AS f09_brazil_premium,
    COALESCE(argentina_tax_pct, 30.0) AS f10_argentina_tax,
    
    -- TRUMP FEATURES
    COALESCE(trump_agricultural_impact, 0.0) AS f11_trump_ag_impact,
    COALESCE(trump_soybean_relevance, 0.0) AS f12_trump_soy_relevance,
    COALESCE(trump_weighted_impact, 0.0) AS f13_trump_weighted,
    COALESCE(trump_impact_ma_7d, 0.0) AS f14_trump_ma7d,
    
    -- BIG EIGHT SIGNALS
    COALESCE(vix_stress, 0.3) AS f15_vix_stress,
    COALESCE(china_relations, 0.2) AS f16_china_relations,
    COALESCE(tariff_threat, 0.2) AS f17_tariff_threat,
    COALESCE(biofuel_cascade, 1.2) AS f18_biofuel_cascade,
    COALESCE(big8_composite, 0.45) AS f19_big8_composite,
    COALESCE(market_stress_level, 0) AS f20_market_stress,
    
    -- CFTC POSITIONING
    COALESCE(cftc_net_position, 0.0) AS f21_cftc_net,
    COALESCE(cftc_position_change, 0.0) AS f22_cftc_change,
    
    -- SOCIAL SENTIMENT
    COALESCE(social_sentiment, 0.0) AS f23_social_avg,
    COALESCE(social_extreme, 0.0) AS f24_social_extreme,
    
    -- TECHNICALS
    COALESCE(zl_f_rsi_14, 50.0) AS f25_zl_rsi,
    COALESCE(zl_f_macd_hist, 0.0) AS f26_zl_macd,
    COALESCE(zl_f_open_int, 100000) AS f27_zl_open_int,
    COALESCE(adm_close, 50.0) AS f28_adm_close,
    COALESCE(bg_close, 40.0) AS f29_bg_close,
    COALESCE(dar_close, 35.0) AS f30_dar_close,
    
    -- VIX INTERACTIONS (MULTIPLIERS)
    COALESCE(vix_trump_interaction, 0.0) AS f31_vix_x_trump,
    COALESCE(vix_china_interaction, 0.0) AS f32_vix_x_china,
    COALESCE(vix_big8_interaction, 0.0) AS f33_vix_x_big8,
    COALESCE(amplified_trump_signal, 0.0) AS f34_trump_amplified,
    
    -- ADDITIONAL KEY FEATURES
    COALESCE(zl_f_volume, 50000) AS f35_zl_volume,
    COALESCE(zl_daily_change, 0.0) AS f36_zl_daily_change,
    COALESCE(zl_volatility_20d, 1.0) AS f37_zl_volatility,
    COALESCE(zl_ma_7d, 45.0) AS f38_zl_ma7d,
    COALESCE(vix_daily_change, 0.0) AS f39_vix_daily_change,
    COALESCE(dxy_5d_change, 0.0) AS f40_dxy_change,
    
    -- CHINA/BRAZIL FEATURES
    COALESCE(china_import_mom, 0.0) AS f41_china_mom,
    COALESCE(brazil_premium_ratio, 0.0) AS f42_brazil_ratio,
    COALESCE(china_cancellation, 0) AS f43_china_cancel,
    COALESCE(us_export_mt, 0.0) AS f44_us_exports,
    COALESCE(brazil_argentina_spread, -30.0) AS f45_brazil_arg_spread,
    
    -- BIOFUEL
    COALESCE(biodiesel_price, 4.0) AS f46_biodiesel,
    COALESCE(ethanol_price, 2.5) AS f47_ethanol,
    COALESCE(rin_d5_price, 1.2) AS f48_rin_d5,
    COALESCE(rin_7d_change, 0.0) AS f49_rin_change,
    COALESCE(rin_zl_ratio, 0.033) AS f50_rin_zl_ratio,
    
    -- SOYBEAN/MEAL FEATURES
    COALESCE(zs_f_close, 11.0) AS f51_soybean_price,
    COALESCE(zm_f_close, 350.0) AS f52_meal_price,
    
    -- TRUMP DETAILS
    COALESCE(trump_post_count, 0) AS f53_trump_posts,
    COALESCE(trump_confidence, 0.7) AS f54_trump_confidence,
    
    -- FINAL CALCULATED FEATURES
    COALESCE(biodiesel_mandate_gal, 0) AS f55_biodiesel_mandate,
    COALESCE(soybean_oil_biodiesel_pct, 0.3) AS f56_soy_oil_bio_pct,
    
    -- INTERACTION TERMS
    COALESCE(trump_agricultural_impact * china_relations, 0.0) AS f57_trump_china_interaction,
    COALESCE(vix_stress * big8_composite, 0.135) AS f58_vix_big8_interaction,
    COALESCE(cftc_net_position * vix_stress, 0.0) AS f59_cftc_vix_interaction,
    COALESCE(rin_d4_price * biofuel_cascade, 1.8) AS f60_rin_biofuel_interaction
    
  FROM `cbi-v14.models_v4.trump_rich_2023_2025`
  WHERE target_1m IS NOT NULL
    AND date >= '2023-01-01'
    AND date <= CURRENT_DATE()
)
SELECT * FROM validated_data
ORDER BY date;

-- Verify the table
SELECT 
  COUNT(*) AS row_count,
  COUNT(DISTINCT date) AS date_count,
  MIN(date) AS start_date,
  MAX(date) AS end_date,
  COUNT(*) - 2 AS feature_count  -- Exclude date and target
FROM `cbi-v14.models_v4.training_data_1m_clean`;

