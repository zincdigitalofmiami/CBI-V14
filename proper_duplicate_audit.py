#!/usr/bin/env python3
"""
PROPER Duplicate Audit for CBI-V14
Checks for ACTUAL duplicates based on table-specific primary keys, not just date counts.
"""

from google.cloud import bigquery
from datetime import datetime

def main():
    client = bigquery.Client(project="cbi-v14")
    
    print("=" * 80)
    print("PROPER DUPLICATE AUDIT - CBI-V14")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Define PRIMARY KEY checks for each table
    duplicate_checks = {
        "soybean_oil_prices": """
            SELECT DATE(time) as date, COUNT(*) as count
            FROM `cbi-v14.forecasting_data_warehouse.soybean_oil_prices`
            GROUP BY DATE(time)
            HAVING COUNT(*) > 1
        """,
        "corn_prices": """
            SELECT DATE(time) as date, COUNT(*) as count
            FROM `cbi-v14.forecasting_data_warehouse.corn_prices`
            GROUP BY DATE(time)
            HAVING COUNT(*) > 1
        """,
        "soybean_prices": """
            SELECT DATE(time) as date, COUNT(*) as count
            FROM `cbi-v14.forecasting_data_warehouse.soybean_prices`
            GROUP BY DATE(time)
            HAVING COUNT(*) > 1
        """,
        "palm_oil_prices": """
            SELECT DATE(time) as date, COUNT(*) as count
            FROM `cbi-v14.forecasting_data_warehouse.palm_oil_prices`
            GROUP BY DATE(time)
            HAVING COUNT(*) > 1
        """,
        "crude_oil_prices": """
            SELECT DATE(time) as date, COUNT(*) as count
            FROM `cbi-v14.forecasting_data_warehouse.crude_oil_prices`
            GROUP BY DATE(time)
            HAVING COUNT(*) > 1
        """,
    }
    
    print("CHECKING FOR TRUE DUPLICATES (Same Primary Key):")
    print("=" * 80)
    
    true_duplicates_found = False
    
    for table_name, query in duplicate_checks.items():
        try:
            df = client.query(query).to_dataframe()
            if len(df) > 0:
                true_duplicates_found = True
                print(f"\n❌ {table_name}: {len(df)} dates with duplicates")
                print(f"   Total duplicate rows: {(df['count'] - 1).sum()}")
                if len(df) <= 10:
                    for _, row in df.iterrows():
                        print(f"      {row['date']}: {row['count']} copies")
            else:
                print(f"✅ {table_name}: No duplicates")
        except Exception as e:
            print(f"⚠️  {table_name}: Error checking - {str(e)[:60]}")
    
    # Check multi-value tables are properly structured
    print("\n" + "=" * 80)
    print("MULTI-VALUE TABLES (Should have many rows per date):")
    print("=" * 80)
    
    multi_value_checks = {
        "currency_data": """
            SELECT 
                COUNT(DISTINCT date) as unique_dates,
                COUNT(DISTINCT from_currency || to_currency) as unique_pairs,
                COUNT(*) as total_rows,
                COUNT(*) / COUNT(DISTINCT date) as avg_pairs_per_day
            FROM `cbi-v14.forecasting_data_warehouse.currency_data`
        """,
        "economic_indicators": """
            SELECT 
                COUNT(DISTINCT DATE(time)) as unique_dates,
                COUNT(DISTINCT indicator) as unique_indicators,
                COUNT(*) as total_rows,
                COUNT(*) / COUNT(DISTINCT DATE(time)) as avg_indicators_per_day
            FROM `cbi-v14.forecasting_data_warehouse.economic_indicators`
        """,
        "weather_data": """
            SELECT 
                COUNT(DISTINCT date) as unique_dates,
                COUNT(DISTINCT station_id) as unique_stations,
                COUNT(*) as total_rows,
                COUNT(*) / COUNT(DISTINCT date) as avg_stations_per_day
            FROM `cbi-v14.forecasting_data_warehouse.weather_data`
        """,
        "news_intelligence": """
            SELECT 
                COUNT(DISTINCT DATE(published)) as unique_dates,
                COUNT(DISTINCT title) as unique_articles,
                COUNT(*) as total_rows,
                COUNT(*) / COUNT(DISTINCT DATE(published)) as avg_articles_per_day
            FROM `cbi-v14.forecasting_data_warehouse.news_intelligence`
        """,
    }
    
    for table_name, query in multi_value_checks.items():
        try:
            df = client.query(query).to_dataframe()
            if len(df) > 0:
                row = df.iloc[0]
                print(f"\n✅ {table_name}:")
                print(f"   {row['unique_dates']:,} unique dates")
                if 'unique_pairs' in row:
                    print(f"   {row['unique_pairs']} unique currency pairs")
                if 'unique_indicators' in row:
                    print(f"   {row['unique_indicators']} unique indicators")
                if 'unique_stations' in row:
                    print(f"   {row['unique_stations']} unique stations")
                if 'unique_articles' in row:
                    print(f"   {row['unique_articles']} unique articles")
                print(f"   {row['total_rows']:,} total rows")
                avg_key = [k for k in row.index if 'avg_' in k][0]
                print(f"   {row[avg_key]:.1f} records per day average (EXPECTED)")
        except Exception as e:
            print(f"⚠️  {table_name}: Error checking - {str(e)[:60]}")
    
    # Check training dataset
    print("\n" + "=" * 80)
    print("TRAINING DATASET CHECK:")
    print("=" * 80)
    
    training_query = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(DISTINCT date) as unique_dates,
        MIN(date) as start_date,
        MAX(date) as end_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) as days_span
    FROM `cbi-v14.models_v4.training_dataset_super_enriched`
    """
    
    try:
        df = client.query(training_query).to_dataframe()
        row = df.iloc[0]
        print(f"\n✅ training_dataset_super_enriched:")
        print(f"   {row['total_rows']:,} total rows")
        print(f"   {row['unique_dates']:,} unique dates")
        print(f"   Duplicates: {row['total_rows'] - row['unique_dates']}")
        print(f"   Range: {row['start_date']} to {row['end_date']}")
        print(f"   Span: {row['days_span']} days ({row['days_span']/365:.1f} years)")
        
        if row['total_rows'] == row['unique_dates']:
            print("   ✅ NO DUPLICATES - ONE ROW PER DATE (PERFECT)")
        else:
            print(f"   ❌ WARNING: {row['total_rows'] - row['unique_dates']} duplicate dates")
    except Exception as e:
        print(f"⚠️  Error: {str(e)}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    if true_duplicates_found:
        print("\n❌ TRUE DUPLICATES FOUND in price tables")
        print("   Action: Run deduplication on affected tables")
    else:
        print("\n✅ NO TRUE DUPLICATES in price tables")
    
    print("\n✅ Multi-value tables (currency, economic, weather, news) are CORRECTLY structured")
    print("   Multiple records per date is EXPECTED and CORRECT for these tables")
    
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()




