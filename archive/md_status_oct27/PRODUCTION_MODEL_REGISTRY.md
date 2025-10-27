# PRODUCTION MODEL REGISTRY
**Date:** October 27, 2025  
**Status:** ✅ VERIFIED PRODUCTION MODELS

---

## 🎯 OFFICIAL PRODUCTION MODELS

### V4 Enriched Boosted Tree Suite
**Status:** ✅ PRODUCTION READY  
**Performance:** Institutional-grade (MAPE ~2.16%)  
**Created:** October 23, 2025

| Horizon | Model ID | MAPE | MAE | R² | Status |
|---------|----------|------|-----|----|---------| 
| **1-Week** | `cbi-v14.models.zl_boosted_tree_1w_v3_enriched` | 2.14% | $1.65 | 0.955 | ✅ PROD |
| **1-Month** | `cbi-v14.models.zl_boosted_tree_1m_v3_enriched` | 2.16% | $1.55 | 0.963 | ✅ PROD |
| **3-Month** | `cbi-v14.models.zl_boosted_tree_3m_v3_enriched` | 3.62% | $1.81 | 0.957 | ✅ PROD |
| **6-Month** | `cbi-v14.models.zl_boosted_tree_6m_v3_enriched` | 3.53% | $1.76 | 0.940 | ✅ PROD |

### Dataset Specification
- **Source:** `cbi-v14.models.training_dataset`
- **Features:** 62 columns (33 base + 29 news/social)
- **Rows:** 1,263 (Oct 21, 2020 → Oct 13, 2025)
- **Split:** Random 80/20 train/eval
- **Algorithm:** BOOSTED_TREE_REGRESSOR

---

## 🚫 ARCHIVED MODELS (DO NOT USE)

### V5 Enhanced Models (Failed Experiment)
- `zl_boosted_tree_1w_v5_enhanced` - MAPE 5.38% (worse than V4)
- **Issue:** 145 features introduced noise, degraded performance
- **Status:** ❌ ARCHIVED - Reference only

### Experimental Models (Unverified)
- Any model with MAE ~$0.99-1.23 (internal experiments, not production)
- **Status:** ❌ UNVERIFIED - Require validation

---

## 🔧 PRODUCTION VALIDATION CHECKLIST

### Pre-Deployment Verification
- [ ] Model ID matches registry exactly
- [ ] Feature count = 62 columns
- [ ] Training date = Oct 23, 2025
- [ ] MAPE within expected range (2.1-3.6%)
- [ ] Dataset source verified

### Runtime Checks
```sql
-- Verify model exists and is correct version
SELECT model_id, created, model_type 
FROM `cbi-v14.models.__MODELS__` 
WHERE model_id = 'zl_boosted_tree_1m_v3_enriched'
  AND created = '2025-10-23'
```

### Feature Validation
```python
# Verify feature count in production
expected_features = 62
actual_features = len(model.feature_columns)
assert actual_features == expected_features, f"Feature mismatch: {actual_features} != {expected_features}"
```

---

## 📈 PERFORMANCE ENHANCEMENT ROADMAP

### Phase 1: Simple Ensemble (Week 1)
**Target:** Reduce MAPE by 0.3-0.5 percentage points

1. **Dynamic Weighting System**
   - 30-day rolling performance window
   - Weight = `exp(1/recent_mape)` normalized
   - Update weights daily

2. **Statistical Validation Layer**
   - Z-score bounds: Flag predictions > 3σ
   - Commodity constraints: Physical price limits
   - Extreme prediction blending with simpler models

### Phase 2: Regime Detection (Week 2)
**Target:** 10-15% accuracy improvement during transitions

1. **Two-Regime System**
   - High volatility: VIX > 80th percentile
   - Low volatility: VIX ≤ 80th percentile
   - Separate model weights per regime

2. **Feature Stability Monitoring**
   - Track top 10 feature importance shifts
   - Alert on >20% importance changes
   - Preemptive data quality detection

### Expected Combined Impact
- **Current MAPE:** 2.16%
- **Target MAPE:** 1.8-2.0%
- **Implementation:** <1 week
- **Complexity:** Low (operational improvements only)

---

## 🔒 SECURITY & VERSION CONTROL

### Model Integrity
- **Hash Verification:** SHA-256 checksums for model files
- **Access Control:** Read-only production model access
- **Backup Strategy:** Automated daily model snapshots

### Change Management
- **Approval Required:** Any model changes require explicit approval
- **Testing Protocol:** All changes tested on 30-day holdout
- **Rollback Plan:** Immediate revert capability to last known good

### Documentation Requirements
- **Model Cards:** Full lineage for each production model
- **Performance Tracking:** Daily MAPE monitoring
- **Incident Response:** Escalation procedures for model failures

---

## 📊 MONITORING & ALERTS

### Critical Alerts (Immediate Action)
- MAPE increases >0.5% for 3+ consecutive days
- Feature importance shifts >20% in top 10 features
- Prediction bounds exceeded (>3σ from historical)

### Warning Alerts (24h Review)
- MAPE increases >0.2% for 7+ days
- Data quality issues in news/social feeds
- Model prediction confidence drops below threshold

### Info Alerts (Weekly Review)
- Feature drift in secondary features
- Performance comparison vs benchmark models
- Usage statistics and API health

---

**Registry Maintained By:** CBI-V14 Production Team  
**Last Updated:** October 27, 2025  
**Next Review:** November 27, 2025

---

## ⚠️ CRITICAL WARNINGS

1. **Never use V5 models in production** - Performance degraded
2. **Always verify model ID exactly** - Similar names exist
3. **62 features required** - Other feature counts indicate wrong model
4. **Oct 23, 2025 creation date** - Earlier dates are deprecated models

**When in doubt, refer to this registry. No exceptions.**
