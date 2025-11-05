# BigQuery Apostrophe Fix - Implementation Plan
**Date:** November 5, 2025  
**Status:** ✅ SOLUTION VERIFIED & READY

---

## Root Cause Confirmed

**Error:** `Syntax error: concatenated string literals must be separated by whitespace or comments at [17:53]`

**Root Cause:** BigQuery Standard SQL does NOT support doubled apostrophes (`''`) for escaping in single-quoted string literals. BigQuery interprets `'string''part'` as two concatenated strings.

**Solution Verified:** ✅ Use **double quotes** (`"`) for string literals containing apostrophes.

---

## Test Results Summary

### ✅ SUCCESSFUL Tests

1. **Double Quotes in Simple SELECT**
   ```sql
   SELECT "Gallagher's Steakhouse" as name
   ```
   ✅ Works perfectly

2. **Double Quotes in STRUCT (Named)**
   ```sql
   STRUCT("Gallagher's Steakhouse" as name)
   ```
   ✅ Works perfectly

3. **Double Quotes in STRUCT (Positional)**
   ```sql
   STRUCT('Test' as name),
   STRUCT("Gallagher's Steakhouse")
   ```
   ✅ Works perfectly - mixed quotes allowed

4. **Multiple Apostrophes**
   ```sql
   STRUCT("Bobby's Burger"),
   STRUCT("Darla's Southern Cajun Bistro")
   ```
   ✅ All work perfectly

### ❌ FAILED Tests

1. **Double Apostrophe (`''`)**
   ```sql
   SELECT 'Gallagher''s' as name
   ```
   ❌ Error: Concatenated string literals

2. **Backslash Escape (`\'`)**
   ```sql
   SELECT 'Gallagher\'s' as name
   ```
   ❌ Error: Unclosed string literal

---

## Fix Strategy

### Approach: Mixed Quotes (Recommended)

**For strings WITH apostrophes:**
- Change: `'427 - Gallagher''s Steakhouse'`
- To: `"427 - Gallagher's Steakhouse"`

**For strings WITHOUT apostrophes:**
- Keep: `'1033 - America'` (no change)

**Rationale:**
- Minimal changes (only ~17 lines)
- BigQuery supports mixed quotes
- Maintains readability

### Alternative: All Double Quotes

**For ALL strings:**
- Change: `'1033 - America'` → `"1033 - America"`
- Change: `'427 - Gallagher''s Steakhouse'` → `"427 - Gallagher's Steakhouse"`

**Rationale:**
- Consistent style
- No future apostrophe issues
- More changes (~142 lines)

---

## Implementation Steps

### Step 1: Identify All Lines with Apostrophes

**Pattern to Find:**
- Lines containing `''` (doubled apostrophe)
- Approximately 17 restaurant names

**Restaurants Known to Have Apostrophes:**
1. Gallagher's Steakhouse
2. Bobby's Burger (2 instances)
3. Bugsy's Steakhouse
4. Darla's Southern Cajun Bistro
5. Flanker's @Carver Road Hospitality
6. Forum Food Court - Bobby's Burgers
7. Hell's Kitchen
8. Huey Magoo's
9. Jack Binion's Steakhouse
10. Jason Aldean's Kitchen + Bar
11. Jerry's
12. Main Kitchen (GR Burgr & Pinky's)
13. Pinky's
14. Smokey Joe's
15. Tony Roma's
16. Victory's Cafe
17. William B's Steakhouse

### Step 2: Fix SQL File

**For each line with apostrophe:**
1. Find: `STRUCT('...', '...NAME''s...', '...', ...)`
2. Replace: `STRUCT('...', "NAME's", '...', ...)`
3. Remove doubled apostrophe: `''` → `'`
4. Change outer quotes: `'...'` → `"...`

**Example Fix:**
```sql
# BEFORE (BROKEN):
STRUCT('7WNL0LxbReq02l9hQpDDhQ', '427 - Gallagher''s Steakhouse', 'Steakhouse', 1.2),

# AFTER (FIXED):
STRUCT('7WNL0LxbReq02l9hQpDDhQ', "427 - Gallagher's Steakhouse", 'Steakhouse', 1.2),
```

### Step 3: Verify Fix

**Test Query:**
```sql
SELECT * FROM UNNEST([
  STRUCT('7WNL0LxbReq02l9hQpDDhQ' as glide_rowID, "427 - Gallagher's Steakhouse" as restaurant_name, 'Steakhouse' as cuisine_type, 1.2 as oil_multiplier)
])
```

**Expected:** ✅ No errors

### Step 4: Create Table

**Execute Fixed SQL:**
```bash
bq query --location=us-central1 --use_legacy_sql=false < fixed_sql_file.sql
```

**Verify:**
- 142 rows created
- No NULL values
- All restaurant names correct

---

## Files to Update

1. **`bigquery_sql/CREATE_VEGAS_CUISINE_MULTIPLIERS.sql`**
   - Fix ~17 lines with apostrophes
   - Change single quotes to double quotes for restaurant names with apostrophes

---

## Verification Checklist

- [ ] All lines with `''` identified
- [ ] SQL file fixed (apostrophes use double quotes)
- [ ] Test query executes successfully
- [ ] Full SQL executes without errors
- [ ] Table created with 142 rows
- [ ] All restaurant names verified (no corruption)
- [ ] JOIN with `vegas_restaurants` works correctly

---

## Risk Assessment

**Risk Level:** LOW

**Reasons:**
- Solution is verified (double quotes work)
- Minimal changes (only ~17 lines)
- BigQuery officially supports double-quoted strings
- Easy to test before full execution

**Rollback Plan:**
- Original SQL file preserved
- Can revert if needed

---

## Conclusion

**Status:** ✅ **READY FOR IMPLEMENTATION**

**Solution:** Use double quotes for strings with apostrophes

**Next Action:** Fix SQL file, then create table

---

**Audit Completed:** November 5, 2025  
**Solution Verified:** ✅ YES  
**Ready to Implement:** ✅ YES

