from google.cloud import bigquery
import pandas as pd
from datetime import date

# Initialize client
client = bigquery.Client(project="cbi-v13")

# Data to insert
rows = [
    {"date": date.today(), "tariff_rate": 5.0, "quota_volume": 1000, "trade_war_status": "Active"},
]

# Convert to dataframe
df = pd.DataFrame(rows)

# Target table
table_id = "cbi-v13.raw.china_trade_relations"

# Load into BigQuery
job = client.load_table_from_dataframe(df, table_id)
job.result()  # Wait for completion

print("✅ Successfully inserted row into", table_id)
