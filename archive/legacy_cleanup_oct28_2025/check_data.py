import pandas as pd
import sys

# Check training_dataset_final_enhanced.csv
df = pd.read_csv('training_dataset_final_enhanced.csv')

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Duplicates: {df.duplicated().sum()}")
print(f"Date duplicates: {df['date'].duplicated().sum()}")

# Check for 999 values
for col in df.columns:
    if df[col].dtype in ['float64', 'int64']:
        count = (df[col] == 999).sum()
        if count > 0:
            print(f"999 in {col}: {count}")

print("DONE")







