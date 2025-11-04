# Complete Analysis - ALL 4 Models Performance

**Date:** November 4, 2025  
**Question:** Why do models perform differently? Complete analysis.

---

## ACTUAL MAPE VALUES (ALL 4 MODELS)

| Model | MAPE | Rank | Training Rows | Features |
|-------|------|------|---------------|----------|
| **6M** | **0.67%** | 🥇 Best | 1,198 | 258 |
| **3M** | **0.69%** | 🥈 2nd | 1,329 | 268 |
| **1M** | **0.70%** | 🥉 3rd | 1,347 | 274 |
| **1W** | **0.72%** | 4th | 1,448 | 276 |

---

## WHY PERFORMANCE DIFFERS

### 1. Feature Count (Fewer = Better)

**6M (0.67% MAPE - BEST):**
- **258 features** (excludes 28 NULL columns)
- Excludes: 8 standard + 7 news + 11 trump NULLs
- **Most focused** - least noise

**3M (0.69% MAPE - 2nd):**
- **268 features** (excludes 18 NULL columns)
- Excludes: 8 standard + 7 news + 1 trump NULLs
- **More focused** than 1W/1M

**1M (0.70% MAPE - 3rd):**
- **274 features** (excludes 10 NULL columns)
- Excludes: 8 standard + 2 news NULLs
- **More features** = more potential noise

**1W (0.72% MAPE - 4th/Worst):**
- **276 features** (excludes 8 NULL columns)
- **Most features** = most potential noise
- Includes features with sparse data

**PATTERN:** Fewer features (more NULL exclusions) = Better MAPE

---

### 2. Training Data Rows

| Model | Training Rows | Impact |
|-------|---------------|--------|
| 1W | 1,448 | Most rows, but worst MAPE |
| 1M | 1,347 | Second most rows, 3rd best MAPE |
| 3M | 1,329 | Third most rows, 2nd best MAPE |
| 6M | 1,198 | Fewest rows, BEST MAPE |

**KEY INSIGHT:** More rows ≠ Better performance. **Feature quality matters more than row count.**

---

### 3. NULL Feature Exclusions

**6M (BEST - 0.67%):**
- Excludes 28 NULL columns
- Most aggressive feature filtering
- Only uses features with real data

**3M (2nd - 0.69%):**
- Excludes 18 NULL columns
- Excludes news columns (100% NULL in 3M timeframe)
- Excludes trump columns that don't exist

**1M (3rd - 0.70%):**
- Excludes 10 NULL columns
- Keeps more features (some may be sparse)

**1W (WORST - 0.72%):**
- Excludes only 8 NULL columns
- Keeps most features (includes sparse data)

**PATTERN:** More NULL exclusions = Better MAPE

---

### 4. Horizon Stability

**6M (180 days):**
- Longest horizon = most stable
- Less affected by daily/weekly noise
- Best signal-to-noise ratio

**3M (90 days):**
- Medium-term = stable
- Good signal-to-noise ratio

**1M (30 days):**
- Short-medium = more volatility
- More noise than 3M/6M

**1W (7 days):**
- Shortest horizon = most volatility
- Most affected by daily noise
- Worst signal-to-noise ratio

**PATTERN:** Longer horizon = More stable = Better MAPE

---

## COMPLETE ANSWER

**Why 6M is BEST (0.67%):**
1. ✅ **Fewest features (258)** - Most focused, least noise
2. ✅ **Excludes most NULLs (28)** - Only real data
3. ✅ **Longest horizon (180 days)** - Most stable predictions
4. ✅ **Best signal-to-noise ratio**

**Why 3M is 2nd (0.69%):**
1. ✅ **Fewer features (268)** - More focused than 1W/1M
2. ✅ **Excludes 18 NULLs** - Removes news columns (100% NULL)
3. ✅ **Medium-term horizon (90 days)** - Stable predictions
4. ✅ **Good signal-to-noise ratio**

**Why 1M is 3rd (0.70%):**
1. ⚠️ **More features (274)** - More potential noise
2. ⚠️ **Excludes only 10 NULLs** - Keeps some sparse features
3. ⚠️ **Short-medium horizon (30 days)** - More volatility
4. ⚠️ **Less stable than 3M/6M**

**Why 1W is WORST (0.72%):**
1. ❌ **Most features (276)** - Most potential noise
2. ❌ **Excludes only 8 NULLs** - Keeps sparse/noisy features
3. ❌ **Shortest horizon (7 days)** - Most volatility/noise
4. ❌ **Worst signal-to-noise ratio**

---

## KEY TAKEAWAY

**Performance order: 6M > 3M > 1M > 1W**

**Reason:** Feature quality (fewer NULLs) + Horizon stability (longer = better) = Better MAPE

**6M wins because:** Most aggressive feature filtering (258 features) + Longest horizon (180 days) = Best signal-to-noise ratio

