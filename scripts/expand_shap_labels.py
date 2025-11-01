#!/usr/bin/env python3
"""
Expand shap_business_labels.json to include all 205 training features + 4 1W signals.
Generates business labels based on naming patterns.
"""

import json
import re

# Load existing labels (keep user-provided examples)
with open('config/shap_business_labels.json', 'r') as f:
    config = json.load(f)

# Read all feature names
with open('/tmp/feature_names.txt', 'r') as f:
    all_features = [line.strip() for line in f if line.strip()]

# User-provided examples (keep these as-is)
user_provided = {
    'f_usd_brl_7d_avg', 'f_usd_ars_7d_avg', 'f_china_imports_30d', 'f_brazil_crush_margin',
    'f_us_crush_margin', 'f_biofuel_mandate_score', 'f_weather_anomaly_br', 'f_weather_anomaly_us',
    'f_shipping_cost_br', 'f_soymeal_spread', 'f_palm_oil_spread', 'f_sentiment_aggr',
    'f_inventory_ratio_us', 'f_corn_competition_index', 'f_energy_crude_corr', 'f_legislation_event_score',
    'f_tourism_index_vegas'
}

# Feature name mapping (some user examples use 'f_' prefix, actual features may not)
feature_mapping = {
    'usd_brl_7d_avg': 'usd_brl_7d_change',  # Map user example to actual feature
    'usd_ars_7d_avg': 'fx_usd_ars_30d_z',
    'china_imports_30d': 'cn_imports',
    'brazil_crush_margin': 'crush_margin',
    'us_crush_margin': 'crush_margin',
    'biofuel_mandate_score': 'feature_biofuel_ethanol',
    'weather_anomaly_br': 'weather_brazil_temp',
    'weather_anomaly_us': 'weather_us_temp',
    'shipping_cost_br': 'export_capacity_index',
    'soymeal_spread': 'meal_price_per_ton',
    'palm_oil_spread': 'palm_price',
    'sentiment_aggr': 'avg_sentiment',
    'inventory_ratio_us': 'supply_demand_ratio',
    'corn_competition_index': 'corn_soy_ratio_lag1',
    'energy_crude_corr': 'corr_zl_crude_30d',
    'legislation_event_score': 'feature_geopolitical_volatility',
    'tourism_index_vegas': 'import_demand_index'
}

def generate_business_label(feature_name):
    """Generate business-friendly label from technical feature name."""
    # Handle special cases first
    if feature_name.startswith('feature_'):
        name = feature_name.replace('feature_', '').replace('_', ' ').title()
        return name + " Index"
    
    # Split by underscores and capitalize
    parts = feature_name.split('_')
    
    # Common patterns
    if parts[0] == 'cn':
        return 'China Imports'
    if parts[0] == 'br':
        return 'Brazil ' + ' '.join(parts[1:]).replace('_', ' ').title()
    if 'argentina' in feature_name:
        return 'Argentina ' + ' '.join(parts[1:]).replace('_', ' ').title()
    if 'china' in feature_name:
        return 'China ' + ' '.join([p for p in parts if p != 'china']).replace('_', ' ').title()
    if 'brazil' in feature_name:
        return 'Brazil ' + ' '.join([p for p in parts if p != 'brazil']).replace('_', ' ').title()
    if parts[0] == 'usd' and 'brl' in feature_name:
        return 'USD/BRL Exchange Rate' + (' (7-Day Change)' if '7d' in feature_name else '')
    if parts[0] == 'usd' and 'cny' in feature_name:
        return 'USD/CNY Exchange Rate' + (' (7-Day Change)' if '7d' in feature_name else '')
    if parts[0] == 'fx' and 'ars' in feature_name:
        return 'USD/ARS Exchange Rate (30-Day Z-Score)'
    if parts[0] == 'fx' and 'myr' in feature_name:
        return 'USD/MYR Exchange Rate (30-Day Z-Score)'
    if 'crude' in feature_name or 'wti' in feature_name:
        return 'Crude Oil (WTI) ' + ' '.join([p for p in parts if p not in ['crude', 'oil', 'wti']]).replace('_', ' ').title()
    if 'corn' in feature_name:
        return 'Corn ' + ' '.join([p for p in parts if p != 'corn']).replace('_', ' ').title()
    if 'palm' in feature_name:
        return 'Palm Oil ' + ' '.join([p for p in parts if p != 'palm']).replace('_', ' ').title()
    if 'wheat' in feature_name:
        return 'Wheat ' + ' '.join([p for p in parts if p != 'wheat']).replace('_', ' ').title()
    if 'vix' in feature_name:
        return 'VIX ' + ' '.join([p for p in parts if p != 'vix']).replace('_', ' ').title()
    if 'dxy' in feature_name or 'dollar' in feature_name:
        return 'Dollar Index (DXY) ' + ' '.join([p for p in parts if p not in ['dxy', 'dollar', 'index']]).replace('_', ' ').title()
    if 'cftc' in feature_name:
        return 'CFTC ' + ' '.join(parts[1:]).replace('_', ' ').title()
    if 'corr' in feature_name:
        # Extract correlation pair
        if 'zl_corn' in feature_name:
            pair = 'Soybean Oil vs Corn'
        elif 'zl_crude' in feature_name:
            pair = 'Soybean Oil vs Crude Oil'
        elif 'zl_palm' in feature_name:
            pair = 'Soybean Oil vs Palm Oil'
        elif 'zl_vix' in feature_name:
            pair = 'Soybean Oil vs VIX'
        elif 'zl_dxy' in feature_name:
            pair = 'Soybean Oil vs Dollar Index'
        elif 'zl_wheat' in feature_name:
            pair = 'Soybean Oil vs Wheat'
        else:
            pair = ' vs '.join([p.upper() for p in parts if p != 'corr'])
        
        # Extract time window
        time_windows = {'7d': '7-Day', '30d': '30-Day', '90d': '90-Day', '180d': '180-Day', '365d': '365-Day'}
        window = next((time_windows[tw] for tw in time_windows if tw in feature_name), '')
        
        return f'{pair} Correlation ({window})' if window else f'{pair} Correlation'
    
    if 'zl_price' in feature_name:
        return 'Soybean Oil Price' + (' (Current)' if 'current' in feature_name else ' (Lag ' + feature_name.split('lag')[-1] + ')' if 'lag' in feature_name else '')
    if 'zl_volume' in feature_name:
        return 'Soybean Oil Volume'
    
    if 'weather' in feature_name:
        region = 'Brazil' if 'brazil' in feature_name else 'Argentina' if 'argentina' in feature_name else 'U.S.'
        metric = 'Temperature' if 'temp' in feature_name else 'Precipitation'
        return f'{region} Weather {metric}'
    
    if 'sentiment' in feature_name:
        return 'Market Sentiment ' + ' '.join([p for p in parts if p != 'sentiment']).replace('_', ' ').title()
    
    if 'crush_margin' in feature_name:
        return 'Crush Margin' + (' (7-Day MA)' if '7d' in feature_name else ' (30-Day MA)' if '30d' in feature_name else '')
    
    if 'trump' in feature_name or 'xi' in feature_name:
        return 'Geopolitical Signal ' + ' '.join(parts).replace('_', ' ').title()
    
    if 'tariff' in feature_name:
        return 'Tariff Impact ' + ' '.join([p for p in parts if p != 'tariff']).replace('_', ' ').title()
    
    if 'import' in feature_name or 'export' in feature_name:
        return ' '.join(parts).replace('_', ' ').title()
    
    # Default: capitalize and add spaces
    return ' '.join(parts).replace('_', ' ').title()

def generate_interpretation(feature_name, label):
    """Generate interpretation based on feature type."""
    lower_name = feature_name.lower()
    
    # Price-related
    if 'price' in lower_name or 'crude' in lower_name or 'corn' in lower_name or 'palm' in lower_name:
        if 'lag' in lower_name or 'lead' in lower_name:
            return "Historical price reference → trend continuation or reversal signal"
        return "Rising price → demand pressure → bullish"
    
    # Correlation
    if 'corr' in lower_name:
        return "Strong correlation → synchronized movement → trend confirmation"
    
    # FX rates
    if 'usd' in lower_name or 'fx' in lower_name or 'brl' in lower_name or 'cny' in lower_name or 'ars' in lower_name:
        if 'brl' in lower_name or 'ars' in lower_name:
            return "Currency weakness → lower export cost → bearish signal"
        return "FX rate movement → export competitiveness → price impact"
    
    # China
    if 'china' in lower_name or 'cn_' in lower_name:
        if 'import' in lower_name:
            return "Higher imports → stronger demand → bullish"
        if 'sentiment' in lower_name:
            return "Positive sentiment → demand confidence → bullish"
        return "China market signal → demand driver → price impact"
    
    # Weather
    if 'weather' in lower_name or 'temp' in lower_name or 'precip' in lower_name:
        return "Weather stress → yield risk → supply pressure → bullish"
    
    # Sentiment
    if 'sentiment' in lower_name:
        return "Positive sentiment → market confidence → bullish"
    
    # Volatility
    if 'vix' in lower_name or 'volatility' in lower_name:
        return "High volatility → risk premium → price uncertainty"
    
    # Crush margin
    if 'crush' in lower_name:
        return "Rising margins → stronger processing demand → bullish"
    
    # CFTC
    if 'cftc' in lower_name:
        if 'long' in lower_name:
            return "Commercial longs → bullish positioning → upward pressure"
        if 'short' in lower_name:
            return "Commercial shorts → bearish positioning → downward pressure"
        return "Futures positioning → price direction signal"
    
    # Features
    if 'feature_' in lower_name:
        return "Composite signal → market condition indicator → directional bias"
    
    # Default
    return "Signal change → market condition shift → price impact"

def get_category(feature_name):
    """Assign category based on feature type."""
    lower_name = feature_name.lower()
    
    if 'usd' in lower_name or 'fx' in lower_name or 'brl' in lower_name or 'cny' in lower_name or 'ars' in lower_name or 'dxy' in lower_name:
        return 'FX'
    if 'china' in lower_name or 'cn_' in lower_name:
        return 'Demand'
    if 'weather' in lower_name or 'temp' in lower_name or 'precip' in lower_name or 'yield' in lower_name:
        return 'Weather'
    if 'crush' in lower_name or 'meal' in lower_name or 'processing' in lower_name:
        return 'Processing'
    if 'biofuel' in lower_name or 'mandate' in lower_name or 'policy' in lower_name or 'legislation' in lower_name:
        return 'Policy'
    if 'corr' in lower_name:
        return 'Correlation'
    if 'sentiment' in lower_name or 'mentions' in lower_name or 'posts' in lower_name:
        return 'Sentiment'
    if 'import' in lower_name or 'export' in lower_name or 'supply' in lower_name or 'demand' in lower_name:
        return 'Supply'
    if 'palm' in lower_name or 'substitution' in lower_name:
        return 'Substitution'
    if 'vix' in lower_name or 'volatility' in lower_name:
        return 'Volatility'
    if 'crude' in lower_name or 'energy' in lower_name or 'wti' in lower_name:
        return 'Energy'
    if 'tariff' in lower_name or 'trade' in lower_name or 'trump' in lower_name:
        return 'Policy'
    if 'cftc' in lower_name:
        return 'Positioning'
    if 'price' in lower_name or 'lag' in lower_name or 'lead' in lower_name:
        return 'Price'
    
    return 'Other'

# Build complete feature dictionary
features_dict = {}
features_dict.update(config['features'])  # Keep existing user-provided ones

# Add all training features
for feature_name in all_features:
    # Skip if already exists (user-provided or mapped)
    if feature_name in features_dict:
        continue
    
    # Map user examples to actual features if needed
    mapped_feature = feature_mapping.get(feature_name, feature_name)
    if mapped_feature in features_dict:
        continue
    
    # Generate label and interpretation
    label = generate_business_label(feature_name)
    interpretation = generate_interpretation(feature_name, label)
    category = get_category(feature_name)
    
    features_dict[feature_name] = {
        "business_label": label,
        "interpretation": interpretation,
        "category": category
    }

# Add 1W signals (already in config, but ensure they're there)
features_dict['volatility_score_1w'] = config['features'].get('volatility_score_1w', {
    "business_label": "1W Volatility Score",
    "interpretation": "Short-term volatility indicator for gate blend",
    "category": "Volatility"
})

features_dict['delta_1w_vs_spot'] = config['features'].get('delta_1w_vs_spot', {
    "business_label": "1W Forecast Delta vs Spot",
    "interpretation": "Difference between 1W forecast and current spot price",
    "category": "Volatility"
})

features_dict['momentum_1w_7d'] = config['features'].get('momentum_1w_7d', {
    "business_label": "7-Day Price Momentum",
    "interpretation": "Recent price momentum trend (7-day)",
    "category": "Momentum"
})

features_dict['short_bias_score_1w'] = config['features'].get('short_bias_score_1w', {
    "business_label": "Short-Term Bias Score",
    "interpretation": "Short-term market bias indicator",
    "category": "Momentum"
})

# Update config
config['features'] = features_dict
config['total_features'] = len(features_dict)
config['last_updated'] = "2025-01-XX (Auto-expanded to all 209 features)"

# Write updated config
with open('config/shap_business_labels.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"✅ Expanded shap_business_labels.json to {len(features_dict)} features")
print(f"   - Training features: {len(all_features)}")
print(f"   - 1W signals: 4")
print(f"   - Total: {len(features_dict)}")

