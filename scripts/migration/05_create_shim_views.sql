-- ⚠️ CRITICAL: NO FAKE DATA ⚠️
-- This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
-- All data must come from authenticated APIs, official sources, or validated historical records.
--

-- Phase 6: Create Shim Views for Backward Compatibility
-- These views point old table names to new tables
-- Will be removed after 30-day grace period

-- Production training data shims (pointing to prod surface)
CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_1w` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1w`;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_1m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_1m`;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_3m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_3m`;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_6m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_6m`;

CREATE OR REPLACE VIEW `cbi-v14.models_v4.production_training_data_12m` AS
SELECT * FROM `cbi-v14.training.zl_training_prod_allhistory_12m`;

-- Note: These shim views allow existing notebooks and scripts to continue working
-- They will be removed after validation period (30 days)

