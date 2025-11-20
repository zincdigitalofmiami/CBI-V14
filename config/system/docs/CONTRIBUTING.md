---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Contributing to CBI-V14

## Critical Rules

Before contributing, read [PROJECT_RULES.md](./PROJECT_RULES.md) carefully.

**Most Important Rule**: **NO MOCK DATA - EVER**

## Getting Started

1. **Fork the repository**

2. **Clone and setup**
   ```bash
   git clone https://github.com/your-username/CBI-V14.git
   cd CBI-V14
   make setup
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make changes**
   - Follow code quality standards
   - Write tests
   - Update documentation

5. **Verify compliance**
   ```bash
   make check-rules  # MUST pass
   make lint         # MUST pass
   make test         # MUST pass
   ```

6. **Commit with conventional format**
   ```bash
   git add .
   git commit -m "feat(forecast): add confidence intervals"
   # Pre-commit hooks will run automatically
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Review Process

All PRs require:
- Pass all automated checks
- At least 1 approval from maintainer
- No mock data violations
- Updated documentation

## Questions?

Open an issue with the `question` label.
