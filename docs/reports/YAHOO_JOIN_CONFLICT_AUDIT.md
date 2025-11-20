---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# YAHOO JOIN CONFLICT AUDIT - READ ONLY
**Date:** November 17, 2025  
**Status:** READ ONLY - NO CHANGES  
**Purpose:** Find where Yahoo is being joined incorrectly

---

## THE USER'S STATEMENT

**"yahoo should have never been joined with yahoo"**

This suggests:
1. Yahoo data is being joined to itself (self-join)
2. Yahoo appears multiple times in the pipeline
3. Yahoo and Alpha both provide ZL data, causing duplication
4. Something else entirely

---

## CURRENT JOIN PIPELINE (join_spec.yaml)

### Join Sequence:
1. **base_prices** (source: `staging/yahoo_historical_all_symbols.parquet`)
   - Loads Yahoo ZL=F prices (6,380 rows)
   - This is the BASE, not a join

2. **add_macro** (left: `<<base_prices>>`, right: FRED)
   - Joins FRED to Yahoo base

3. **add_weather** (left: `<<add_macro>>`, right: Weather)
   - Joins Weather to previous result

4. **add_cftc** (left: `<<add_weather>>`, right: CFTC)
   - Joins CFTC to previous result

5. **add_usda** (left: `<<add_cftc>>`, right: USDA)
   - Joins USDA to previous result

6. **add_biofuels** (left: `<<add_usda>>`, right: EIA)
   - Joins EIA to previous result

7. **add_regimes** (left: `<<add_biofuels>>`, right: regime_calendar)
   - Joins regimes to previous result

8. **add_alpha_enhanced** (left: `<<add_regimes>>`, right: `staging/alpha/daily/alpha_complete_ready_for_join.parquet`)
   - **JOINS ON:** `["date", "symbol"]`
   - **HOW:** `left`
   - **This is where the conflict might be!**

---

## THE PROBLEM: ALPHA JOIN ON ["date", "symbol"]

### What Yahoo Provides:
- **Symbol:** ZL=F
- **Data:** Raw OHLCV prices (6,380 rows)
- **Format:** 1 row per date for ZL=F

### What Alpha Provides (per prepare_alpha_for_joins.py):
- **Symbols:** CORN, WHEAT, WTI, BRENT, NATURAL_GAS, COTTON, SUGAR, COFFEE, COPPER, ALUMINUM
- **Data:** Prices + 50+ indicators per symbol
- **Format:** Multiple rows (one per symbol per date)

### The Join:
```python
# In join_spec.yaml:
- name: "add_alpha_enhanced"
  left: "<<add_regimes>>"  # Has ZL=F from Yahoo
  right: "staging/alpha/daily/alpha_complete_ready_for_join.parquet"  # Has CORN, WHEAT, etc. (NO ZL)
  on: ["date", "symbol"]
  how: "left"
```

### What Happens:
1. Left side has: ZL=F rows (from Yahoo)
2. Right side has: CORN, WHEAT, WTI, etc. (from Alpha) - **NO ZL**
3. Join on ["date", "symbol"]:
   - ZL=F rows: **NO MATCH** in Alpha → NaN for all Alpha columns ✅ (This is correct!)
   - CORN rows: **NO MATCH** in left (Yahoo) → **NOT ADDED** (left join keeps left rows only)

### Result:
- ZL=F rows get Alpha columns filled with NaN ✅
- Other symbols (CORN, WHEAT, etc.) from Alpha are **NOT added** to the dataset ❌

---

## THE REAL ISSUE: ALPHA SYMBOLS NOT BEING ADDED

**The join is a LEFT join, which means:**
- It keeps all rows from the LEFT (Yahoo ZL=F)
- It only adds columns from the RIGHT (Alpha indicators)
- It does NOT add new rows for Alpha symbols

**If Alpha has CORN, WHEAT, etc., they won't appear in the final dataset!**

---

## WHAT THE PLANS SAY

### From TRAINING_SURFACE_FIX_THEN_ALPHA.plan.md:
```
Step 8: + Alpha (multi-symbol: ZL + 69 others with 50+ indicators each)
FINAL: ~480K rows (70 symbols × ~6.8K dates) with all features
```

**This suggests Alpha should ADD new symbols, not just add columns!**

### From CORRECTED_DATA_SOURCE_SPLIT.md:
```
Alpha provides:
- All commodities (except ZL): CORN, WHEAT, SOYBEANS (ZS), SOYBEAN MEAL (ZM), WTI, BRENT, etc.
- ALL 50+ technical indicators for ALL symbols (including ZL!)
```

**This says Alpha should have indicators for ZL too!**

### From prepare_alpha_for_joins.py:
```python
for symbol in ['CORN', 'WHEAT', 'WTI', 'BRENT', 'NATURAL_GAS', 'COTTON', 'SUGAR', 'COFFEE', 'COPPER', 'ALUMINUM']:
    # NO ZL in this list!
```

**Alpha is NOT collecting ZL indicators!**

---

## CONFLICTS IDENTIFIED

### Conflict #1: Alpha Should Have ZL Indicators
- **Plan says:** "Alpha provides ALL 50+ technical indicators for ALL symbols (including ZL!)"
- **Code does:** Alpha only collects indicators for 10 symbols (CORN, WHEAT, etc.), **NO ZL**
- **Result:** ZL won't get Alpha indicators

### Conflict #2: Join Type Wrong for Multi-Symbol Expansion
- **Plan says:** "FINAL: ~480K rows (70 symbols × ~6.8K dates)"
- **Join does:** LEFT join keeps only Yahoo's ZL rows, doesn't add Alpha's other symbols
- **Result:** Only 6,380 rows (ZL only), not 480K rows (70 symbols)

### Conflict #3: Alpha Should NOT Have ZL Prices
- **Plan says:** "Yahoo = ZL=F prices ONLY"
- **Alpha provides:** Prices + indicators for other symbols
- **If Alpha also had ZL prices:** Would duplicate Yahoo's ZL prices ❌
- **Current state:** Alpha doesn't have ZL prices ✅ (but also doesn't have ZL indicators ❌)

---

## WHAT "YAHOO JOINED WITH YAHOO" MIGHT MEAN

### Possibility 1: Alpha Has ZL Prices (Duplication)
- If `prepare_alpha_prices()` collected ZL prices
- Then join would merge Yahoo ZL prices with Alpha ZL prices
- **This would be "Yahoo joined with Yahoo" (via Alpha)**

### Possibility 2: Yahoo Appears Twice in Pipeline
- Check if `base_prices` is referenced multiple times
- Check if Yahoo staging file is used in multiple joins
- **Current audit:** Yahoo only appears once as base_prices ✅

### Possibility 3: Self-Join on Yahoo Data
- If join_spec.yaml has a join where left=Yahoo and right=Yahoo
- **Current audit:** No self-join found ✅

### Possibility 4: Alpha ZL Indicators Join Creates Duplicate ZL Rows
- If Alpha has ZL indicators with different dates than Yahoo
- Join on ["date", "symbol"] might create multiple ZL rows per date
- **Need to check:** Does Alpha have ZL data at all?

---

## QUESTIONS TO ANSWER

1. **Does Alpha collect ZL indicators?** (prepare_alpha_for_joins.py says NO)
2. **Does Alpha collect ZL prices?** (Should be NO, but need to verify)
3. **Should the Alpha join be OUTER instead of LEFT?** (To add Alpha symbols as new rows)
4. **Is there a separate step that adds Alpha symbols?** (Not found in join_spec.yaml)
5. **Are there multiple join_spec.yaml files?** (Need to check)

---

## FILES TO CHECK

1. `scripts/staging/prepare_alpha_for_joins.py` - What symbols does it process?
2. `scripts/ingest/collect_alpha_master.py` - What symbols does it collect?
3. `registry/join_spec.yaml` - Is there a self-join or duplicate Yahoo reference?
4. `docs/plans/TRAINING_SURFACE_FIX_THEN_ALPHA.plan.md` - What does it say about the join?
5. Any other join_spec files in the codebase?

---

## IMMEDIATE FINDINGS

### ✅ Yahoo Only Appears Once
- `base_prices` is the only Yahoo reference
- No self-join found

### ❌ Alpha Join Type May Be Wrong
- LEFT join won't add Alpha symbols as new rows
- Plan expects 70 symbols, but LEFT join keeps only ZL

### ❌ Alpha Doesn't Collect ZL
- `prepare_alpha_for_joins.py` excludes ZL from symbol list
- Plan says Alpha should provide ZL indicators

### ⚠️ Need to Verify
- Does Alpha collection script try to collect ZL?
- Is there a separate step that adds Alpha symbols?
- What does the actual Alpha staging file contain?

---

## NEXT STEPS (READ ONLY - NO CHANGES)

1. Check `scripts/ingest/collect_alpha_master.py` for ZL collection
2. Check actual Alpha staging files for ZL data
3. Review all plans for conflicting statements about ZL
4. Check if there are multiple join pipelines
5. Verify what the user means by "yahoo joined with yahoo"





