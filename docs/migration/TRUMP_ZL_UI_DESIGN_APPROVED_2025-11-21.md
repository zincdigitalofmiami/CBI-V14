---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Trump/ZL Probability Analysis - Approved UI Design

**Date:** November 21, 2025  
**Status:** ✅ APPROVED by Kirk  
**Location:** Legislative Page (below the fold)  
**Purpose:** Provide probability-based decision support for procurement, NOT financial advice

---

## 🎯 DESIGN PRINCIPLE

> **Trump tweets are ONE INPUT into a 400-feature trained model, not a standalone buy/sell signal.**

### Critical Requirements:

1. ✅ **Probability-based** ("72% chance") not certainty ("will drop")
2. ✅ **Integrated model** (Trump = 1 of 400 features) not single-signal
3. ✅ **Decision support** ("Consider IF...") not commands ("LOCK NOW!")
4. ✅ **SHAP transparency** (show all drivers) not black box
5. ✅ **Legal protection** (disclaimers) not financial advice
6. ✅ **Uncertainty display** (confidence + ranges) not point estimates

---

## ❌ WRONG APPROACH (REJECTED)

### What NOT to Do:

```
🚨 URGENT: LOCK CONTRACTS NOW
Trump tariff tweet detected
Expected -2.8% drop in 48 hours
[LOCK NOW BUTTON]
```

**Problems:**
- ❌ Commands action based on single signal (Trump tweet)
- ❌ Ignores 400-feature trained model
- ❌ Presents prediction as certainty
- ❌ Legal liability (financial advice)
- ❌ No SHAP transparency

---

## ✅ APPROVED APPROACH

### Three-Card Intelligence Strip

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    TRUMP/ZL PROBABILITY ANALYSIS                         │
├──────────────────┬──────────────────────┬──────────────────────────────┤
│  🌩️ TRUMP SIGNAL │  📊 MODEL FORECAST   │  💡 PROCUREMENT INSIGHT      │
│  ──────────      │  ──────────          │  ──────────                  │
│                  │                      │                              │
│  Activity: HIGH  │  72% probability     │  Price likely to decline     │
│  [GAUGE]         │  of -2% to -4% move  │  2-4% over 48-72h based on   │
│         ▲        │  in next 48-72h      │  400-feature trained model   │
│                  │                      │                              │
│  Tariff signal   │  Model confidence:   │  Consider locking IF:        │
│  detected (85%)  │  Medium ████████░░   │  • Already near targets      │
│                  │                      │  • Low inventory position    │
│  ⚠️ This is 1 of │  Top Drivers (SHAP): │  • Risk-averse to volatility │
│  400+ features   │  1. RINs: +11.2¢     │                              │
│  in the model    │  2. Trump: -3.1¢     │  Consider waiting IF:        │
│                  │  3. Weather: +6.8¢   │  • Time flexibility (>1 wk)  │
│  7d trend: ▂▅█↑  │  4. Crush: +3.5¢     │  • Model confidence Low-Med  │
│  (Escalating)    │                      │  • Bullish drivers strengthen│
│                  │  Range: $50.50-$51.80│                              │
│                  │  Current: $52.50     │  Historical:                 │
│                  │                      │  Similar 2018 pattern:       │
│                  │                      │  78% → -2% to -5% in 3-5d    │
│                  │                      │                              │
│                  │                      │  ⚠️ Not financial advice.    │
│                  │                      │  Consult risk management.    │
└──────────────────┴──────────────────────┴──────────────────────────────┘
```

---

## 📊 CARD 1: TRUMP SIGNAL (Context, Not Trigger)

### Purpose:
Show Trump activity level with critical context that it's **1 of 400+ features**.

### Visual Elements:

**1. Activity Gauge:**
```
    LOW ────── MODERATE ────── HIGH ────── EXTREME
     🟢          🟡              🔴           🟣
                                  ▲
                               [Current]
```

**2. Signal Type:**
```
Tariff signal detected
Confidence: 85%
```

**3. Critical Context Banner:**
```
⚠️ This is 1 of 400+ features in the model
   (VIX, RINs, weather, crush, CFTC, etc.)
```

**4. 7-Day Trend Sparkline:**
```
7d trend: ▂▅█ Escalating ↑
```

### Data Contract:

```json
"trump_signal": {
  "activity_level": "HIGH",
  "activity_score": 0.75,
  "signal_type": "tariff_rhetoric",
  "confidence": 0.85,
  "context_text": "This is 1 of 400+ features in the trained model",
  "trend_7d": [0.2, 0.3, 0.5, 0.7, 0.9],
  "trend_direction": "escalating"
}
```

### Copy Guidelines:

**✅ Approved Language:**
- "Trump signal activity: HIGH"
- "Tariff rhetoric detected (85% confidence)"
- "This is 1 of 400+ features"
- "7-day trend: Escalating"

**❌ Rejected Language:**
- "Trump threat level" (too alarmist)
- "Imminent tariff" (too certain)
- "Trump predicts" (misleading)
- Any language suggesting Trump signal alone drives decision

---

## 📊 CARD 2: MODEL FORECAST (Integrated Prediction)

### Purpose:
Show **integrated model output** from 400-feature trained model, not Trump alone.

### Visual Elements:

**1. Probability Statement (Primary):**
```
72% probability of -2% to -4% decline
over next 48-72 hours
```

**2. Confidence Bar:**
```
Model Confidence: Medium ████████░░
```

**3. Price Range:**
```
Forecast Range:
  Current:   $52.50/cwt
  Baseline:  $52.00/cwt
  Expected:  $50.50 - $51.80/cwt
```

**4. SHAP Top Drivers:**
```
Top Drivers (SHAP):
  1. RINs momentum:    +11.2¢ (bullish)
  2. Trump signal:     -3.1¢  (bearish)
  3. Brazil weather:   +6.8¢  (bullish)
  4. Crush margin:     +3.5¢  (bullish)
  
Net Model Output: -2.8% likely
```

### Data Contract:

```json
"model_forecast": {
  "direction": "decline",
  "probability": 0.72,
  "range_min_pct": -4.0,
  "range_max_pct": -2.0,
  "time_horizon_hours": "48-72",
  "confidence_level": "medium",
  "confidence_score": 0.68,
  
  "price_forecast": {
    "current": 52.50,
    "baseline": 52.00,
    "expected_min": 50.50,
    "expected_max": 51.80
  },
  
  "shap_drivers": [
    {"feature": "RINs momentum", "impact_cents": 11.2, "direction": "bullish"},
    {"feature": "Trump tariff signal", "impact_cents": -3.1, "direction": "bearish"},
    {"feature": "Brazil weather", "impact_cents": 6.8, "direction": "bullish"},
    {"feature": "Crush margin", "impact_cents": 3.5, "direction": "bullish"}
  ],
  
  "net_output_pct": -2.8
}
```

### Copy Guidelines:

**✅ Approved Language:**
- "72% probability of -2% to -4% decline"
- "Model confidence: Medium"
- "Based on 400-feature trained model"
- "Expected range: $50.50 - $51.80"
- "Top drivers (SHAP): RINs +11.2¢, Trump -3.1¢..."

**❌ Rejected Language:**
- "Price will drop 2.8%" (no certainty)
- "Guaranteed decline" (no guarantees)
- "Trump predicts -2.8%" (model predicts, not Trump)
- Any language hiding SHAP drivers

---

## 📊 CARD 3: PROCUREMENT INSIGHT (Decision Support)

### Purpose:
Provide **conditional logic** for decision-making, NOT commands or financial advice.

### Visual Elements:

**1. Summary Statement:**
```
Price likely to decline 2-4% over 48-72h
based on 400-feature trained model
```

**2. Consider Locking IF:**
```
✓ Already near procurement targets
✓ Low inventory position
✓ Risk-averse to volatility
```

**3. Consider Waiting IF:**
```
✓ Time flexibility (>1 week)
✓ Model confidence is Low-Medium
✓ Bullish drivers (RINs, weather) strengthen
```

**4. Historical Context:**
```
Similar signals (2018 tariff + VIX spike):
  → 78% resulted in -2% to -5% moves
  → Avg time to bottom: 3-5 days
```

**5. Disclaimer (Required):**
```
⚠️ Not financial advice.
   Consult your risk management team.
```

### Data Contract:

```json
"procurement_insight": {
  "summary": "Price likely to decline 2-4% over 48-72h based on 400-feature model",
  
  "consider_locking_if": [
    "Already near procurement targets",
    "Low inventory position",
    "Risk-averse to volatility"
  ],
  
  "consider_waiting_if": [
    "Time flexibility (>1 week)",
    "Model confidence is Low-Medium",
    "Bullish drivers (RINs, weather) strengthen"
  ],
  
  "historical_context": {
    "similar_pattern": "2018 tariff + VIX spike",
    "success_rate": 0.78,
    "typical_move": "-2% to -5%",
    "avg_time_to_bottom_days": "3-5"
  },
  
  "disclaimer": "Not financial advice. Consult your risk management team."
}
```

### Copy Guidelines:

**✅ Approved Language:**
- "Price likely to decline" (not "will decline")
- "Consider locking IF..." (conditional)
- "Consider waiting IF..." (both sides)
- "Not financial advice. Consult risk management."
- "Based on 400-feature trained model"

**❌ Rejected Language:**
- "LOCK CONTRACTS NOW" (command)
- "You must lock" (imperative)
- "Guaranteed savings" (no guarantees)
- Any [LOCK NOW] or [BUY NOW] buttons
- Any language that sounds like financial advice

---

## 📋 MANDATORY FRONTEND CHECKLIST

Before deploying this UI, verify:

### Legal & Compliance:
- [ ] Disclaimer included on all cards: "Not financial advice"
- [ ] No action buttons ([LOCK NOW], [BUY NOW])
- [ ] No imperative commands ("must", "should", "lock")
- [ ] Conditional language only ("Consider IF...")

### Probability & Uncertainty:
- [ ] Probability stated ("72% chance of...")
- [ ] Range shown, not point estimate ("$50.50 - $51.80")
- [ ] Confidence level displayed ("Medium")
- [ ] Time horizon specified ("48-72 hours")

### Model Integration:
- [ ] Trump shown as 1 of 400+ features
- [ ] SHAP top 4 drivers visible
- [ ] Model confidence visible
- [ ] Net model output shown

### Both Sides:
- [ ] Bullish AND bearish scenarios
- [ ] "Consider locking IF..." present
- [ ] "Consider waiting IF..." present
- [ ] Historical context included

### Visual Clarity:
- [ ] 7-day trend sparkline
- [ ] Activity gauge (not "threat meter")
- [ ] Color coding (green/yellow/red, not red-only)
- [ ] SHAP bars for top drivers

---

## 🔧 COMPLETE API CONTRACT

### Endpoint:
```
GET /api/trump-zl-probability-analysis
```

### Response Schema:

```json
{
  "generated_at": "2025-11-21T14:30:00Z",
  "data_available": true,
  "data_source": "400-feature trained model + real-time Trump data",
  
  "trump_signal": {
    "activity_level": "HIGH",
    "activity_score": 0.75,
    "signal_type": "tariff_rhetoric",
    "confidence": 0.85,
    "context_text": "This is 1 of 400+ features in the trained model",
    "trend_7d": [0.2, 0.3, 0.5, 0.7, 0.9],
    "trend_direction": "escalating",
    "triggers": ["High threat rhetoric", "Elevated posting frequency"]
  },
  
  "model_forecast": {
    "direction": "decline",
    "probability": 0.72,
    "range_min_pct": -4.0,
    "range_max_pct": -2.0,
    "time_horizon_hours": "48-72",
    "confidence_level": "medium",
    "confidence_score": 0.68,
    
    "price_forecast": {
      "current": 52.50,
      "baseline": 52.00,
      "expected_min": 50.50,
      "expected_max": 51.80
    },
    
    "shap_drivers": [
      {"feature": "RINs momentum", "impact_cents": 11.2, "direction": "bullish"},
      {"feature": "Trump tariff signal", "impact_cents": -3.1, "direction": "bearish"},
      {"feature": "Brazil weather", "impact_cents": 6.8, "direction": "bullish"},
      {"feature": "Crush margin", "impact_cents": 3.5, "direction": "bullish"}
    ],
    
    "net_output_pct": -2.8
  },
  
  "procurement_insight": {
    "summary": "Price likely to decline 2-4% over 48-72h based on 400-feature trained model",
    
    "consider_locking_if": [
      "Already near procurement targets",
      "Low inventory position",
      "Risk-averse to volatility"
    ],
    
    "consider_waiting_if": [
      "Time flexibility (>1 week)",
      "Model confidence is Low-Medium",
      "Bullish drivers (RINs, weather) strengthen"
    ],
    
    "historical_context": {
      "similar_pattern": "2018 tariff + VIX spike",
      "success_rate": 0.78,
      "typical_move": "-2% to -5%",
      "avg_time_to_bottom_days": "3-5"
    },
    
    "disclaimer": "Not financial advice. Consult your risk management team."
  }
}
```

---

## 📚 RELATED DOCUMENTATION

### Backend Implementation:
- `scripts/predictions/trump_action_predictor.py` - Trump signal detection
- `scripts/predictions/zl_impact_predictor.py` - ZL impact analysis
- `scripts/specialized/TRUMP_SENTIMENT_QUANT_ENGINE.py` - Sentiment scoring

### Audit Verification:
- `docs/migration/NON_SYMBOL_DATA_AUDIT_2025-11-21.md` - Confirms Trump scoring ✅ 100% implemented
- `docs/migration/QUAD_CHECK_PLAN_2025-11-21.md` - Section 10 (Dashboard Best Practices)

### Training Integration:
- Trump features feed into `features.master_features_all` (1 of 400+ features)
- Policy shock scoring: `policy_trump_score` via 5-component formula
- Training weights: regime-based + shock-based multipliers
- SHAP integration: Geopolitical group (Big 8 Pillar #2)

---

## ✅ APPROVAL STATUS

**Approved by:** Kirk (November 21, 2025)

**Key Decision:**
> "Be very careful when having alerts to lock contracts purely based on a trump tweet and not the overall trained data. Better yet, we need to have a softer approach... 'XX% probability that price will hit/rise/drop over the next XX period'."

**Implementation Status:**
- ✅ Design approved
- ✅ API contract defined
- ✅ Copy guidelines established
- ✅ Legal disclaimers required
- ⏳ Frontend implementation pending

---

**Next Steps:**
1. Frontend team implements 3-card Intelligence Strip
2. Backend team deploys `/api/trump-zl-probability-analysis` endpoint
3. QA verifies all checklist items before production
4. Legal team reviews disclaimer language
5. Deploy to Legislative page (below the fold)

