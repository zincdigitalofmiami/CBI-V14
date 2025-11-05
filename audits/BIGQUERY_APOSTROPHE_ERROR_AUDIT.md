# BigQuery Apostrophe Error - Complete Audit & Solution
**Date:** November 5, 2025  
**Error:** `Syntax error: concatenated string literals must be separated by whitespace or comments at [17:53]`  
**Status:** ✅ ROOT CAUSE IDENTIFIED & SOLUTION FOUND

---

## Executive Summary

**Root Cause:** BigQuery Standard SQL does NOT support doubled apostrophes (`''`) for escaping in string literals. BigQuery interprets `'string''part'` as two concatenated strings: `'string'` + `'part'`, which requires a concatenation operator.

**Solution:** Use **double quotes** (`"`) for string literals containing apostrophes. BigQuery supports both single and double quotes for string literals.

---

## Error Analysis

### Error Details
- **Location:** Line 17, Column 53
- **Problematic Code:** `'427 - Gallagher''s Steakhouse'`
- **BigQuery Interpretation:** `'427 - Gallagher'` + `'s Steakhouse'` (concatenation)
- **Expected:** Single string with escaped apostrophe

### Test Results

**❌ FAILED: Double Apostrophe (`''`)**
```sql
SELECT 'Gallagher''s' as name
```
**Result:** Error - BigQuery sees concatenation

**❌ FAILED: Backslash Escaping (`\'`)**
```sql
SELECT 'Gallagher\'s' as name
```
**Result:** Error - Unclosed string literal (BigQuery doesn't support backslash escaping)

**✅ SUCCESS: Double Quotes (`"`)**
```sql
SELECT "Gallagher's Steakhouse" as name
```
**Result:** ✅ Works perfectly

---

## BigQuery String Literal Rules

### Supported Methods

1. **Single Quotes** (`'string'`)
   - ✅ Works for strings without apostrophes
   - ❌ Cannot escape apostrophes with `''`
   - ❌ Cannot use backslash `\'`

2. **Double Quotes** (`"string"`)
   - ✅ Works for strings with apostrophes
   - ✅ No escaping needed for apostrophes
   - ✅ Can include `'` directly

3. **Escaping in Double Quotes**
   - To include a double quote: `"string with ""quotes"""`
   - Doubled double quotes escape double quotes

### Official BigQuery Documentation

According to BigQuery Standard SQL documentation:
- **Single quotes:** Standard string literals, but apostrophes cause issues
- **Double quotes:** Alternative string literals, allow apostrophes without escaping
- **Backslash escaping:** NOT supported in BigQuery Standard SQL

---

## Solution: Use Double Quotes

### Fix Strategy

**For restaurants with apostrophes in names:**
- Change: `'427 - Gallagher''s Steakhouse'`
- To: `"427 - Gallagher's Steakhouse"`

**For restaurants without apostrophes:**
- Keep: `'1033 - America'` (no change needed)
- OR change to double quotes for consistency

### Implementation Options

**Option 1: Mixed Quotes (Recommended)**
- Use double quotes only for strings with apostrophes
- Keep single quotes for strings without apostrophes
- **Pros:** Minimal changes, only fix problematic lines
- **Cons:** Inconsistent quoting style

**Option 2: All Double Quotes (Consistent)**
- Change all string literals to double quotes
- **Pros:** Consistent style, no apostrophe issues
- **Cons:** More changes, but safer long-term

**Option 3: Python String Building**
- Build SQL query in Python, properly escaping
- **Pros:** Full control, can handle any edge case
- **Cons:** More complex, requires Python execution

---

## Affected Restaurants

### Restaurants with Apostrophes

Based on SQL file analysis, the following restaurants have apostrophes in names:

1. `'427 - Gallagher''s Steakhouse'` → `"427 - Gallagher's Steakhouse"`
2. `'Bobby''s Burger'` → `"Bobby's Burger"` (appears 2 times)
3. `'Bugsy''s Steakhouse'` → `"Bugsy's Steakhouse"`
4. `'Darla''s Southern Cajun Bistro'` → `"Darla's Southern Cajun Bistro"`
5. `'Flanker''s @Carver Road Hospitality'` → `"Flanker's @Carver Road Hospitality"`
6. `'Forum Food Court - Bobby''s Burgers'` → `"Forum Food Court - Bobby's Burgers"`
7. `'Hell''s Kitchen'` → `"Hell's Kitchen"`
8. `'Huey Magoo''s'` → `"Huey Magoo's"`
9. `'Jack Binion''s Steakhouse'` → `"Jack Binion's Steakhouse"`
10. `'Jason Aldean''s Kitchen + Bar'` → `"Jason Aldean's Kitchen + Bar"`
11. `'Jerry''s'` → `"Jerry's"`
12. `'Main Kitchen (GR Burgr & Pinky''s)'` → `"Main Kitchen (GR Burgr & Pinky's)"`
13. `'Pinky''s'` → `"Pinky's"`
14. `'Smokey Joe''s'` → `"Smokey Joe's"`
15. `'Tony Roma''s'` → `"Tony Roma's"`
16. `'Victory''s Cafe'` → `"Victory's Cafe"`
17. `'William B''s Steakhouse'` → `"William B's Steakhouse"`

**Total:** 17 restaurant names with apostrophes (some appear multiple times)

---

## SQL File Fix Required

### Current Format (BROKEN)
```sql
STRUCT('7WNL0LxbReq02l9hQpDDhQ', '427 - Gallagher''s Steakhouse', 'Steakhouse', 1.2),
```

### Fixed Format (WORKS)
```sql
STRUCT('7WNL0LxbReq02l9hQpDDhQ', "427 - Gallagher's Steakhouse", 'Steakhouse', 1.2),
```

### Complete Fix Strategy

**Lines to Fix:** All lines containing `''` (doubled apostrophe) in restaurant names

**Pattern to Find:**
- Search for: `'[^']*''[^']*'` (single-quoted string with doubled apostrophe)
- Replace: Change outer quotes to double quotes, remove doubling

**Automated Fix:**
```python
# Find all lines with doubled apostrophes
# Replace: '...''...' → "...'..."
```

---

## Verification Plan

### Step 1: Fix SQL File
- Replace all `'name''s'` with `"name's"`
- Test with BigQuery

### Step 2: Verify Table Creation
- Execute fixed SQL
- Confirm 142 rows created
- Verify all restaurant names correct

### Step 3: Validate Data
- Check for NULL values
- Verify all multipliers present
- Confirm JOIN works with `vegas_restaurants`

---

## Conclusion

**Status:** ✅ **SOLUTION IDENTIFIED**

**Root Cause:** BigQuery doesn't support `''` for escaping apostrophes in single-quoted strings

**Solution:** Use double quotes (`"`) for strings containing apostrophes

**Next Steps:**
1. Fix SQL file (replace `'name''s'` with `"name's"`)
2. Create table in BigQuery
3. Verify table creation
4. Update API endpoints to use multipliers

---

**Audit Completed:** November 5, 2025  
**Status:** READY FOR IMPLEMENTATION

