-- ============================================
-- ADD MISSING TECHNICAL INDICATOR COLUMNS
-- Adds only columns that don't exist
-- ============================================

-- Add Bollinger Band columns
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS bb_upper FLOAT64,
ADD COLUMN IF NOT EXISTS bb_middle FLOAT64,
ADD COLUMN IF NOT EXISTS bb_lower FLOAT64,
ADD COLUMN IF NOT EXISTS bb_percent FLOAT64;

-- Add RSI column
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS rsi_14 FLOAT64;

-- Add MACD columns
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS macd_line FLOAT64,
ADD COLUMN IF NOT EXISTS macd_signal FLOAT64,
ADD COLUMN IF NOT EXISTS macd_histogram FLOAT64;

-- Add 90-day MA
ALTER TABLE `cbi-v14.models_v4.training_dataset_super_enriched`
ADD COLUMN IF NOT EXISTS ma_90d FLOAT64;

-- Verify columns added
SELECT 
  column_name,
  data_type
FROM `cbi-v14.models_v4.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'training_dataset_super_enriched'
  AND column_name IN (
    'bb_upper', 'bb_middle', 'bb_lower', 'bb_percent',
    'rsi_14', 'macd_line', 'macd_signal', 'macd_histogram', 'ma_90d'
  )
ORDER BY column_name;

