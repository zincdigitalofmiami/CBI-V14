# ENHANCED CALCULATOR DRY TEST
## Step-by-Step Math Validation with Real Data

### TEST SCENARIO: F1 Race at Caesars Palace

**Event Data:**
- Event: F1 Race - Las Vegas Grand Prix
- Event Type: F1 Race
- Start Date: 2024-11-16
- End Date: 2024-11-18 (3 days)
- Expected Attendance: 450,000
- Location: Las Vegas Strip
- Casino Group: Caesars Entertainment
- Is Strip Wide: TRUE
- Coordinates: (36.1171, -115.1744) - Caesars Palace

**Restaurant Data:**
- Restaurant: Gordon Ramsay Steakhouse
- Casino: Caesars Palace
- Casino Group: Caesars Entertainment
- Cuisine Type: steakhouse
- Fryer Count: 3
- Base Daily Usage: 15 lbs per fryer per week (from cuisine base usage)
- Coordinates: (36.1165, -115.1740) - Same casino, ~0.1 miles apart
- Demographic Profile: { income_level: 'high', age_group: '35-50' }

**Baseline Traffic:**
- Caesars Palace Baseline Daily Traffic: 50,000

---

## STEP-BY-STEP CALCULATION

### Step 1: Base Gallons Calculation

**Input:**
- Cuisine Type: steakhouse
- Base Usage (from cuisineBaseUsage): 5 lbs per fryer per week
- Fryer Count: 3

**Calculation:**
```
Weekly Usage = fryer_count × base_usage_per_fryer
Weekly Usage = 3 × 5 = 15 lbs/week

Daily Usage = weekly_usage / 7
Daily Usage = 15 / 7 = 2.143 lbs/day

Convert to Gallons (assuming 7.6 lbs/gal for soybean oil):
Base Daily Gallons = 2.143 / 7.6 = 0.282 gallons/day
```

**Result:**
- Base Daily Gallons: **0.282 gal/day**

---

### Step 2: Traffic Ratio Calculation

**Function:** `calculateTrafficRatio(event, restaurant)`

**Input:**
- Event Attendance: 450,000
- Baseline Traffic: 50,000
- Is Strip Wide: TRUE

**Calculation:**
```
Traffic Ratio = event_attendance / baseline_traffic
Traffic Ratio = 450,000 / 50,000 = 9.0

Since is_strip_wide = TRUE:
Capped at 9.0 (from Grok's data)
```

**Result:**
- Traffic Ratio: **9.0×**

---

### Step 3: Cuisine Match Factor

**Function:** `calculateCuisineMatch(event, restaurant, cuisineAffinities)`

**Input:**
- Event Type: F1 Race
- Cuisine Type: steakhouse
- Special Match: 'steakhouse' + 'F1 Race' = 1.8× (from specialMatches)

**Calculation:**
```
Check specialMatches['F1 Race']['steakhouse'] = 1.8
```

**Result:**
- Cuisine Factor: **1.8×**

---

### Step 4: Demo/Psycho Spend Factor

**Function:** `calculateDemoPsychoSpendFactor(event, restaurant)`

**Input:**
- Event Type: F1 Race
- Spending Profile: { avgSpend: 966, psychoSegment: 'affluent thrill-seekers', factor: 1.6 }
- Restaurant Income Level: 'high'

**Calculation:**
```
Spending Intensity = avg_spend / baseline (200)
Spending Intensity = 966 / 200 = 4.83

Factor = spending_intensity × profile_factor
Factor = 4.83 × 1.6 = 7.728

Since restaurant.income_level === 'high' AND profile.avgSpend > 500:
Boost = 1.2×
Final Factor = 7.728 × 1.2 = 9.274
```

**Result:**
- Demo/Psycho Spend Factor: **9.274×**

---

### Step 5: Location Likelihood

**Function:** `calculateLocationLikelihood(event, restaurant)`

**Input:**
- Event Coordinates: (36.1171, -115.1744)
- Restaurant Coordinates: (36.1165, -115.1740)
- Event Casino Group: Caesars Entertainment
- Restaurant Casino Group: Caesars Entertainment

**Calculation:**
```
Distance = Haversine formula
Distance = sqrt((36.1171 - 36.1165)² + (-115.1744 - -115.1740)²) × 69 miles/degree
Distance ≈ 0.08 miles

Since distance <= 0.1 miles:
Base Likelihood = 0.90 (90%)

Since casino_group_id matches:
Boost = 1.5×
Final Likelihood = min(0.90 × 1.5, 0.95) = 0.95 (95%)
```

**Result:**
- Location Likelihood: **0.95 (95%)**

---

### Step 6: Duration Factor

**Function:** `calculateDurationFactor(event)`

**Input:**
- Start Date: 2024-11-16
- End Date: 2024-11-18
- Event Type: F1 Race
- Duration Days: 3

**Calculation:**
```
Duration Days = (end_date - start_date) + 1
Duration Days = (2024-11-18 - 2024-11-16) + 1 = 3 days

Linger Factor for 'F1 Race': 1.0 (no extra linger, already multi-day)

Since durationDays > 1 and <= 3:
Factor = 1.0 + (durationDays × 0.7 × lingerFactor)
Factor = 1.0 + (3 × 0.7 × 1.0)
Factor = 1.0 + 2.1 = 3.1
```

**Result:**
- Duration Factor: **3.1×**

---

### Step 7: Raw Multiplier Calculation

**Calculation:**
```
Raw Multiplier = traffic_ratio × cuisine_factor × demo_psycho_factor × location_likelihood × duration_factor

Raw Multiplier = 9.0 × 1.8 × 9.274 × 0.95 × 3.1

Step by step:
= 9.0 × 1.8 = 16.2
= 16.2 × 9.274 = 150.24
= 150.24 × 0.95 = 142.73
= 142.73 × 3.1 = 442.46
```

**Result:**
- Raw Multiplier: **442.46×**

---

### Step 8: Apply Event-Specific Cap

**Input:**
- Event Type: F1 Race
- Cap Value: 3.4× (from vegas_event_multiplier_caps)

**Calculation:**
```
Capped Multiplier = min(raw_multiplier, cap_value)
Capped Multiplier = min(442.46, 3.4) = 3.4
```

**Result:**
- Capped Multiplier: **3.4×**

**Note:** This is the conservative cap from Grok's backtesting. The raw multiplier (442×) is clearly unrealistic, so the cap is essential.

---

### Step 9: Surge Gallons Calculation

**Calculation:**
```
Surge Gallons = base_gallons × (capped_multiplier - 1.0)

For 3-day event:
Base Gallons for 3 Days = 0.282 × 3 = 0.846 gallons
Surge Gallons = 0.846 × (3.4 - 1.0) = 0.846 × 2.4 = 2.03 gallons
```

**Result:**
- Surge Gallons: **2.03 gallons** (over 3 days)

---

### Step 10: Revenue Calculation

**Input:**
- Price per Gallon: $3.50 (example from code)
- Surge Gallons: 2.03

**Calculation:**
```
Surge Revenue = surge_gallons × price_per_gallon
Surge Revenue = 2.03 × 3.50 = $7.11
```

**Result:**
- Surge Revenue: **$7.11**

---

### Step 11: AI Insight Generation

**Function:** `generateGrokStyleInsight()`

**Input:**
- Event Type: F1 Race
- Psychographic Profile: 'affluent thrill-seekers'
- Location Likelihood: 95%
- Casino Group Match: TRUE
- Cuisine Factor: 1.8×
- Spending: $966/person
- Duration: 3 days

**Generated Insight:**
```
"affluent thrill-seekers (psycho: f1 race) × Las Vegas Strip = 95% to Caesars Entertainment venues with steakhouse cuisine match (1.8×) ($966 spend/person), 3 day impact"
```

---

### Step 12: Urgency Level & Purchase Date

**Input:**
- Event Start: 2024-11-16
- Today: 2024-10-15 (assumed)
- Lead Time for F1 Race: 3 days (from eventTypeDefinitions)

**Calculation:**
```
Days Until Event = (2024-11-16 - 2024-10-15) = 32 days

Recommended Purchase Date = event_start - lead_time
Recommended Purchase Date = 2024-11-16 - 3 = 2024-11-13

Days Until Purchase = (2024-11-13 - 2024-10-15) = 29 days

Since days_until_purchase > 7:
Urgency Level = 'LOW'
```

**Result:**
- Urgency Level: **LOW**
- Recommended Purchase Date: **2024-11-13**
- Days Until Purchase: **29 days**

---

## FINAL RESULTS SUMMARY

### Calculation Breakdown:
| Factor | Value | Notes |
|--------|-------|-------|
| Base Daily Gallons | 0.282 gal/day | From steakhouse (5 lbs/fryer/week) |
| Traffic Ratio | 9.0× | 450K / 50K baseline |
| Cuisine Factor | 1.8× | Steakhouse + F1 special match |
| Demo/Psycho Factor | 9.274× | High spending + high-end restaurant |
| Location Likelihood | 0.95 (95%) | Same casino group, close proximity |
| Duration Factor | 3.1× | 3-day event with linger |
| **Raw Multiplier** | **442.46×** | Before capping |
| **Capped Multiplier** | **3.4×** | F1 Race cap (conservative) |
| **Surge Gallons (3 days)** | **2.03 gal** | Additional oil needed |
| **Surge Revenue** | **$7.11** | At $3.50/gal |

### AI Insight:
"affluent thrill-seekers (psycho: f1 race) × Las Vegas Strip = 95% to Caesars Entertainment venues with steakhouse cuisine match (1.8×) ($966 spend/person), 3 day impact"

### Urgency:
- Level: **LOW**
- Purchase by: **November 13, 2024**

---

## MATH VALIDATION

### ✅ Checks Passed:

1. **Base Calculation:** ✅ Correct
   - 3 fryers × 5 lbs/week = 15 lbs/week
   - 15 lbs/week ÷ 7 = 2.143 lbs/day
   - 2.143 lbs ÷ 7.6 lbs/gal = 0.282 gal/day ✓

2. **Traffic Ratio:** ✅ Correct
   - 450,000 ÷ 50,000 = 9.0 ✓

3. **Cuisine Match:** ✅ Correct
   - Special match lookup: steakhouse + F1 = 1.8× ✓

4. **Spend Factor:** ✅ Correct
   - 966 ÷ 200 = 4.83
   - 4.83 × 1.6 = 7.728
   - 7.728 × 1.2 = 9.274 ✓

5. **Location:** ✅ Correct
   - Distance ~0.08 miles = 90% base
   - Same casino group = 1.5× boost
   - 0.90 × 1.5 = 0.95 (capped) ✓

6. **Duration:** ✅ Correct
   - 3 days with 1.0 linger factor
   - 1.0 + (3 × 0.7 × 1.0) = 3.1 ✓

7. **Raw Multiplier:** ✅ Correct
   - 9.0 × 1.8 × 9.274 × 0.95 × 3.1 = 442.46 ✓

8. **Capping:** ✅ Correct
   - min(442.46, 3.4) = 3.4 ✓

9. **Surge Calculation:** ✅ Correct
   - 0.846 × (3.4 - 1.0) = 2.03 gal ✓

### ⚠️ Observations:

1. **Raw Multiplier is Extremely High (442×):**
   - This shows why capping is CRITICAL
   - Without cap, calculations would be unrealistic
   - Cap of 3.4× is conservative and validated

2. **Demo/Psycho Factor is Very High (9.274×):**
   - This is driven by $966 spending vs $200 baseline (4.83×)
   - Plus 1.6× factor = 7.728×
   - Plus 1.2× boost for high-end restaurant = 9.274×
   - This seems high - may need review

3. **Location Likelihood at 95%:**
   - Makes sense for same casino group, close proximity
   - Validates the casino group matching logic

4. **Final Surge is Small (2.03 gal):**
   - This is because base usage is small (0.282 gal/day)
   - For a restaurant with more fryers, surge would scale proportionally

---

## SCALING TEST

### Test with Larger Restaurant:

**Input:**
- Fryer Count: 10 (instead of 3)
- All other factors same

**Calculation:**
```
Base Daily Gallons = (10 × 5 / 7) / 7.6 = 0.94 gal/day
Base for 3 Days = 0.94 × 3 = 2.82 gal
Surge = 2.82 × (3.4 - 1.0) = 2.82 × 2.4 = 6.77 gal
Revenue = 6.77 × 3.50 = $23.70
```

**Result:** Surge scales proportionally with fryer count ✓

---

## VALIDATION AGAINST GROK'S DATA

**Grok's F1 2023 Validation:**
- 3.6× spend multiplier
- 85% to Caesars venues

**Our Calculation:**
- Capped Multiplier: 3.4× (conservative, close to 3.6×) ✓
- Location Likelihood: 95% (higher than 85%, but for same casino group) ✓

**Assessment:** Our calculations align with Grok's backtested data.

---

## RECOMMENDATIONS

### Potential Issues:

1. **Demo/Psycho Factor May Be Too High:**
   - 9.274× seems excessive
   - Consider: Is the 1.2× boost for high-end restaurants correct?
   - Consider: Should spending_intensity be capped before multiplying?

2. **Raw Multiplier Before Cap:**
   - 442× is clearly unrealistic
   - This validates the need for capping
   - Consider logging raw multiplier for debugging

3. **Base Usage Calculation:**
   - Currently in pounds, converted to gallons
   - Ensure consistency: are all calculations in same units?
   - Consider storing base_usage_gallons directly

### Suggested Adjustments:

1. **Add Intermediate Logging:**
   - Log each factor separately
   - Log raw multiplier before capping
   - This helps debug unrealistic calculations

2. **Review Demo/Psycho Factor:**
   - Consider capping spending_intensity at 5.0× before applying factor
   - Or reduce the 1.2× boost for high-end restaurants to 1.1×

3. **Consider Compound vs Simple Multiplication:**
   - Current: All factors multiplied together
   - Alternative: Some factors could be additive rather than multiplicative
   - Example: Location likelihood could reduce other factors rather than multiply

---

## CONCLUSION

### ✅ Math is Correct:
All calculations are mathematically sound and follow the formulas correctly.

### ⚠️ Factor Values May Need Tuning:
- Demo/Psycho factor (9.274×) seems high
- Raw multiplier (442×) shows why capping is essential
- Final capped result (3.4×) aligns with Grok's validation

### ✅ Overall Assessment:
The math works correctly. The high raw multiplier demonstrates why event-specific caps are critical. The final result (3.4× surge) is reasonable and aligns with backtested data.

**Recommendation:** Proceed with implementation, but monitor demo/psycho factor values in production and adjust if needed.

