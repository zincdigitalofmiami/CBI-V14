---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# 🔧 DATA FORMAT ISSUE EXPLANATION

**Date**: November 16, 2025  
**Issue**: BigQuery data types incompatible with pandas

---

## ❓ THE QUESTION

**"Why is the data we have now in the external drive not usable due to BigQuery styling? I thought we had already pulled all that data in from BigQuery?"**

---

## ✅ YOU'RE CORRECT - DATA WAS ALREADY PULLED

**Yes, the data WAS already exported from BigQuery to the external drive.**

**Current Status**:
- ✅ 332 files in `TrainingData/raw/` (267MB)
- ✅ 19 files in `TrainingData/exports/` (23MB)
- ✅ Data exists and was exported from BigQuery

---

## ⚠️ THE PROBLEM: BigQuery Data Type Incompatibility

### The Issue

When data is exported from BigQuery to Parquet, it sometimes uses **BigQuery-specific data types** that pandas/pyarrow cannot read directly.

**Error Encountered**:
```
TypeError: data type 'dbdate' not understood
```

### What This Means

1. **Data EXISTS** ✅ - Files are on the external drive
2. **Data was EXPORTED** ✅ - Successfully pulled from BigQuery
3. **Data has INCOMPATIBLE TYPES** ❌ - BigQuery types like `dbdate` need conversion

### Example

**BigQuery Export**:
- Column: `date` with type `dbdate` (BigQuery-specific)
- Column: `timestamp` with type `dbdatetime` (BigQuery-specific)

**Pandas Cannot Read**:
- Pandas doesn't understand `dbdate` or `dbdatetime`
- Needs conversion to standard types: `date` → `datetime64[ns]`

---

## 🔄 THE SOLUTION: Conformance Step

### What "Conformance" Means

**Conformance** = Converting BigQuery data types to standard pandas-compatible types

**Process**:
```
BigQuery Export → raw/ (has dbdate types)
       ↓
   Conformance Script
       ↓
   staging/ (has datetime64 types) ✅ Usable by pandas
```

### Conformance Script Purpose

The `scripts/conform/validate_and_conform.py` script will:

1. **Read** parquet files from `raw/` (with BigQuery types)
2. **Convert** data types:
   - `dbdate` → `datetime64[ns]`
   - `dbdatetime` → `datetime64[ns]`
   - `dbfloat64` → `float64`
   - etc.
3. **Validate** data (ranges, duplicates, outliers)
4. **Save** to `staging/` (with standard pandas types)
5. **Quarantine** any bad data

---

## 📊 CURRENT DATA STATUS

### What We Have
- ✅ **332 files** in `raw/` - Exported from BigQuery
- ✅ **Data exists** - Historical data is there
- ⚠️ **Type issues** - Some files have `dbdate` types

### What We Need
- 🔧 **Conformance scripts** - To convert BigQuery types to pandas types
- ✅ **Processed data** - In `staging/` directory (usable by pandas)

---

## 🎯 WHY THIS MATTERS

### Scripts Need Usable Data

All our prediction scripts expect:
```python
df = pd.read_parquet("TrainingData/staging/data.parquet")  # ✅ Works
```

But currently:
```python
df = pd.read_parquet("TrainingData/raw/data.parquet")  # ❌ Fails with dbdate error
```

### The Fix

Once conformance scripts run:
- `raw/` → `staging/` conversion happens
- All data types are standard pandas types
- Scripts can read data without errors

---

## 📋 ACTION PLAN

### Phase 1: Conformance (Next Step)

1. **Create conformance scripts** (`scripts/conform/validate_and_conform.py`)
2. **Process all raw files**:
   - Read from `raw/`
   - Convert BigQuery types to pandas types
   - Validate data quality
   - Save to `staging/`
3. **Result**: All data in `staging/` is usable by pandas

### Current Workaround

If you need to use the data NOW:
```python
# Workaround: Read with pyarrow and convert types manually
import pyarrow.parquet as pq
import pandas as pd

# Read with pyarrow (handles BigQuery types)
table = pq.read_table("TrainingData/raw/data.parquet")

# Convert to pandas with type conversion
df = table.to_pandas()

# Manually fix date columns
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
```

---

## ✅ SUMMARY

**Your Understanding**: ✅ Correct - Data was already pulled from BigQuery

**The Issue**: ⚠️ BigQuery-specific data types (`dbdate`, etc.) need conversion

**The Solution**: 🔧 Conformance scripts convert types: `raw/` → `staging/`

**Status**: 
- Data exists ✅
- Needs type conversion ⚠️
- Will be fixed in Phase 1 conformance step 🔧

---

**The data IS there, it just needs type conversion to be usable by pandas!**
