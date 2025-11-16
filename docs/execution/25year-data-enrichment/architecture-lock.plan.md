<!-- 54cc6542-3f87-4cff-8720-b5d318bccad7 296fa9d9-0f21-45d0-95a7-2bc790577525 -->
# Complete 25-Year Data Enrichment - Institutional Grade

## Philosophy

**"Fully loaded, 25 years, all the fancy math, production-grade guardrails"**

- Mac M4 = compute engine (free, fast, deterministic)
- BigQuery = thin dashboard read layer only
- Staging + quarantine = no bad data reaches training
- Declarative join specs with automated tests
- QA gates block between every phase
- Single-pass feature build (efficient)
- Pre-flight harness ensures metric parity

---

## Related Plans & Documentation

**🧠 Complete System Knowledge**: See `COMPLETE_SYSTEM_KNOWLEDGE.md` for EVERYTHING you need to know:
- Core mission and architecture
- Data source structure (local drive, not BigQuery)
- Zero tolerance fake data policy
- All scripts and their purposes
- User personas (Chris, Kevin)
- Page structure and buildout status
- Key decisions and rationale
- Quick reference guide

**📋 Page Buildout Roadmap**: See `../../PAGE_BUILDOUT_ROADMAP.md` for complete dashboard page specifications, including:
- Completed pages (Dashboard, Legislative, Strategy, Vegas Intel)
- Planned pages (Sentiment page - future buildout)
- Page priority matrix
- Feature specifications

**📊 System Understanding**: See `../../SYSTEM_UNDERSTANDING_COMPLETE.md` for:
- Complete system architecture
- User personas (Chris, Kevin)
- Page structure and purposes
- Data flow diagrams

---

## Directory Structure (External Drive)

```
/Volumes/Satechi Hub/Projects/CBI-V14/
├── TrainingData/
│   ├── raw/           # Immutable source zone (API downloads, never edited)
│   ├── staging/       # Validated, conformed (units/timezones/dtypes fixed)
│   ├── features/      # Engineered signals (Big 8, tech, macro, weather)
│   ├── labels/        # Forward targets by horizon (7d, 30d, 90d, etc.)
│   ├── exports/       # Final training parquet per horizon
│   └── quarantine/    # Failed validations (human triage)
├── registry/
│   ├── feature_registry.json    # Semantic metadata (reliability, impact)
│   ├── join_spec.yaml           # Declarative joins with tests
│   └── regime_calendar.parquet  # Static regime assignments
└── scripts/
    ├── ingest/        # API pulls → raw/ (or quarantine/)
    ├── conform/       # raw/ → staging/ (validation)
    ├── features/      # staging/ → features/ (calculations)
    ├── labels/        # Date offsets → labels/
    ├── assemble/      # features + labels → exports/
    └── qa/            # Automated QA gates
```

---

## Phase 0: Setup + Forensic Inventory (2 hours)

### 0.1 Create Directory Structure

```bash
cd "/Volumes/Satechi Hub/Projects/CBI-V14"
mkdir -p TrainingData/{raw,staging,features,labels,exports,quarantine}
mkdir -p registry
mkdir -p scripts/{ingest,conform,features,labels,assemble,qa}
```

### 0.2 Forensic Audit of Existing Data

Inventory what's already on external drive, identify keep-vs-replace decisions.

**Script:** `scripts/qa/forensic_audit.py`

```python
import pandas as pd
from pathlib import Path

drive = Path("/Volumes/Satechi Hub/Projects/CBI-V14")

# Check existing exports
for f in (drive / "TrainingData/exports").glob("*.parquet"):
    df = pd.read_parquet(f)
    print(f"{f.name}: {len(df)} rows, {len(df.columns)} cols, "
          f"{df['date'].min()} to {df['date'].max()}")

# Decision: Keep yahoo_finance_comprehensive, archive old regime files
```

**Output:** Gap analysis - what to pull, what to keep.

---

## Phase 1: Data Collection with Validation (10 hours)

**Strategy:** Fill Tier 1 critical gaps. Turn watchlists into dated, numeric time series.

### Tier 1 Critical Gaps (Must-Have)

**1. China Demand Composite (8 sub-series)**

- Monthly China soy imports (FAS/USDA)
- Weekly purchase pace
- Dalian vs CBOT basis spread
- State reserve actions (Sinograin/COFCO announcements)
- China crush margins
- Hog herd size (meal demand proxy)
- ASF outbreak severity indices
- Tariff/quota event timeline

**2. Tariff Intelligence (Dated Events)**

- Section 301 timelines (announcement vs effective dates)
- Exclusion lists (product-level exemptions)
- Retaliatory schedules (China's response)
- Trade deal milestones

**3. Biofuel Policy & Prices**

- EIA biodiesel production (weekly)
- EIA renewable diesel production
- RIN prices (D4, D5, D6)
- LCFS credit prices (California/Oregon)
- Mandate paths (RFS, state LCFS, SAF, Brazil RenovaBio, Indonesia B35→B40)

**4. Substitute Oils (Full History)**

- Palm oil (FCPO/MPOB continuous series)
- Sunflower oil (Ukraine/Russia exports + prices)
- Rapeseed/canola oil (ICE/Euronext)
- Corn oil (distillers oil)
- FOB spreads between oils

### 1.1 Create Feature Registry (Metadata)

**File:** `registry/feature_registry.json`

```json
{
  "metadata_version": "1.0",
  "last_updated": "2025-11-16",
  "features": {
    "fed_funds_rate": {
      "source": "FRED:DFF",
      "reliability": 0.98,
      "policy_impact": 85,
      "category": "macro_rates",
      "update_frequency": "daily",
      "available_from": "2000-01-01"
    },
    "vix": {
      "source": "FRED:VIXCLS",
      "reliability": 0.95,
      "policy_impact": 90,
      "category": "volatility",
      "update_frequency": "daily",
      "available_from": "2000-01-01"
    },
    "feature_tariff_threat": {
      "source": "computed_big8",
      "reliability": 0.75,
      "policy_impact": 95,
      "category": "big8_signals",
      "update_frequency": "daily",
      "available_from": "2020-01-01"
    }
  }
}
```

### 1.2 Collect FRED Data (with retry logic)

**Script:** `scripts/ingest/collect_fred_historical.py`

```python
#!/usr/bin/env python3
import requests
import pandas as pd
import time
from pathlib import Path

FRED_API_KEY = "dc195c8658c46ee1df83bcd4fd8a690b"
RAW_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw")
CACHE_DIR = RAW_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

def retry_with_backoff(func, max_retries=3):
    """Retry with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                # Check cache
                cache_file = CACHE_DIR / f"{func.__name__}_last_good.pkl"
                if cache_file.exists():
                    print(f"⚠️  Using cached value from {cache_file}")
                    return pd.read_pickle(cache_file)
                raise e
            wait = 2 ** attempt
            print(f"❌ Attempt {attempt + 1} failed, retrying in {wait}s...")
            time.sleep(wait)

def fetch_fred_series(series_id, series_name):
    """Fetch with retry and caching (FIXED: env secrets + dual cache)"""
    def _fetch():
        # FIX #4: Use environment variable, not hardcoded
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            raise RuntimeError("FRED_API_KEY not set in environment")
        
        response = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={'series_id': series_id, 'api_key': api_key, 
                    'file_type': 'json', 'observation_start': '2000-01-01'}
        )
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # FIX #5: Save BOTH series-specific and last-good cache
        pd.to_pickle(df, CACHE_DIR / f"fred_{series_id}.pkl")
        pd.to_pickle(df, CACHE_DIR / f"last_good_{series_id}.pkl")
        
        return df[['date', 'value']].rename(columns={'value': series_name})
    
    # FIX #5: Check both cache locations
    def _get_cached():
        for cache_file in [CACHE_DIR / f"fred_{series_id}.pkl", 
                          CACHE_DIR / f"last_good_{series_id}.pkl"]:
            if cache_file.exists():
                return pd.read_pickle(cache_file)
        return None
    
    return retry_with_backoff(_fetch, fallback_func=_get_cached)

# FRED series to pull (30+)
FRED_SERIES = {
    'DFF': 'fed_funds_rate',
    'DGS10': 'treasury_10y',
    'DGS2': 'treasury_2y',
    'T10Y2Y': 'yield_curve_spread',
    'CPIAUCSL': 'cpi_all',
    'VIXCLS': 'vix',
    'DTWEXBGS': 'usd_broad_index',
    'DCOILWTICO': 'crude_oil_wti',
    'BALTIC': 'baltic_dry_index',
    # ... add all 30+ series
}

# Fetch all
all_series = []
for series_id, name in FRED_SERIES.items():
    df = fetch_fred_series(series_id, name)
    print(f"✅ {name}: {len(df)} rows")
    all_series.append(df)

# Merge
fred_master = all_series[0]
for df in all_series[1:]:
    fred_master = fred_master.merge(df, on='date', how='outer')

# Save to raw
fred_master.to_parquet(RAW_DIR / "fred_macro_2000_2025.parquet")
print(f"✅ Saved: {len(fred_master)} rows × {len(fred_master.columns)} cols")
```

### 1.3 Conformance & Validation (raw → staging)

**Script:** `scripts/conform/validate_and_conform.py`

```python
#!/usr/bin/env python3
"""
Validate raw data and conform to staging.
Failed rows → quarantine for human review.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/raw")
STAGING_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/staging")
QUARANTINE_DIR = Path("/Volumes/Satechi Hub/Projects/CBI-V14/TrainingData/quarantine")

def validate_range(df, col, min_val, max_val):
    """Check value ranges"""
    mask = (df[col] < min_val) | (df[col] > max_val)
    return df[~mask], df[mask]

def validate_jumps(df, col, threshold=0.30):
    """Flag >30% jumps"""
    pct_change = df[col].pct_change().abs()
    mask = pct_change > threshold
    return df[~mask], df[mask]

def conform_fred_data():
    """Conform FRED data to staging"""
    df = pd.read_parquet(RAW_DIR / "fred_macro_2000_2025.parquet")
    
    quarantined = pd.DataFrame()
    
    # Validate VIX range (0-100)
    if 'vix' in df.columns:
        df_clean, df_bad = validate_range(df, 'vix', 0, 150)
        if len(df_bad) > 0:
            df_bad['quarantine_reason'] = 'vix_out_of_range'
            quarantined = pd.concat([quarantined, df_bad])
            df = df_clean
    
    # Validate sudden jumps in fed_funds_rate
    if 'fed_funds_rate' in df.columns:
        df_clean, df_bad = validate_jumps(df, 'fed_funds_rate', 0.20)
        if len(df_bad) > 0:
            df_bad['quarantine_reason'] = 'fed_rate_jump_>20pct'
            quarantined = pd.concat([quarantined, df_bad])
            df = df_clean
    
    # Check for duplicates
    dups = df[df.duplicated(subset=['date'], keep=False)]
    if len(dups) > 0:
        dups['quarantine_reason'] = 'duplicate_date'
        quarantined = pd.concat([quarantined, dups])
        df = df.drop_duplicates(subset=['date'], keep='first')
    
    # Save clean data to staging
    df.to_parquet(STAGING_DIR / "fred_macro_2000_2025.parquet")
    print(f"✅ Staging: {len(df)} rows passed validation")
    
    # Save quarantined data
    if len(quarantined) > 0:
        quarantined.to_parquet(QUARANTINE_DIR / f"fred_quarantine_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.parquet")
        print(f"⚠️  Quarantine: {len(quarantined)} rows ({quarantined['quarantine_reason'].value_counts().to_dict()})")
    
    return df

# Run for all raw sources
conform_fred_data()
# conform_noaa_data()
# conform_cftc_data()
# ...
```

**QA Gate:** Block Phase 2 if >10% of data quarantined.

---

[Content continues for all 1335 lines...]
