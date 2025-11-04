# BigQuery ML Models - Complete Audit Report

**Generated:** 2025-11-04T11:37:49.870003
**Project:** cbi-v14
**Dataset:** models_v4

---

📊 SUMMARY
Total Models: 24
Credible for Use: 17
Review Needed: 7

================================================================================
MODEL: arima_baseline_1m
================================================================================

📍 Location: cbi-v14.models_v4.arima_baseline_1m
📅 Created: 2025-10-28 15:30:46.628000+00:00
🔄 Modified: 2025-10-28 15:30:46.703000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (2 files):
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/oct31_2025_cleanup/automl_legacy/TRAINING_STATUS.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 7 days old

🎯 Inferred Purpose:
   - 1 Month forecast horizon
   - ARIMA time series model

================================================================================
MODEL: arima_baseline_1w
================================================================================

📍 Location: cbi-v14.models_v4.arima_baseline_1w
📅 Created: 2025-10-28 15:30:45.001000+00:00
🔄 Modified: 2025-10-28 15:30:45.085000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (6 files):
   - scripts/train_baseline_models.py
   - docs/ENSEMBLE_ARCHITECTURE_PLAN.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/COMPLETE_IMPLEMENTATION_SUMMARY.md
   - archive/md_status_oct27/FINAL_STATUS_2025-10-22.md
   - archive/oct31_2025_cleanup/automl_legacy/TRAINING_STATUS.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 7 days old

🎯 Inferred Purpose:
   - 1 Week forecast horizon
   - ARIMA time series model

================================================================================
MODEL: arima_baseline_3m
================================================================================

📍 Location: cbi-v14.models_v4.arima_baseline_3m
📅 Created: 2025-10-28 15:30:47.128000+00:00
🔄 Modified: 2025-10-28 15:30:47.211000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (2 files):
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/oct31_2025_cleanup/automl_legacy/TRAINING_STATUS.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 7 days old

🎯 Inferred Purpose:
   - 3 Month forecast horizon
   - ARIMA time series model

================================================================================
MODEL: arima_baseline_6m
================================================================================

📍 Location: cbi-v14.models_v4.arima_baseline_6m
📅 Created: 2025-10-28 15:30:48.899000+00:00
🔄 Modified: 2025-10-28 15:30:48.964000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (2 files):
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/oct31_2025_cleanup/automl_legacy/TRAINING_STATUS.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 7 days old

🎯 Inferred Purpose:
   - 6 Month forecast horizon
   - ARIMA time series model

================================================================================
MODEL: baseline_boosted_tree_1m_v14_FINAL
================================================================================

📍 Location: cbi-v14.models_v4.baseline_boosted_tree_1m_v14_FINAL
📅 Created: 2025-10-28 00:56:08.416000+00:00
🔄 Modified: 2025-10-28 00:56:08.557000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1347
   - Date Range: 2020-01-06 to 2025-09-10
   - Distinct Dates: 1347

📈 Evaluation Metrics:
   - MAE: 4.2305
   - RMSE: 6.9705
   - R²: 0.7099
   - Explained Variance: N/A
   - MAPE: 10.31%

⚠️  Training Errors: 3
   - Job bfceaef6-6f6c-4af6-a3ff-185b0dd3740a: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 658cc3be-9a3f-4936-919f-2d7c71c6f780: Column vix_index in SELECT * EXCEPT list does not exist at [16:145]
   - Job cc8d74b3-03c4-4bcd-9965-36d4956ae0d6: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.

📝 Used in Codebase (6 files):
   - archive/legacy_cleanup_oct28_2025/validate_baseline_forecasts.py
   - archive/legacy_cleanup_oct28_2025/monitor_forecasts.py
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/legacy_cleanup_oct28_2025/BASELINE_TRAINING_SUCCESS_REPORT.md
   - archive/legacy_cleanup_oct28_2025/FINAL_STATUS_BASELINE_V14_COMPLETE.md
   - archive/legacy_cleanup_oct28_2025/TRAINED_MODELS_REGISTRY.md

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Sufficient training data: 1347 rows
     ✅ Good R²: 0.7099
     ✅ Recent model: 7 days old

   Issues:
     ⚠️  High MAE: 4.2305
     ⚠️  High MAPE: 10.31%
     ⚠️  Training errors found: 3

🎯 Inferred Purpose:
   - 1 Month forecast horizon

================================================================================
MODEL: baseline_boosted_tree_1w_v14_FINAL
================================================================================

📍 Location: cbi-v14.models_v4.baseline_boosted_tree_1w_v14_FINAL
📅 Created: 2025-10-28 00:51:13.066000+00:00
🔄 Modified: 2025-10-28 00:51:13.179000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1448
   - Date Range: 2020-01-02 to 2025-10-13
   - Distinct Dates: 1448

📈 Evaluation Metrics:
   - MAE: 4.1519
   - RMSE: 7.2491
   - R²: 0.7243
   - Explained Variance: N/A
   - MAPE: 11.53%

⚠️  Training Errors: 2
   - Job 1b92d120-ad11-4f95-9789-dc260f366cb7: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 766ca6fe-afcf-4ff5-988e-71f37fdb39fe: Column vix_index in SELECT * EXCEPT list does not exist at [16:145]

📝 Used in Codebase (6 files):
   - archive/legacy_cleanup_oct28_2025/validate_baseline_forecasts.py
   - archive/legacy_cleanup_oct28_2025/monitor_forecasts.py
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/legacy_cleanup_oct28_2025/BASELINE_TRAINING_SUCCESS_REPORT.md
   - archive/legacy_cleanup_oct28_2025/FINAL_STATUS_BASELINE_V14_COMPLETE.md
   - archive/legacy_cleanup_oct28_2025/TRAINED_MODELS_REGISTRY.md

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Sufficient training data: 1448 rows
     ✅ Good R²: 0.7243
     ✅ Recent model: 7 days old

   Issues:
     ⚠️  High MAE: 4.1519
     ⚠️  High MAPE: 11.53%
     ⚠️  Training errors found: 2

🎯 Inferred Purpose:
   - 1 Week forecast horizon

================================================================================
MODEL: baseline_boosted_tree_3m_v14_FINAL
================================================================================

📍 Location: cbi-v14.models_v4.baseline_boosted_tree_3m_v14_FINAL
📅 Created: 2025-10-28 01:01:01.898000+00:00
🔄 Modified: 2025-10-28 01:01:01.980000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1329
   - Date Range: 2020-01-02 to 2025-06-13
   - Distinct Dates: 1329

📈 Evaluation Metrics:
   - MAE: 6.7205
   - RMSE: 10.9567
   - R²: 0.3028
   - Explained Variance: N/A
   - MAPE: 16.61%

⚠️  Training Errors: 3
   - Job 33dea857-ca4e-48e5-8bed-9e3a297c24dd: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 92cccf6d-5343-4d60-baed-5b504cf2145c: Column vix_index in SELECT * EXCEPT list does not exist at [16:145]
   - Job ce169671-94e4-435a-b76b-669a4a81766a: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.

📝 Used in Codebase (6 files):
   - archive/legacy_cleanup_oct28_2025/validate_baseline_forecasts.py
   - archive/legacy_cleanup_oct28_2025/monitor_forecasts.py
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/legacy_cleanup_oct28_2025/BASELINE_TRAINING_SUCCESS_REPORT.md
   - archive/legacy_cleanup_oct28_2025/FINAL_STATUS_BASELINE_V14_COMPLETE.md
   - archive/legacy_cleanup_oct28_2025/TRAINED_MODELS_REGISTRY.md

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Sufficient training data: 1329 rows
     ✅ Recent model: 7 days old

   Issues:
     ⚠️  High MAE: 6.7205
     ⚠️  High MAPE: 16.61%
     ⚠️  Poor R²: 0.3028
     ⚠️  Training errors found: 3

🎯 Inferred Purpose:
   - 3 Month forecast horizon

================================================================================
MODEL: baseline_boosted_tree_6m_v14_FINAL
================================================================================

📍 Location: cbi-v14.models_v4.baseline_boosted_tree_6m_v14_FINAL
📅 Created: 2025-10-28 01:05:58.598000+00:00
🔄 Modified: 2025-10-28 01:05:58.705000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1198
   - Date Range: 2020-01-02 to 2025-02-04
   - Distinct Dates: 1198

📈 Evaluation Metrics:
   - MAE: 3.6522
   - RMSE: 6.7708
   - R²: 0.6847
   - Explained Variance: N/A
   - MAPE: 8.42%

⚠️  Training Errors: 3
   - Job 66742f07-179a-434b-b49f-614e951ea191: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 1045037f-4509-4d8c-ab53-2b113a08d80e: Column vix_index in SELECT * EXCEPT list does not exist at [16:145]
   - Job aaa8d48f-a14c-4a0d-8d48-e6b420652f2b: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.

📝 Used in Codebase (6 files):
   - archive/legacy_cleanup_oct28_2025/validate_baseline_forecasts.py
   - archive/legacy_cleanup_oct28_2025/monitor_forecasts.py
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/legacy_cleanup_oct28_2025/BASELINE_TRAINING_SUCCESS_REPORT.md
   - archive/legacy_cleanup_oct28_2025/FINAL_STATUS_BASELINE_V14_COMPLETE.md
   - archive/legacy_cleanup_oct28_2025/TRAINED_MODELS_REGISTRY.md

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Sufficient training data: 1198 rows
     ✅ Recent model: 7 days old

   Issues:
     ⚠️  High MAE: 3.6522
     ⚠️  Moderate MAPE: 8.42%
     ⚠️  Moderate R²: 0.6847
     ⚠️  Training errors found: 3

🎯 Inferred Purpose:
   - 6 Month forecast horizon

================================================================================
MODEL: bqml_1m
================================================================================

📍 Location: cbi-v14.models_v4.bqml_1m
📅 Created: 2025-11-04 17:29:13.457000+00:00
🔄 Modified: 2025-11-04 17:29:13.529000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1347
   - Date Range: 2020-01-06 to 2025-09-10
   - Distinct Dates: 1347

📈 Evaluation Metrics:
   - MAE: 0.3758
   - RMSE: 0.6673
   - R²: 0.9973
   - Explained Variance: N/A
   - MAPE: 0.72%

⚠️  Training Errors: 4
   - Job script_job_63416fff9b4f0cdbf4a3ee0651ab2260_1: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 7211c7f2-7acd-413f-abf1-2f467728e239: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 08a249f3-ed22-4d08-ad54-9d2dac19031d: Failed to calculate mean since the entries in corresponding column 'treasury_10y_yield' are all NULLs.

📝 Used in Codebase (35 files):
   - bigquery_sql/train_1m_model.sql
   - bigquery_sql/train_maximum_power.sql
   - bigquery_sql/train_all_horizons_clean.sql
   - bigquery_sql/train_bqml_1m_mean.sql
   - bigquery_sql/COMPARE_1W_1M_MAPE.sql
   - bigquery_sql/train_all_models_optimized.sql
   - bigquery_sql/CALCULATE_MAPE_1M.sql
   - bigquery_sql/GET_REAL_MAPE_MANUAL_CALC.sql
   - bigquery_sql/GET_REAL_MAPE_ALL_MODELS.sql
   - bigquery_sql/TRAIN_BQML_1M_FRESH.sql

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Sufficient training data: 1347 rows
     ✅ Excellent MAE: 0.3758
     ✅ Excellent MAPE: 0.72%
     ✅ Excellent R²: 0.9973
     ✅ Recent model: 0 days old

   Issues:
     ⚠️  Training errors found: 4

🎯 Inferred Purpose:
   - 1 Month forecast horizon
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_1m_all_features
================================================================================

📍 Location: cbi-v14.models_v4.bqml_1m_all_features
📅 Created: 2025-11-04 01:19:05.733000+00:00
🔄 Modified: 2025-11-04 01:19:05.802000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1347
   - Date Range: 2020-01-06 to 2025-09-10
   - Distinct Dates: 1347

📈 Evaluation Metrics:
   - MAE: 0.6969
   - RMSE: 0.9801
   - R²: 0.9943
   - Explained Variance: N/A
   - MAPE: 1.29%

⚠️  Training Errors: 1
   - Job script_job_63416fff9b4f0cdbf4a3ee0651ab2260_1: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.

📝 Used in Codebase (9 files):
   - bigquery_sql/COMPARE_1W_1M_MAPE.sql
   - bigquery_sql/CALCULATE_MAPE_1M.sql
   - bigquery_sql/GET_REAL_MAPE_MANUAL_CALC.sql
   - bigquery_sql/GET_REAL_MAPE_ALL_MODELS.sql
   - bigquery_sql/TRAIN_BQML_1M_FRESH.sql
   - docs/MODEL_PROTECTION_GUIDE.md
   - docs/CORRECTED_BILLING_ANALYSIS.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - docs/CBI_V14_COMPLETE_EXECUTION_PLAN.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Sufficient training data: 1347 rows
     ✅ Excellent MAE: 0.6969
     ✅ Excellent MAPE: 1.29%
     ✅ Excellent R²: 0.9943
     ✅ Recent model: 0 days old

   Issues:
     ⚠️  Training errors found: 1

🎯 Inferred Purpose:
   - 1 Month forecast horizon
   - Uses all available features
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_1m_mean
================================================================================

📍 Location: cbi-v14.models_v4.bqml_1m_mean
📅 Created: 2025-11-02 23:37:21.349000+00:00
🔄 Modified: 2025-11-02 23:37:21.441000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

⚠️  Training Errors: 3
   - Job 7211c7f2-7acd-413f-abf1-2f467728e239: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 08a249f3-ed22-4d08-ad54-9d2dac19031d: Failed to calculate mean since the entries in corresponding column 'treasury_10y_yield' are all NULLs.
   - Job d552ce3e-b492-42c3-9296-7ca92562d2cc: Training option MIN_REL_PROGRESS can be used only when EARLY_STOP is true.

📝 Used in Codebase (24 files):
   - bigquery_sql/train_all_horizons_clean.sql
   - bigquery_sql/train_bqml_1m_mean.sql
   - bigquery_sql/train_all_models_optimized.sql
   - scripts/train_all_models_fixed.py
   - scripts/training_readiness_audit_deep.py
   - scripts/populate_feature_importance.py
   - scripts/comprehensive_training_audit.py
   - scripts/train_all_models_optimized.py
   - scripts/execute_phase_1.py
   - scripts/check_model_status.py

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Recent model: 1 days old

   Issues:
     ⚠️  Training errors found: 3

🎯 Inferred Purpose:
   - 1 Month forecast horizon
   - May use mean imputation or aggregation
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_1w
================================================================================

📍 Location: cbi-v14.models_v4.bqml_1w
📅 Created: 2025-11-04 17:25:44.563000+00:00
🔄 Modified: 2025-11-04 17:25:44.632000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1448
   - Date Range: 2020-01-02 to 2025-10-13
   - Distinct Dates: 1448

📈 Evaluation Metrics:
   - MAE: 0.3769
   - RMSE: 0.6438
   - R²: 0.9978
   - Explained Variance: N/A
   - MAPE: 0.74%

⚠️  Training Errors: 37
   - Job script_job_4b65b95759d17c2d1fe98034dfe2dc86_1: Failed to calculate mean since the entries in corresponding column 'social_sentiment_volatility' are all NULLs.
   - Job script_job_9c57a4ff23a006d2a5170db29736a488_1: Failed to calculate mean since the entries in corresponding column 'trump_soybean_sentiment_7d' are all NULLs.
   - Job script_job_9aa8ca6fc075b4204c5caadce676b0dd_1: Duplicate column econ_gdp_growth in SELECT * EXCEPT list at [44:5]

📝 Used in Codebase (62 files):
   - bigquery_sql/FINAL_BQML_TRAINING_QUERY.sql
   - bigquery_sql/BQML_1W.sql
   - bigquery_sql/train_maximum_power.sql
   - bigquery_sql/CALCULATE_MAPE_COMPARISON.sql
   - bigquery_sql/train_1w_with_all_data.sql
   - bigquery_sql/train_1w_clean.sql
   - bigquery_sql/train_all_horizons_clean.sql
   - bigquery_sql/TRAIN_BQML_1W_FRESH.sql
   - bigquery_sql/train_with_null_handling.sql
   - bigquery_sql/COMPARE_1W_1M_MAPE.sql

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Sufficient training data: 1448 rows
     ✅ Excellent MAE: 0.3769
     ✅ Excellent MAPE: 0.74%
     ✅ Excellent R²: 0.9978
     ✅ Recent model: 0 days old

   Issues:
     ⚠️  Training errors found: 37

🎯 Inferred Purpose:
   - 1 Week forecast horizon
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_1w_all_features
================================================================================

📍 Location: cbi-v14.models_v4.bqml_1w_all_features
📅 Created: 2025-11-04 00:35:41.519000+00:00
🔄 Modified: 2025-11-04 00:35:41.592000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1448
   - Date Range: 2020-01-02 to 2025-10-13
   - Distinct Dates: 1448

📈 Evaluation Metrics:
   - MAE: 0.6393
   - RMSE: 0.9129
   - R²: 0.9956
   - Explained Variance: N/A
   - MAPE: 1.21%

⚠️  Training Errors: 2
   - Job script_job_4b65b95759d17c2d1fe98034dfe2dc86_1: Failed to calculate mean since the entries in corresponding column 'social_sentiment_volatility' are all NULLs.
   - Job script_job_78986bcce89087b87e5861d446ae9261_1: Failed to calculate mean since the entries in corresponding column 'treasury_10y_yield' are all NULLs.

📝 Used in Codebase (19 files):
   - bigquery_sql/FINAL_BQML_TRAINING_QUERY.sql
   - bigquery_sql/CALCULATE_MAPE_COMPARISON.sql
   - bigquery_sql/TRAIN_BQML_1W_FRESH.sql
   - bigquery_sql/COMPARE_1W_1M_MAPE.sql
   - bigquery_sql/train_all_features_with_nulls.sql
   - bigquery_sql/GET_REAL_MAPE_MANUAL_CALC.sql
   - bigquery_sql/GET_REAL_MAPE_ALL_MODELS.sql
   - docs/MODEL_PROTECTION_GUIDE.md
   - docs/FINAL_TRAINING_STATUS.md
   - docs/BQML_NULL_HANDLING_ANALYSIS.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Sufficient training data: 1448 rows
     ✅ Excellent MAE: 0.6393
     ✅ Excellent MAPE: 1.21%
     ✅ Excellent R²: 0.9956
     ✅ Recent model: 0 days old

   Issues:
     ⚠️  Training errors found: 2

🎯 Inferred Purpose:
   - 1 Week forecast horizon
   - Uses all available features
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_3m_all_features
================================================================================

📍 Location: cbi-v14.models_v4.bqml_3m_all_features
📅 Created: 2025-11-04 01:51:37.687000+00:00
🔄 Modified: 2025-11-04 01:51:37.854000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1329
   - Date Range: 2020-01-02 to 2025-06-13
   - Distinct Dates: 1329

📈 Evaluation Metrics:
   - MAE: 0.3704
   - RMSE: 0.6271
   - R²: 0.9977
   - Explained Variance: N/A
   - MAPE: 0.70%

⚠️  Training Errors: 2
   - Job script_job_98f8aa0deb7e15460b7f2bd083cf9dd4_1: Failed to calculate mean since the entries in corresponding column 'trump_soybean_sentiment_7d' are all NULLs.
   - Job script_job_9c76ee91d26bcfce34ddb61e12352ab8_1: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.

📝 Used in Codebase (8 files):
   - bigquery_sql/CALCULATE_MAPE_3M.sql
   - bigquery_sql/TRAIN_BQML_3M_FRESH.sql
   - bigquery_sql/GET_REAL_MAPE_MANUAL_CALC.sql
   - bigquery_sql/GET_REAL_MAPE_ALL_MODELS.sql
   - docs/MODEL_PROTECTION_GUIDE.md
   - docs/CORRECTED_BILLING_ANALYSIS.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - docs/CBI_V14_COMPLETE_EXECUTION_PLAN.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Sufficient training data: 1329 rows
     ✅ Excellent MAE: 0.3704
     ✅ Excellent MAPE: 0.70%
     ✅ Excellent R²: 0.9977
     ✅ Recent model: 0 days old

   Issues:
     ⚠️  Training errors found: 2

🎯 Inferred Purpose:
   - 3 Month forecast horizon
   - Uses all available features
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_3m_mean
================================================================================

📍 Location: cbi-v14.models_v4.bqml_3m_mean
📅 Created: 2025-11-02 23:40:23.876000+00:00
🔄 Modified: 2025-11-02 23:40:23.935000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

⚠️  Training Errors: 3
   - Job c98937fd-6f91-40b1-bb8c-ea5bc6d6c6c7: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job ea99420e-6b52-48ee-8f9b-acd982293174: Failed to calculate mean since the entries in corresponding column 'treasury_10y_yield' are all NULLs.
   - Job fd6423d1-ed7e-4ffa-b1d0-bbcac21180b6: Training option MIN_REL_PROGRESS can be used only when EARLY_STOP is true.

📝 Used in Codebase (23 files):
   - bigquery_sql/train_all_horizons_clean.sql
   - bigquery_sql/train_all_models_optimized.sql
   - bigquery_sql/train_bqml_3m_mean.sql
   - scripts/train_all_models_fixed.py
   - scripts/training_readiness_audit_deep.py
   - scripts/populate_feature_importance.py
   - scripts/comprehensive_training_audit.py
   - scripts/train_all_models_optimized.py
   - scripts/execute_phase_1.py
   - scripts/check_model_status.py

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Recent model: 1 days old

   Issues:
     ⚠️  Training errors found: 3

🎯 Inferred Purpose:
   - 3 Month forecast horizon
   - May use mean imputation or aggregation
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_6m_all_features
================================================================================

📍 Location: cbi-v14.models_v4.bqml_6m_all_features
📅 Created: 2025-11-04 01:59:24.037000+00:00
🔄 Modified: 2025-11-04 01:59:24.189000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📊 Training Data:
   - Rows: 1198
   - Date Range: 2020-01-02 to 2025-02-04
   - Distinct Dates: 1198

📈 Evaluation Metrics:
   - MAE: 0.6563
   - RMSE: 0.9101
   - R²: 0.9943
   - Explained Variance: N/A
   - MAPE: 1.21%

⚠️  Training Errors: 8
   - Job script_job_b69327e14d8360bd976fdb0b6e28a747_1: Failed to calculate mean since the entries in corresponding column 'trade_policy_events' are all NULLs.
   - Job script_job_de9a3c3cca07deeb9a1a5c57fe2b3a94_1: Failed to calculate mean since the entries in corresponding column 'trump_policy_impact_avg' are all NULLs.
   - Job script_job_6897bacc0d18cb4cf9144b8b69d9fe3a_1: Failed to calculate mean since the entries in corresponding column 'trump_policy_events' are all NULLs.

📝 Used in Codebase (8 files):
   - bigquery_sql/TRAIN_BQML_6M_FRESH.sql
   - bigquery_sql/GET_REAL_MAPE_MANUAL_CALC.sql
   - bigquery_sql/CALCULATE_MAPE_6M.sql
   - bigquery_sql/GET_REAL_MAPE_ALL_MODELS.sql
   - docs/MODEL_PROTECTION_GUIDE.md
   - docs/CORRECTED_BILLING_ANALYSIS.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - docs/CBI_V14_COMPLETE_EXECUTION_PLAN.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Sufficient training data: 1198 rows
     ✅ Excellent MAE: 0.6563
     ✅ Excellent MAPE: 1.21%
     ✅ Excellent R²: 0.9943
     ✅ Recent model: 0 days old

   Issues:
     ⚠️  Training errors found: 8

🎯 Inferred Purpose:
   - 6 Month forecast horizon
   - Uses all available features
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: bqml_6m_mean
================================================================================

📍 Location: cbi-v14.models_v4.bqml_6m_mean
📅 Created: 2025-11-02 23:43:18.397000+00:00
🔄 Modified: 2025-11-02 23:43:18.467000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

⚠️  Training Errors: 3
   - Job 74332ff7-d68b-4e06-8576-df0cd0042d6f: Failed to calculate mean since the entries in corresponding column 'news_article_count' are all NULLs.
   - Job 53a99997-abec-46a0-bf35-c585d954a99a: Failed to calculate mean since the entries in corresponding column 'treasury_10y_yield' are all NULLs.
   - Job a725e7ec-de8d-4095-8813-a8ed58037ef6: Training option MIN_REL_PROGRESS can be used only when EARLY_STOP is true.

📝 Used in Codebase (23 files):
   - bigquery_sql/train_bqml_6m_mean.sql
   - bigquery_sql/train_all_horizons_clean.sql
   - bigquery_sql/train_all_models_optimized.sql
   - scripts/train_all_models_fixed.py
   - scripts/training_readiness_audit_deep.py
   - scripts/populate_feature_importance.py
   - scripts/comprehensive_training_audit.py
   - scripts/train_all_models_optimized.py
   - scripts/execute_phase_1.py
   - scripts/check_model_status.py

✅ Credibility Assessment:
   - Status: ⚠️  REVIEW NEEDED
   - Recommendation: REVIEW BEFORE USE

   Strengths:
     ✅ Recent model: 1 days old

   Issues:
     ⚠️  Training errors found: 3

🎯 Inferred Purpose:
   - 6 Month forecast horizon
   - May use mean imputation or aggregation
   - BigQuery ML model (BOOSTED_TREE_REGRESSOR)

================================================================================
MODEL: zl_arima_1m_v4
================================================================================

📍 Location: cbi-v14.models_v4.zl_arima_1m_v4
📅 Created: 2025-10-23 19:24:07.357000+00:00
🔄 Modified: 2025-10-23 19:24:07.451000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (5 files):
   - forecast/v4_model_predictions.py
   - models_v4/MODEL_REGISTRY.md
   - models_v4/V4_EVALUATION_REPORT.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/TRAINING_STATUS_OCT23.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 11 days old

🎯 Inferred Purpose:
   - 1 Month forecast horizon
   - ARIMA time series model

================================================================================
MODEL: zl_arima_1w_v4
================================================================================

📍 Location: cbi-v14.models_v4.zl_arima_1w_v4
📅 Created: 2025-10-23 19:23:58.180000+00:00
🔄 Modified: 2025-10-23 19:23:58.292000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (5 files):
   - forecast/v4_model_predictions.py
   - models_v4/MODEL_REGISTRY.md
   - models_v4/V4_EVALUATION_REPORT.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/TRAINING_STATUS_OCT23.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 11 days old

🎯 Inferred Purpose:
   - 1 Week forecast horizon
   - ARIMA time series model

================================================================================
MODEL: zl_arima_3m_v4
================================================================================

📍 Location: cbi-v14.models_v4.zl_arima_3m_v4
📅 Created: 2025-10-23 19:24:16.644000+00:00
🔄 Modified: 2025-10-23 19:24:16.762000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (5 files):
   - forecast/v4_model_predictions.py
   - models_v4/MODEL_REGISTRY.md
   - models_v4/V4_EVALUATION_REPORT.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/TRAINING_STATUS_OCT23.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 11 days old

🎯 Inferred Purpose:
   - 3 Month forecast horizon
   - ARIMA time series model

================================================================================
MODEL: zl_arima_6m_v4
================================================================================

📍 Location: cbi-v14.models_v4.zl_arima_6m_v4
📅 Created: 2025-10-23 19:24:27.009000+00:00
🔄 Modified: 2025-10-23 19:24:27.117000+00:00
🏷️  Model Type: ARIMA_PLUS
📍 Location: us-central1

📝 Used in Codebase (5 files):
   - forecast/v4_model_predictions.py
   - models_v4/MODEL_REGISTRY.md
   - models_v4/V4_EVALUATION_REPORT.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/TRAINING_STATUS_OCT23.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 11 days old

🎯 Inferred Purpose:
   - 6 Month forecast horizon
   - ARIMA time series model

================================================================================
MODEL: zl_baseline_clean_1w
================================================================================

📍 Location: cbi-v14.models_v4.zl_baseline_clean_1w
📅 Created: 2025-10-27 21:59:22.593000+00:00
🔄 Modified: 2025-10-27 21:59:22.662000+00:00
🏷️  Model Type: BOOSTED_TREE_REGRESSOR
📍 Location: us-central1

📝 Used in Codebase (1 files):
   - docs/BQML_MODELS_COMPLETE_AUDIT.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 7 days old

🎯 Inferred Purpose:
   - 1 Week forecast horizon

================================================================================
MODEL: zl_dnn_1m_v4
================================================================================

📍 Location: cbi-v14.models_v4.zl_dnn_1m_v4
📅 Created: 2025-10-23 19:20:29.688000+00:00
🔄 Modified: 2025-10-23 19:20:29.834000+00:00
🏷️  Model Type: DNN_REGRESSOR
📍 Location: us-central1

📝 Used in Codebase (6 files):
   - forecast/v4_model_predictions.py
   - archive/oct31_2025_cleanup/scripts_legacy/evaluate_v4_models.py
   - models_v4/MODEL_REGISTRY.md
   - models_v4/V4_EVALUATION_REPORT.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/BAD_DATA_TRAINING_AUDIT.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 11 days old

🎯 Inferred Purpose:
   - 1 Month forecast horizon
   - Neural Network model

================================================================================
MODEL: zl_dnn_1w_v4
================================================================================

📍 Location: cbi-v14.models_v4.zl_dnn_1w_v4
📅 Created: 2025-10-23 19:07:15.187000+00:00
🔄 Modified: 2025-10-23 19:07:15.385000+00:00
🏷️  Model Type: DNN_REGRESSOR
📍 Location: us-central1

📝 Used in Codebase (6 files):
   - forecast/v4_model_predictions.py
   - archive/oct31_2025_cleanup/scripts_legacy/evaluate_v4_models.py
   - models_v4/MODEL_REGISTRY.md
   - models_v4/V4_EVALUATION_REPORT.md
   - docs/BQML_MODELS_COMPLETE_AUDIT.md
   - archive/md_status_oct27/BAD_DATA_TRAINING_AUDIT.md

✅ Credibility Assessment:
   - Status: ✅ CREDIBLE
   - Recommendation: USE

   Strengths:
     ✅ Recent model: 11 days old

🎯 Inferred Purpose:
   - 1 Week forecast horizon
   - Neural Network model
