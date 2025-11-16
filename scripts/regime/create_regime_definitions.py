#!/usr/bin/env python3
"""
Create fresh market regime definitions based on 25-year historical analysis.
No dependency on BigQuery legacy regimes - this is our new intelligence.

Author: AI Assistant
Date: November 16, 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

DRIVE = Path("/Volumes/Satechi Hub/Projects/CBI-V14")
REGISTRY_DIR = DRIVE / "registry"

def create_regime_calendar():
    """
    Define market regimes based on comprehensive historical research.
    These are data-driven periods with distinct market characteristics.
    """
    
    # Define regimes based on thorough market analysis
    # Weight scale: 50-500 (10x differential max, as per spec)
    
    regimes = [
        # Pre-2000: Foundation period
        {
            'regime': 'tech_bubble_1998_2000',
            'start_date': '1998-01-01',
            'end_date': '2000-03-31',
            'weight': 50,  # Historical baseline
            'description': 'Tech bubble period, commodity bear market, strong USD'
        },
        
        # 2000-2007: Commodity supercycle emergence
        {
            'regime': 'commodity_emergence_2000_2003',
            'start_date': '2000-04-01',
            'end_date': '2003-12-31',
            'weight': 75,
            'description': 'Tech crash, weak USD, early China demand growth'
        },
        {
            'regime': 'china_supercycle_2004_2007',
            'start_date': '2004-01-01',
            'end_date': '2007-07-31',
            'weight': 100,
            'description': 'China WTO effect, commodity supercycle, biofuel mandate start'
        },
        
        # 2008-2009: Financial crisis
        {
            'regime': 'financial_crisis_2008_2009',
            'start_date': '2007-08-01',
            'end_date': '2009-06-30',
            'weight': 200,  # High weight - extreme volatility patterns
            'description': 'Global financial crisis, commodity crash and recovery'
        },
        
        # 2010-2014: QE era
        {
            'regime': 'qe_commodity_boom_2010_2011',
            'start_date': '2009-07-01',
            'end_date': '2011-12-31',
            'weight': 150,
            'description': 'QE-driven commodity boom, Arab Spring, food crisis'
        },
        {
            'regime': 'plateau_transition_2012_2014',
            'start_date': '2012-01-01',
            'end_date': '2014-06-30',
            'weight': 100,
            'description': 'High plateau prices, US shale revolution beginning'
        },
        
        # 2014-2016: Commodity crash
        {
            'regime': 'commodity_crash_2014_2016',
            'start_date': '2014-07-01',
            'end_date': '2016-12-31',
            'weight': 250,  # High weight - regime shift patterns
            'description': 'Oil crash, China slowdown, strong USD, deflation fears'
        },
        
        # 2017-2019: Trade war
        {
            'regime': 'pre_tradewar_2017',
            'start_date': '2017-01-01',
            'end_date': '2017-12-31',
            'weight': 125,
            'description': 'Trump inauguration, pre-trade war positioning'
        },
        {
            'regime': 'tradewar_escalation_2018_2019',
            'start_date': '2018-01-01',
            'end_date': '2019-12-31',
            'weight': 300,  # High weight - policy-driven volatility
            'description': 'US-China trade war, tariffs, soybean demand destruction'
        },
        
        # 2020-2021: COVID
        {
            'regime': 'covid_shock_2020',
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'weight': 350,  # Very high - unprecedented patterns
            'description': 'COVID pandemic, negative oil, supply chain chaos'
        },
        {
            'regime': 'covid_recovery_2021',
            'start_date': '2021-01-01',
            'end_date': '2021-06-30',
            'weight': 200,
            'description': 'Vaccine rollout, stimulus boom, inflation emergence'
        },
        
        # 2021-2023: Inflation era
        {
            'regime': 'inflation_surge_2021_2022',
            'start_date': '2021-07-01',
            'end_date': '2022-12-31',
            'weight': 400,  # Very high - inflation regime shift
            'description': 'Supply chain crisis, Ukraine war, Fed pivot, energy crisis'
        },
        {
            'regime': 'disinflation_2023',
            'start_date': '2023-01-01',
            'end_date': '2023-10-31',
            'weight': 250,
            'description': 'Fed tightening, banking stress, China reopening'
        },
        
        # 2023-2025: Current era
        {
            'regime': 'trump_return_2024_2025',
            'start_date': '2023-11-01',
            'end_date': '2025-12-31',
            'weight': 500,  # Maximum weight - current regime
            'description': 'Trump 2.0 anticipation, tariff threats, biofuel policy shifts'
        },
        
        # Catch-all for any gaps
        {
            'regime': 'baseline',
            'start_date': '1900-01-01',
            'end_date': '2099-12-31',
            'weight': 100,
            'description': 'Default regime for any unclassified periods'
        }
    ]
    
    # Create regime weights DataFrame
    regime_weights = pd.DataFrame(regimes)
    regime_weights['start_date'] = pd.to_datetime(regime_weights['start_date'])
    regime_weights['end_date'] = pd.to_datetime(regime_weights['end_date'])
    
    # Create daily regime calendar
    date_range = pd.date_range(start='2000-01-01', end='2025-12-31', freq='D')
    regime_calendar = pd.DataFrame({'date': date_range})
    
    # Assign regimes to each date
    def get_regime(date):
        for _, regime in regime_weights.iterrows():
            if regime['regime'] == 'baseline':
                continue  # Skip baseline in first pass
            if regime['start_date'] <= date <= regime['end_date']:
                return regime['regime']
        return 'baseline'  # Default if no match
    
    regime_calendar['regime'] = regime_calendar['date'].apply(get_regime)
    
    # Add training weight
    weight_map = dict(zip(regime_weights['regime'], regime_weights['weight']))
    regime_calendar['training_weight'] = regime_calendar['regime'].map(weight_map)
    
    # Save to registry
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    
    regime_calendar.to_parquet(REGISTRY_DIR / "regime_calendar.parquet")
    regime_weights.to_parquet(REGISTRY_DIR / "regime_weights.parquet")
    
    print("="*80)
    print("REGIME DEFINITIONS CREATED")
    print("="*80)
    print(f"\nRegime Calendar: {len(regime_calendar)} days")
    print(f"Date Range: {regime_calendar['date'].min()} to {regime_calendar['date'].max()}")
    print(f"Unique Regimes: {regime_calendar['regime'].nunique()}")
    print(f"\nRegime Distribution:")
    print(regime_calendar['regime'].value_counts())
    print(f"\nWeight Distribution:")
    print(f"Min Weight: {regime_weights['weight'].min()}")
    print(f"Max Weight: {regime_weights['weight'].max()}")
    print(f"Weight Range: {regime_weights['weight'].min()}-{regime_weights['weight'].max()}")
    
    # Show regime details
    print("\nRegime Details:")
    for _, r in regime_weights.iterrows():
        if r['regime'] != 'baseline':
            days = ((regime_calendar['regime'] == r['regime']).sum())
            print(f"  {r['regime']}: weight={r['weight']}, days={days}")
    
    return regime_calendar, regime_weights


if __name__ == "__main__":
    regime_calendar, regime_weights = create_regime_calendar()
    print(f"\n✅ Saved to: {REGISTRY_DIR}")
    print("  - regime_calendar.parquet")
    print("  - regime_weights.parquet")
