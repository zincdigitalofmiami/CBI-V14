# Pre-Implementation Audit - API Endpoints Multiplier Integration
**Date:** November 5, 2025  
**Status:** ✅ COMPLETE - READY FOR IMPLEMENTATION

---

## Executive Summary

**Key Finding:** `upsell-opportunities` endpoint **ALREADY USES** cuisine multipliers! ✅  
**Remaining:** 4 endpoints need multiplier integration  
**Impact:** Multipliers show significant impact (e.g., Buffet 2.2× = +505 gal/week)

---

## Endpoint-by-Endpoint Analysis

### 1. `/api/v4/vegas/metrics` ❌ NEEDS UPDATE

**Current State:**
- ❌ Does NOT use cuisine multipliers
- ❌ Hardcoded TPM: 4
- ❌ Hardcoded event multiplier: 2.0
- ❌ Hardcoded upsell %: 0.68 (68%)
- ❌ Hardcoded price: $8.20/gal
- ❌ No query parameters (Kevin Override)

**Formula:**
```sql
-- Current (WRONG):
ROUND((SUM(f.xhrM0) * 4) / 7.6, 0) as weekly_base_gallons
-- Revenue: weekly_base × (3/7) × 2.0 × 0.68 × 8.20

-- Should be (CORRECT):
ROUND((SUM(f.xhrM0) * 4 * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 0) as weekly_base_gallons
```

**Changes Needed:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply `oil_multiplier` to base gallons calculation
3. Replace hardcoded values with NULL or query params
4. Add Kevin Override query parameters

**Impact:** HIGH - Base metrics calculation affects all dashboard numbers

---

### 2. `/api/v4/vegas/upsell-opportunities` ✅ ALREADY UPDATED

**Current State:**
- ✅ **ALREADY USES cuisine multipliers** (Line 54, 59-60, 76, 82, 88, 94, etc.)
- ✅ Accepts query parameters (Kevin Override)
- ✅ Handles NULL values correctly
- ✅ Pulls ZL cost from Dashboard

**Formula:**
```sql
-- Already correct:
COALESCE(c.oil_multiplier, 1.0) as cuisine_multiplier
ROUND((total_capacity_lbs * ${tpmValue}) / 7.6 * cuisine_multiplier, 2)
```

**Status:** ✅ **NO CHANGES NEEDED** - This endpoint is already correct!

---

### 3. `/api/v4/vegas/events` ❌ NEEDS UPDATE

**Current State:**
- ❌ Does NOT use cuisine multipliers
- ❌ Hardcoded TPM: 4
- ❌ Hardcoded volume multipliers: 3.4, 2.5, 1.8, 1.3 (based on fryer count)
- ❌ Hardcoded upsell %: 0.68 (68%)
- ❌ Hardcoded price: $8.20/gal
- ❌ Fake date: `DATE_ADD(CURRENT_DATE(), INTERVAL 14 DAY)`
- ❌ Bug: `row.expected_attendance` referenced but not selected
- ❌ No query parameters (Kevin Override)

**Formula:**
```sql
-- Current (WRONG):
ROUND((SUM(f.xhrM0) * 4) / 7.6, 0) as weekly_base_gallons
CASE 
  WHEN COUNT(f.glide_rowID) >= 20 THEN 3.4
  WHEN COUNT(f.glide_rowID) >= 10 THEN 2.5
  WHEN COUNT(f.glide_rowID) >= 5 THEN 1.8
  ELSE 1.3
END as volume_multiplier

-- Should be (CORRECT):
ROUND((SUM(f.xhrM0) * 4 * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 0) as weekly_base_gallons
-- Volume multiplier should be Kevin input, not hardcoded
```

**Changes Needed:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply `oil_multiplier` to base gallons calculation
3. Remove fake date → NULL
4. Fix bug: Remove `expected_attendance` reference or select it
5. Replace hardcoded volume multipliers with query params
6. Add Kevin Override query parameters

**Impact:** HIGH - Event volume calculations are critical

---

### 4. `/api/v4/vegas/customers` ❌ NEEDS UPDATE

**Current State:**
- ❌ Does NOT use cuisine multipliers
- ❌ Hardcoded TPM: 4 (in formula: `* 4`)
- ❌ Hardcoded relationship scores: 85, 70, 50, 30 (based on fryer count)
- ❌ No query parameters (Kevin Override)

**Formula:**
```sql
-- Current (WRONG):
ROUND((SUM(f.xhrM0) * 4) / 7.6, 2) as weekly_gallons

-- Should be (CORRECT):
ROUND((SUM(f.xhrM0) * COALESCE(${tpmValue}, 4) * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 2) as weekly_gallons
```

**Changes Needed:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply `oil_multiplier` to weekly gallons calculation
3. Make TPM a query parameter (default 4)
4. Add Kevin Override query parameters

**Impact:** MEDIUM - Customer relationship matrix uses this data

---

### 5. `/api/v4/vegas/margin-alerts` ❌ NEEDS UPDATE

**Current State:**
- ❌ Does NOT use cuisine multipliers
- ❌ Hardcoded TPM: 4
- ❌ Hardcoded margin per gallon: 0.70
- ❌ Hardcoded price: $8.20
- ❌ Hardcoded cost: $7.50
- ❌ No query parameters (Kevin Override)
- ❌ No ZL cost from Dashboard

**Formula:**
```sql
-- Current (WRONG):
ROUND((SUM(f.xhrM0) * 4) / 7.6 * 0.70 * 4, 0) as risk_amount_monthly
ROUND(((8.20 - 7.50) / 8.20) * 100, 1) as current_margin_pct

-- Should be (CORRECT):
ROUND((SUM(f.xhrM0) * COALESCE(${tpmValue}, 4) * COALESCE(cm.oil_multiplier, 1.0)) / 7.6 * COALESCE(${marginPerGal}, NULL) * 4, 0) as risk_amount_monthly
-- Pull price and cost from Dashboard or query params
```

**Changes Needed:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply `oil_multiplier` to weekly gallons calculation
3. Pull ZL cost from Dashboard (like upsell-opportunities does)
4. Make price, cost, margin query parameters
5. Add Kevin Override query parameters

**Impact:** HIGH - Margin protection is critical

---

## Dry Run Results

### Test 1: Basic JOIN Pattern ✅ SUCCESS

**Query:**
```sql
SELECT 
  r.glide_rowID,
  r.MHXYO as restaurant_name,
  cm.oil_multiplier,
  COUNT(f.glide_rowID) as fryer_count,
  SUM(f.xhrM0) as total_capacity_lbs,
  ROUND((SUM(f.xhrM0) * 4 * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 2) as weekly_gallons_with_multiplier
FROM vegas_restaurants r
LEFT JOIN vegas_fryers f ON r.glide_rowID = f.`2uBBn`
LEFT JOIN vegas_cuisine_multipliers cm ON r.glide_rowID = cm.glide_rowID
WHERE r.s8tNr = 'Open'
GROUP BY r.glide_rowID, r.MHXYO, cm.oil_multiplier
HAVING fryer_count > 0
ORDER BY weekly_gallons_with_multiplier DESC
LIMIT 5
```

**Results:**
- ✅ 5 rows returned
- ✅ Multipliers applied correctly
- ✅ Buffet: 2.2× = 636.8 gal/week
- ✅ Fried Chicken: 2.0× = 526.3 gal/week

### Test 2: Impact Analysis ✅ SUCCESS

**Top Impact Differences:**
1. Buffet (2.2×): +505.3 gal/week
2. Banquets (1.5×): +365.8 gal/week
3. Bacchanal Buffet (2.2×): +284.2 gal/week
4. Employee Dining (1.4×): +273.7 gal/week
5. Fried Chicken (2.0×): +263.2 gal/week

**Conclusion:** Multipliers have significant impact on calculations!

---

## Implementation Plan

### Phase 1: Metrics Endpoint (HIGH PRIORITY)

**Changes:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply multiplier to base gallons: `* COALESCE(cm.oil_multiplier, 1.0)`
3. Replace hardcoded values with NULL or query params
4. Add query parameter support

**Formula Update:**
```sql
-- OLD:
ROUND((SUM(f.xhrM0) * 4) / 7.6, 0) as weekly_base_gallons

-- NEW:
ROUND((SUM(f.xhrM0) * COALESCE(${tpmValue}, 4) * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 0) as weekly_base_gallons
```

### Phase 2: Events Endpoint (HIGH PRIORITY)

**Changes:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply multiplier to base gallons
3. Remove fake date → NULL
4. Fix bug: Remove `expected_attendance` reference
5. Replace hardcoded volume multipliers with query params
6. Add query parameter support

**Formula Update:**
```sql
-- OLD:
ROUND((SUM(f.xhrM0) * 4) / 7.6, 0) as weekly_base_gallons
CASE WHEN COUNT(f.glide_rowID) >= 20 THEN 3.4 ... END as volume_multiplier

-- NEW:
ROUND((SUM(f.xhrM0) * COALESCE(${tpmValue}, 4) * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 0) as weekly_base_gallons
-- Volume multiplier from query params
```

### Phase 3: Customers Endpoint (MEDIUM PRIORITY)

**Changes:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply multiplier to weekly gallons
3. Make TPM a query parameter (default 4)
4. Add query parameter support

**Formula Update:**
```sql
-- OLD:
ROUND((SUM(f.xhrM0) * 4) / 7.6, 2) as weekly_gallons

-- NEW:
ROUND((SUM(f.xhrM0) * COALESCE(${tpmValue}, 4) * COALESCE(cm.oil_multiplier, 1.0)) / 7.6, 2) as weekly_gallons
```

### Phase 4: Margin Alerts Endpoint (HIGH PRIORITY)

**Changes:**
1. Add JOIN to `vegas_cuisine_multipliers`
2. Apply multiplier to weekly gallons
3. Pull ZL cost from Dashboard (like upsell-opportunities)
4. Make price, cost, margin query parameters
5. Add query parameter support

**Formula Update:**
```sql
-- OLD:
ROUND((SUM(f.xhrM0) * 4) / 7.6 * 0.70 * 4, 0) as risk_amount_monthly
ROUND(((8.20 - 7.50) / 8.20) * 100, 1) as current_margin_pct

-- NEW:
ROUND((SUM(f.xhrM0) * COALESCE(${tpmValue}, 4) * COALESCE(cm.oil_multiplier, 1.0)) / 7.6 * COALESCE(${marginPerGal}, NULL) * 4, 0) as risk_amount_monthly
-- Pull price and cost from Dashboard or query params
```

---

## JOIN Pattern Template

**Standard JOIN Pattern:**
```sql
LEFT JOIN `cbi-v14.forecasting_data_warehouse.vegas_cuisine_multipliers` cm
  ON r.glide_rowID = cm.glide_rowID
```

**Multiplier Usage:**
```sql
COALESCE(cm.oil_multiplier, 1.0) as cuisine_multiplier
-- Then multiply: base_calculation * cuisine_multiplier
```

---

## Fake Data Removal Checklist

### Metrics Endpoint
- [ ] Remove hardcoded TPM: 4 → Query param or NULL
- [ ] Remove hardcoded event multiplier: 2.0 → Query param or NULL
- [ ] Remove hardcoded upsell %: 0.68 → Query param or NULL
- [ ] Remove hardcoded price: $8.20 → Query param or NULL

### Events Endpoint
- [ ] Remove fake date: `DATE_ADD(CURRENT_DATE(), INTERVAL 14 DAY)` → NULL
- [ ] Remove hardcoded volume multipliers: 3.4, 2.5, 1.8, 1.3 → Query params
- [ ] Fix bug: Remove `expected_attendance` reference
- [ ] Remove hardcoded TPM: 4 → Query param
- [ ] Remove hardcoded upsell %: 0.68 → Query param
- [ ] Remove hardcoded price: $8.20 → Query param

### Customers Endpoint
- [ ] Remove hardcoded TPM: 4 → Query param (default 4)

### Margin Alerts Endpoint
- [ ] Remove hardcoded TPM: 4 → Query param
- [ ] Remove hardcoded margin: 0.70 → Query param or calculate
- [ ] Remove hardcoded price: $8.20 → Query param or Dashboard
- [ ] Remove hardcoded cost: $7.50 → Dashboard (ZL cost)

---

## Implementation Order

1. ✅ **Skip:** `upsell-opportunities` (already updated)
2. 🔴 **Priority 1:** `metrics` (affects all dashboard numbers)
3. 🔴 **Priority 2:** `events` (critical for event forecasting)
4. 🟡 **Priority 3:** `margin-alerts` (high impact, but less frequent)
5. 🟢 **Priority 4:** `customers` (lower impact, relationship matrix)

---

## Risk Assessment

**Risk Level:** LOW
- JOIN pattern tested and verified ✅
- Multiplier table exists and is populated ✅
- All open restaurants have multipliers ✅
- Upsell-opportunities endpoint already uses pattern ✅

**Rollback Plan:**
- All changes are additive (JOINs)
- Original formulas preserved in git history
- Can revert individual endpoints if needed

---

## Verification Plan

After implementation, verify:
1. ✅ All endpoints return data
2. ✅ Multipliers applied correctly (spot check high-multiplier restaurants)
3. ✅ NULL handling works (missing multipliers default to 1.0)
4. ✅ Query parameters work (Kevin Override)
5. ✅ No fake data in responses
6. ✅ Calculations match expected values

---

## Conclusion

**Status:** ✅ **READY FOR IMPLEMENTATION**

**Summary:**
- 1 endpoint already updated (upsell-opportunities) ✅
- 4 endpoints need updates
- JOIN pattern verified and tested
- Impact is significant (e.g., +505 gal/week for Buffet)

**Next Steps:**
1. Implement metrics endpoint
2. Implement events endpoint
3. Implement margin-alerts endpoint
4. Implement customers endpoint
5. Verify all endpoints

---

**Audit Completed:** November 5, 2025  
**Status:** READY FOR IMPLEMENTATION







