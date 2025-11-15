-- ============================================
-- LAG ALIGNMENT CHECK
-- Verify all event/policy features use t-1 (causal alignment)
-- Date: November 2025
-- ============================================

-- Check that all policy/event features are properly lagged
-- Rule: Use t-1 for all (causal) - features should predict future, not current

CREATE OR REPLACE TABLE `cbi-v14.models_v4.lag_alignment_audit` AS
WITH current_data AS (
  SELECT 
    date,
    trump_policy_events,
    trade_war_intensity,
    news_intelligence_7d,
    argentina_export_tax
  FROM `cbi-v14.training.zl_training_prod_allhistory_1m`
  WHERE date >= '2024-01-01'
),
lagged_data AS (
  SELECT 
    date,
    LAG(trump_policy_events, 1) OVER (ORDER BY date) as trump_policy_events_lag1,
    LAG(trade_war_intensity, 1) OVER (ORDER BY date) as trade_war_intensity_lag1,
    LAG(news_intelligence_7d, 1) OVER (ORDER BY date) as news_intelligence_7d_lag1,
    LAG(argentina_export_tax, 1) OVER (ORDER BY date) as argentina_export_tax_lag1
  FROM current_data
),
alignment_check AS (
  SELECT 
    cd.date,
    -- Check if current features match lagged (should NOT match for causal alignment)
    CASE 
      WHEN cd.trump_policy_events = ld.trump_policy_events_lag1 THEN 'MISALIGNED'
      ELSE 'ALIGNED'
    END as trump_alignment,
    CASE 
      WHEN cd.trade_war_intensity = ld.trade_war_intensity_lag1 THEN 'MISALIGNED'
      ELSE 'ALIGNED'
    END as trade_alignment,
    CASE 
      WHEN cd.news_intelligence_7d = ld.news_intelligence_7d_lag1 THEN 'MISALIGNED'
      ELSE 'ALIGNED'
    END as news_alignment,
    CASE 
      WHEN cd.argentina_export_tax = ld.argentina_export_tax_lag1 THEN 'MISALIGNED'
      ELSE 'ALIGNED'
    END as argentina_alignment
  FROM current_data cd
  JOIN lagged_data ld ON cd.date = ld.date
)
SELECT 
  cd.date,
  ac.trump_alignment,
  ac.trade_alignment,
  ac.news_alignment,
  ac.argentina_alignment
FROM alignment_check ac;

-- Show sample misalignments
SELECT 
  date,
  trump_alignment,
  trade_alignment,
  news_alignment,
  argentina_alignment
FROM `cbi-v14.models_v4.lag_alignment_audit`
WHERE trump_alignment = 'MISALIGNED' 
   OR trade_alignment = 'MISALIGNED'
   OR news_alignment = 'MISALIGNED'
   OR argentina_alignment = 'MISALIGNED'
LIMIT 10;

