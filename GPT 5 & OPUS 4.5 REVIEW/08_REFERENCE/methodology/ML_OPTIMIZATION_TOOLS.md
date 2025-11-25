---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# ML Optimization Tools for M4 Mac Mini - CBI-V14

## ✅ Tools We're Installing (Recommended)

### 1. **Polars** ⭐ HIGHLY RECOMMENDED
- **Why**: Your codebase has 57+ files using pandas. Polars is 2-10x faster with similar API.
- **Use Case**: Replace pandas in data processing scripts for faster execution
- **Example**: 
  ```python
  import polars as pl
  df = pl.read_csv("large_file.csv")  # Much faster than pandas
  ```

### 2. **DuckDB** ⭐ HIGHLY RECOMMENDED
- **Why**: Perfect for querying large datasets on external drive without loading into memory
- **Use Case**: Analyze CSV/Parquet files directly on external drive
- **Example**:
  ```python
  import duckdb
  conn = duckdb.connect("$CBI_V14_TRAINING_DATA/cbi_v14_data.duckdb")
  result = conn.execute("SELECT * FROM 'large_file.csv' WHERE price > 50").df()
  ```

### 3. **DVC (Data Version Control)** ⚠️ OPTIONAL
- **Why**: Version large training datasets that Git can't handle
- **Use Case**: Track changes to training datasets, models, and data pipelines
- **Note**: Only needed if you want to version large files (>100MB)

### 4. **MLflow** ⚠️ OPTIONAL
- **Why**: Track experiments, parameters, and models
- **Use Case**: If you do local model training (beyond BQML)
- **Note**: You primarily use BQML, so this is optional

### 5. **htop / bpytop** ✅ RECOMMENDED
- **Why**: Monitor CPU, GPU, memory during training
- **Use Case**: Real-time system monitoring
- **Usage**: `bpytop` (press 'g' for GPU view)

## ❌ Tools We're NOT Installing (Not Needed)

### 1. **MLX** - Not Needed
- **Why**: You're committed to TensorFlow Metal, which is already optimized for Apple Silicon
- **Alternative**: TensorFlow Metal provides GPU/Neural Engine acceleration

### 2. **Core ML** - Not Needed
- **Why**: You use BQML (cloud) and TensorFlow Metal (local), not Core ML
- **Use Case**: Only if you were building iOS/macOS apps with ML

### 3. **GCS FUSE** - Not Needed
- **Why**: You use BigQuery API directly, which is more efficient
- **Alternative**: Direct `gsutil` or BigQuery API calls are faster

## 🎯 What This Means for Your Workflow

### Current Workflow (Pandas)
```python
import pandas as pd
df = pd.read_csv("large_file.csv")  # Slow, loads into memory
result = df[df['price'] > 50]  # Memory intensive
```

### Optimized Workflow (Polars + DuckDB)
```python
# Option 1: Polars (faster pandas)
import polars as pl
df = pl.read_csv("large_file.csv")  # 2-10x faster
result = df.filter(pl.col('price') > 50)  # More efficient

# Option 2: DuckDB (query without loading)
import duckdb
conn = duckdb.connect()
result = conn.execute("""
    SELECT * FROM read_csv('large_file.csv') 
    WHERE price > 50
""").df()  # Never loads full file into memory
```

## 📊 Performance Expectations

| Tool | Speedup | Memory | Use When |
|------|---------|--------|----------|
| **Polars** | 2-10x faster | Similar | Replacing pandas in scripts |
| **DuckDB** | 10-100x faster | Much lower | Querying large files on external drive |
| **TensorFlow Metal** | GPU acceleration | Optimized | Local model training |

## 🚀 Quick Start

After running `setup_new_machine.sh`, test the tools:

```bash
# Test Polars
python3 -c "import polars as pl; print('Polars:', pl.__version__)"

# Test DuckDB
python3 -c "import duckdb; print('DuckDB:', duckdb.__version__)"

# Test TensorFlow Metal GPU
python3 -c "import tensorflow as tf; gpus = tf.config.list_physical_devices('GPU'); print('GPU:', gpus)"

# Monitor system
bpytop  # Press 'g' for GPU view
```

## 💡 Migration Strategy

### Phase 1: Keep Pandas, Add Polars
- Install Polars alongside pandas
- Test Polars on new scripts
- Compare performance

### Phase 2: Migrate High-Impact Scripts
- Identify slow pandas operations (check logs)
- Migrate to Polars for 2-10x speedup
- Keep pandas for compatibility

### Phase 3: Use DuckDB for Large Files
- For files >1GB on external drive
- Use DuckDB to query without loading
- Saves memory and time

## 📝 Notes

- **TensorFlow Metal** is already optimized for M4 Mac Mini
- **BigQuery** remains primary data source (cloud)
- **External drive** stores training data for CPU optimization
- **Monitoring tools** help ensure GPU is being used

---

**Bottom Line**: Polars and DuckDB will significantly speed up your data processing. The other tools are optional but useful for specific use cases.

