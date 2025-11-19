# Deployment Safety Gates Plan

This plan hardens the BigQuery deployment path so schema pushes never fail mid‑run or drift from expectations. Each gate is enforced before advancing to the next execution phase (schema, overlay views, migrations, validation).

## 1. Pre-Flight Automation
- `sqlfluff lint` + `bq query --dry_run` on every SQL file referenced by a deployment step (`PRODUCTION_READY_BQ_SCHEMA.sql`, overlay SQL, ad-hoc migrations).
- `shellcheck` on every bash helper (e.g., `deploy_bq_schema.sh`), unit tests or smoke CLI run for Python helpers (`migrate_master_features.py`, `validate_bq_deployment.py`).
- CI job blocks merges if any lint/test fails; results archived in `DEPLOYMENT_EXECUTION_PLAN.md`.

## 2. Environment Diff Audit
- Refresh `BQ_CURRENT_STATE_REPORT.md` before any run (script dumps datasets, tables, views, row counts).
- Compare report vs. `TABLE_MAPPING_MATRIX.md` to flag missing or unexpected objects; fix or document exceptions.
- Confirm no legacy staging tables will collide with new schema names.

## 3. Idempotent Deployment Scripts
- Every dataset/table/create statement must be guarded with existence checks (`bq ls`, `--if-exists`, or conditional SQL).
- Keep `set -e` for real failures but wrap dataset creation in functions that swallow “already exists” responses.
- Scripts log each action (created, skipped, patched) and write summary artifacts (e.g., `Logs/deploy_YYYYMMDD.log`).

## 4. Staged Dry Runs
- Execute schema scripts against a non-prod project or in dry-run mode before prod deployment; capture output in `DEPLOYMENT_SCRIPTS_READY.md`.
- For bash/Python scripts, run with `--dry_run` or mock flags to ensure argument parsing and BQ calls succeed.
- Validate filesystem prerequisites (external drive folders, config files) via `pre_flight_harness.py`.

## 5. Formal Deployment Checklist
- Expand `BQ_DEPLOYMENT_READINESS_CHECKLIST.md` to include sign-off lines for: lint/test pass, diff audit reviewed, dry-run logs attached, rollback path documented.
- Require two-person acknowledgment (author + reviewer) before running Phase 1; store signatures/date inside the checklist.
- Gate Phase 2/3 (overlay creation, migrations, validation) on successful completion of prior checklist sections.

## 6. Post-Execution Validation
- Immediately run `validate_bq_deployment.py` after each phase; attach results to `DEPLOYMENT_STATUS_FINAL.md`.
- If validation fails, halt next phases and open an issue describing the failure, logs, and remediation plan.
- Monitor dashboards/jobs for 24h post-deploy; record observations in `SYSTEM_STATUS_YYYYMMDD.md`.

## 7. Continuous Improvement
- After every deployment, conduct a brief retro (5–10 bullets) noting surprises, missing checks, or manual work; append to `DEPLOYMENT_EXECUTION_PLAN.md`.
- Update this safety plan whenever a new gap is discovered so future runs inherit the fix automatically.

Adhering to these gates ensures future BigQuery deployments are predictable, auditable, and safe even when the environment already contains partial data.
