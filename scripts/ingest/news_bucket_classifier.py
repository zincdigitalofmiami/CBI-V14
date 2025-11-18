#!/usr/bin/env python3
"""
News Bucket Classifier - Regime-Based Organization
Classifies news articles into 10 major buckets/regimes for ZL intelligence
Works for both ScrapeCreators and Alpha Vantage sources
"""

from typing import Dict, List, Tuple, Optional
import re

# ============================================================================
# BUCKET DEFINITIONS - 10 Major Regimes
# ============================================================================

BUCKET_KEYWORDS = {
    '1_BIOFUEL_POLICY': {
        'priority': 'P0',
        'impact': 'high',
        'lead_days': 120,
        'keywords': [
            # Primary
            'renewable fuel standard', 'rfs', 'saf credit', 'saf tax credit',
            'lcfs', 'low carbon fuel standard', 'biodiesel blend', 'b20', 'b40', 'b35',
            'renewable diesel capacity', 'biofuel mandate',
            # Agencies
            'epa biofuel', 'epa renewable', 'doe biofuel', 'carb lcfs',
            # Lobbying
            'biofuel lobby', 'pac donation biofuel', 'epa hearing biofuel',
            # Capacity
            'renewable diesel plant', 'hydrotreater conversion', 'saf plant'
        ],
        'triggers': [
            'proposed rule', 'final rule', 'expanded credit', 'retroactive volumes',
            'industry petition', 'lobby disclosure', 'refinery conversion'
        ]
    },
    
    '2_PALM_SUPPLY_POLICY': {
        'priority': 'P0',
        'impact': 'high',
        'lead_days': 60,
        'keywords': [
            'cpo export levy', 'palm oil export tax', 'indonesia export ban',
            'mpob', 'dmo', 'malaysia supply', 'el nino dry estates',
            'india edible oil duty', 'palm oil', 'indonesia palm', 'malaysia palm'
        ],
        'triggers': [
            'port congestion', 'labor shortage', 'estate yield down',
            'harvest disruption', 'export quota'
        ]
    },
    
    '3_CHINA_DEMAND': {
        'priority': 'P0',
        'impact': 'high',
        'lead_days': 37,
        'keywords': [
            'sinograin', 'cofco', 'ndrc soybean', 'state reserves',
            'soybean auctions', 'strategic stockpile', 'dalian soy oil',
            'dce futures', 'cny devaluation', 'yuan liquidity',
            'china soybean', 'china soy', 'china crush', 'china import'
        ],
        'triggers': [
            'food security directive', 'import suspension', 'port delays',
            'customs inspections', 'african swine fever'
        ]
    },
    
    '4_US_POLICY_TARIFFS': {
        'priority': 'P0',
        'impact': 'high',
        'lead_days': 227,
        'keywords': [
            'tariff threat', '301 investigation', 'trade retaliation',
            'sanction exemption', 'argentina cooperation', 'imf debt restructuring',
            'trump tariff', 'farm belt support', 'agricultural exception',
            'farm bill', 'commodity credit', 'crop insurance'
        ],
        'triggers': [
            'national security review', 'executive order', 'trade enforcement',
            'mark-up session', 'budget resolution'
        ]
    },
    
    '5_SOUTH_AMERICA_SUPPLY': {
        'priority': 'P0',
        'impact': 'high',
        'lead_days': 105,
        'keywords': [
            # Brazil/Argentina crop
            'conab', 'mapa brazil', 'soybean harvest brazil', 'brazil soybean',
            'mato grosso', 'argentina soybean', 'rosario', 'brazil crop',
            # Weather
            'drought', 'la niña', 'el niño', 'moisture stress', 'flash drought',
            'flood', 'precipitation', 'brazil weather', 'argentina weather',
            # Logistics
            'br-163', 'rosario strike', 'port strike', 'truck blockade',
            'barge delays', 'sojadólar'
        ],
        'triggers': [
            'yield reduction', 'export license delay', 'crop stress',
            'planting delays'
        ]
    },
    
    '6_SHIPPING_LOGISTICS': {
        'priority': 'P1',
        'impact': 'medium',
        'lead_days': 33,
        'keywords': [
            # Chokepoints
            'red sea attacks', 'suez disruption', 'panama canal drought',
            'bab el-mandeb', 'strait of malacca',
            # Freight
            'baltic dry index', 'dry bulk rate', 'freight rate',
            'mr tanker', 'clean tanker',
            # Strikes
            'port strike', 'dockworker strike', 'ilwu', 'longshoreman',
            # Insurance
            'marine insurance', 'war risk premium', 'reinsurance'
        ],
        'triggers': [
            'ships diverted', 'draft restrictions', 'strike notice',
            'rate surge', 'tonnage shortage'
        ]
    },
    
    '7_HIDDEN_DRIVERS': {
        'priority': 'P1',
        'impact': 'predictive',
        'lead_days': 180,
        'keywords': [
            # SWF
            'sovereign wealth fund', 'swf investment', 'stake acquisition agribusiness',
            # Carbon/EUDR
            'eudr enforcement', 'carbon credit', 'deforestation compliance',
            'cbio', 'renovabio',
            # Defense
            'fms sale', 'security guarantee', 'naval escort',
            # Pharma
            'pharmaceutical licensing', 'patent extension', 'vaccine distribution',
            # CBDC
            'digital yuan', 'cbdc corridor', 'brl-cny settlement',
            # Infrastructure
            'port dredging', 'port expansion', 'grain terminal',
            # Academic
            'agricultural mou', 'university exchange', 'crop science partnership'
        ],
        'triggers': [
            '5% stake', 'strategic equity', 'traceability deadline',
            'security memorandum', 'digital settlement pilot'
        ]
    },
    
    '8_MACRO_FX': {
        'priority': 'P1',
        'impact': 'medium',
        'lead_days': 18,
        'keywords': [
            # FX
            'brl weakness', 'real depreciation', 'peso collapse',
            'fx intervention', 'soydollar', 'currency',
            # Macro
            'fed rate cut', 'inflation spike', 'qe expectations',
            'federal reserve', 'interest rate',
            # Positioning
            'cftc', 'managed money', 'speculator positions', 'cot report',
            # Risk
            'vix spike', 'market turmoil', 'risk aversion'
        ],
        'triggers': [
            'fx swap activation', 'intervention round', 'rate decision'
        ]
    },
    
    '9_ENERGY_INPUTS': {
        'priority': 'P2',
        'impact': 'medium',
        'lead_days': 227,
        'keywords': [
            # Fertilizer
            'nitrogen shortage', 'potash sanctions', 'ammonia plant outage',
            'urea tender', 'fertilizer', 'potash',
            # Energy
            'diesel shortage', 'crude rally', 'diesel crack spread',
            'refinery outage', 'crude oil', 'energy price'
        ],
        'triggers': [
            'sanction risk', 'export restriction', 'plant accident'
        ]
    },
    
    '10_MARKET_STRUCTURE_POLICY': {
        'priority': 'P2',
        'impact': 'low-medium',
        'lead_days': 105,
        'keywords': [
            # GMO/Agrochemical
            'glyphosate ban', 'trait approval', 'pesticide restriction',
            'agrochemical', 'gmo',
            # Black Sea
            'odessa attack', 'sunflower oil export', 'black sea corridor',
            # Infrastructure
            'grain silo', 'port fire', 'pipeline rupture',
            # Credit
            'credit tightening', 'ag loan default', 'lgfv debt',
            # Politics
            'election', 'agriculture minister', 'nationalization',
            # Disease
            'soybean rust', 'white mold', 'crop disease',
            # Traceability
            'blockchain traceability', 'eudr compliance tech'
        ],
        'triggers': [
            'ban proposal', 'port hit', 'bond rollover', 'election result'
        ]
    }
}

# Bucket priority to integer mapping
BUCKET_PRIORITY_SCORE = {'P0': 100, 'P1': 50, 'P2': 25}


def classify_article_to_bucket(
    title: str,
    description: str = '',
    query: str = '',
    av_topics: List[Dict] = None
) -> Dict:
    """
    Classify article into one of 10 buckets.
    
    Works for both ScrapeCreators and Alpha Vantage sources.
    
    Args:
        title: Article headline
        description: Article summary/snippet
        query: Search query (ScrapeCreators only, optional)
        av_topics: Alpha Vantage topic array (optional)
    
    Returns:
        dict with bucket classification:
        {
            'bucket': '1_BIOFUEL_POLICY',
            'bucket_priority': 'P0',
            'bucket_impact': 'high',
            'bucket_lead_days': 120,
            'category': 'biofuel_mandates',  # nullable
            'match_score': 85.0,             # confidence score
            'matched_keywords': ['rfs', 'epa biofuel'],
            'matched_triggers': ['proposed rule']
        }
    """
    # Combine all text for matching
    search_text = ' '.join([
        str(title),
        str(description),
        str(query),
        str(av_topics) if av_topics else ''
    ]).lower()
    
    # Score each bucket
    bucket_scores = {}
    
    for bucket_name, bucket_data in BUCKET_KEYWORDS.items():
        score = 0
        matched_keywords = []
        matched_triggers = []
        
        # Check primary keywords
        for keyword in bucket_data['keywords']:
            if keyword.lower() in search_text:
                score += 10
                matched_keywords.append(keyword)
        
        # Check trigger phrases (worth more)
        for trigger in bucket_data.get('triggers', []):
            if trigger.lower() in search_text:
                score += 25
                matched_triggers.append(trigger)
        
        # Bonus if query matches bucket (ScrapeCreators)
        if query and any(kw.lower() in query.lower() for kw in bucket_data['keywords']):
            score += 15
        
        # Bonus for P0 buckets (prioritize high-impact)
        if bucket_data['priority'] == 'P0':
            score += 5
        
        bucket_scores[bucket_name] = {
            'score': score,
            'matched_keywords': matched_keywords,
            'matched_triggers': matched_triggers
        }
    
    # Check for irrelevant keywords that disqualify the article
    irrelevant_patterns = [
        'tech startup', 'venture capital', 'crypto', 'bitcoin', 'nft',
        'movie', 'film', 'tv show', 'entertainment', 'celebrity',
        'sports', 'football', 'basketball', 'gaming',
        'stock split', 'dividend', 'earnings call', 'quarterly results'
    ]
    
    # Check if article contains irrelevant patterns WITHOUT commodity context
    commodity_context_keywords = [
        'soybean', 'soy', 'palm oil', 'edible oil', 'vegetable oil',
        'commodity', 'futures', 'agricultural', 'crop', 'biofuel'
    ]
    
    has_commodity_context = any(kw in search_text for kw in commodity_context_keywords)
    has_irrelevant_patterns = any(pattern in search_text for pattern in irrelevant_patterns)
    
    if has_irrelevant_patterns and not has_commodity_context:
        # Return None to indicate article should be filtered out
        return None
    
    # Find best match
    best_bucket = max(bucket_scores.items(), key=lambda x: x[1]['score'])
    bucket_name, bucket_result = best_bucket
    
    # Require minimum score of 15 to be classified (otherwise filter out)
    # This prevents weak matches from being included
    if bucket_result['score'] < 15:
        return None
    
    bucket_data = BUCKET_KEYWORDS[bucket_name]
    
    return {
        'bucket': bucket_name,
        'bucket_priority': bucket_data['priority'],
        'bucket_impact': bucket_data['impact'],
        'bucket_lead_days': bucket_data['lead_days'],
        'category': None,  # TODO: Map to specific category if needed
        'match_score': bucket_result['score'],
        'matched_keywords': bucket_result['matched_keywords'][:5],  # Top 5
        'matched_triggers': bucket_result['matched_triggers'][:3]   # Top 3
    }


def get_bucket_keywords_for_filter(bucket_name: str) -> List[str]:
    """
    Get all keywords for a bucket (for filtering).
    
    Used to create bucket-level filters (less strict than full matrix).
    """
    if bucket_name not in BUCKET_KEYWORDS:
        return []
    
    bucket_data = BUCKET_KEYWORDS[bucket_name]
    return bucket_data['keywords'] + bucket_data.get('triggers', [])


def filter_article_by_buckets(
    title: str,
    description: str = '',
    query: str = '',
    allowed_buckets: List[str] = None
) -> Tuple[bool, Optional[Dict]]:
    """
    Filter article based on bucket classification.
    
    Less strict than institutional keyword matrix filter.
    Returns (is_relevant, classification_dict).
    
    Args:
        title: Article headline
        description: Article summary/snippet
        query: Search query (optional)
        allowed_buckets: List of bucket names to allow (None = allow all P0/P1)
    
    Returns:
        tuple: (is_relevant: bool, classification: dict or None)
    """
    classification = classify_article_to_bucket(title, description, query)
    
    # If classification is None, article was filtered out
    if classification is None:
        return (False, None)
    
    # If no buckets specified, default to P0 and P1 buckets
    if not allowed_buckets:
        allowed_buckets = get_p0_p1_buckets()
    
    # Check if classified bucket is in allowed list
    is_relevant = classification['bucket'] in allowed_buckets
    
    return (is_relevant, classification)


def get_priority_buckets() -> List[str]:
    """Get P0 buckets (highest priority)."""
    return [name for name, data in BUCKET_KEYWORDS.items() if data['priority'] == 'P0']


def get_p0_p1_buckets() -> List[str]:
    """Get P0 and P1 buckets (high + medium priority)."""
    return [name for name, data in BUCKET_KEYWORDS.items() if data['priority'] in ['P0', 'P1']]


if __name__ == '__main__':
    # Test the classifier
    test_articles = [
        {
            'title': 'EPA Proposes New Renewable Fuel Standards',
            'description': 'EPA announces final rule for RFS volumes with expanded SAF credit',
            'query': 'EPA biofuel mandate'
        },
        {
            'title': 'Indonesia Raises CPO Export Levy',
            'description': 'Government increases palm oil export tax to boost downstream industry',
            'query': 'palm oil export tax Indonesia'
        },
        {
            'title': 'Syensqo exercises call option to redeem bonds',
            'description': 'Corporate bond redemption announcement',
            'query': ''
        },
        {
            'title': 'Brazil Soybean Harvest Delayed by Drought',
            'description': 'CONAB reports Mato Grosso dryness affecting harvest pace',
            'query': 'Brazil soybean harvest drought'
        }
    ]
    
    print("="*80)
    print("BUCKET CLASSIFIER TEST")
    print("="*80)
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n{i}. {article['title'][:60]}")
        
        result = classify_article_to_bucket(
            article['title'],
            article['description'],
            article['query']
        )
        
        if result is None:
            print(f"   ❌ FILTERED OUT (irrelevant or low score)")
        else:
            print(f"   Bucket: {result['bucket']}")
            print(f"   Priority: {result['bucket_priority']}")
            print(f"   Impact: {result['bucket_impact']}")
            print(f"   Lead Days: {result['bucket_lead_days']}")
            print(f"   Match Score: {result['match_score']}")
            
            if result['matched_keywords']:
                print(f"   Keywords: {', '.join(result['matched_keywords'][:3])}")
            if result['matched_triggers']:
                print(f"   Triggers: {', '.join(result['matched_triggers'])}")
        
        # Test filter
        is_relevant, classification = filter_article_by_buckets(
            article['title'],
            article['description'],
            article['query'],
            allowed_buckets=get_p0_p1_buckets()
        )
        print(f"   Passes P0/P1 filter: {'✅' if is_relevant else '❌'}")

