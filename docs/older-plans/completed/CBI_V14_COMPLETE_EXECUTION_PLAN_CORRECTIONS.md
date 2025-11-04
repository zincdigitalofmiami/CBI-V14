# CBI V14 Complete Execution Plan - Correction Mapping

**Date:** 2025-11-01  
**Purpose:** Surgical corrections to naming, datasets, and file paths

## Critical Dataset Replacements

### All Dataset References Must Be Changed:

| Original (In Plan) | Corrected Value |
|-------------------|----------------|
| `crystal_ball.*` | `cbi-v14.forecasting_data_warehouse.*` |
| `project.dataset.*` | `cbi-v14.forecasting_data_warehouse.*` |
| `your-project-id` | `cbi-v14` |
| `YOUR-PROJECT-ID` | `cbi-v14` |
| `[your-gcp-project-id]` | `cbi-v14` |
| `your-project` | `cbi-v14` |

### Training/Model Dataset:
| Original | Corrected |
|----------|-----------|
| `crystal_ball.training_features_master` | `cbi-v14.models_v4.training_dataset_super_enriched` |
| `crystal_ball.training_features_1w` | `cbi-v14.models_v4.training_features_1w` (or appropriate) |
| `crystal_ball.bqml_soy_1w_mean` | `cbi-v14.models_v4.bqml_soy_1w_mean` |

### Predictions Dataset:
| Original | Corrected |
|----------|-----------|
| `crystal_ball.production_forecasts` | `cbi-v14.predictions_uc1.production_forecasts` or `cbi-v14.forecasting_data_warehouse.production_forecasts` |

## File Path Corrections

### Python Files:
| Original Path | Corrected Path |
|--------------|----------------|
| `web_scraper.py` | `cbi-v14-ingestion/web_scraper.py` |
| `phase_0_data_refresh.py` | `scripts/phase_0_data_refresh.py` or `cbi-v14-ingestion/phase_0_data_refresh.py` |

### SQL Files:
| Original Path | Corrected Path |
|--------------|----------------|
| All SQL references | `bigquery_sql/` prefix |

### Next.js Files:
| Original Path | Corrected Path |
|--------------|----------------|
| `tailwind.config.ts` | `dashboard-nextjs/tailwind.config.js` (update existing) |
| `app/layout.tsx` | `dashboard-nextjs/src/app/layout.tsx` (update existing) |
| `app/globals.css` | `dashboard-nextjs/src/app/globals.css` (append to existing) |
| `components/ui/Card.tsx` | `dashboard-nextjs/src/components/ui/Card.tsx` (new) |
| `components/ui/CircularGauge.tsx` | `dashboard-nextjs/src/components/ui/CircularGauge.tsx` (new) |
| `components/ui/DataTable.tsx` | `dashboard-nextjs/src/components/ui/DataTable.tsx` (new) |
| `lib/chartConfig.ts` | `dashboard-nextjs/src/lib/chartConfig.ts` (new) |
| `components/charts/ForecastChart.tsx` | `dashboard-nextjs/src/components/charts/ForecastChart.tsx` (new) |

## Project ID Consistency

All references must use:
- **Project ID:** `cbi-v14` (lowercase, with hyphen)
- **NOT:** `your-project-id`, `YOUR-PROJECT-ID`, `project`, `[your-gcp-project-id]`

## Code Constants to Update

### Python Files:
```python
# OLD:
project_id = "your-project-id"
dataset_id = "crystal_ball"

# NEW:
PROJECT_ID = "cbi-v14"
DATASET_ID = "forecasting_data_warehouse"
```

### SQL Files:
```sql
-- OLD:
`project.dataset.table_name`
`crystal_ball.table_name`

-- NEW:
`cbi-v14.forecasting_data_warehouse.table_name`
`cbi-v14.models_v4.table_name` (for training/model tables)
```

## Cloud Function References

| Original | Corrected |
|----------|-----------|
| `https://YOUR-REGION-PROJECT.cloudfunctions.net/cbi-forecast-api` | `https://us-central1-cbi-v14.cloudfunctions.net/cbi-forecast-api` |
| `https://REGION-PROJECT_ID.cloudfunctions.net/cbi-forecast-api` | `https://us-central1-cbi-v14.cloudfunctions.net/cbi-forecast-api` |

## Vercel References

| Original | Corrected |
|----------|-----------|
| `https://cbi-YOUR-PROJECT.vercel.app` | `https://cbi-v14.vercel.app` (or actual domain) |

## Specific Table Names to Verify

All web scraping tables should use:
- Dataset: `cbi-v14.forecasting_data_warehouse`
- Table naming: snake_case (e.g., `futures_prices_barchart`)

## Verification Checklist

After applying corrections:
- [ ] Zero occurrences of `crystal_ball` in document
- [ ] Zero occurrences of `your-project-id` placeholders
- [ ] All file paths match existing directory structure
- [ ] All BigQuery references use full `cbi-v14.dataset.table` format
- [ ] Python constants match existing codebase conventions
- [ ] SQL queries reference correct datasets



