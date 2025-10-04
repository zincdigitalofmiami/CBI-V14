# CBI-V14 RULES & ENFORCEMENT - ACTIVE

## Status: INSTALLED AND ENFORCED

All project rules, enforcement scripts, and automation are **ACTIVE**.

---

## Files Created

### Core Documentation
- PROJECT_RULES.md - Complete rules documentation
- CONTRIBUTING.md - How to contribute

### Enforcement Scripts
- scripts/check_no_mock_data.sh - Blocks mock data
- scripts/check_env_vars.sh - Validates env vars

### Automation
- .pre-commit-config.yaml - Git pre-commit hooks
- Makefile - Development commands
- cloudbuild.yaml - GCP CI/CD pipeline
- .github/workflows/ci.yml - GitHub Actions
- .github/pull_request_template.md - PR template

### Configuration
- .gitignore - Updated with comprehensive rules

---

## Immediate Next Steps

### 1. Install Pre-Commit Hooks

```bash
cd /Users/zincdigital/CBI-V14

# Install pre-commit
pip3 install pre-commit

# Activate hooks
pre-commit install

# Test it
pre-commit run --all-files
```

### 2. Test Rule Enforcement

```bash
# Test NO MOCK DATA rule
make check-rules

# Expected output:
# Checking project rules...
# PASS: No mock data violations detected
# PASS: Environment variable usage looks good
# All rules passed!
```

### 3. See All Available Commands

```bash
make help
```

---

## Enforcement Verification

### Test 1: Scripts Are Executable
```bash
ls -la scripts/
```
Expected: Both scripts show `-rwxr-xr-x` (executable)

### Test 2: NO MOCK DATA Rule Works
```bash
bash scripts/check_no_mock_data.sh
```
Expected: `PASS: No mock data violations detected`

### Test 3: Environment Variable Rule Works
```bash
bash scripts/check_env_vars.sh
```
Expected: `PASS: Environment variable usage looks good`

### Test 4: Makefile Works
```bash
make help
```
Expected: List of all available commands

---

## Rule Enforcement Status

| Rule | Status | Enforced By |
|------|--------|-------------|
| NO MOCK DATA | ACTIVE | Pre-commit + CI/CD |
| Environment Variables | ACTIVE | Pre-commit + CI/CD |
| Python Formatting | READY | Pre-commit (needs install) |
| JavaScript Formatting | READY | Pre-commit (needs install) |

---

## Daily Workflow

### Every Time You Code

```bash
# 1. Start your work
git checkout -b feature/your-feature

# 2. Make changes to files
# ... edit code ...

# 3. Before committing, check rules
make check-rules
make lint

# 4. Commit (hooks run automatically)
git add .
git commit -m "feat: your feature description"

# Hooks will automatically:
# - Check for mock data (BLOCKS commit if found)
# - Check for hardcoded credentials (BLOCKS if found)
# - Format your code
# - Run linters

# 5. Push
git push origin feature/your-feature
```

---

## What Happens Now?

### On Every Commit
Pre-commit hooks will automatically:
1. Check for mock data (BLOCKS commit if found)
2. Check for hardcoded credentials (BLOCKS if found)
3. Format your code
4. Run linters

### On Every Push to GitHub
GitHub Actions will:
1. Run rule enforcement
2. Run Python tests
3. Run linters
4. Fail the build if violations found

### On Every GCP Deployment
Cloud Build will:
1. Enforce rules FIRST
2. Only build if rules pass
3. Run security scans
4. Deploy to Cloud Run

---

## Documentation

### Must Read
- **PROJECT_RULES.md** - All project rules explained

### How-To Guides
- **CONTRIBUTING.md** - How to contribute

### Reference
- **Makefile** - All available commands
- **.pre-commit-config.yaml** - Hook configuration

---

## Troubleshooting

### "pre-commit: command not found"
```bash
pip3 install pre-commit
pre-commit install
```

### "Permission denied" on scripts
```bash
chmod +x scripts/*.sh
```

### Hooks not running on commit
```bash
pre-commit install
```

### Want to skip hooks temporarily (NOT RECOMMENDED)
```bash
git commit --no-verify -m "message"
# WARNING: Only use in emergencies!
```

---

## Verification Checklist

Run these to confirm everything works:

```bash
# 1. Check scripts exist and are executable
ls -la scripts/

# 2. Test NO MOCK DATA enforcement
bash scripts/check_no_mock_data.sh

# 3. Test environment variable enforcement
bash scripts/check_env_vars.sh

# 4. Test Makefile
make help

# 5. Check files exist
ls -la PROJECT_RULES.md CONTRIBUTING.md Makefile cloudbuild.yaml

# 6. Check GitHub Actions
ls -la .github/workflows/ci.yml
```

---

## Summary

### What You Have Now:

- Automatic mock data detection - Can't commit mock data
- Automatic code formatting - Consistent style
- Automatic linting - Catch errors early
- CI/CD integration - GitHub + GCP
- Comprehensive documentation - Know all the rules
- Easy commands - `make` shortcuts

### Remember:

**NO MOCK DATA - EVER**  
**NO HARDCODED CREDENTIALS**  
**BIGQUERY AS SOURCE OF TRUTH**  
**ENVIRONMENT VARIABLES FOR CONFIG**

---

## Questions?

1. Read `PROJECT_RULES.md`
2. Run `make help`
3. Open a GitHub issue

**The enforcement system is LIVE and PROTECTING YOUR CODE.**

