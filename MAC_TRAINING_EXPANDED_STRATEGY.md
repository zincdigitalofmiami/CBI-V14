# Mac Training Expanded Strategy - Full Dataset, Weighted, Advanced Features
**Date**: November 7, 2025  
**Purpose**: Comprehensive Mac-based training strategy leveraging full dataset, regime weighting, and all advanced features

---

## Strategic Shift: Mac Training Unlocks Everything

### Key Realizations

1. **No Cost Constraints**: Local Mac training = unlimited iterations, experiments, feature engineering
2. **No Column Limits**: Can use ALL 9,213+ features (not limited to 1,000 like Vertex AI)
3. **Full Historical Data**: Use ALL 125 years (16,824 rows) with regime weighting
4. **Advanced Features**: SHAP, Monte Carlo, what-if scenarios, ensemble models
5. **Multiple Specialized Models**: Like JPM/GS - different models for different regimes/focuses

---

## Architecture: Multi-Model Ensemble Approach (JPM/GS Style)

### Tier 1: Regime-Specialized Models

**Concept**: Train separate models optimized for different market regimes, then ensemble

| Model | Focus | Training Data | Weight | Architecture |
|-------|-------|--------------|--------|--------------|
| **Trump_2.0_Model** | Current regime | 2023-2025 (weighted 5,000) | Primary | LSTM + Attention |
| **Trade_War_Model** | Tariff impacts | 2017-2019 (weighted 1,500) | High | GRU + Policy features |
| **Crisis_Model** | Volatility spikes | 2008-2009, 2020 (weighted 500-800) | Medium | Deep Feedforward |
| **Inflation_Model** | Substitution effects | 2021-2022 (weighted 1,200) | High | LSTM + Cross-asset |
| **Historical_Model** | Long-term patterns | Pre-2000 (weighted 50) | Low | Feedforward |

**Ensemble Strategy**: Weighted average based on current regime detection

### Tier 2: Feature-Focused Models

**Concept**: Specialized models for different feature categories (like GS Quant signal packages)

| Model | Feature Focus | Purpose |
|-------|--------------|---------|
| **Neural_Signals_Model** | Big Eight signals, neural scores | Proprietary signal integration |
| **Policy_Model** | Trump sentiment, tariffs, trade | Policy-driven price movements |
| **Fundamentals_Model** | Crush margins, China imports, USDA | Supply/demand fundamentals |
| **Technical_Model** | Price patterns, momentum, volatility | Technical analysis signals |
| **Cross_Asset_Model** | Palm oil, crude, FX, correlations | Cross-asset relationships |

**Ensemble Strategy**: Stacking or weighted voting based on feature importance

### Tier 3: Horizon-Specialized Models

**Concept**: Different architectures optimized for different forecast horizons

| Horizon | Architecture | Rationale |
|---------|-------------|-----------|
| **1M (22 days)** | LSTM with 30-day lookback | Short-term patterns, momentum |
| **3M (66 days)** | GRU with 90-day lookback | Medium-term trends |
| **6M (132 days)** | Deep Feedforward | Long-term fundamentals |
| **12M (264 days)** | Transformer (optional) | Very long-term structural changes |

---

## Full Dataset Strategy: 125 Years with Regime Weighting

### Data Architecture

**Master Training Table**:
- **Rows**: 16,824 (1900-2025, daily)
- **Features**: 9,213+ (all available, no limits)
- **Regime Weights**: 50-5,000 (per REGIME_BASED_TRAINING_STRATEGY.md)
- **Targets**: 4 horizons (1M, 3M, 6M, 12M)

**Regime Weight Implementation (Mac Training)**:

Since TensorFlow/Keras doesn't have built-in `weight_column` like Vertex AI, we use:

1. **Sample Weighting** (Keras `sample_weight` parameter):
```python
# Calculate sample weights from regime weights
sample_weights = training_data['training_weight'] / training_data['training_weight'].max()
# Normalize to 0-1 range for Keras
```

2. **Weighted Loss Function**:
```python
def weighted_mse_loss(weights):
    def loss(y_true, y_pred):
        return tf.reduce_mean(weights * tf.square(y_true - y_pred))
    return loss
```

3. **Stratified Sampling** (alternative):
```python
# Oversample high-weight regimes during training
# Use imbalanced-learn or custom sampler
```

### Effective Training Distribution

With regime weighting, effective training distribution:

```
Trump 2.0:     700 rows × 5,000 weight = 3,500,000 effective samples
Trade War:     700 rows × 1,500 weight = 1,050,000 effective samples
Inflation:     500 rows × 1,200 weight =   600,000 effective samples
COVID:         500 rows ×   800 weight =   400,000 effective samples
Financial:     500 rows ×   500 weight =   250,000 effective samples
Commodity:     700 rows ×   400 weight =   280,000 effective samples
QE:            1,000 rows × 300 weight =   300,000 effective samples
Pre-Crisis:    1,500 rows × 100 weight =   150,000 effective samples
Historical:    12,224 rows × 50 weight =   611,200 effective samples
                                        -------------------------
                                Total:  7,141,200 weighted samples
```

**Result**: Trump 2.0 represents ~49% of effective training weight despite being 4% of rows!

---

## Feature Engineering: Exhaust All 9,213+ Features

### Feature Categories (Expanded)

1. **Price & Technicals** (~1,500 features)
   - All 224 Yahoo Finance symbols × 7 indicators = 1,568 features
   - Technical indicators: RSI, MACD, Bollinger, ATR, ADX, Stochastic
   - Moving averages: 7, 14, 30, 60, 90, 180, 365 day windows
   - Momentum: ROC, momentum, rate of change
   - Volatility: Historical volatility, realized volatility, GARCH

2. **Cross-Asset Correlations** (~500 features)
   - Palm oil, crude oil, corn, wheat, soybean meal
   - FX pairs: DXY, EUR/USD, BRL/USD, CNY/USD, ARS/USD
   - Correlation windows: 7d, 14d, 30d, 60d, 90d, 180d, 365d
   - Rolling correlations, dynamic correlations
   - Cointegration tests, Granger causality

3. **Economic Indicators** (~200 features)
   - Fed funds rate, employment, inflation expectations
   - Credit spreads, term spreads, yield curves (2Y, 5Y, 10Y, 30Y)
   - GDP, PMI, consumer confidence, retail sales
   - Leading indicators, coincident indicators
   - Economic surprise indices

4. **Commodity Fundamentals** (~300 features)
   - USDA WASDE: stocks, production, exports, imports
   - China imports (US, Brazil, Argentina)
   - Brazil/Argentina exports, harvest progress
   - Crush margins, processing capacity, utilization
   - Basis spreads, regional premiums

5. **Geopolitical/Policy** (~400 features)
   - Trump sentiment scores (8 different metrics)
   - Policy impact scores, executive orders
   - Tariff rates, trade war intensity
   - China relations, cancellation flags
   - ICE enforcement, labor policy
   - RFS mandates, biofuel policy

6. **Market Structure** (~200 features)
   - CFTC positioning (all categories)
   - Open interest, volume, liquidity
   - VIX levels, stress indicators
   - Social sentiment, news sentiment
   - Options flow, implied volatility

7. **Weather/Logistics** (~150 features)
   - Brazil/Argentina precipitation, temperature
   - US Midwest weather
   - Harvest pace, export capacity
   - Freight rates, port logistics
   - El Niño/La Niña indicators

8. **Biofuel Markets** (~100 features)
   - RIN prices (D4, D5, D6, D7)
   - RFS mandates, biodiesel/ethanol prices
   - Blending economics, margins
   - Policy changes, credit programs

9. **Interaction Terms** (~2,000 features)
   - VIX × Trump sentiment
   - China imports × tariff rates
   - RIN prices × crush margins
   - Cross-feature multiplications (top 100 features × top 20 features)
   - Regime-specific interactions

10. **Lagged Features** (~3,000 features)
    - Lag 1, 3, 7, 14, 30, 60, 90, 180, 365 days
    - Rolling statistics: mean, std, min, max, median
    - Percentile ranks, z-scores
    - Change rates, accelerations

11. **Neural/Proprietary Signals** (~50 features)
    - Big Eight neural signals
    - Dollar neural score, Fed neural score, Crush neural score
    - Composite scores, regime indicators

12. **Time-Based Features** (~100 features)
    - Day of week, month, quarter, year
    - Holiday indicators, seasonality
    - Time since major events
    - Cyclical patterns

**Total**: ~9,500 features (all available, no limits!)

---

## Model Architectures: Advanced Deep Learning

### Architecture 1: LSTM with Attention (1M Horizon)

**Purpose**: Short-term patterns with attention to key drivers

```python
model = Sequential([
    Input(shape=(sequence_length, n_features)),
    LSTM(256, return_sequences=True),
    LSTM(128, return_sequences=True),
    Attention(),  # Focus on important time steps
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(1)  # target_1m
])
```

**Features**: 
- 30-day lookback window
- Attention mechanism highlights important time steps
- Dropout for regularization
- Optimized for 1M horizon

### Architecture 2: GRU with Policy Gates (Trade War Focus)

**Purpose**: Policy-driven price movements

```python
model = Sequential([
    Input(shape=(sequence_length, n_features)),
    GRU(256, return_sequences=True),
    PolicyGate(),  # Custom layer that gates based on policy features
    GRU(128),
    Dense(64, activation='relu'),
    Dense(1)  # target_1m
])
```

**Features**:
- GRU for efficiency
- Policy gates: amplify policy features during policy events
- Optimized for tariff/trade war periods

### Architecture 3: Deep Feedforward with Feature Selection (6M/12M)

**Purpose**: Long-term fundamentals

```python
model = Sequential([
    Input(shape=(n_features,)),
    Dense(512, activation='relu'),
    BatchNormalization(),
    Dropout(0.4),
    Dense(256, activation='relu'),
    BatchNormalization(),
    Dropout(0.3),
    Dense(128, activation='relu'),
    Dropout(0.2),
    Dense(64, activation='relu'),
    Dense(1)  # target_6m or target_12m
])
```

**Features**:
- Deep network for complex interactions
- Batch normalization for stability
- Feature selection layer (top 1,000 features)
- Optimized for long-term forecasts

### Architecture 4: Transformer (Optional, 12M Horizon)

**Purpose**: Very long-term structural changes

```python
# Multi-head attention for long-range dependencies
transformer = TransformerEncoder(
    num_layers=4,
    d_model=256,
    num_heads=8,
    dff=1024
)
```

**Features**:
- Self-attention for long-range dependencies
- Positional encoding for time series
- Optimized for 12M horizon

---

## Training Strategy: Regime-Weighted with Advanced Techniques

### Training Configuration

```python
# Regime-weighted training
sample_weights = calculate_regime_weights(training_data)

# Model compilation
model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss=weighted_mse_loss(sample_weights),
    metrics=['mae', 'mape']
)

# Callbacks
callbacks = [
    EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True),
    ModelCheckpoint('best_model.h5', save_best_only=True),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10),
    TensorBoard(log_dir='./logs')
]

# Training with sample weights
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    sample_weight=sample_weights_train,  # <-- REGIME WEIGHTING
    epochs=200,
    batch_size=64,
    callbacks=callbacks
)
```

### Advanced Training Techniques

1. **Curriculum Learning**: Start with recent data, gradually add historical
2. **Mixup Augmentation**: Synthetic data generation for small regimes
3. **Focal Loss**: Focus on hard-to-predict samples
4. **Multi-Task Learning**: Predict multiple horizons simultaneously
5. **Transfer Learning**: Pre-train on historical data, fine-tune on Trump era

---

## Ensemble Strategy: Multiple Models, Multiple Focuses

### Ensemble Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INPUT FEATURES                        │
│              (9,500 features, 16,824 rows)               │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Regime       │ │ Feature     │ │ Horizon    │
│ Specialized  │ │ Focused     │ │ Specialized│
│ Models       │ │ Models      │ │ Models     │
│              │ │             │ │            │
│ • Trump 2.0  │ │ • Neural    │ │ • 1M LSTM  │
│ • Trade War  │ │ • Policy    │ │ • 3M GRU   │
│ • Crisis     │ │ • Fund      │ │ • 6M FF    │
│ • Inflation  │ │ • Technical │ │ • 12M TF   │
│ • Historical │ │ • Cross-Ass │ │            │
└───────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
            ┌───────────▼───────────┐
            │   ENSEMBLE LAYER      │
            │  (Weighted Average)  │
            │  or Stacking Model   │
            └───────────┬───────────┘
                        │
            ┌───────────▼───────────┐
            │   FINAL PREDICTIONS   │
            │  (P10, P50, P90)     │
            └───────────────────────┘
```

### Ensemble Methods

1. **Weighted Average**: 
   - Weight by validation performance
   - Weight by regime match (use Trump model more in Trump era)

2. **Stacking**:
   - Train meta-model on base model predictions
   - Learns optimal combination

3. **Dynamic Weighting**:
   - Adjust weights based on current regime
   - Use regime detection to select best models

---

## Advanced Features: SHAP, Monte Carlo, What-If

### SHAP Explainability

```python
# Global feature importance
explainer = shap.DeepExplainer(model, background_data)
shap_values = explainer.shap_values(test_data)

# Per-forecast explanations
for i, forecast in enumerate(predictions):
    shap.waterfall_plot(shap_values[i], feature_names)
```

**Output**: 
- Global: Top 20 features driving model
- Local: Per-forecast feature contributions
- Interaction: Feature interaction effects

### Monte Carlo Uncertainty

```python
# Monte Carlo dropout for prediction intervals
def monte_carlo_predict(model, X, n_samples=1000):
    predictions = []
    for _ in range(n_samples):
        pred = model(X, training=True)  # Enable dropout
        predictions.append(pred)
    
    # Calculate percentiles
    p10 = np.percentile(predictions, 10, axis=0)
    p50 = np.percentile(predictions, 50, axis=0)
    p90 = np.percentile(predictions, 90, axis=0)
    
    return p10, p50, p90
```

**Output**: P10/P50/P90 prediction intervals for risk management

### What-If Scenario Engine

```python
# Real-time scenario testing
def what_if_scenario(baseline_features, overrides):
    scenario_features = baseline_features.copy()
    scenario_features.update(overrides)
    
    # Re-predict with scenario
    scenario_pred = model.predict(scenario_features)
    baseline_pred = model.predict(baseline_features)
    
    return {
        'baseline': baseline_pred,
        'scenario': scenario_pred,
        'delta': scenario_pred - baseline_pred,
        'delta_pct': (scenario_pred - baseline_pred) / baseline_pred * 100
    }
```

**Use Cases**:
- "What if tariffs increase to 25%?"
- "What if VIX spikes to 40?"
- "What if China cancels 1M tons?"

---

## Implementation Plan

### Phase 1: Data Preparation (Week 1)

1. **Create Master Training Table**
   - Consolidate ALL 9,500+ features
   - Add regime weights (50-5,000)
   - Add regime labels
   - Create 4 target columns (1M, 3M, 6M, 12M)

2. **Feature Engineering**
   - Generate all interaction terms
   - Create all lag features
   - Calculate rolling statistics
   - Normalize/standardize features

3. **Data Validation**
   - Check for NULLs, duplicates
   - Validate regime weights
   - Verify target calculations

### Phase 2: Model Development (Week 2-3)

1. **Build Base Models**
   - LSTM for 1M horizon
   - GRU for 3M horizon
   - Feedforward for 6M/12M horizons

2. **Implement Regime Weighting**
   - Sample weight calculation
   - Weighted loss function
   - Validation on weighted data

3. **Train Specialized Models**
   - Trump 2.0 model
   - Trade War model
   - Crisis model
   - Feature-focused models

### Phase 3: Ensemble & Advanced Features (Week 4)

1. **Build Ensemble**
   - Weighted average ensemble
   - Stacking meta-model
   - Dynamic weighting

2. **Implement Advanced Features**
   - SHAP explainability
   - Monte Carlo uncertainty
   - What-if scenario engine

3. **Validation & Testing**
   - Out-of-sample testing
   - Regime-specific validation
   - Performance metrics

### Phase 4: Deployment (Week 5)

1. **Model Export**
   - SavedModel format
   - Version control
   - Metadata tracking

2. **Integration**
   - Dashboard integration
   - Prediction pipeline
   - Monitoring setup

---

## Success Metrics

### Model Performance
- **1M Horizon**: MAPE <2%, R² >0.90
- **3M Horizon**: MAPE <4%, R² >0.85
- **6M Horizon**: MAPE <6%, R² >0.75
- **12M Horizon**: MAPE <10%, R² >0.65

### Regime-Specific Performance
- **Trump 2.0 Era**: MAPE <2% (primary focus)
- **Trade War Era**: MAPE <3% (validation)
- **Other Regimes**: MAPE <8% (acceptable)

### Advanced Features
- **SHAP**: Feature importance rankings
- **Monte Carlo**: P10/P90 intervals with 80% coverage
- **What-If**: <2 second response time

---

## Key Advantages of Mac Training

1. **No Cost Constraints**: Unlimited training iterations
2. **No Column Limits**: Use all 9,500+ features
3. **Full Historical Data**: 125 years with intelligent weighting
4. **Advanced Architectures**: LSTM, GRU, Transformers, Attention
5. **Multiple Models**: Specialized models for different focuses
6. **Ensemble**: Combine multiple models for robustness
7. **Advanced Features**: SHAP, Monte Carlo, what-if scenarios
8. **Rapid Iteration**: Test ideas quickly, no cloud costs

---

## Next Steps

1. **Verify Mac Environment**: Test GPU acceleration
2. **Create Master Training Table**: All features, all history, regime weights
3. **Build First Model**: LSTM for 1M horizon with regime weighting
4. **Iterate**: Add specialized models, ensemble, advanced features
5. **Deploy**: Integrate with dashboard, prediction pipeline

**This is the institutional-grade approach - no compromises, no limits, full power of Mac training!**

