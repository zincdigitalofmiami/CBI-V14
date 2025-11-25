# Cursor Rules for CBI-V14
# These rules help AI assistants understand what's CURRENT vs LEGACY

## CRITICAL: Read First
1. ALWAYS read `docs/plans/GPT_READ_FIRST.md` before starting work
2. Use `docs/plans/MASTER_PLAN.md` and `docs/plans/TRAINING_PLAN.md` as sources of truth
3. IGNORE everything in `archive/` and `legacy/` directories
4. Review `docs/reference/BEST_PRACTICES_DRAFT.md` for comprehensive best practices

## Current Architecture
- Training: Local M4 Mac → Vertex AI deployment
- NOT: BQML training, AutoML, cloud-first
- Source of Truth: `docs/plans/TRAINING_MASTER_EXECUTION_PLAN.md`

## Legacy Work (DO NOT USE)
- Everything in `archive/` directory
- Everything in `legacy/` directory
- BQML training plans (we use Vertex AI now)
- AutoML references (we use custom neural models)

## Current Files (USE THESE)
- `scripts/data_quality_checks.py`
- `scripts/export_training_data.py`
- `src/training/baselines/*.py`
- `vertex-ai/deployment/*.py`

## Before Referencing Any File
- Check if it's in `archive/` → IGNORE
- Check if it's in `legacy/` → IGNORE
- Check if it mentions BQML → IGNORE
- Check if it mentions AutoML → IGNORE

---

## BEST PRACTICES (MANDATORY)

### 🔴 CRITICAL RULES (Must Always Follow)

#### Data Quality
1. **NO FAKE DATA** - NEVER use placeholders, synthetic data, or fake values. ONLY use real, verified data from authenticated APIs or official sources.
2. **ALWAYS CHECK BEFORE CREATING** - Before creating ANY table/schema/dataset/folder/file, check if it already exists. Verify naming conventions, check for duplicates, validate schema compatibility.
3. **ALWAYS AUDIT AFTER WORK** - After ANY data modification, run data quality checks. Audit for errors, nulls, duplicates, gaps. Verify row counts, date ranges, value ranges.

#### Cost & Resource Management
4. **us-central1 ONLY** - ALL BigQuery datasets, GCS buckets, and GCP resources MUST be in us-central1. NEVER create resources in US multi-region or other regions. See `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` - AI created ~$250/month mistake.
5. **NO COSTLY RESOURCES WITHOUT APPROVAL** - Do NOT create Cloud SQL, Cloud Workstations, Compute Engine, Vertex AI endpoints, or any paid GCP resources without explicit user approval. Estimate costs if > $5/month and ask for approval.

#### Research & Validation
6. **RESEARCH BEST PRACTICES** - ALWAYS research online for best practices before implementing. Verify current practices (not outdated), cite sources, compare approaches, validate against industry standards.
7. **RESEARCH QUANT FINANCE** - For modeling features, research quant finance best practices. Study academic papers, industry standards, proven methodologies. Validate formulas against authoritative sources.

### 🟡 HIGH PRIORITY (Should Always Follow)

#### Pre-Work Validation
- **Check existing resources** - Tables, schemas, datasets, folders, wiring before creating/modifying
- **Validate naming conventions** - Follow `{asset}_{function}_{scope}_{regime}_{horizon}` pattern
- **Verify schema compatibility** - Before merging/joining data
- **Review existing patterns** - Don't reinvent, follow codebase patterns

#### Post-Work Validation
- **Run data quality checks** - Use `scripts/data_quality_checks.py` after data modifications
- **Test queries/scripts** - Verify they work before declaring success
- **Validate BigQuery views/tables** - Ensure accessible and correct
- **Audit for errors** - Check logs, verify outputs, test edge cases

#### Code Quality
- **Test all code** - Before committing, validate error handling, verify logging
- **Document complex logic** - Explain why, not just what. Cite sources for formulas
- **Follow naming conventions** - Use source prefixes (`databento_`, `yahoo_`, `fred_`)
- **No hardcoded values** - Use config/env variables, Keychain for API keys

### 🟢 MEDIUM PRIORITY (Best Practices)

#### Data Engineering
- **Idempotent pipelines** - Safe to re-run, proper error handling and retries
- **Preserve source data** - Never modify raw layer, track data lineage
- **Validate transformations** - Test with known inputs/outputs, document logic
- **Feature engineering** - Validate calculations, test edge cases, audit importance

#### Model Development
- **Pre-training validation** - Run 24-audit suite (`config/bigquery/bigquery-sql/24_AUDIT_SUITE.sql`)
- **Local training only** - Use M4 Mac, NOT Vertex AI, NOT BQML
- **Post-training validation** - Evaluate on holdout set, validate predictions, audit SHAP
- **Save metadata** - Version, hyperparameters, performance metrics

#### Integration & Deployment
- **Pre-integration checks** - Run audit framework, validate schema, check conflicts
- **Test in staging** - Before production, validate all queries/scripts
- **Rollback planning** - Always have rollback plan, backup critical data, test procedures

#### Monitoring & Maintenance
- **Monitor data quality** - Daily automated checks, track model performance
- **Clean up resources** - Temporary files, test data, old backups
- **Review costs** - Monthly GCP billing, BigQuery usage audits
- **Update documentation** - When code changes, maintain README files

#### Security
- **API keys in Keychain** - Use `src/utils/keychain_manager.py`, NEVER hardcode
- **Proper IAM roles** - Least privilege, isolate sensitive data (MES private, ZL public)
- **Audit access** - Track who accessed what, validate permissions

---

## WORKFLOW CHECKLIST

### Before Starting Work
- [ ] Read `docs/plans/GPT_READ_FIRST.md`
- [ ] Check existing resources (tables, datasets, files)
- [ ] Research best practices for the task
- [ ] Verify naming conventions
- [ ] Estimate costs if creating GCP resources

### During Work
- [ ] Follow existing patterns in codebase
- [ ] Use source prefixes for columns
- [ ] Document complex logic
- [ ] Test code as you write
- [ ] Validate data at each stage

### After Work
- [ ] Run data quality checks
- [ ] Audit for errors (nulls, duplicates, gaps)
- [ ] Test queries/scripts
- [ ] Verify BigQuery views/tables
- [ ] Update documentation
- [ ] Clean up temporary resources

---

## QUICK REFERENCE

### Cost Lessons
- See `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` - AI created ~$250/month mistake
- Always use us-central1, never US multi-region
- Get approval for any resource > $5/month

### Data Quality
- No placeholders (0.5, 1.0, all-same values)
- Quarantine suspicious data, never delete
- Validate at raw → curated → training stages

### BigQuery Best Practices
- Partition on date columns
- Cluster on frequently filtered columns
- Limit query date ranges
- Monitor query costs (stay under 1 TB/month)

### Model Training
- Run 24-audit suite before training
- Use local M4 Mac only
- Validate training data quality
- Save models with proper metadata

---

## RELATED DOCUMENTATION
- `docs/plans/MASTER_PLAN.md` - Source of truth
- `docs/plans/TRAINING_PLAN.md` - Training strategy
- `docs/reference/BEST_PRACTICES_DRAFT.md` - Detailed best practices
- `docs/reports/costs/AI_MIGRATION_NIGHTMARE.md` - Cost lessons learned

