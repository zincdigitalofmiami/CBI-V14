# How to Load Your 2-Year Palm Oil CSV Data

**Updated:** October 7, 2025  
**Tool:** `cbi-v14-ingestion/csv_data_loader.py` (already exists and updated)

---

## ✅ **LOADER IS READY**

I've updated `csv_data_loader.py` to handle palm oil data:
- Added FCPO routing to `palm_oil_prices` table
- Added canonical metadata (source_name, confidence_score, provenance_uuid)

---

## 📋 **STEP-BY-STEP INSTRUCTIONS:**

### **Step 1: Place Your CSV File**

Put your 2-year palm oil CSV in this directory:
```bash
/Users/zincdigital/CBI-V14/data/csv/
```

**Naming:** File name should contain "FCPO" or "PALM" (e.g., `FCPO_price-history.csv`)

### **Step 2: Verify CSV Format**

Your CSV should have these columns (any of these names work):
```
Time, Open, High, Low, Last (or Close), Volume
```

**Example:**
```
Time,Open,High,Low,Last,Volume
2023-01-03,1050.00,1055.00,1048.00,1052.00,12500
2023-01-04,1052.00,1058.00,1050.00,1056.00,14200
...
```

### **Step 3: Dry Run (See What Will Happen)**

```bash
cd /Users/zincdigital/CBI-V14
python3 cbi-v14-ingestion/csv_data_loader.py --dry-run
```

**Expected output:**
```
MAP: FCPO_price-history.csv → symbol=FC → table=cbi-v14.forecasting_data_warehouse.palm_oil_prices rows=730
```

### **Step 4: Load the Data**

```bash
python3 cbi-v14-ingestion/csv_data_loader.py --load --only-symbols=FC
```

**This will:**
- Load your 2-year palm oil CSV
- Add canonical metadata automatically
- Append to `palm_oil_prices` table
- Show row count when complete

### **Step 5: Verify Data Loaded**

```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='cbi-v14')
query = '''
SELECT 
    COUNT(*) as total_rows,
    MIN(DATE(time)) as earliest,
    MAX(DATE(time)) as latest,
    COUNT(DISTINCT symbol) as symbols
FROM \`cbi-v14.forecasting_data_warehouse.palm_oil_prices\`
WHERE source_name = \"Barchart\"
'''
print(client.query(query).to_dataframe())
"
```

**Expected:**
```
total_rows  earliest    latest      symbols
730         2023-XX-XX  2025-XX-XX  1
```

---

## 🔧 **TROUBLESHOOTING:**

### **Problem: "No CSV files found"**
**Solution:** Check directory path
```bash
ls -la /Users/zincdigital/CBI-V14/data/csv/
```

If directory doesn't exist:
```bash
mkdir -p /Users/zincdigital/CBI-V14/data/csv/
# Then move your palm oil CSV there
```

### **Problem: "Unknown mapping for contract"**
**Solution:** Rename your CSV to include "FCPO" in the filename
```bash
# If your file is named differently:
mv your_palm_file.csv FCPO_price-history.csv
```

### **Problem: Column name mismatch**
**Solution:** The loader expects these column names:
- `Time` (or `Date`)
- `Open`, `High`, `Low`, `Last` (or `Close`)
- `Volume`

If your CSV has different names, let me know and I'll update the loader.

---

## 💡 **WHAT HAPPENS AFTER LOADING:**

Once your 2-year palm oil data is loaded (~500-730 rows):

1. ✅ **IMMEDIATE:** Soy-palm spread can be calculated
2. ✅ **IMMEDIATE:** Rolling correlations (20d, 60d, 120d)
3. ✅ **IMMEDIATE:** Percentile regime classification
4. ✅ **READY:** LightGBM training can begin (sufficient historical data)
5. ✅ **READY:** Walk-forward validation (2023-2024 train, 2025 test)

**You won't need to wait 7-14 days - you'll have 2 years of data immediately!**

---

## 📍 **YOUR CSV FILE LOCATION:**

**Put it here:**
```
/Users/zincdigital/CBI-V14/data/csv/FCPO_price-history.csv
```

**Then run:**
```bash
cd /Users/zincdigital/CBI-V14
python3 cbi-v14-ingestion/csv_data_loader.py --dry-run  # Preview
python3 cbi-v14-ingestion/csv_data_loader.py --load --only-symbols=FC  # Load
```

---

**Loader is ready. Place your CSV and run the commands above!** 🚀
