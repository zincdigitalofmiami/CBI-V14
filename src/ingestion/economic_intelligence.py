#!/usr/bin/env python3
"""
Economic Intelligence Multi-Source System
Fed, Treasury, BLS, International Central Banks, Economic Calendars
"""

import pandas as pd
import requests
from google.cloud import bigquery
import yfinance as yf
from datetime import datetime, timedelta
import json
from bigquery_utils import safe_load_to_bigquery, intelligence_collector, quick_save_to_bigquery

PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"

class EconomicIntelligence:
    """
    Comprehensive economic data collection with backup sources
    Targets 15-20% price variance from macro factors
    """
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.economic_sources = self._build_economic_matrix()
        
    def _build_economic_matrix(self):
        """Economic intelligence source matrix with backups"""
        return {
            'us_federal_reserve': [
                {'name': 'FRED_API', 'endpoint': 'https://api.stlouisfed.org/fred/', 'priority': 1},
                {'name': 'Fed_Speeches', 'endpoint': 'https://www.federalreserve.gov/newsevents/speech/', 'priority': 2},
                {'name': 'FOMC_Minutes', 'endpoint': 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm', 'priority': 1},
                {'name': 'Yahoo_Finance_Fed', 'endpoint': 'DGS10', 'priority': 3}  # Backup via yfinance
            ],
            
            'us_treasury': [
                {'name': 'Treasury_API', 'endpoint': 'https://api.fiscaldata.treasury.gov/services/api/v1/', 'priority': 1},
                {'name': 'Treasury_Auctions', 'endpoint': 'https://www.treasurydirect.gov/auctions/', 'priority': 2},
                {'name': 'TreasuryDirect', 'endpoint': 'https://www.treasurydirect.gov/', 'priority': 3}
            ],
            
            'bls_labor': [
                {'name': 'BLS_API', 'endpoint': 'https://api.bls.gov/publicAPI/v2/', 'priority': 1},
                {'name': 'BLS_BigQuery', 'endpoint': 'bigquery-public-data.bls', 'priority': 1},  # We tested this
                {'name': 'Yahoo_Finance_Econ', 'endpoint': 'economic_indicators', 'priority': 3}
            ],
            
            'international_central_banks': [
                {'name': 'ECB_API', 'endpoint': 'https://sdw-wsrest.ecb.europa.eu/service/', 'priority': 2},
                {'name': 'Bank_Brazil', 'endpoint': 'https://www3.bcb.gov.br/sgspub/', 'priority': 2},
                {'name': 'PBOC_China', 'endpoint': 'http://www.pbc.gov.cn/en/', 'priority': 3},
                {'name': 'BCRA_Argentina', 'endpoint': 'http://www.bcra.gob.ar/', 'priority': 3}
            ],
            
            'economic_calendars': [
                {'name': 'TradingEconomics', 'endpoint': 'https://tradingeconomics.com/calendar', 'priority': 2},
                {'name': 'ForexFactory', 'endpoint': 'https://www.forexfactory.com/calendar', 'priority': 2},
                {'name': 'Investing_Calendar', 'endpoint': 'https://www.investing.com/economic-calendar/', 'priority': 2},
                {'name': 'MarketWatch_Calendar', 'endpoint': 'https://www.marketwatch.com/economy-politics/calendar', 'priority': 3}
            ]
        }
    
    @intelligence_collector('economic_indicators')
    def collect_economic_intelligence(self):
        """
        Comprehensive economic intelligence collection with automatic BigQuery loading
        Combines Fed data and correlation analysis
        """
        fed_data = self.collect_fed_intelligence()
        correlations = self.hunt_economic_correlations()
        
        # Convert fed_data to DataFrame format
        economic_records = []
        for data_source in fed_data:
            if hasattr(data_source, 'to_dict'):
                # Convert DataFrame to records
                records = data_source.reset_index().to_dict('records')
                for record in records:
                    record['data_source'] = 'fed_intelligence'
                    record['collection_timestamp'] = datetime.now()
                    economic_records.append(record)
        
        # Add correlation discoveries
        for symbol, corr_data in correlations.items():
            economic_records.append({
                'symbol': symbol,
                'correlation': corr_data['correlation'],
                'hunt_value': corr_data['hunt_value'],
                'data_source': 'correlation_discovery',
                'collection_timestamp': datetime.now()
            })
        
        return pd.DataFrame(economic_records) if economic_records else pd.DataFrame()
    
    def collect_fed_intelligence(self):
        """Comprehensive Fed data collection with multiple sources"""
        fed_data = []
        
        # Source 1: Yahoo Finance (immediate backup)
        try:
            fed_tickers = ['^TNX', '^IRX', '^FVX', '^TYX']  # 10Y, 3M, 5Y, 30Y
            for ticker in fed_tickers:
                data = yf.download(ticker, period='1y', progress=False)
                if not data.empty:
                    data['instrument'] = ticker
                    fed_data.append(data)
        except Exception as e:
            print(f"Yahoo Finance Fed backup failed: {e}")
        
        # Source 2: BLS BigQuery (tested working)
        try:
            query = """
            SELECT series_id, year, period, value, date
            FROM `bigquery-public-data.bls.unemployment_cps`
            WHERE series_id IN ('LNS14000000', 'LNS12000000')  -- Unemployment, employment
            AND year >= 2022
            ORDER BY year DESC, period DESC
            """
            bls_df = self.client.query(query).to_dataframe()
            if not bls_df.empty:
                fed_data.append(bls_df)
        except Exception as e:
            print(f"BLS BigQuery failed: {e}")
        
        return fed_data
    
    def hunt_economic_correlations(self):
        """
        Use neural network insights to hunt for economic source connections
        """
        print("Hunting economic correlations for source discovery...")
        
        # Get current price and economic data
        query = f"""
        SELECT
            date,
            close_price as zl_price
        FROM `{PROJECT_ID}.curated.vw_soybean_oil_features_daily`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
        """
        price_df = self.client.query(query).to_dataframe()
        
        # Hunt for correlated economic indicators
        hunt_targets = [
            # Currency correlations (15-20% variance)
            {'symbol': 'BRL=X', 'hypothesis': 'Brazilian Real affects export competitiveness'},
            {'symbol': 'DXY', 'hypothesis': 'USD strength affects commodity prices'},
            {'symbol': 'CNY=X', 'hypothesis': 'Chinese Yuan affects import demand'},
            
            # Interest rate correlations
            {'symbol': '^TNX', 'hypothesis': '10Y Treasury affects inventory carrying costs'},
            {'symbol': '^IRX', 'hypothesis': '3M rate affects short-term financing'},
            
            # Inflation correlations  
            {'symbol': 'CPIAUCSL', 'hypothesis': 'CPI inflation affects food commodity demand'},
            
            # Energy correlations (biofuel linkage)
            {'symbol': 'CL=F', 'hypothesis': 'Crude oil affects biofuel demand for soy oil'},
            {'symbol': 'NG=F', 'hypothesis': 'Natural gas affects processing costs'}
        ]
        
        discovered_correlations = {}
        
        for target in hunt_targets:
            try:
                # Test correlation with price data
                econ_data = yf.download(target['symbol'], period='1y', progress=False)
                if not econ_data.empty and len(price_df) > 10:
                    # Simple correlation test
                    merged = pd.merge(price_df, econ_data[['Close']], 
                                    left_on='date', right_index=True, how='inner')
                    
                    if len(merged) > 10:
                        correlation = merged['value'].corr(merged['Close'])
                        if abs(correlation) > 0.3:  # Significant correlation
                            discovered_correlations[target['symbol']] = {
                                'correlation': correlation,
                                'hypothesis': target['hypothesis'],
                                'data_points': len(merged),
                                'hunt_value': 'HIGH' if abs(correlation) > 0.5 else 'MEDIUM'
                            }
                            print(f"CORRELATION DISCOVERED: {target['symbol']} = {correlation:.3f}")
            except Exception as e:
                print(f"Correlation test failed for {target['symbol']}: {e}")
        
        return discovered_correlations

def main():
    """Execute economic intelligence collection (surgical fix approach)"""
    intel = EconomicIntelligence()
    
    print("=== ECONOMIC INTELLIGENCE COLLECTION ===")
    print("Using surgical fix with simple data collection")
    
    # Collect Fed data from multiple sources
    fed_data = intel.collect_fed_intelligence()
    print(f"Fed data sources collected: {len(fed_data)}")
    
    # Hunt for correlations to discover new sources
    correlations = intel.hunt_economic_correlations()
    print(f"Economic correlations discovered: {len(correlations)}")
    
    # Display hunt results
    for symbol, data in correlations.items():
        print(f"{symbol}: {data['correlation']:.3f} correlation - {data['hunt_value']} priority")
    
    # SURGICAL FIX: Use quick_save_to_bigquery for simple data
    if correlations:
        correlation_records = []
        for symbol, data in correlations.items():
            correlation_records.append({
                'symbol': symbol,
                'correlation': data['correlation'],
                'hunt_value': data['hunt_value'],
                'data_source': 'economic_correlation_discovery',
                'timestamp': datetime.now()
            })
        
        quick_save_to_bigquery(correlation_records, 'economic_indicators')
        print(f"✅ Saved {len(correlation_records)} correlation discoveries to BigQuery")
    
    print("✅ Economic intelligence collection completed")

if __name__ == "__main__":
    main()
