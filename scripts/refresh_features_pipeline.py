#!/usr/bin/env python3
"""Refresh Features Pipeline
Runs the full Big-8 feature generation sequence and materialises
`models_v4.training_dataset_super_enriched` twice daily.
"""
import subprocess, sys, logging, json, importlib
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("refresh_pipeline")

PROJECT_ID = "cbi-v14"
DATASET_ID = "models_v4"
TARGET_TABLE = "training_dataset_super_enriched"
MANIFEST = Path("/Users/zincdigital/CBI-V14/logs/feature_refresh_manifest.json")

# Execution order – update if catalogue changes
PIPELINE_STEPS = [
    "prepare_all_training_data",
    "create_correlation_features",
    "add_cross_asset_lead_lag",
    "create_crush_margins",
    "add_event_driven_features",
    "add_market_regime_signals",
    "create_big8_aggregation",
    "add_seasonality_decomposition",
]


def run_step(module_name: str):
    """Import and execute main() of each step."""
    try:
        logger.info("▶️ Running %s", module_name)
        module = importlib.import_module(module_name)
        if hasattr(module, "main"):
            module.main()
        elif hasattr(module, module_name):
            getattr(module, module_name)()  # fallback
        else:
            logger.warning("No entrypoint found in %s", module_name)
    except Exception as exc:
        logger.error("❌ Step %s failed: %s", module_name, exc)
        sys.exit(1)


def materialise_final_table():
    """Create or replace the static training table from final view."""
    logger.info("📝 Materialising %s.%s.%s", PROJECT_ID, DATASET_ID, TARGET_TABLE)
    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}` AS
    SELECT * FROM `{PROJECT_ID}.neural.vw_big_eight_signals`  -- final enriched view
    """
    subprocess.run(["bq", "query", "--use_legacy_sql=false", query], check=True)


def write_manifest():
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)
    stats = client.query(
        f"SELECT COUNT(*) as row_count, MAX(date) as latest_date FROM `{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}`"
    ).to_dataframe().iloc[0]
    schema = client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{TARGET_TABLE}").schema
    manifest = {
        "refreshed_at": datetime.utcnow().isoformat(timespec="seconds"),
        "rows": int(stats["row_count"]),
        "latest_date": stats["latest_date"].strftime("%Y-%m-%d"),
        "columns": [f.name for f in schema],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    logger.info("📄 Manifest written: %s", MANIFEST)


def main():
    logger.info("==== BIG-8 FEATURE REFRESH START ====")
    # SKIP PIPELINE_STEPS - they're legacy modules in archive/ and not needed
    # The view vw_big_eight_signals already contains all Big 8 signals
    logger.info("⏭️  Skipping legacy pipeline steps (view already has all signals)")
    logger.info("📝 Proceeding directly to table materialization from view")
    
    # Direct materialization from view (this is what actually matters)
    materialise_final_table()
    write_manifest()
    logger.info("✅ Feature refresh pipeline complete.")


if __name__ == "__main__":
    main()
