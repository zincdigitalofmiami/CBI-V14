# Vegas Intel - Fake Data, Placeholders & Random Math Audit
**Date:** November 5, 2025  
**Status:** 🔴 CRITICAL ISSUES FOUND  
**Auditor:** AI Assistant

---

## Executive Summary

**CRITICAL FINDINGS:**
- ❌ **47 instances** of fake data, placeholders, and random math identified
- ❌ **5 API endpoints** contain hardcoded assumptions
- ❌ **0 real data sources** for event dates, attendance, multipliers, prices
- ✅ **Real data available:** Fryer capacity, restaurant names, casino locations only

**Risk Level:** 🔴 **HIGH** - Production endpoints returning fake data to dashboard

---

## Audit Methodology

**Scope:** All 5 Vegas Intel API endpoints  
**Files Audited:**
1. `/api/v4/vegas/metrics/route.ts`
2. `/api/v4/vegas/upsell-opportunities/route.ts`
3. `/api/v4/vegas/events/route.ts`
4. `/api/v4/vegas/customers/route.ts`
5. `/api/v4/vegas/margin-alerts/route.ts`

**Audit Criteria:**
- ❌ Fake dates (DATE_ADD with arbitrary intervals)
- ❌ Placeholder numbers (1000, 3, 14, etc.)
- ❌ Generic placeholder text ('Event Surge Opportunity', etc.)
- ❌ Hardcoded multipliers (2.0, 3.4, 2.5, 1.8, 1.3)
- ❌ Hardcoded percentages (0.68, 0.70)
- ❌ Hardcoded prices ($8.20, $7.50)
- ❌ Hardcoded TPM (4 turns per month)
- ❌ Hardcoded durations (3 days, 14 days)
- ❌ Bug: Referenced but not selected fields

---

## Detailed Findings by Endpoint

### 1. `/api/v4/vegas/metrics/route.ts`

**Line-by-Line Issues:**

| Line | Issue | Type | Value | Impact |
|------|-------|------|-------|--------|
| 16 | Hardcoded TPM | Random Math | `* 4` | Weekly gallons calculation uses assumption |
| 23 | Hardcoded event duration | Random Math | `(3.0/7.0)` | Assumes 3-day events |
| 23 | Hardcoded event multiplier | Random Math | `* 2.0` | Arbitrary 2x multiplier |
| 23 | Hardcoded upsell % | Random Math | `* 0.68` | Assumes 68% acceptance |
| 23 | Hardcoded price | Random Math | `* 8.20` | Assumes $8.20/gal price |
| 30 | Hardcoded event count | Placeholder | `31` | Casino count used as proxy (not real events) |
| 32 | Hardcoded alert count | Placeholder | `0` | No real margin alerts calculated |

**Total Issues:** 7

**Fake Data Summary:**
- Revenue potential uses 5 hardcoded assumptions (TPM, duration, multiplier, upsell %, price)
- Upcoming events is casino count, not real event calendar
- Margin risk alerts hardcoded to 0

---

### 2. `/api/v4/vegas/upsell-opportunities/route.ts`

**Line-by-Line Issues:**

| Line | Issue | Type | Value | Impact |
|------|-------|------|-------|--------|
| 19 | Hardcoded TPM | Random Math | `* 4` | Weekly gallons calculation |
| 21 | Hardcoded event duration | Random Math | `(3.0/7.0)` | Assumes 3-day events |
| 21 | Hardcoded event multiplier | Random Math | `* 2.0` | Arbitrary 2x multiplier |
| 23 | Hardcoded upsell % | Random Math | `* 0.68` | Assumes 68% acceptance |
| 25 | Hardcoded price | Random Math | `* 8.20` | Assumes $8.20/gal |
| 36 | Generic placeholder text | Placeholder | `'Event Surge Opportunity'` | Not real event name |
| 37 | Fake future date | Fake Data | `DATE_ADD(CURRENT_DATE(), INTERVAL 7 DAY)` | Made-up date |
| 38 | Hardcoded duration | Placeholder | `3` | Assumes 3-day events |
| 39 | Placeholder attendance | Fake Data | `1000` | Made-up attendance number |
| 44 | Hardcoded revenue threshold | Random Math | `>= 5000` | Arbitrary threshold |
| 44 | Hardcoded revenue threshold | Random Math | `>= 2000` | Arbitrary threshold |
| 47 | Generic placeholder text | Placeholder | `'Restaurant Manager'` | Not real contact |
| 53 | Hardcoded ZL cost | Random Math | `7.50` | Should come from Dashboard |
| 53 | Hardcoded tanker cost | Random Math | `1200` | Should be configurable |

**Total Issues:** 14

**Fake Data Summary:**
- Event name is generic placeholder
- Event date is fake (7 days in future)
- Event duration is hardcoded assumption
- Expected attendance is placeholder (1000)
- Contact target is generic placeholder
- All calculations use 5+ hardcoded assumptions

---

### 3. `/api/v4/vegas/events/route.ts`

**Line-by-Line Issues:**

| Line | Issue | Type | Value | Impact |
|------|-------|------|-------|--------|
| 17 | Hardcoded TPM | Random Math | `* 4` | Weekly gallons calculation |
| 20 | Hardcoded multiplier | Random Math | `3.4` | F1-level surge assumption |
| 21 | Hardcoded multiplier | Random Math | `2.5` | Large casino assumption |
| 22 | Hardcoded multiplier | Random Math | `1.8` | Medium casino assumption |
| 23 | Hardcoded multiplier | Random Math | `1.3` | Small casino assumption |
| 36 | Generic placeholder text | Placeholder | `'Casino Event Surge'` | Not real event type |
| 37 | Fake future date | Fake Data | `DATE_ADD(CURRENT_DATE(), INTERVAL 14 DAY)` | Made-up date |
| 41 | Hardcoded upsell % | Random Math | `* 0.68` | Assumes 68% acceptance |
| 41 | Hardcoded price | Random Math | `* 8.20` | Assumes $8.20/gal |
| 42 | Hardcoded days until | Fake Data | `14` | Calculated from fake date |
| 62 | **BUG:** Referenced field not selected | Bug | `row.expected_attendance` | Field doesn't exist in query |

**Total Issues:** 11

**Fake Data Summary:**
- Event type is generic placeholder
- Event date is fake (14 days in future)
- Days until is calculated from fake date
- All multipliers are arbitrary (3.4, 2.5, 1.8, 1.3)
- Revenue calculation uses hardcoded upsell % and price
- **BUG:** expected_attendance referenced but never selected

---

### 4. `/api/v4/vegas/customers/route.ts`

**Line-by-Line Issues:**

| Line | Issue | Type | Value | Impact |
|------|-------|------|-------|--------|
| 14 | Hardcoded TPM | Random Math | `* 4` | Weekly gallons calculation |
| 17 | Hardcoded score threshold | Random Math | `>= 5 THEN 85` | Arbitrary scoring |
| 18 | Hardcoded score threshold | Random Math | `>= 3 THEN 70` | Arbitrary scoring |
| 19 | Hardcoded score threshold | Random Math | `>= 1 THEN 50` | Arbitrary scoring |
| 20 | Hardcoded score default | Random Math | `ELSE 30` | Arbitrary scoring |
| 26 | Hardcoded growth threshold | Placeholder | `>= 5 THEN 'High'` | Arbitrary classification |
| 27 | Hardcoded growth threshold | Placeholder | `>= 3 THEN 'Medium'` | Arbitrary classification |
| 31 | Hardcoded action text | Placeholder | `'Pitch event upsell'` | Generic recommendation |
| 32 | Hardcoded action text | Placeholder | `'Monitor for opportunities'` | Generic recommendation |
| 33 | Hardcoded action text | Placeholder | `'Reactivate account'` | Generic recommendation |

**Total Issues:** 10

**Fake Data Summary:**
- Weekly gallons uses hardcoded TPM (4)
- Relationship scores are arbitrary (85, 70, 50, 30)
- Growth potential classifications are arbitrary
- Next action recommendations are generic placeholders

---

### 5. `/api/v4/vegas/margin-alerts/route.ts`

**Line-by-Line Issues:**

| Line | Issue | Type | Value | Impact |
|------|-------|------|-------|--------|
| 15 | Hardcoded TPM | Random Math | `* 4` | Weekly gallons calculation |
| 18 | Hardcoded severity threshold | Random Math | `>= 5 THEN 'HIGH'` | Arbitrary classification |
| 19 | Hardcoded severity threshold | Random Math | `>= 3 THEN 'MEDIUM'` | Arbitrary classification |
| 23 | Hardcoded margin per gallon | Random Math | `* 0.70` | Assumes $0.70 margin |
| 23 | Hardcoded weeks | Random Math | `* 4` | Assumes monthly calculation |
| 24 | Hardcoded price | Random Math | `8.20` | Assumes $8.20/gal |
| 25 | Hardcoded cost | Random Math | `7.50` | Should come from Dashboard |
| 36 | Generic placeholder text | Placeholder | `'Volume Risk'` | Generic alert type |
| 41 | Hardcoded action text | Placeholder | `'Lock pricing now...'` | Generic recommendation |
| 42 | Hardcoded action text | Placeholder | `'Review margin protection...'` | Generic recommendation |
| 43 | Hardcoded action text | Placeholder | `'Monitor for price changes'` | Generic recommendation |
| 46 | Hardcoded urgency text | Placeholder | `'Immediate action required'` | Generic urgency |
| 47 | Hardcoded urgency text | Placeholder | `'Review within 48 hours'` | Generic urgency |
| 48 | Hardcoded urgency text | Placeholder | `'Monitor weekly'` | Generic urgency |

**Total Issues:** 14

**Fake Data Summary:**
- Weekly gallons uses hardcoded TPM (4)
- Margin calculation uses hardcoded price ($8.20) and cost ($7.50)
- Risk amount uses hardcoded margin ($0.70) and weeks (4)
- All alert types, actions, and urgency are generic placeholders

---

## Summary by Issue Type

### Fake Data (Made-Up Values)
- ❌ **3 instances** of fake future dates
- ❌ **1 instance** of placeholder attendance (1000)
- ❌ **1 instance** of fake days_until (14)

### Placeholders (Generic Text)
- ❌ **6 instances** of generic event/alert names
- ❌ **6 instances** of generic action recommendations
- ❌ **3 instances** of generic contact targets
- ❌ **3 instances** of generic urgency text

### Random Math (Hardcoded Assumptions)
- ❌ **5 instances** of hardcoded TPM (4 turns/month)
- ❌ **8 instances** of hardcoded event multipliers (2.0, 3.4, 2.5, 1.8, 1.3)
- ❌ **4 instances** of hardcoded upsell percentages (0.68, 0.70)
- ❌ **5 instances** of hardcoded prices ($8.20, $7.50)
- ❌ **2 instances** of hardcoded event duration (3 days)
- ❌ **2 instances** of hardcoded revenue thresholds (5000, 2000)
- ❌ **1 instance** of hardcoded tanker cost (1200)
- ❌ **1 instance** of hardcoded margin (0.70)
- ❌ **1 instance** of hardcoded weeks (4)
- ❌ **10 instances** of hardcoded scoring thresholds (85, 70, 50, 30)

### Bugs
- ❌ **1 bug:** `expected_attendance` referenced but not selected in events query

---

## Real Data Available (From Glide API)

**✅ CONFIRMED REAL DATA:**
- Restaurant names (`r.MHXYO`)
- Restaurant status (`r.s8tNr` - Open/Closed)
- Oil types (`r.U0Jf2`)
- Delivery frequency (`r.Po4Zg`)
- Last order date (`r.uwU2A`)
- Fryer count per restaurant (`COUNT(f.glide_rowID)`)
- Fryer capacity in lbs (`f.xhrM0`)
- Casino names (`c.Name`)
- Casino locations (`c.L9K9x`)
- Total customers count
- Active customers count
- Total fryers count
- Total capacity in lbs

**❌ NOT AVAILABLE (Confirmed):**
- Event calendar (no event dates, attendees, event types)
- Historical usage data
- Pricing data (except ZL cost from Dashboard)
- Turns Per Month (TPM) metrics
- Upsell acceptance rates
- Event multipliers from historical data
- Contact names/roles
- Real event names/types

---

## Impact Assessment

### High Impact Issues
1. **Fake Event Dates** - Dashboard shows fake future dates
2. **Fake Attendance** - Dashboard shows placeholder numbers (1000)
3. **Random Math in Revenue** - All revenue calculations use 5+ assumptions
4. **Hardcoded Prices** - Pricing not from real sources
5. **Hardcoded Multipliers** - Event surge calculations are arbitrary

### Medium Impact Issues
1. **Generic Placeholder Text** - UI shows generic names instead of real data
2. **Hardcoded TPM** - Weekly gallons assume 4 turns/month
3. **Arbitrary Scoring** - Relationship scores use arbitrary thresholds
4. **Generic Recommendations** - Action items are generic placeholders

### Low Impact Issues
1. **Hardcoded Constants** - Industry standards (7.6 lbs/gal) may be acceptable
2. **Threshold Values** - Revenue thresholds for urgency classification

---

## Recommendations

### Immediate Actions (This Week)

1. **Remove ALL fake dates:**
   - Return `NULL` for `event_date` fields
   - Remove `DATE_ADD(CURRENT_DATE(), INTERVAL X DAY)`
   - Frontend must handle `NULL` dates

2. **Remove ALL placeholder numbers:**
   - Return `NULL` for `expected_attendance`
   - Return `NULL` for `days_until` if no real event data
   - Remove `1000 as expected_attendance`

3. **Remove ALL generic placeholder text:**
   - Use restaurant/casino names or `NULL`
   - Remove generic event names
   - Remove generic contact targets
   - Remove generic action recommendations

4. **Fix bug in events endpoint:**
   - Remove `row.expected_attendance` reference or add to SELECT

### Short-Term Actions (This Month)

1. **Remove ALL hardcoded multipliers:**
   - Require Kevin input via query params
   - Return `NULL` for calculated fields if inputs missing
   - Update formulas: `base_gallons × kevin_multiplier` or `NULL`

2. **Remove ALL hardcoded percentages:**
   - Require Kevin input for upsell %
   - Return `NULL` for upsell calculations if input missing

3. **Remove ALL hardcoded prices:**
   - Pull ZL cost from Dashboard forecast (real source)
   - Require Kevin input for price per gallon
   - Return `NULL` for revenue if price missing

4. **Remove ALL hardcoded TPM:**
   - Require Kevin input for turns per month
   - Return `NULL` for weekly gallons if TPM missing

5. **Implement query parameters:**
   - All APIs accept: `?tpm=4&upsell_pct=0.68&price_per_gal=8.20&event_multiplier=2.0&event_days=3`
   - If params missing, return `NULL` for calculated fields

### Medium-Term Actions (Next Quarter)

1. **Build Kevin Override UI:**
   - Provide all inputs before calculations
   - Show which fields are `NULL` and why
   - Display real data vs. calculated fields clearly

2. **Real Data Integration:**
   - Integrate real event calendar (if approved)
   - Track historical upsell acceptance rates
   - Store Kevin's inputs in scenario library

---

## Compliance Checklist

### Current State
- [ ] ❌ No fake dates
- [ ] ❌ No placeholder numbers
- [ ] ❌ No generic placeholder text
- [ ] ❌ No random math (hardcoded multipliers)
- [ ] ❌ No random math (hardcoded percentages)
- [ ] ❌ No random math (hardcoded prices)
- [ ] ❌ No random math (hardcoded TPM)
- [ ] ❌ No bugs (referenced fields exist)

### Target State
- [ ] ✅ All dates are `NULL` or real
- [ ] ✅ All numbers are real or `NULL`
- [ ] ✅ All text is real or `NULL`
- [ ] ✅ All multipliers come from Kevin input or `NULL`
- [ ] ✅ All percentages come from Kevin input or `NULL`
- [ ] ✅ All prices come from real sources or Kevin input or `NULL`
- [ ] ✅ All TPM comes from Kevin input or `NULL`
- [ ] ✅ All referenced fields exist

---

## File-by-File Fix Requirements

### 1. `/api/v4/vegas/metrics/route.ts`
**Required Changes:**
- Accept query params: `tpm`, `event_days`, `event_multiplier`, `upsell_pct`, `price_per_gal`
- Remove hardcoded values (4, 3.0/7.0, 2.0, 0.68, 8.20)
- Return `NULL` for `revenue_potential` if params missing
- Return `NULL` for `upcoming_events` (not real event count)

### 2. `/api/v4/vegas/upsell-opportunities/route.ts`
**Required Changes:**
- Accept query params: `tpm`, `event_days`, `event_multiplier`, `upsell_pct`, `price_per_gal`, `zl_cost`, `tanker_cost`
- Remove fake date (`DATE_ADD`)
- Remove placeholder attendance (1000)
- Remove generic event name (`'Event Surge Opportunity'`)
- Remove generic contact (`'Restaurant Manager'`)
- Return `NULL` for calculated fields if params missing

### 3. `/api/v4/vegas/events/route.ts`
**Required Changes:**
- Accept query params: `tpm`, `event_multiplier`, `upsell_pct`, `price_per_gal`
- Remove fake date (`DATE_ADD`)
- Remove generic event type (`'Casino Event Surge'`)
- Remove hardcoded multipliers (3.4, 2.5, 1.8, 1.3) - use Kevin input
- Fix bug: Remove `row.expected_attendance` or add to SELECT
- Return `NULL` for calculated fields if params missing

### 4. `/api/v4/vegas/customers/route.ts`
**Required Changes:**
- Accept query param: `tpm`
- Remove hardcoded TPM (4)
- Keep relationship scores (based on real fryer count - acceptable)
- Keep growth potential (based on real fryer count - acceptable)
- Return `NULL` for `weekly_gallons` if TPM not provided

### 5. `/api/v4/vegas/margin-alerts/route.ts`
**Required Changes:**
- Accept query params: `tpm`, `price_per_gal`, `zl_cost`
- Pull ZL cost from Dashboard forecast (real source)
- Remove hardcoded TPM (4)
- Remove hardcoded price ($8.20)
- Remove hardcoded cost ($7.50) - use Dashboard forecast
- Keep severity thresholds (based on real fryer count - acceptable)
- Return `NULL` for calculated fields if params missing

---

## Conclusion

**Status:** 🔴 **CRITICAL** - Production endpoints contain 47 instances of fake data, placeholders, and random math

**Action Required:** IMMEDIATE removal of all fake data, placeholders, and random math

**Priority:** HIGH - Dashboard is displaying fake data to users

**Estimated Fix Time:** 2-3 days for all 5 endpoints

---

**Audit Completed:** November 5, 2025  
**Next Review:** After fixes implemented

