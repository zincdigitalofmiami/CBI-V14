# CBI-V14 Best Practices - Draft for Review

**Date:** November 2025  
**Status:** DRAFT - Awaiting approval before adding to .cursorrules

---

## 📋 PROPOSED BEST PRACTICES

### 1. Data Quality & Validation

#### 1.1 No Fake Data (CRITICAL)
- ✅ **NEVER** use placeholders, synthetic data, or fake values
- ✅ **ONLY** use real, verified data from authenticated APIs or official sources
- ✅ **VALIDATE** all data sources before ingestion
- ✅ **QUARANTINE** suspicious data, never delete (move to `raw_intelligence.quarantine_*`)
- ✅ **AUDIT** for placeholder values (0.5, 1.0, all-same values) before training

#### 1.2 Pre-Creation Validation
- ✅ **ALWAYS** check for existing tables/schemas/datasets/folders before creating
- ✅ **VERIFY** naming conventions match project standards (`{asset}_{function}_{scope}_{regime}_{horizon}`)
- ✅ **CHECK** for duplicate resources (tables, datasets, files)
- ✅ **VALIDATE** schema compatibility before merging/joining
- ✅ **REVIEW** existing wiring/connections before modifying

#### 1.3 Post-Work Auditing
- ✅ **ALWAYS** run data quality checks after any data modification
- ✅ **AUDIT** for errors, nulls, duplicates, gaps after work
- ✅ **VERIFY** row counts, date ranges, value ranges match expectations
- ✅ **TEST** queries/scripts before declaring success
- ✅ **VALIDATE** BigQuery views/tables are accessible and correct

---

### 2. Research & Best Practices

#### 2.1 Online Research Requirements
- ✅ **ALWAYS** research online for best practices before implementing
- ✅ **VERIFY** current best practices (not outdated tutorials)
- ✅ **CITE** sources when implementing new patterns
- ✅ **COMPARE** multiple approaches before choosing
- ✅ **VALIDATE** against industry standards (quant finance, data engineering)

#### 2.2 Quant Finance Modeling Research
- ✅ **RESEARCH** quant finance modeling best practices for each new feature
- ✅ **STUDY** academic papers, industry standards, proven methodologies
- ✅ **VALIDATE** mathematical formulas against authoritative sources
- ✅ **REVIEW** similar implementations in production systems
- ✅ **CONSULT** domain experts' work (papers, blogs, documentation)

#### 2.3 Architecture Patterns
- ✅ **FOLLOW** existing patterns in codebase (don't reinvent)
- ✅ **RESEARCH** BigQuery best practices for data warehousing
- ✅ **STUDY** time-series forecasting best practices
- ✅ **REVIEW** feature engineering patterns for commodities
- ✅ **VALIDATE** against project's architecture (local training, BigQuery storage)

---

### 3. Cost & Resource Management

#### 3.1 GCP Resource Creation
- ✅ **NEVER** create Cloud SQL, Cloud Workstations, Compute Engine, Vertex AI endpoints without explicit approval
- ✅ **ALWAYS** use us-central1 region (NEVER US multi-region or other regions)
- ✅ **ESTIMATE** costs before creating any paid resource
- ✅ **ASK** for approval if cost > $5/month
- ✅ **CLEAN UP** all resources after testing/experimentation

#### 3.2 BigQuery Best Practices
- ✅ **USE** partitioning on date columns (reduces query costs)
- ✅ **USE** clustering on frequently filtered columns
- ✅ **LIMIT** query date ranges (don't scan full history unless needed)
- ✅ **CACHE** results when possible (dashboard queries)
- ✅ **MONITOR** query costs (stay under 1 TB/month free tier)

#### 3.3 Storage Management
- ✅ **CLEAN UP** temporary files, test datasets, backup tables
- ✅ **ARCHIVE** old data instead of deleting (move to `z_archive_*`)
- ✅ **COMPRESS** large files (Parquet with snappy compression)
- ✅ **MONITOR** storage growth (BigQuery, external drive, GCS)

---

### 4. Code Quality & Standards

#### 4.1 Code Review & Testing
- ✅ **TEST** all code before committing
- ✅ **VALIDATE** error handling (don't silently fail)
- ✅ **VERIFY** logging is informative (not just print statements)
- ✅ **CHECK** for hardcoded values (use config/env variables)
- ✅ **REVIEW** code for security issues (API keys, credentials)

#### 4.2 Documentation
- ✅ **DOCUMENT** complex logic, formulas, decisions
- ✅ **UPDATE** documentation when code changes
- ✅ **CITE** sources for mathematical formulas
- ✅ **EXPLAIN** why, not just what
- ✅ **LINK** to related documentation

#### 4.3 Naming & Organization
- ✅ **FOLLOW** project naming conventions exactly
- ✅ **USE** source prefixes for all columns (`databento_`, `yahoo_`, `fred_`)
- ✅ **ORGANIZE** files in correct directories (don't scatter)
- ✅ **NAME** variables/functions descriptively
- ✅ **AVOID** abbreviations unless standard (ZL, MES, FRED are OK)

---

### 5. Data Engineering Best Practices

#### 5.1 Data Pipeline Design
- ✅ **DESIGN** pipelines to be idempotent (safe to re-run)
- ✅ **IMPLEMENT** proper error handling and retries
- ✅ **LOG** all pipeline steps (start, progress, completion, errors)
- ✅ **VALIDATE** data at each stage (raw → curated → training)
- ✅ **MONITOR** pipeline health (latency, failures, data quality)

#### 5.2 Data Transformation
- ✅ **PRESERVE** source data (never modify raw layer)
- ✅ **TRACK** data lineage (where data came from, how transformed)
- ✅ **VALIDATE** transformations (test with known inputs/outputs)
- ✅ **DOCUMENT** transformation logic (SQL comments, Python docstrings)
- ✅ **VERSION** transformation scripts (git, not in code)

#### 5.3 Feature Engineering
- ✅ **VALIDATE** feature calculations against known values
- ✅ **TEST** edge cases (nulls, zeros, extreme values)
- ✅ **DOCUMENT** feature definitions (what, why, how calculated)
- ✅ **VERIFY** feature distributions (no unexpected spikes/drops)
- ✅ **AUDIT** feature importance (SHAP, correlation analysis)

---

### 6. Model Development Best Practices

#### 6.1 Pre-Training Validation
- ✅ **RUN** 24-audit suite before training (`config/bigquery/bigquery-sql/24_AUDIT_SUITE.sql`)
- ✅ **VALIDATE** training data quality (no placeholders, proper regimes, date coverage)
- ✅ **VERIFY** feature completeness (all expected columns present)
- ✅ **CHECK** target variable quality (no nulls, reasonable ranges)
- ✅ **AUDIT** regime weights (50-5000 scale, proper distribution)

#### 6.2 Training Best Practices
- ✅ **USE** local M4 Mac for training (NOT Vertex AI, NOT BQML)
- ✅ **SAVE** models with proper metadata (version, hyperparameters, performance)
- ✅ **TRACK** training metrics (loss, validation metrics, MAPE, Sharpe)
- ✅ **VALIDATE** model outputs (reasonable predictions, no NaN/Inf)
- ✅ **DOCUMENT** model decisions (architecture, features, hyperparameters)

#### 6.3 Post-Training Validation
- ✅ **EVALUATE** on holdout set (never train/test leakage)
- ✅ **VALIDATE** predictions are reasonable (within expected ranges)
- ✅ **AUDIT** for overfitting (train vs validation performance)
- ✅ **TEST** on different regimes (model performance across market conditions)
- ✅ **VERIFY** SHAP values make sense (feature importance aligns with domain knowledge)

---

### 7. Integration & Deployment

#### 7.1 Pre-Integration Checks
- ✅ **RUN** pre-integration audit framework before any integration
- ✅ **VALIDATE** schema compatibility
- ✅ **CHECK** for data conflicts (overlaps, duplicates)
- ✅ **TEST** rollback procedures
- ✅ **VERIFY** backup/restore procedures work

#### 7.2 Deployment Best Practices
- ✅ **TEST** in staging/development first
- ✅ **VALIDATE** all queries/scripts work in production environment
- ✅ **MONITOR** after deployment (errors, performance, data quality)
- ✅ **DOCUMENT** deployment steps (for rollback if needed)
- ✅ **VERIFY** dashboard/API endpoints work correctly

#### 7.3 Rollback Planning
- ✅ **ALWAYS** have rollback plan before making changes
- ✅ **BACKUP** critical data before modifications
- ✅ **TEST** rollback procedures
- ✅ **DOCUMENT** rollback steps
- ✅ **VERIFY** rollback works (test in non-production)

---

### 8. Monitoring & Maintenance

#### 8.1 Continuous Monitoring
- ✅ **MONITOR** data quality daily (automated checks)
- ✅ **TRACK** model performance (MAPE, Sharpe, prediction accuracy)
- ✅ **ALERT** on anomalies (data gaps, prediction errors, pipeline failures)
- ✅ **REVIEW** costs monthly (GCP billing, BigQuery usage)
- ✅ **AUDIT** resource usage (unused tables, orphaned files)

#### 8.2 Maintenance Best Practices
- ✅ **CLEAN UP** temporary files, test data, old backups regularly
- ✅ **ARCHIVE** old data (don't delete, move to archive)
- ✅ **UPDATE** dependencies (security patches, bug fixes)
- ✅ **REVIEW** and optimize slow queries
- ✅ **DOCUMENT** maintenance procedures

---

### 9. Communication & Collaboration

#### 9.1 Documentation Standards
- ✅ **UPDATE** documentation when code changes
- ✅ **EXPLAIN** decisions, not just implementations
- ✅ **CITE** sources for formulas, methodologies
- ✅ **LINK** related documentation
- ✅ **MAINTAIN** up-to-date README files

#### 9.2 Error Reporting
- ✅ **LOG** errors with full context (what, where, when, why)
- ✅ **INCLUDE** stack traces, input data, expected vs actual
- ✅ **DOCUMENT** error resolution steps
- ✅ **ALERT** on critical errors (don't silently fail)
- ✅ **TRACK** error patterns (recurring issues)

---

### 10. Security & Compliance

#### 10.1 API Keys & Credentials
- ✅ **NEVER** hardcode API keys or credentials
- ✅ **USE** macOS Keychain for API keys (`src/utils/keychain_manager.py`)
- ✅ **ROTATE** credentials regularly
- ✅ **AUDIT** credential usage (who has access, when used)
- ✅ **SECURE** service account keys (Vercel env vars, not in code)

#### 10.2 Data Access Control
- ✅ **IMPLEMENT** proper IAM roles (least privilege)
- ✅ **ISOLATE** sensitive data (MES private, ZL public)
- ✅ **AUDIT** data access (who accessed what, when)
- ✅ **VALIDATE** access controls work (test permissions)
- ✅ **DOCUMENT** access patterns (who needs what)

---

## 🎯 PRIORITY LEVELS

### CRITICAL (Must Always Follow)
1. No fake data
2. us-central1 only
3. No costly resources without approval
4. Always check existing resources before creating
5. Always audit after work

### HIGH (Should Always Follow)
1. Research best practices before implementing
2. Validate data quality at each stage
3. Test code before committing
4. Document complex logic
5. Monitor costs and usage

### MEDIUM (Best Practice)
1. Research quant finance methodologies
2. Follow existing patterns
3. Clean up temporary resources
4. Update documentation
5. Track model performance

---

## 📝 IMPLEMENTATION NOTES

### How These Will Be Added to .cursorrules
- Organized by category (matching above)
- Clear, actionable statements
- Priority indicators (CRITICAL, HIGH, MEDIUM)
- Links to detailed documentation
- Examples where helpful

### Review Questions
1. Are all categories covered?
2. Are priorities correct?
3. Are statements clear and actionable?
4. Should any be added/removed/modified?
5. Are there project-specific practices missing?

---

**Status:** DRAFT - Awaiting review before implementation

