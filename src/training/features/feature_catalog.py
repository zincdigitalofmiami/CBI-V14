#!/usr/bin/env python3
"""
Comprehensive feature catalog for CBI-V14 training.
Maps all 444 columns to categories for intelligent feature selection.
"""

from typing import List, Dict, Set
from pathlib import Path

class FeatureCatalog:
    """Maps all 444 features to categories for model-specific selection."""
    
    # Core identifiers and targets (excluded from features)
    EXCLUDED = {'date', 'target_1w', 'target_1m', 'target_3m', 'target_6m', 'zl_price_current'}
    
    # Intelligence features (38+ features)
    INTELLIGENCE = {
        'china_mentions', 'china_posts', 'import_posts', 'soy_posts',
        'china_sentiment', 'china_sentiment_volatility', 'china_policy_impact',
        'import_demand_index', 'china_posts_7d_ma', 'china_sentiment_30d_ma',
        'trump_mentions', 'trumpxi_china_mentions', 'trump_xi_co_mentions',
        'xi_mentions', 'tariff_mentions', 'co_mention_sentiment',
        'trumpxi_sentiment_volatility', 'trumpxi_policy_impact', 'max_policy_impact',
        'tension_index', 'volatility_multiplier', 'co_mentions_7d_ma',
        'trumpxi_volatility_30d_ma', 'china_tariff_rate', 'trade_war_intensity',
        'trade_war_impact_score', 'trump_soybean_sentiment_7d',
        'trump_agricultural_impact_30d', 'trump_soybean_relevance_30d',
        'days_since_trump_policy', 'trump_policy_intensity_14d',
        'social_sentiment_momentum_7d', 'social_sentiment_avg',
        'social_sentiment_volatility', 'social_post_count', 'bullish_ratio',
        'bearish_ratio', 'social_sentiment_7d', 'social_volume_7d',
        'trump_policy_events', 'trump_policy_impact_avg', 'trump_policy_impact_max',
        'trade_policy_events', 'china_policy_events', 'ag_policy_events',
        'trump_policy_7d', 'trump_events_7d', 'china_news_count',
        'biofuel_news_count', 'tariff_news_count', 'weather_news_count',
        'news_intelligence_7d', 'news_volume_7d', 'news_sentiment_avg',
        'avg_sentiment', 'sentiment_volatility', 'sentiment_volume'
    }
    
    # Signal features (Big 8 and derived signals)
    SIGNALS = {
        'feature_vix_stress', 'feature_harvest_pace', 'feature_china_relations',
        'feature_tariff_threat', 'feature_geopolitical_volatility',
        'feature_biofuel_cascade', 'feature_hidden_correlation',
        'feature_biofuel_ethanol', 'big8_composite_score'
    }
    
    # Technical indicators
    TECHNICAL = {
        'rsi_proxy', 'rsi_14', 'bb_width', 'bb_upper', 'bb_middle', 'bb_lower',
        'bb_percent', 'price_ma_ratio', 'momentum_30d', 'macd_proxy',
        'macd_line', 'macd_signal', 'macd_histogram', 'atr_14',
        'historical_volatility_30d', 'volatility_30d', 'volatility_90d',
        'price_momentum_1w', 'price_momentum_1m', 'price_momentum_7d',
        'price_momentum_30d', 'price_vs_ma30', 'price_vs_ma200',
        'ma50_vs_ma200', 'is_golden_cross', 'volume_sma_ratio',
        'momentum_divergence', 'lead_signal_confidence',
        'palm_accuracy_30d', 'crude_accuracy_30d', 'volatility_regime',
        'is_low_vol', 'is_normal_vol', 'is_high_vol'
    }
    
    # Economic indicators
    ECONOMIC = {
        'cftc_commercial_long', 'cftc_commercial_short', 'cftc_commercial_net',
        'cftc_managed_long', 'cftc_managed_short', 'cftc_managed_net',
        'cftc_open_interest', 'cftc_commercial_extreme', 'cftc_spec_extreme',
        'treasury_10y_yield', 'econ_gdp_growth', 'econ_inflation_rate',
        'econ_unemployment_rate', 'fed_funds_rate', 'real_yield', 'yield_curve',
        'br_yield', 'gdp_growth', 'unemployment_rate', 'cpi_yoy',
        'economic_stress_index'
    }
    
    # Commodity prices
    COMMODITY_PRICES = {
        'corn_price', 'wheat_price', 'oil_price_per_cwt', 'bean_price_per_bushel',
        'meal_price_per_ton', 'crush_margin', 'crush_margin_7d_ma',
        'crush_margin_30d_ma', 'palm_price', 'crude_price', 'soybean_meal_price',
        'heating_oil_price', 'natural_gas_price', 'gasoline_price', 'sugar_price',
        'biodiesel_spread', 'ethanol_spread', 'biofuel_crack',
        'clean_energy_momentum_30d', 'clean_energy_momentum_7d', 'nat_gas_impact',
        'sugar_ethanol_spread', 'biodiesel_margin', 'ethanol_margin',
        'oil_to_gas_ratio', 'soy_to_corn_ratio', 'biodiesel_spread_ma30',
        'ethanol_spread_ma30', 'biodiesel_spread_vol', 'ethanol_spread_vol',
        'soyb_close', 'soyb_ma_7d', 'soyb_ma_30d', 'soyb_ma_200d',
        'soyb_rsi_14', 'soyb_macd_line', 'soyb_bb_upper', 'soyb_bb_width',
        'soyb_atr_14', 'soyb_momentum_10', 'corn_etf_close', 'corn_etf_ma_7d',
        'corn_etf_ma_30d', 'corn_etf_ma_200d', 'corn_etf_rsi_14',
        'corn_etf_macd_line', 'corn_etf_bb_upper', 'corn_etf_bb_width',
        'corn_etf_atr_14', 'corn_etf_momentum_10', 'weat_close', 'weat_ma_7d',
        'weat_ma_30d', 'weat_ma_200d', 'weat_rsi_14', 'weat_macd_line',
        'weat_bb_upper', 'weat_bb_width', 'weat_atr_14', 'weat_momentum_10',
        'brent_close', 'brent_rsi_14', 'brent_macd_line', 'brent_ma_30d',
        'brent_ma_200d', 'copper_close', 'copper_rsi_14', 'copper_macd_line',
        'copper_ma_30d', 'copper_ma_200d', 'natgas_yahoo_close',
        'natgas_yahoo_rsi_14', 'natgas_yahoo_ma_30d', 'natgas_yahoo_momentum_10',
        'natgas_yahoo_roc_10'
    }
    
    # Currency/FX
    CURRENCY = {
        'usd_cny_rate', 'usd_brl_rate', 'dollar_index', 'usd_index',
        'usd_cny_7d_change', 'usd_brl_7d_change', 'dollar_index_7d_change',
        'usd_ars_rate', 'usd_myr_rate', 'fx_usd_ars_30d_z', 'fx_usd_myr_30d_z',
        'dxy_level', 'dxy_yahoo_close', 'dxy_yahoo_rsi_14', 'dxy_yahoo_macd_line',
        'dxy_yahoo_ma_30d', 'dxy_yahoo_ma_200d', 'brlusd_close', 'brlusd_rsi_14',
        'brlusd_ma_30d', 'brlusd_momentum_10', 'brlusd_roc_10', 'cnyusd_close',
        'cnyusd_rsi_14', 'cnyusd_ma_30d', 'cnyusd_momentum_10', 'cnyusd_roc_10',
        'mxnusd_close', 'mxnusd_rsi_14', 'mxnusd_ma_30d', 'mxnusd_momentum_10',
        'mxnusd_roc_10'
    }
    
    # Weather
    WEATHER = {
        'brazil_month', 'brazil_temperature_c', 'brazil_precipitation_mm',
        'growing_degree_days', 'brazil_precip_30d_ma', 'brazil_temp_7d_ma',
        'weather_brazil_temp', 'weather_brazil_precip', 'weather_argentina_temp',
        'weather_us_temp', 'brazil_temp_c', 'brazil_precip_mm',
        'brazil_conditions_score', 'brazil_heat_stress_days', 'brazil_drought_days',
        'brazil_flood_days', 'argentina_temp_c', 'argentina_precip_mm',
        'argentina_conditions_score', 'argentina_heat_stress_days',
        'argentina_drought_days', 'argentina_flood_days', 'us_midwest_temp_c',
        'us_midwest_precip_mm', 'us_midwest_conditions_score',
        'us_midwest_heat_stress_days', 'us_midwest_drought_days',
        'us_midwest_flood_days', 'global_weather_risk_score'
    }
    
    # RIN/RFS biofuel
    RIN_RFS = {
        'rin_d4_price', 'rin_d5_price', 'rin_d6_price',
        'rfs_mandate_biodiesel', 'rfs_mandate_advanced', 'rfs_mandate_total'
    }
    
    # Price lags and returns
    PRICE_LAGS = {
        'zl_price_lag1', 'zl_price_lag7', 'zl_price_lag30',
        'return_1d', 'return_7d', 'ma_7d', 'ma_30d', 'ma_50d', 'ma_90d',
        'ma_100d', 'ma_200d', 'palm_lag1', 'palm_lag2', 'palm_lag3',
        'palm_momentum_3d', 'crude_lag1', 'crude_lag2', 'crude_momentum_2d',
        'vix_lag1', 'vix_lag2', 'vix_spike_lag1', 'dxy_lag1', 'dxy_lag2',
        'dxy_momentum_3d', 'corn_lag1', 'wheat_lag1', 'corn_soy_ratio_lag1',
        'leadlag_zl_price'
    }
    
    # Correlations
    CORRELATIONS = {
        'palm_lead2_correlation', 'crude_lead1_correlation', 'vix_lead1_correlation',
        'dxy_lead1_correlation', 'palm_direction_correct', 'crude_direction_correct',
        'vix_inverse_correct', 'corr_zl_palm_7d', 'corr_zl_palm_30d',
        'corr_zl_palm_90d', 'corr_zl_palm_180d', 'corr_zl_palm_365d',
        'corr_zl_crude_7d', 'corr_zl_crude_30d', 'corr_zl_crude_90d',
        'corr_zl_crude_180d', 'corr_zl_crude_365d', 'corr_zl_vix_7d',
        'corr_zl_vix_30d', 'corr_zl_vix_90d', 'corr_zl_vix_180d',
        'corr_zl_vix_365d', 'corr_zl_dxy_7d', 'corr_zl_dxy_30d',
        'corr_zl_dxy_90d', 'corr_zl_dxy_180d', 'corr_zl_dxy_365d',
        'corr_zl_corn_7d', 'corr_zl_corn_30d', 'corr_zl_corn_90d',
        'corr_zl_corn_365d', 'corr_zl_wheat_7d', 'corr_zl_wheat_30d',
        'corr_palm_crude_30d', 'corr_corn_wheat_30d', 'corn_zl_correlation_30d',
        'wheat_zl_correlation_30d', 'crude_zl_correlation_30d',
        'usd_zl_correlation_30d'
    }
    
    # Event/calendar features
    EVENTS = {
        'is_wasde_day', 'is_fomc_day', 'is_china_holiday', 'is_crop_report_day',
        'is_stocks_day', 'is_planting_day', 'is_major_usda_day',
        'event_impact_level', 'days_to_next_event', 'days_since_last_event',
        'pre_event_window', 'post_event_window', 'event_vol_mult',
        'is_options_expiry', 'is_quarter_end', 'is_month_end'
    }
    
    # Trade/logistics
    TRADE_LOGISTICS = {
        'brazil_market_share', 'us_export_impact', 'tradewar_event_vol_mult',
        'export_seasonality_factor', 'export_capacity_index', 'harvest_pressure',
        'supply_demand_ratio', 'cn_imports', 'cn_imports_fixed',
        'argentina_export_tax', 'argentina_china_sales_mt',
        'argentina_competitive_threat', 'industrial_demand_index',
        'china_soybean_sales', 'china_weekly_cancellations_mt',
        'argentina_vessel_queue_count', 'argentina_port_throughput_teu',
        'baltic_dry_index', 'soybean_weekly_sales', 'soybean_oil_weekly_sales',
        'soybean_meal_weekly_sales'
    }
    
    # Seasonal/time features
    SEASONAL = {
        'seasonal_index', 'monthly_zscore', 'yoy_change', 'day_of_week',
        'month', 'quarter', 'day_of_week_num', 'day_of_month', 'month_num',
        'seasonal_sin', 'seasonal_cos', 'seasonal_month_factor', 'time_weight'
    }
    
    # Market indices and ETFs
    MARKET_INDICES = {
        'vix_index_new', 'crude_oil_wti_new', 'wti_7d_change', 'vix_level',
        'vix_yahoo_close', 'vix_yahoo_rsi_14', 'vix_yahoo_ma_30d',
        'vix_yahoo_macd_line', 'vix_yahoo_bb_upper', 'hyg_close',
        'hyg_rsi_14', 'hyg_ma_30d', 'hyg_macd_line', 'hyg_bb_width',
        'icln_price', 'tan_price', 'dba_price', 'vegi_price', 'rn'
    }
    
    # Company equity features
    EQUITY = {
        'adm_close', 'adm_pe_ratio', 'adm_beta', 'adm_analyst_target',
        'adm_market_cap', 'bg_close', 'bg_pe_ratio', 'bg_beta',
        'bg_analyst_target', 'bg_market_cap', 'ntr_close', 'ntr_pe_ratio',
        'ntr_beta', 'ntr_analyst_target', 'ntr_market_cap', 'dar_close',
        'dar_pe_ratio', 'dar_beta', 'dar_analyst_target', 'dar_market_cap',
        'tsn_close', 'tsn_pe_ratio', 'tsn_beta', 'tsn_analyst_target',
        'tsn_market_cap', 'cf_close', 'cf_pe_ratio', 'cf_beta',
        'cf_analyst_target', 'cf_market_cap', 'mos_close', 'mos_pe_ratio',
        'mos_beta', 'mos_analyst_target', 'mos_market_cap'
    }
    
    # Volume
    VOLUME = {
        'zl_volume', 'news_article_count', 'news_avg_score'
    }
    
    @classmethod
    def get_all_feature_groups(cls) -> Dict[str, Set[str]]:
        """Return all feature groups."""
        return {
            'intelligence': cls.INTELLIGENCE,
            'signals': cls.SIGNALS,
            'technical': cls.TECHNICAL,
            'economic': cls.ECONOMIC,
            'commodity_prices': cls.COMMODITY_PRICES,
            'currency': cls.CURRENCY,
            'weather': cls.WEATHER,
            'rin_rfs': cls.RIN_RFS,
            'price_lags': cls.PRICE_LAGS,
            'correlations': cls.CORRELATIONS,
            'events': cls.EVENTS,
            'trade_logistics': cls.TRADE_LOGISTICS,
            'seasonal': cls.SEASONAL,
            'market_indices': cls.MARKET_INDICES,
            'equity': cls.EQUITY,
            'volume': cls.VOLUME
        }
    
    @classmethod
    def get_features_for_model(cls, model_type: str, include_groups: List[str] = None) -> List[str]:
        """
        Get feature list for specific model type.
        
        Args:
            model_type: 'tree', 'neural', 'all'
            include_groups: List of feature groups to include. If None, includes all.
        
        Returns:
            List of feature names
        """
        groups = cls.get_all_feature_groups()
        
        if include_groups:
            # Only include specified groups
            features = set()
            for group in include_groups:
                if group in groups:
                    features.update(groups[group])
        else:
            # Include all groups
            features = set()
            for group_features in groups.values():
                features.update(group_features)
        
        # Remove excluded features
        features = features - cls.EXCLUDED
        
        return sorted(list(features))
    
    @classmethod
    def get_feature_count_by_category(cls) -> Dict[str, int]:
        """Get count of features per category."""
        groups = cls.get_all_feature_groups()
        return {name: len(features) for name, features in groups.items()}
    
    @classmethod
    def validate_features(cls, available_features: List[str]) -> Dict[str, List[str]]:
        """
        Validate which catalog features are available in dataset.
        
        Returns:
            Dict with 'available', 'missing', 'extra' keys
        """
        all_catalog_features = cls.get_features_for_model('all')
        available_set = set(available_features)
        catalog_set = set(all_catalog_features)
        
        return {
            'available': sorted(list(catalog_set & available_set)),
            'missing': sorted(list(catalog_set - available_set)),
            'extra': sorted(list(available_set - catalog_set - cls.EXCLUDED))
        }



