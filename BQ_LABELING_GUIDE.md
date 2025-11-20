---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# BigQuery Dataset Labeling Guide
**Date:** November 18, 2025  
**Purpose:** Organization and discovery of 12 BigQuery datasets

---

## 🏷️ Label Schema

All datasets are labeled with 4 dimensions:

### 1. **tier** - Data Processing Level
- `raw` - Original data from external sources
- `derived` - Calculated/processed data
- `ml` - Machine learning features and training
- `production` - Live predictions and forecasts
- `ops` - Infrastructure and operations

### 2. **category** - Functional Domain
- `market` - Market/price data
- `intelligence` - Fundamental/macro data
- `signals` - Trading signals
- `classification` - Regime classification
- `analysis` - Driver analysis
- `features` - Feature engineering
- `training` - Training data
- `neural` - Neural network data
- `forecasts` - Predictions
- `monitoring` - Performance tracking
- `reference` - Metadata/dimensions
- `operations` - Operational logs

### 3. **purpose** - Use Case
- `trading` - Trading decisions
- `regime` - Regime identification
- `drivers` - Driver analysis
- `training` - Model training
- `export` - Training exports
- `serving` - Live predictions
- `observability` - Monitoring
- `metadata` - Reference data
- `logging` - Operational logs

### 4. **data_type** - Data Characteristics
- `ohlcv` - Price data
- `fundamental` - Macro/fundamental
- `calculated` - Derived calculations
- `categorical` - Classification data
- `analytical` - Analysis outputs
- `engineered` - Feature engineering
- `labeled` - Training labels
- `vectors` - Neural vectors
- `predictions` - Forecast outputs
- `metrics` - Performance metrics
- `dimensional` - Reference dimensions
- `operational` - Operations data

---

## 📊 Dataset Label Mapping

### Tier 1: Raw Data Collection

| Dataset | tier | category | purpose | data_type |
|---------|------|----------|---------|-----------|
| `market_data` | raw | market | trading | ohlcv |
| `raw_intelligence` | raw | intelligence | training | fundamental |

### Tier 2: Derived/Processed

| Dataset | tier | category | purpose | data_type |
|---------|------|----------|---------|-----------|
| `signals` | derived | signals | trading | calculated |
| `regimes` | derived | classification | regime | categorical |
| `drivers` | derived | analysis | drivers | analytical |

### Tier 3: Machine Learning

| Dataset | tier | category | purpose | data_type |
|---------|------|----------|---------|-----------|
| `features` | ml | features | training | engineered |
| `training` | ml | training | export | labeled |
| `neural` | ml | neural | training | vectors |

### Tier 4: Production

| Dataset | tier | category | purpose | data_type |
|---------|------|----------|---------|-----------|
| `predictions` | production | forecasts | serving | predictions |

### Tier 5: Infrastructure

| Dataset | tier | category | purpose | data_type |
|---------|------|----------|---------|-----------|
| `monitoring` | ops | monitoring | observability | metrics |
| `dim` | ops | reference | metadata | dimensional |
| `ops` | ops | operations | logging | operational |

---

## 🚀 Usage

### Apply Labels

```bash
# Apply labels to all datasets
./scripts/deployment/apply_bq_labels.sh
```

### Query by Labels

```bash
# List all ML datasets
bq ls --project_id=cbi-v14 --filter 'labels.tier:ml'

# List all production datasets
bq ls --project_id=cbi-v14 --filter 'labels.tier:production'

# List all training-related datasets
bq ls --project_id=cbi-v14 --filter 'labels.purpose:training'

# List all datasets with calculated data
bq ls --project_id=cbi-v14 --filter 'labels.data_type:calculated'
```

### View Labels in Console

In the BigQuery console, labels appear as tags on each dataset:
- Navigate to BigQuery → Select dataset → Details tab → Labels section

### Filter in Console

Use the filter bar in BigQuery console:
- Click "Filter" → "Labels" → Select label key/value

---

## 🎨 Visual Organization

### By Tier (Recommended View)

```
📊 RAW (2 datasets)
├── market_data
└── raw_intelligence

⚙️ DERIVED (3 datasets)
├── signals
├── regimes
└── drivers

🤖 ML (3 datasets)
├── features
├── training
└── neural

🚀 PRODUCTION (1 dataset)
└── predictions

🔧 OPS (3 datasets)
├── monitoring
├── dim
└── ops
```

### By Purpose (Alternative View)

```
📈 TRADING
├── market_data (raw)
└── signals (derived)

🎓 TRAINING
├── raw_intelligence (raw)
├── features (ml)
├── training (ml)
└── neural (ml)

🔮 SERVING
└── predictions (production)

📊 OPERATIONS
├── monitoring (ops)
├── dim (ops)
└── ops (ops)
```

---

## 🔍 Discovery Patterns

### Find Raw Data Sources

```bash
bq ls --filter 'labels.tier:raw'
# Returns: market_data, raw_intelligence
```

### Find Training Data

```bash
bq ls --filter 'labels.purpose:training'
# Returns: raw_intelligence, features, training, neural
```

### Find Production-Ready Data

```bash
bq ls --filter 'labels.tier:production OR labels.tier:ops'
# Returns: predictions, monitoring, dim, ops
```

### Find Calculated/Derived Data

```bash
bq ls --filter 'labels.data_type:calculated OR labels.data_type:analytical'
# Returns: signals, drivers
```

---

## 🔄 Label Lifecycle

### Initial Application
- Labels applied during deployment via `apply_bq_labels.sh`
- Run automatically as part of deployment sequence

### Maintenance
- Labels persist across schema changes
- Update labels if dataset purpose changes
- Review labels quarterly for accuracy

### Adding New Datasets
When adding new datasets, follow the labeling convention:

```bash
# Example: New dataset for alternative data
bq update --project_id=cbi-v14 \
          --set_label tier:raw \
          --set_label category:intelligence \
          --set_label purpose:training \
          --set_label data_type:alternative \
          alt_data
```

---

## 📋 Benefits

### 1. **Organization**
- 12 datasets organized into 5 clear tiers
- Easy to understand data flow: raw → derived → ml → production

### 2. **Discovery**
- Find relevant datasets quickly using filters
- Identify dataset purpose at a glance

### 3. **Governance**
- Clear data lineage (tier indicates processing level)
- Easier to set access controls by tier/purpose

### 4. **Cost Management**
- Track costs by tier (raw vs. derived)
- Identify expensive ML vs. cheap reference data

### 5. **Documentation**
- Self-documenting architecture
- New team members understand structure immediately

---

## 🎯 Best Practices

### Do:
- ✅ Apply labels during initial deployment
- ✅ Use consistent label values across datasets
- ✅ Review labels when dataset purpose changes
- ✅ Use labels for access control policies
- ✅ Document custom labels in this guide

### Don't:
- ❌ Create labels with spaces or special characters
- ❌ Use more than 64 key-value pairs per dataset
- ❌ Change label schema without updating documentation
- ❌ Forget to label new datasets

---

## 📚 Reference

### BigQuery Label Limits
- Max labels per dataset: 64
- Max label key length: 63 characters
- Max label value length: 63 characters
- Allowed characters: lowercase letters, numbers, hyphens, underscores

### Standard Label Keys (CBI-V14)
- `tier` - Required
- `category` - Required
- `purpose` - Required
- `data_type` - Required
- `owner` - Optional (team/person responsible)
- `env` - Optional (prod/dev/test)
- `cost_center` - Optional (for billing)

---

**Last Updated:** November 18, 2025  
**Script:** `scripts/deployment/apply_bq_labels.sh`  
**Status:** Production-ready





