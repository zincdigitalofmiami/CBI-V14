#!/usr/bin/env python3
"""
Feature Registry - Semantic Metadata for Neural Engine and AI Agent
Provides economic context and relationships for all features in the system
"""

from google.cloud import bigquery
from typing import Dict, List, Optional
import pandas as pd

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
METADATA_TABLE = "feature_metadata"

class FeatureRegistry:
    """
    Feature registry that provides semantic understanding of all data features
    Used by neural engine for feature engineering and AI agent for explanations
    """
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self._cache = None
        self._load_metadata()
    
    def _load_metadata(self):
        """Load all feature metadata into memory for fast lookups"""
        query = f"""
        SELECT 
            feature_name,
            feature_type,
            asset_class,
            economic_meaning,
            directional_impact,
            typical_lag_days,
            typical_range_min,
            typical_range_max,
            source_table,
            source_column,
            related_features,
            chat_aliases,
            policy_impact_score,
            affected_commodities,
            source_reliability_score,
            related_futures_contract,
            is_crush_component,
            top_producing_countries
        FROM `{PROJECT_ID}.{DATASET_ID}.{METADATA_TABLE}`
        WHERE is_active = TRUE
        """
        
        df = self.client.query(query).to_dataframe()
        self._cache = df.set_index('feature_name').to_dict('index')
        print(f"✅ Loaded {len(self._cache)} features from metadata registry")
    
    def get_feature(self, feature_name: str) -> Optional[Dict]:
        """
        Get metadata for a specific feature
        
        Args:
            feature_name: Name of the feature (e.g., 'fed_funds_rate')
            
        Returns:
            Dict with feature metadata or None if not found
        """
        if self._cache is None:
            self._load_metadata()
        
        return self._cache.get(feature_name)
    
    def get_features_by_type(self, feature_type: str) -> List[Dict]:
        """
        Get all features of a specific type
        
        Args:
            feature_type: One of 'MACRO', 'CURRENCY', 'COMMODITY', 'WEATHER', 'SENTIMENT'
            
        Returns:
            List of feature metadata dicts
        """
        if self._cache is None:
            self._load_metadata()
        
        return [
            {'feature_name': name, **meta} 
            for name, meta in self._cache.items() 
            if meta.get('feature_type') == feature_type
        ]
    
    def get_features_by_impact(self, directional_impact: str) -> List[Dict]:
        """
        Get all features with specific directional impact on prices
        
        Args:
            directional_impact: 'POSITIVE', 'NEGATIVE', 'COMPLEX', 'LEADING', 'TARGET'
            
        Returns:
            List of feature metadata dicts
        """
        if self._cache is None:
            self._load_metadata()
        
        return [
            {'feature_name': name, **meta} 
            for name, meta in self._cache.items() 
            if meta.get('directional_impact') == directional_impact
        ]
    
    def get_related_features(self, feature_name: str) -> List[str]:
        """
        Get features related to a specific feature
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            List of related feature names
        """
        meta = self.get_feature(feature_name)
        if meta and meta.get('related_features'):
            return meta['related_features']
        return []
    
    def translate_chat_query(self, user_query: str) -> Optional[str]:
        """
        Translate natural language query to feature name
        
        Args:
            user_query: User's natural language (e.g., "interest rates", "oil prices")
            
        Returns:
            Canonical feature name or None
        """
        if self._cache is None:
            self._load_metadata()
        
        user_query_lower = user_query.lower()
        
        # Check each feature's chat aliases
        for feature_name, meta in self._cache.items():
            aliases = meta.get('chat_aliases')
            if aliases is not None and len(aliases) > 0:
                for alias in aliases:
                    if alias and (alias.lower() in user_query_lower or user_query_lower in alias.lower()):
                        return feature_name
        
        # Also check exact feature name match
        if user_query in self._cache:
            return user_query
        
        return None
    
    def get_lag_features(self, min_lag_days: int = 1) -> List[Dict]:
        """
        Get features that have typical lag effects
        Used for automatic lag feature generation in neural pipeline
        
        Args:
            min_lag_days: Minimum lag days to filter (default 1)
            
        Returns:
            List of features with lag metadata
        """
        if self._cache is None:
            self._load_metadata()
        
        return [
            {'feature_name': name, **meta} 
            for name, meta in self._cache.items() 
            if meta.get('typical_lag_days', 0) >= min_lag_days
        ]
    
    def explain_feature(self, feature_name: str, include_related: bool = True) -> str:
        """
        Generate human-readable explanation of a feature
        Used by AI agent for chat responses
        
        Args:
            feature_name: Name of the feature
            include_related: Whether to include related features
            
        Returns:
            Formatted explanation string
        """
        meta = self.get_feature(feature_name)
        if not meta:
            return f"❌ Feature '{feature_name}' not found in registry"
        
        explanation = [
            f"📊 **{feature_name.replace('_', ' ').title()}**",
            f"",
            f"**Type:** {meta.get('asset_class', 'N/A')} ({meta.get('feature_type', 'N/A')})",
            f"",
            f"**Economic Meaning:**",
            f"{meta.get('economic_meaning', 'No description available')}",
            f"",
            f"**Market Impact:** {meta.get('directional_impact', 'Unknown')}",
        ]
        
        if meta.get('typical_lag_days'):
            explanation.append(f"**Typical Lag:** {meta['typical_lag_days']} days")
        
        if meta.get('typical_range_min') is not None:
            explanation.append(
                f"**Typical Range:** {meta['typical_range_min']} - {meta['typical_range_max']}"
            )
        
        related = meta.get('related_features')
        if include_related and related is not None and len(related) > 0:
            explanation.append(f"")
            explanation.append(f"**Related Features:** {', '.join(related)}")
        
        return "\n".join(explanation)
    
    def get_all_features_summary(self) -> pd.DataFrame:
        """
        Get summary table of all features
        Useful for dashboard display
        
        Returns:
            DataFrame with feature summary
        """
        if self._cache is None:
            self._load_metadata()
        
        return pd.DataFrame([
            {
                'Feature': name,
                'Type': meta.get('feature_type'),
                'Asset Class': meta.get('asset_class'),
                'Impact': meta.get('directional_impact'),
                'Lag (days)': meta.get('typical_lag_days', 0)
            }
            for name, meta in self._cache.items()
        ])


# Singleton instance for easy import
feature_registry = FeatureRegistry()


# Convenience functions for quick access
def get_feature(name: str) -> Optional[Dict]:
    """Get metadata for a feature"""
    return feature_registry.get_feature(name)


def explain_feature(name: str) -> str:
    """Get human-readable explanation of a feature"""
    return feature_registry.explain_feature(name)


def translate_query(user_query: str) -> Optional[str]:
    """Translate natural language to feature name"""
    return feature_registry.translate_chat_query(user_query)


if __name__ == "__main__":
    # Demo usage
    print("=== Feature Registry Demo ===\n")
    
    # Example 1: Get feature metadata
    print("1. Fed Funds Rate Metadata:")
    fed_meta = get_feature('fed_funds_rate')
    print(f"   Type: {fed_meta['feature_type']}")
    print(f"   Impact: {fed_meta['directional_impact']}")
    print(f"   Lag: {fed_meta['typical_lag_days']} days")
    print()
    
    # Example 2: Natural language translation
    print("2. Natural Language Translation:")
    print(f"   'interest rates' → {translate_query('interest rates')}")
    print(f"   'palm oil' → {translate_query('palm oil')}")
    print(f"   'Brazil currency' → {translate_query('Brazil currency')}")
    print()
    
    # Example 3: Get all macro features
    print("3. All MACRO features:")
    macro_features = feature_registry.get_features_by_type('MACRO')
    for f in macro_features:
        print(f"   - {f['feature_name']}")
    print()
    
    # Example 4: Explain a feature (for AI agent)
    print("4. Feature Explanation (for AI chat):")
    print(explain_feature('soybean_oil_prices'))

