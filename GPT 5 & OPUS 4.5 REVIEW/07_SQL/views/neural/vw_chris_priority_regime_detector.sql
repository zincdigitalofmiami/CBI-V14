-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

CREATE OR REPLACE VIEW `cbi-v14.neural.vw_chris_priority_regime_detector` AS
SELECT
  b8.*,

  -- Normalize/alias labor/ICE risk if naming varies across sources
  COALESCE(b8.feature_ice_labor_disruption, b8.feature_labor_disruption, 0.0) AS feature_labor_stress,

  -- Primary labor override flag (dominance test)
  CASE
    WHEN ABS(COALESCE(b8.feature_ice_labor_disruption, b8.feature_labor_disruption, 0.0)) >= GREATEST(
           ABS(COALESCE(b8.feature_vix_stress, 0.0)),
           ABS(COALESCE(b8.feature_harvest_pace, 0.0)),
           ABS(COALESCE(b8.feature_china_relations, 0.0)),
           ABS(COALESCE(b8.feature_tariff_probability, 0.0)),
           ABS(COALESCE(b8.feature_geopolitical_volatility, 0.0)),
           ABS(COALESCE(b8.feature_biofuel_impact, 0.0)),
           ABS(COALESCE(b8.feature_hidden_correlation, 0.0))
         )
    THEN TRUE ELSE FALSE END AS labor_override_flag,

  -- Primary driver attribution including labor
  CASE
    WHEN labor_override_flag THEN 'labor_stress'
    WHEN ABS(COALESCE(b8.feature_vix_stress,0)) >= ABS(COALESCE(b8.feature_harvest_pace,0))
         AND ABS(COALESCE(b8.feature_vix_stress,0)) >= ABS(COALESCE(b8.feature_china_relations,0)) THEN 'vix_stress'
    WHEN ABS(COALESCE(b8.feature_harvest_pace,0)) >= ABS(COALESCE(b8.feature_china_relations,0)) THEN 'harvest_pace'
    ELSE 'china_relations'
  END AS primary_signal_driver_labor_aware
FROM `cbi-v14.neural.vw_big_eight_signals` b8;







