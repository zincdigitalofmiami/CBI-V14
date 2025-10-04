# CBI-V14 PROJECT RULES & STANDARDS

**Last Updated**: 2025-10-03  
**Enforcement Level**: MANDATORY  
**Violations**: Will fail CI/CD pipeline

---

## CRITICAL RULES (ZERO TOLERANCE)

### RULE #1: NO MOCK DATA - EVER
**Status**: ABSOLUTE - NO EXCEPTIONS

#### What This Means:
- No hardcoded arrays/objects representing fake data
- No `mockData.js`, `fixtures.js`, `sampleData.js` files
- No `faker.js` or data generation libraries
- No commented-out mock data "for testing"
- No `if (process.env.USE_MOCK_DATA)` conditionals
- ALL data must come from BigQuery, Cloud Storage, or external APIs

#### Enforcement:
```bash
# Pre-commit hook checks for:
- Files named *mock*.js, *fake*.js, *sample*.js
- Variables named mockData, fakeData, sampleData, dummyData
- Imports from 'faker', '@faker-js/faker'
- Comments containing "mock data", "fake data", "TODO: replace with real"
```

#### Exceptions:
- **NONE** - If you need test data, use real BigQuery data in a `test` dataset

---

### RULE #2: BIGQUERY AS SOURCE OF TRUTH
**All application data MUST flow through BigQuery**

#### Requirements:
- Primary data source: `cbi-v14.forecasting_data_warehouse`
- All tables must be partitioned and clustered
- Never query production tables directly from frontend
- Always use FastAPI endpoints that validate and sanitize queries

#### Approved Data Flow:
```
BigQuery → FastAPI Backend → React Frontend
         ↓
    (cached in TanStack Query)
```

---

### RULE #3: ENVIRONMENT VARIABLES FOR ALL CONFIGURATION
**No hardcoded project IDs, dataset names, or credentials**

#### Required Format:
```python
# CORRECT
PROJECT = os.environ["PROJECT"]  # Fails if not set

# WRONG
PROJECT = os.environ.get("PROJECT", "cbi-v14")  # Has default
PROJECT = "cbi-v14"  # Hardcoded
```

#### Mandatory Variables:
- `PROJECT` - GCP project ID
- `DATASET` - BigQuery dataset name
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account key path

#### Never Commit:
- `.env` files with actual credentials
- Service account JSON keys
- API keys in plaintext

---

### RULE #4: IMMUTABLE INFRASTRUCTURE
**All infrastructure changes via Terraform or documented shell scripts**

#### Approved Methods:
1. Terraform configurations in `/terraform-deploy/`
2. Versioned shell scripts (e.g., `bigquery_harden_finalize.sh`)
3. Cloud Build YAML for CI/CD

#### Forbidden:
- Manual GCP Console changes without documentation
- Untracked shell scripts that modify infrastructure

---

## CODE QUALITY STANDARDS

### Python Standards
- **Style**: Black formatter (line length 100)
- **Linting**: Pylint + Flake8
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public functions

### JavaScript/React Standards
- **Style**: Prettier (2 spaces, single quotes)
- **Linting**: ESLint with react-hooks rules
- **PropTypes**: Required for all components OR TypeScript

### SQL Standards (BigQuery)
- Use Standard SQL (not legacy)
- Always qualify table names with `project.dataset.table`
- Use parameterized queries for user input
- Add comments explaining business logic

---

## DEVELOPMENT WORKFLOW

### Git Branch Strategy
```
main (production)
  ↑
develop (integration)
  ↑
feature/[ticket-id]-description
hotfix/[ticket-id]-description
```

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `docs`: Documentation changes
- `test`: Adding tests
- `chore`: Build/tooling changes

---

## SECURITY STANDARDS

### Authentication
- ✅ Use Application Default Credentials
- ❌ Never commit service account keys
- ✅ Store secrets in GCP Secret Manager

### BigQuery Access
- ✅ Use parameterized queries
- ❌ Never concatenate user input into SQL

---

## DATA QUALITY STANDARDS

### BigQuery Table Requirements
1. **Partitioning**: All time-series tables MUST be partitioned by date/timestamp
2. **Clustering**: Cluster on frequently filtered columns
3. **Schema**: Explicitly define schema (no auto-detect in production)

---

## TESTING STANDARDS

**Coverage Requirement: 80% minimum**

- Unit tests for all business logic
- Integration tests for BigQuery connections
- No mock data in tests - use real data snapshots

---

## DOCUMENTATION STANDARDS

### Required Files:
- `README.md` - Project overview, setup instructions
- `CONTRIBUTING.md` - How to contribute
- `CHANGELOG.md` - Version history
- `API_DOCS.md` - API endpoint reference

---

## DEPLOYMENT STANDARDS

### Pre-Deployment Checklist
```bash
# 1. All tests pass
make test

# 2. No linting errors
make lint

# 3. Rules enforced
make check-rules

# 4. Environment variables documented
cat .env.example
```

---

## RULE UPDATES

To propose changes:
1. Open GitHub issue with `[RULE CHANGE]` prefix
2. Discuss with team
3. Create PR updating this file
4. Requires 2 approvals from maintainers

**Version**: 1.0.0  
**Last Review**: 2025-10-03  
**Next Review**: 2025-11-03

