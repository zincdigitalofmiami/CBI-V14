-- Build INSERT statement with proper type handling
-- Generates NULL casts for all columns except explicitly populated ones

SELECT CONCAT(
  'CAST(NULL AS ', data_type, ') AS `', column_name, '`,'
) AS col_def
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND column_name NOT IN (
    'date','zl_price_current','zl_price_lag1','zl_price_lag7','zl_price_lag30',
    'return_1d','return_7d','ma_7d','ma_30d','volatility_30d','zl_volume',
    'feature_vix_stress','feature_harvest_pace','feature_china_relations',
    'feature_tariff_threat','feature_geopolitical_volatility','feature_biofuel_cascade',
    'feature_hidden_correlation','feature_biofuel_ethanol','big8_composite_score',
    'market_regime','fx_usd_ars_30d_z','fx_usd_myr_30d_z',
    'target_1w','target_1m','target_3m','还是会'
  )
ORDER BY ordinal_position;



