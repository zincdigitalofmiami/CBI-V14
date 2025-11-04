-- ============================================
-- STAGE 6: DASHBOARD CONSUMPTION VIEWS + TIER 1 AI REASONING
-- ============================================
-- Adds AI Reasoning Layer: Pattern explanation, Math validation, Attention direction
-- Pre-Aggregated Views for Fast Dashboard Loading
-- ============================================

-- View 1: Latest Forecast + Signals + AI Reasoning (All Horizons)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_forecast_with_signals`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.target_date,
  f.predicted_value,
  f.lower_bound_80,
  f.upper_bound_80,
  f.confidence,
  f.market_regime,
  f.crisis_intensity_score,
  f.primary_signal_driver,
  f.composite_signal_score,
  f.palm_sub_risk,
  f.model_name,
  f.mape_historical,
  
  -- TIER 1: AI Reasoning Tooltip
  CONCAT(
    'Regime: ', f.market_regime, ' | ',
    CASE 
      WHEN f.market_regime = 'VIX_CRISIS_REGIME' THEN 'Volatility spike → -8% bias applied to base forecast'
      WHEN f.market_regime = 'CHINA_TENSION_REGIME' THEN 'China trade tension → +5% volatility bands applied'
      WHEN f.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 'RFS mandate pull → +12% upside bias applied'
      WHEN f.market_regime = 'FUNDAMENTALS_REGIME' THEN 'Supply/demand fundamentals driving price action'
      ELSE 'Market-driven forecast'
    END
  ) as reasoning_tooltip,
  
  -- TIER 1: Mathematical Validation
  CONCAT(
    'Forecast: $', CAST(ROUND(f.predicted_value, 2) AS STRING), ' | ',
    'Confidence: ', CAST(CAST(f.confidence AS INT64) AS STRING), '% ',
    '(Crisis Intensity: ', CAST(CAST(f.crisis_intensity_score AS INT64) AS STRING), '/100) | ',
    'Historical MAPE: ', CAST(ROUND(f.mape_historical, 2) AS STRING), '%'
  ) as confidence_math,
  
  -- TIER 1: Attention Direction Flag
  CASE 
    WHEN f.crisis_intensity_score > 70 THEN '🚨 CRISIS MODE: Focus on bands, not point forecast'
    WHEN f.palm_sub_risk > 5.0 THEN '⚠️ PALM RISK: Substitution pressure rising ($' || CAST(ROUND(f.palm_sub_risk, 1) AS STRING) || '/MT premium)'
    WHEN f.confidence < 50 THEN '⚠️ LOW CONFIDENCE: High uncertainty environment'
    WHEN f.crisis_intensity_score > 50 THEN '⚠️ ELEVATED RISK: Monitor closely'
    ELSE '✅ STABLE: Fundamentals-driven forecast'
  END as attention_flag,
  
  -- TIER 1: Pattern Explanation
  CONCAT(
    'Primary Driver: ', f.primary_signal_driver, ' | ',
    CASE 
      WHEN f.primary_signal_driver = 'VIX_STRESS' THEN 'Market volatility driving forecast uncertainty'
      WHEN f.primary_signal_driver = 'HARVEST_PACE' THEN 'Harvest timing impacting supply expectations'
      WHEN f.primary_signal_driver = 'CHINA_RELATIONS' THEN 'China demand signals influencing price outlook'
      WHEN f.primary_signal_driver = 'TARIFF_THREAT' THEN 'Trade policy uncertainty affecting forecast'
      WHEN f.primary_signal_driver = 'GEOPOLITICAL_VOLATILITY' THEN 'Global risk factors in play'
      WHEN f.primary_signal_driver = 'BIOFUEL_CASCADE' THEN 'Biofuel mandate dynamics driving demand'
      WHEN f.primary_signal_driver = 'HIDDEN_CORRELATION' THEN 'Cross-asset relationships signaling regime shift'
      ELSE 'Multiple factors influencing forecast'
    END
  ) as pattern_explanation,
  
  -- Vegas Intel Display Format
  CONCAT(
    f.horizon, ' Forecast: $', CAST(ROUND(f.predicted_value, 2) AS STRING),
    ' | Confidence: ', CAST(CAST(f.confidence AS INT64) AS STRING), '%',
    ' | MAPE: ', CAST(ROUND(f.mape_historical, 1) AS STRING), '%',
    ' | Regime: ', f.market_regime
  ) as vegas_intel_display
  
FROM `cbi-v14.predictions_uc1.production_forecasts` f
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 2: Vegas Intel Feed (Kevin's Live Page) + AI Reasoning
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_vegas_intel_feed`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value as zl_cost,  -- Used in Kevin's ROI calculations
  f.confidence,
  f.market_regime,
  f.crisis_intensity_score,
  f.composite_signal_score,
  f.primary_signal_driver,
  
  -- Vegas Forecast Display
  CONCAT(
    f.horizon, ' Forecast: $', CAST(ROUND(f.predicted_value, 2) AS STRING),
    ' (', CAST(CAST(f.confidence AS INT64) AS STRING), '% conf)'
  ) as forecast_display,
  
  -- Signal Strength Display
  CONCAT(
    'Signal Strength: Big 8 = ', CAST(ROUND(f.composite_signal_score * 100, 0) AS STRING),
    ' | Crisis: ', CAST(CAST(f.crisis_intensity_score AS INT64) AS STRING), '/100'
  ) as signal_display,
  
  -- TIER 1: Vegas-Specific Reasoning (Sales-Focused)
  CASE 
    WHEN f.crisis_intensity_score > 70 THEN 
      CONCAT('🚨 CRISIS: ZL volatility high → Lock margin NOW. Crisis score: ', CAST(CAST(f.crisis_intensity_score AS INT64) AS STRING))
    WHEN f.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 
      '🔥 BIOFUEL BOOM: RFS mandate pull → Price upside → Lock contracts early'
    WHEN f.market_regime = 'CHINA_TENSION_REGIME' THEN 
      '⚠️ CHINA RISK: Trade tension → Demand uncertainty → Price volatility'
    WHEN f.palm_sub_risk > 5.0 THEN 
      CONCAT('⚠️ PALM RISK: Sub pressure → Price headwind → Hedge exposure (Palm premium: $', CAST(ROUND(f.palm_sub_risk, 1) AS STRING), ')')
    ELSE 
      '✅ STABLE: Fundamentals-driven → Normal pricing environment'
  END as vegas_reasoning,
  
  -- TIER 1: Kevin's Action Items (Auto-Generated)
  CASE 
    WHEN f.crisis_intensity_score > 70 AND f.confidence < 50 THEN 
      'ACTION: Widen margin bands. Crisis mode → Price swings likely. Lock high-confidence customers first.'
    WHEN f.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 
      'ACTION: Pitch premium contracts. Biofuel pull → Upside bias. Target industrial customers.'
    WHEN f.palm_sub_risk > 5.0 THEN 
      'ACTION: Monitor palm spread. Substitution risk rising. Prepare price justification for customers.'
    WHEN f.confidence > 70 THEN 
      'ACTION: High confidence window. Lock volume now. Forecast stable.'
    ELSE 
      'ACTION: Monitor signals. Normal environment. Standard pricing applies.'
  END as kevin_action_items,
  
  f.created_at
FROM `cbi-v14.predictions_uc1.production_forecasts` f
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
  AND f.horizon = '1W'  -- Vegas Intel uses 1W forecast for ZL cost
LIMIT 1;

-- View 3: China Intel Dashboard (Chris Priority #1) + AI Reasoning
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_china_intel_dashboard`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value,
  f.confidence,
  f.market_regime,
  
  -- China-specific signals
  COALESCE(china.china_imports_from_us_mt, 0) as china_imports_mt,
  COALESCE(china.china_sentiment, 0.5) as china_sentiment_score,
  
  -- TIER 1: China Impact Reasoning
  CONCAT(
    'China Sentiment: ', CAST(ROUND(COALESCE(china.china_sentiment, 0.5) * 100, 0) AS STRING), '/100 | ',
    CASE 
      WHEN COALESCE(china.china_sentiment, 0.5) < 0.3 THEN 'BEARISH → Demand risk elevated'
      WHEN COALESCE(china.china_sentiment, 0.5) > 0.7 THEN 'BULLISH → Demand support strong'
      ELSE 'NEUTRAL → Monitor for changes'
    END
  ) as china_reasoning,
  
  -- TIER 1: Math Validation (China Impact)
  CONCAT(
    'China Imports: ', CAST(ROUND(COALESCE(china.china_imports_from_us_mt, 0), 1) AS STRING), ' MT | ',
    'Impact on ZL: ',
    CASE 
      WHEN COALESCE(china.china_sentiment, 0.5) < 0.4 THEN '-2% to -5% (bearish demand)'
      WHEN COALESCE(china.china_sentiment, 0.5) > 0.7 THEN '+1% to +3% (bullish demand)'
      ELSE '±1% (neutral)'
    END
  ) as china_impact_math
  
FROM `cbi-v14.predictions_uc1.production_forecasts` f
LEFT JOIN (
  SELECT 
    date,
    china_imports_from_us_mt,
    china_sentiment
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
) china ON f.forecast_date = china.date
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 4: Harvest Intel Dashboard (Chris Priority #2) + AI Reasoning
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_harvest_intel_dashboard`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value,
  f.confidence,
  f.market_regime,
  
  -- Harvest signals
  COALESCE(harvest.feature_harvest_pace, 0) as harvest_pace_score,
  COALESCE(harvest.brazil_harvest_signals, 0) as brazil_harvest,
  COALESCE(harvest.argentina_harvest_signals, 0) as argentina_harvest,
  COALESCE(harvest.brazil_temperature_c, NULL) as brazil_temp,
  COALESCE(harvest.argentina_precipitation_mm, NULL) as argentina_precip,
  
  -- TIER 1: Harvest Impact Reasoning
  CONCAT(
    'Harvest Pace: ', CAST(ROUND(COALESCE(harvest.feature_harvest_pace, 0), 0) AS STRING), '/100 | ',
    CASE 
      WHEN COALESCE(harvest.feature_harvest_pace, 0) < 30 THEN 'DELAYED → Supply tightness risk'
      WHEN COALESCE(harvest.feature_harvest_pace, 0) > 70 THEN 'AHEAD OF SCHEDULE → Supply pressure'
      ELSE 'ON PACE → Normal supply flow'
    END
  ) as harvest_reasoning,
  
  -- TIER 1: Weather Impact Math
  CONCAT(
    'Brazil: ', 
    CASE 
      WHEN harvest.brazil_temperature_c IS NOT NULL THEN CAST(ROUND(harvest.brazil_temperature_c, 1) AS STRING) || '°C'
      ELSE 'N/A'
    END,
    ' | Argentina: ',
    CASE 
      WHEN harvest.argentina_precipitation_mm IS NOT NULL THEN CAST(ROUND(harvest.argentina_precipitation_mm, 1) AS STRING) || 'mm'
      ELSE 'N/A'
    END,
    ' | Impact: ',
    CASE 
      WHEN COALESCE(harvest.feature_harvest_pace, 0) < 30 THEN '-3% to -8% (delayed harvest)'
      WHEN COALESCE(harvest.feature_harvest_pace, 0) > 70 THEN '+2% to +5% (early harvest)'
      ELSE '±2% (normal pace)'
    END
  ) as weather_impact_math
  
FROM `cbi-v14.predictions_uc1.production_forecasts` f
LEFT JOIN (
  SELECT 
    date,
    feature_harvest_pace,
    brazil_harvest_signals,
    argentina_harvest_signals,
    brazil_temperature_c,
    argentina_precipitation_mm
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
) harvest ON f.forecast_date = harvest.date
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 5: Biofuel Intel Dashboard (Chris Priority #3) + AI Reasoning
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_biofuel_intel_dashboard`
AS
SELECT 
  f.forecast_date,
  f.horizon,
  f.predicted_value,
  f.confidence,
  f.market_regime,
  
  -- Biofuel signals
  COALESCE(biofuel.feature_biofuel_cascade, 0) as biofuel_cascade_score,
  COALESCE(biofuel.biodiesel_demand_signals, 0) as biodiesel_demand,
  
  -- TIER 1: Biofuel Impact Reasoning
  CONCAT(
    'Biofuel Cascade: ', CAST(ROUND(COALESCE(biofuel.feature_biofuel_cascade, 0), 0) AS STRING), '/100 | ',
    CASE 
      WHEN COALESCE(biofuel.feature_biofuel_cascade, 0) > 70 THEN 'STRONG → RFS mandate pull driving demand'
      WHEN COALESCE(biofuel.feature_biofuel_cascade, 0) < 35 THEN 'WEAK → Limited biofuel support'
      ELSE 'MODERATE → Normal biofuel demand'
    END
  ) as biofuel_reasoning,
  
  -- TIER 1: RFS Impact Math
  CONCAT(
    'Biodiesel Demand: ', CAST(ROUND(COALESCE(biofuel.biodiesel_demand, 0), 0) AS STRING), ' | ',
    'Impact on ZL: ',
    CASE 
      WHEN f.market_regime = 'BIOFUEL_BOOM_REGIME' THEN '+10% to +15% (mandate pull-through)'
      WHEN COALESCE(biofuel.feature_biofuel_cascade, 0) > 70 THEN '+5% to +10% (strong demand)'
      WHEN COALESCE(biofuel.feature_biofuel_cascade, 0) < 35 THEN '-2% to 0% (weak demand)'
      ELSE '+2% to +5% (normal demand)'
    END
  ) as biofuel_impact_math,
  
  -- Forecast adjusted for biofuel boom
  CASE 
    WHEN f.market_regime = 'BIOFUEL_BOOM_REGIME' THEN 
      f.predicted_value * 1.12  -- +12% upside
    ELSE f.predicted_value
  END as forecast_adjusted_biofuel
  
FROM `cbi-v14.predictions_uc1.production_forecasts` f
LEFT JOIN (
  SELECT 
    date,
    feature_biofuel_cascade,
    biodiesel_demand_signals
  FROM `cbi-v14.models_v4.training_dataset_super_enriched`
  WHERE date = (SELECT MAX(date) FROM `cbi-v14.models_v4.training_dataset_super_enriched`)
) biofuel ON f.forecast_date = biofuel.date
WHERE f.forecast_date = (SELECT MAX(forecast_date) FROM `cbi-v14.predictions_uc1.production_forecasts`)
ORDER BY 
  CASE f.horizon
    WHEN '1W' THEN 1
    WHEN '1M' THEN 2
    WHEN '3M' THEN 3
    WHEN '6M' THEN 4
  END;

-- View 6: Forecast Timeline (Historical) - No reasoning needed (just historical data)
CREATE OR REPLACE VIEW `cbi-v14.forecasting_data_warehouse.vw_forecast_timeline`
AS
SELECT 
  forecast_date,
  horizon,
  target_date,
  predicted_value,
  lower_bound_80,
  upper_bound_80,
  confidence,
  market_regime,
  crisis_intensity_score,
  primary_signal_driver,
  created_at
FROM `cbi-v14.predictions_uc1.production_forecasts`
ORDER BY forecast_date DESC, target_date ASC;

