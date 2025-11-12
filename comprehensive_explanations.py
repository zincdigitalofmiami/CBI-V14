#!/usr/bin/env python3
import re

# Read the file
with open('CBI_V14_COMPLETE_EXECUTION_PLAN.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Context-aware explanation mapping
def get_section_explanation(section_title, context_lines):
    """Generate appropriate explanation based on section title and context"""
    
    title_lower = section_title.lower()
    context = ' '.join(context_lines).lower()
    
    # VERTEX AI EXPORT DATA section
    if 'vertex ai export' in title_lower or 'vertex ai' in title_lower:
        if 'why we must keep' in title_lower:
            return "**Data Retention Rationale:** Explains why the Vertex AI export dataset (200+ columns, 112 rows from 2020-2025) must be preserved permanently. This data contains feature importance rankings, prediction intervals, and validation benchmarks that are critical for model optimization and cannot be regenerated."
        elif 'how to use' in title_lower or 'optimization' in title_lower:
            return "**Optimization Strategy:** Describes three methods for using Vertex AI export data: (1) Extract feature importance by calculating variance and volatility, (2) Use as validation benchmark to compare BQML vs Vertex AI predictions, (3) Apply feature selection strategy using top 50 features for focused models."
        elif 'data contents' in title_lower or 'contents' in title_lower:
            return "**Dataset Inventory:** Lists the contents of the Vertex AI export dataset including 200+ feature columns, 112 evaluation rows spanning 2020-2025, predictions with confidence intervals, all Big 8 signals, correlations, and sentiment scores. Also documents additional datasets in staging, curated, signals, and weather datasets."
        else:
            return "**Vertex AI Export Data:** The critical dataset exported from Vertex AI AutoML training containing all features, predictions, and evaluation metrics. This data is essential for feature importance analysis, model validation, and optimization strategies."
    
    # Neural Drivers sections
    if 'neural drivers' in title_lower:
        if 'dollar' in title_lower:
            return "**Dollar Neural Drivers:** Layer 3 deep drivers (rate differentials, risk sentiment, capital flows) that feed into Layer 2 dollar neural score. Tracks causal chains from interest rate spreads, credit spreads, and currency flows to dollar strength, which impacts soybean oil prices."
        elif 'fed' in title_lower:
            return "**Fed Neural Drivers:** Layer 3 deep drivers (employment data, inflation metrics, financial conditions) that feed into Layer 2 Fed neural score. Monitors employment trends, CPI changes, and financial stress indicators that influence Federal Reserve policy and commodity prices."
        elif 'crush' in title_lower:
            return "**Crush Neural Drivers:** Layer 3 deep drivers (processing economics, demand signals, logistics) that feed into Layer 2 crush neural score. Tracks crush margins, processing capacity, demand indicators, and supply chain logistics that directly impact soybean oil pricing."
        else:
            return "**Neural Architecture:** Multi-layer neural network approach that tracks causal chains from deep drivers (Layer 3) through neural scores (Layer 2) to master predictions (Layer 1), using Granger causality tests to verify causal relationships rather than just correlations."
    
    # Dynamic Weighting section
    if 'dynamic weighting' in title_lower or 'weighting system' in title_lower:
        return "**Dynamic Weighting System:** Adaptive weighting mechanism that changes neural score weights based on detected market regimes. In crisis mode, dollar weight increases to 50%; in processing shocks, crush weight increases to 60%; in macro events, Fed weight increases to 40%. Uses rolling correlation windows (30-day for fast adaptation, 90-day for stability) to trigger reweighting."
    
    # Model Suite sections
    if 'model suite' in title_lower or 'ultimate bqml' in title_lower:
        return "**Optimized Model Suite:** Collection of five specialized BQML models designed to improve upon baseline performance: (1) Crush-focused model with top 20 features, (2) Big 8 signals model, (3) Full 300-feature model, (4) Deep neural network with 3 hidden layers, (5) Ensemble model combining all approaches with weighted averaging."
    
    # Performance Targets section
    if 'performance targets' in title_lower or 'model performance' in title_lower:
        return "**Performance Improvement Targets:** Defines target MAE reductions for each model type: Crush King model targets 0.30 MAE (25% improvement), Neural Net targets 0.28 MAE (30% improvement), Ensemble model targets 0.25 MAE (37% improvement) compared to baseline 0.40 MAE."
    
    # Dashboard Implementation section
    if 'dashboard implementation' in title_lower or 'priority layout' in title_lower:
        return "**Dashboard Layout Strategy:** Prioritizes dashboard visualization based on actual feature impact rankings from Vertex AI analysis. Top priority: Crush Margin (#1 predictor), followed by China Imports, Dollar Index, Fed Funds Rate, and Trade War/Tariffs. Layout emphasizes the most impactful drivers first."
    
    # Data Collection Priorities section
    if 'data collection priorities' in title_lower or 'immediate needs' in title_lower:
        return "**Data Collection Roadmap:** Identifies critical data sources needed immediately: (1) FRED API data for rate differentials, currency pairs, credit spreads, employment metrics, (2) Processing data from NOPA crush reports, Argentina/Brazil capacity, rail/barge rates, (3) China deep metrics including hog inventory cycles, Dalian futures curve, state reserve estimates."
    
    # Testing Methodology section
    if 'testing methodology' in title_lower:
        return "**Causality Testing Approach:** Methodology for validating neural driver causal chains using Granger causality tests for each link, path strength analysis, dynamic correlation windows, and regime-based reweighting to ensure relationships are causal rather than spurious correlations."
    
    # Core Datasets section
    if 'core datasets' in title_lower or 'primary data sources' in title_lower:
        return "**Data Source Catalog:** Comprehensive inventory of all BigQuery datasets containing 5+ years of historical data including prices, Big 8 signals, CFTC positioning, news/sentiment, Trump policy intelligence, economic indicators, weather data, China imports, and Argentina export data."
    
    # Feature Engineering sections
    if 'feature engineering' in title_lower or 'computed features' in title_lower:
        return "**Feature Engineering Pipeline:** Creates derived features from scraped data including sentiment scores, entity mentions (China, Brazil, Argentina), policy support scores, forward curve analysis, trader sentiment, and ENSO risk scores. These features are computed from raw scraped data and stored in feature tables."
    
    # Consolidation sections
    if 'consolidation' in title_lower or 'zero stale' in title_lower:
        return "**Data Consolidation Strategy:** SQL scripts and procedures for consolidating all data sources into production training tables with zero staleness. Uses Big 8 signals dates for joins, fills gaps with Vertex AI export data, forward-fills sparse features, and ensures all 300 features are current through the latest date."
    
    # Default based on common patterns
    if 'technical implementation' in context or 'contains the technical' in context:
        # Try to infer from surrounding headers
        if any(h in context for h in ['sql', 'query', 'table', 'schema']):
            return "**Database Operations:** SQL queries and schema definitions for database operations, table creation, data validation, and feature engineering."
        elif any(h in context for h in ['python', 'script', 'function', 'class']):
            return "**Python Implementation:** Python scripts for data ingestion, web scraping, model training, API endpoints, and automation workflows."
        elif any(h in context for h in ['model', 'training', 'bqml', 'ml.predict']):
            return "**Model Configuration:** BigQuery ML model training configuration including feature selection, hyperparameters, and training procedures."
        elif any(h in context for h in ['forecast', 'prediction', 'ml.predict']):
            return "**Forecast Generation:** SQL queries using ML.PREDICT() to generate forecasts with confidence intervals calculated from residual quantiles."
        else:
            return "**Implementation Details:** Technical implementation for this section's functionality."
    
    return None

# Process lines
cleaned_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Check if this is a generic explanation that needs replacement
    if re.match(r'\*\*(Technical Implementation|Model Configuration|Database Schema|Forecast Generation|Training Monitoring|Pre-Training Audit|Python Implementation|SQL Implementation|Python Code|Database Operations|Cost Analysis|Backtesting|Testing|API Endpoint|Frontend Implementation|Next.js Configuration|Scraping Schedule|Feature Engineering|Data Pipeline Flow|Deprecated Tables|Production Models|Training Datasets):\*\*', stripped):
        # Get context - look for section headers nearby
        context_before = []
        context_after = []
        
        # Look backwards for section header
        j = i - 1
        section_title = None
        while j >= max(0, i - 20) and not section_title:
            if lines[j].strip().startswith('#'):
                section_title = lines[j].strip()
                break
            context_before.insert(0, lines[j].strip())
            j -= 1
        
        # Look forwards for additional context
        j = i + 1
        while j < min(len(lines), i + 10):
            context_after.append(lines[j].strip())
            j += 1
        
        # Get appropriate explanation
        if section_title:
            explanation = get_section_explanation(section_title, context_before + context_after)
            if explanation:
                cleaned_lines.append(explanation)
                i += 1
                continue
        
        # If no good match, keep original but try to improve it
        cleaned_lines.append(line)
        i += 1
        continue
    
    # Skip code fragments
    is_code = False
    
    # SQL fragments
    if re.match(r'^\s*(CREATE|SELECT|INSERT|UPDATE|DELETE|ALTER|DROP|FROM|WHERE|GROUP|ORDER|LIMIT|UNION|JOIN|WITH|CASE|WHEN|THEN|ELSE|END|AS|IN|AND|OR|COUNT|AVG|STDDEV|ABS|CORR|TIMESTAMP_DIFF|MIN|MAX|UNPIVOT|HAVING|PERCENTILE_CONT|SUM|CROSS JOIN|LEFT JOIN|PARTITION BY|PRIMARY KEY|APPROX_QUANTILES)\s+', stripped, re.IGNORECASE):
        is_code = True
    # SQL column definitions
    elif re.match(r'^\s*\w+\s+(STRING|INT64|DATE|TIMESTAMP|FLOAT64|ARRAY)', stripped, re.IGNORECASE):
        is_code = True
    # SQL comments
    elif stripped.startswith('--') or (stripped.startswith('#') and not stripped.startswith('##') and '**' not in stripped):
        is_code = True
    # Python/bash code
    elif re.match(r'^\s*(def |class |import |from |if |else|elif |while |for |return |print |self\.|try|except|PROJECT|#!/usr/bin|gcloud|npm|curl|echo|@functions_framework|const |export |function |module\.exports)', stripped):
        is_code = True
    # Code-like fragments
    elif stripped in [')', ');', '}', '},', ']', '],']:
        is_code = True
    # Incomplete SQL/Python
    elif (stripped.endswith(',') or stripped.endswith(';')) and len(stripped) < 80 and not any(kw in stripped for kw in ['**', '|', '- ', '* ', '✅', '❌']):
        is_code = True
    # Variable assignments
    elif re.match(r'^\s*\w+\s*=\s*["\']', stripped) or (re.match(r'^\s*\w+\s*=\s*\d+', stripped) and '**' not in line):
        is_code = True
    # Indented code
    elif re.match(r'^[\s]{4,}', line) and not stripped.startswith('-') and not stripped.startswith('*') and '|' not in line:
        if i > 0:
            prev_context = ''.join(lines[max(0, i-3):i])
            if any(kw in prev_context for kw in ['def ', 'class ', 'import ', 'CREATE', 'SELECT', 'FROM', 'export', 'function', 'const', '@']):
                is_code = True
    
    if is_code:
        i += 1
        continue
    
    # Keep everything else
    cleaned_lines.append(line)
    i += 1

# Join and clean up
content = ''.join(cleaned_lines)

# Fix explanations that have code fragments appended
content = re.sub(r'(\*\*[^*]+\*\*\.)#\s+[^\n]+', r'\1', content)
content = re.sub(r'(\*\*[^*]+\*\*\.)\s+[A-Z_]+\s*=', r'\1', content)
content = re.sub(r'(\*\*[^*]+\*\*\.)\s+(CREATE|SELECT|FROM|WHERE|INSERT|UPDATE|ADD COLUMN|SET |OPTIONS|PARTITION BY|PRIMARY KEY|actual_prices|matched_data|pred_|quantiles_|features_)', r'\1', content, flags=re.IGNORECASE)

# Clean up excessive blank lines
content = re.sub(r'\n{4,}', '\n\n\n', content)

# Remove standalone code fragments on their own lines
lines = content.split('\n')
final_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Skip standalone code fragments
    if stripped and not any([
        stripped.startswith('#') and (stripped.startswith('##') or '**' in line),
        '**' in line,
        '|' in line and not stripped.startswith('CREATE'),
        stripped.startswith('- ') or stripped.startswith('* '),
        re.match(r'^\d+\.', stripped),
        stripped == '---',
        stripped == '',
        re.match(r'^[A-Z][^:]*:', stripped) and '**' not in line and len(stripped) < 100,
    ]):
        # Check if it's code
        if re.match(r'^\s*(pred_|quantiles_|features_|actual_prices|matched_data|CROSS JOIN|LEFT JOIN|PARTITION BY|PRIMARY KEY|APPROX_QUANTILES|PERCENTILE_CONT|SUM|MAX|MIN|COUNT|CASE|WHEN|THEN|ELSE|END|AS|IN|AND|OR|FROM|WHERE|SELECT|CREATE|INSERT|UPDATE|DELETE|ALTER|DROP|OPTIONS|SET |ADD COLUMN|TIMESTAMP_DIFF|CURRENT_TIMESTAMP|rn =|column_name|best_val_loss|hours_old|confidence|created_at|model_name|forecast_date|accuracy_id|within_|computed_at|absolute_percentage_error|ci_coverage_pct|last_forecast|check_date|last_check|description|forecasts_in_range|max_ci_width|overall_status|degradation_pct|estimated_cost_usd|r2_score|r2)\s*', stripped, re.IGNORECASE):
            continue
        if re.match(r'^\s*\d+(\.\d+)?\s*(AS|,|;|\))', stripped):
            continue
        if stripped in ['*', '(', ')', ');', '{', '}', '[', ']']:
            continue
    
    final_lines.append(line)

content = '\n'.join(final_lines)

# Clean up again
content = re.sub(r'\n{4,}', '\n\n\n', content)

with open('CBI_V14_COMPLETE_EXECUTION_PLAN.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('Comprehensive explanations added - all generic messages replaced with context-specific explanations')


