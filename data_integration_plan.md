# DATA INTEGRATION PLAN
Based on Comprehensive Audit - October 23, 2025

## CURRENT STATE ASSESSMENT

### Training Datasets (6 Found - TOO MANY!)
1. **models.training_complete_enhanced** ✅ BEST CANDIDATE
   - 1,263 rows × 219 columns (most features)
   - 2.1 MB (largest, most complete)
   - Modified: Oct 23, 2025 16:22 (most recent in models)
   - Date range: 2020-10-21 to 2025-10-13

2. **models_v4.training_dataset_super_enriched** 
   - 1,251 rows × 195 columns
   - 1.7 MB
   - Modified: Oct 23, 2025 22:27 (very recent)
   - Missing 12 rows (duplicate dates removed?)

3. **models.training_dataset_enhanced**
   - 1,263 rows × 184 columns
   - 1.6 MB
   - Modified: Oct 22, 2025

4. **models.training_dataset_master**
   - 1,289 rows × 41 columns (too few features!)
   - Just created today at 23:25

5. **models.training_dataset**
   - 1,263 rows × 62 columns (too basic)
   - 0.6 MB

6. **models.training_enhanced_final**
   - 1,323 rows × 183 columns
   - Has extra rows (60 more) - needs investigation

### Data Warehouse Status
✅ **GOOD DATA AVAILABLE:**
- Soybean oil prices: 1,265 rows
- Crude oil: 1,258 rows  
- Palm oil: 1,256 rows
- Corn: 1,265 rows
- VIX: 2,717 rows
- Weather: 13,828 rows
- Currency: 58,952 rows
- Economic indicators: 67,826 rows

⚠️ **PROBLEM DATA:**
- CFTC: Only 72 rows (should be ~250+ for 5 years weekly data)
- Treasury: 1,961 rows (good amount but not linking)
- News: 1,955 rows (sparse coverage)

## ISSUES IDENTIFIED

1. **Too Many Training Datasets** - 6 different versions causing confusion
2. **CFTC Data Too Sparse** - Only 72 rows when we need 250+
3. **Data Not Linking Properly** - Treasury, Economic, CFTC not joining correctly
4. **Duplicate Dates** - Some datasets have 1,251 rows, others 1,263 (12 duplicates)

## ACTION PLAN

### Phase 1: IDENTIFY PRIMARY DATASET (DO NOT DELETE ANYTHING YET)
1. Compare `training_complete_enhanced` vs `training_dataset_super_enriched`
2. Check which has better data quality
3. Designate ONE as primary

### Phase 2: FIX DATA LINKAGES
1. Diagnose why CFTC isn't linking (commodity name mismatch?)
2. Fix Treasury symbol matching (TNX vs US10Y vs DGS10)
3. Fix Economic indicator name matching
4. Ensure date formats align across all tables

### Phase 3: LOAD MISSING DATA
1. Get full CFTC historical data for soybean oil
2. Ensure managed money positions are populated
3. Fill gaps in news coverage

### Phase 4: CREATE FINAL MASTER DATASET
1. Use the PRIMARY dataset as base
2. Properly join all warehouse data
3. Add all calculations and derived features
4. Validate all linkages work

### Phase 5: CLEANUP (ONLY AFTER VERIFICATION)
1. Create backups of everything first
2. Test new master dataset thoroughly
3. Archive old versions to bkp dataset
4. Update all dependent views/models

## DO NOT PROCEED WITHOUT:
1. ✅ Full backup of all training datasets
2. ✅ Verification that new dataset has MORE data than old
3. ✅ Testing that models can train on new dataset
4. ✅ Confirmation from stakeholder

## NEXT IMMEDIATE STEP:
Run detailed comparison of the two best candidates to choose PRIMARY dataset.
