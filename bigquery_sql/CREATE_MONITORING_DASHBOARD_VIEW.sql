-- ============================================
-- CREATE MONITORING DASHBOARD VIEW
-- ============================================
-- Purpose: Aggregate monitoring checks for dashboard display
-- Dataset: cbi-v14.api
-- View: vw_prediction_monitoring
-- ============================================

CREATE OR REPLACE VIEW `cbi-v14.api.vw_prediction_monitoring` AS
SELECT 
  check_date,
  check_type,
  status,
  COUNT(*) as check_count,
  MAX(created_at) as last_check,
  STRING_AGG(DISTINCT message LIMIT 5) as sample_messages
FROM `cbi-v14.predictions_uc1.monitoring_checks`
WHERE check_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY check_date, check_type, status
ORDER BY check_date DESC, check_type, status;

-- ============================================
-- VERIFICATION
-- ============================================
-- Check view returns data
/*
SELECT * FROM `cbi-v14.api.vw_prediction_monitoring`
ORDER BY check_date DESC
LIMIT 20;
*/

