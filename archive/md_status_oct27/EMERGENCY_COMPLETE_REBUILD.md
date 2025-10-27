# EMERGENCY - COMPLETE DATA REBUILD NEEDED

## ROOT CAUSE FOUND

**The original BigQuery table `models.training_complete_enhanced` has WRONG targets!**

- `target_1w` contains PRICES (33-90), not RETURNS (-0.2 to +0.2)
- This bug exists in ALL downloaded datasets
- Models can't learn properly with wrong targets
- 100% "accuracy" is because all prices are positive

## WHAT WENT WRONG IN SOURCE DATA

Someone created the training table and made this mistake:
```sql
-- WRONG (what was done):
target_1w = LEAD(zl_price_current, 5)  -- Returns future price

-- CORRECT (what should have been):
target_1w = (LEAD(zl_price_current, 5) / zl_price_current) - 1  -- Returns % change
```

## SOLUTION

**Don't use ANY pre-made targets. Calculate fresh:**

1. Start with raw `forecasting_data_warehouse` tables
2. Get soybean oil prices
3. Get all features
4. Calculate targets ourselves: `(price[t+5] / price[t]) - 1`
5. Join everything fresh
6. Verify targets are returns, not prices

## THIS EXPLAINS EVERYTHING

- Why all specialists got 100% directional accuracy
- Why MAE was 2-5 (predicting $40-50 prices vs actual $40-50)
- Why I kept making mistakes (working with buggy source data)

## ACTION REQUIRED

**Build dataset from scratch:**
- Pull raw soybean oil prices
- Pull all features separately
- Calculate returns ourselves
- Join everything fresh
- Verify targets before ANY training

**STOP using:**
- `training_complete_enhanced`
- Any dataset with pre-calculated targets
- Any "enhanced" or "enriched" tables (they all have this bug)

**START fresh from warehouse tables only**

