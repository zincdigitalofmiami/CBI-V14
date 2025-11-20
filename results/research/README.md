# Research Results Directory

This directory stores outputs from OpenAI Deep Research tasks.

## Structure

- `research_*.json` - Research results in JSON format
- Each file contains:
  - Query/research question
  - Full research output
  - Response metadata
  - Timestamp (in filename)

## Usage

Research scripts automatically save here when using `--output` flag:

```bash
python3 scripts/research/research_market_regimes.py \
  --asset ZL \
  --output results/research/zl_regimes_$(date +%Y%m%d).json
```

## Analyzing Results

```python
import json

with open('results/research/zl_regimes_20250115.json', 'r') as f:
    data = json.load(f)
    print(data['output'])
```

## Best Practices

- Use descriptive filenames with dates
- Review citations in results
- Integrate findings into feature engineering
- Archive old results periodically
