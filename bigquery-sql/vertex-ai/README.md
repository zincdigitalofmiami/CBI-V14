# Vertex AI SQL Directory

## Purpose
All SQL scripts for Vertex AI training data preparation, schema validation, and data quality checks.

## Naming Conventions
- Pattern: `{action}_{resource}_{horizon}.sql`
- Examples:
  - `create_training_1m.sql` - Create 1M training table
  - `validate_schema.sql` - Schema validation
  - `prepare_features.sql` - Feature preparation

## Structure
- Training table creation scripts
- Schema contract and validation
- Data quality checks
- Feature engineering SQL

## Rules
- ❌ NO `_test`, `_backup`, `_v2` suffixes
- ✅ All files go directly to production
- ✅ Descriptive, unambiguous names

