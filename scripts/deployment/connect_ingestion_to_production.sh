#!/bin/bash
#
# Connect all ingestion scripts to production_training_data_* tables
# This is a TEMPLATE - shows what needs to be done
#

PROJECT_ROOT="/Users/zincdigital/CBI-V14"

echo "================================================================================"
echo "INGESTION → PRODUCTION DATASET CONNECTION PLAN"
echo "================================================================================"
echo ""
echo "The following scripts need to be modified to UPDATE production_training_data_*:"
echo ""
echo "1. scripts/hourly_prices.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "2. scripts/daily_weather.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "3. ingestion/ingest_social_intelligence_comprehensive.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "4. ingestion/backfill_trump_intelligence.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "5. ingestion/ingest_market_prices.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "6. ingestion/ingest_cftc_positioning_REAL.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "7. ingestion/ingest_usda_harvest_api.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "8. ingestion/ingest_eia_biofuel_real.py"
echo "   → Add INSERT/UPDATE to production_training_data_1w/1m/3m/6m"
echo ""
echo "================================================================================"
echo "IMPLEMENTATION PATTERN"
echo "================================================================================"
echo ""
echo "Each ingestion script should:"
echo "  1. Load data from source API"
echo "  2. Process/transform data"
echo "  3. INSERT/UPDATE forecasting_data_warehouse.* (existing)"
echo "  4. ALSO UPDATE production_training_data_* tables (NEW)"
echo ""
echo "Example pattern in Python:"
echo ""
cat << 'EOF'
from google.cloud import bigquery

def update_production_datasets(date, features_dict):
    """
    Update all 4 production datasets with new features
    
    Args:
        date: DATE for this row
        features_dict: Dictionary of column_name: value
    """
    client = bigquery.Client(project='cbi-v14')
    
    # Build UPDATE or INSERT for each production table
    for horizon in ['1w', '1m', '3m', '6m']:
        table_id = f'cbi-v14.models_v4.production_training_data_{horizon}'
        
        # Check if row exists
        check_query = f"""
        SELECT COUNT(*) as exists
        FROM `{table_id}`
        WHERE date = '{date}'
        """
        result = client.query(check_query).to_dataframe()
        
        if result.iloc[0]['exists'] > 0:
            # UPDATE existing row
            set_clauses = [f"{col} = {val}" for col, val in features_dict.items()]
            update_query = f"""
            UPDATE `{table_id}`
            SET {', '.join(set_clauses)}
            WHERE date = '{date}'
            """
            client.query(update_query).result()
        else:
            # INSERT new row
            columns = ['date'] + list(features_dict.keys())
            values = [f"'{date}'"] + [str(v) for v in features_dict.values()]
            insert_query = f"""
            INSERT INTO `{table_id}` ({', '.join(columns)})
            VALUES ({', '.join(values)})
            """
            client.query(insert_query).result()
        
        print(f"✅ Updated {table_id} for {date}")
EOF
echo ""
echo "================================================================================"
echo "NEXT STEPS"
echo "================================================================================"
echo ""
echo "1. Modify each ingestion script to call update_production_datasets()"
echo "2. Test each script individually"
echo "3. Verify production_training_data_* tables are being updated"
echo "4. Monitor for 1 week to ensure daily updates working"
echo ""
echo "================================================================================"








