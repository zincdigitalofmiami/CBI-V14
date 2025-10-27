# FINAL ACTION PLAN - DATA INTEGRATION
October 23, 2025

## ✅ AUDIT COMPLETE - KEY FINDINGS

### PRIMARY DATASET SELECTED
**🏆 `models.training_complete_enhanced`**
- 1,263 rows × 219 columns
- 2.1 MB (largest and most complete)
- Has ALL feature categories
- Modified: Oct 23, 2025 16:22

### CRITICAL ISSUES TO FIX

#### 1. MISSING DATA IN PRIMARY DATASET
Despite having 219 columns, much data is NOT properly filled:
- **CFTC Managed Money**: 0% filled (CRITICAL - completely missing!)
- **CFTC Commercial**: Only 5.7% filled (72 days out of 1,263)
- **Treasury Yields**: 0% filled
- **Economic GDP**: 0% filled
- **Economic Inflation**: Only 1.4% filled (18 days)
- **News**: Only 0.3% filled (4 days)

#### 2. DATA EXISTS IN WAREHOUSE BUT NOT LINKING
The warehouse HAS the data:
- Economic indicators: 67,826 rows available
- Treasury prices: 1,961 rows available
- Currency data: 58,952 rows available
- CFTC: 72 rows (but managed money columns exist, just empty)

## 🔧 IMMEDIATE ACTIONS (IN ORDER)

### Step 1: BACKUP EVERYTHING FIRST
```sql
-- Already have backups in bkp dataset
-- models.training_dataset_backup_20251023 exists
```

### Step 2: DIAGNOSE LINKAGE FAILURES
Need to check:
1. **CFTC commodity name** - Is it "SOYBEAN OIL" or something else?
2. **Treasury symbol** - Is it TNX, US10Y, ^TNX, or DGS10?
3. **Economic indicator names** - Exact names in the 67,826 rows
4. **Date format mismatches** - DATE vs DATETIME vs TIMESTAMP

### Step 3: CREATE PROPER LINKAGE QUERY
Build a new query that:
1. Uses correct filter values for each data source
2. Properly handles date conversions
3. Uses LEFT JOINs to preserve all price data
4. Fills zeros only where appropriate

### Step 4: LOAD MISSING CFTC DATA
The current 72 rows is way too few. Need to:
1. Check if more historical CFTC data exists elsewhere
2. Load weekly CFTC data for full 5-year period (need ~260 rows)
3. Ensure managed money positions are populated

### Step 5: CREATE FINAL MASTER DATASET
Once linkages work:
1. Start with `training_complete_enhanced` as base
2. UPDATE it with properly linked data (don't create new table yet)
3. Validate all features are populated
4. Test that models can train on it

### Step 6: CLEANUP (ONLY AFTER VERIFICATION)
After confirming new dataset works:
1. Archive old versions to bkp
2. Consolidate to ONE training dataset
3. Update all dependent views

## ⚠️ DO NOT PROCEED WITHOUT

1. **Testing linkage fixes on small sample first**
2. **Verifying data is REAL (not zeros everywhere)**
3. **Confirming models train successfully**
4. **Getting stakeholder approval**

## 📊 SUCCESS METRICS

The final dataset should have:
- [ ] CFTC managed money: >50% filled (currently 0%)
- [ ] CFTC commercial: >50% filled (currently 5.7%)
- [ ] Treasury yields: >80% filled (currently 0%)
- [ ] Economic data: >20% filled (currently <2%)
- [ ] All 1,263 rows preserved
- [ ] All 219+ columns preserved
- [ ] No duplicate dates
- [ ] Models train successfully

## NEXT IMMEDIATE COMMAND

Run the diagnostic query to find exact filter values needed:

```python
# diagnose_filter_values.py
# Check exact values for commodity names, symbols, indicators
# This will tell us WHY data isn't linking
```

---
**STATUS**: Ready to fix linkages. Data exists, just not connecting properly.
