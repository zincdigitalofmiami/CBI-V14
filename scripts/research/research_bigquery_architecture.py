#!/usr/bin/env python3
"""
Research BigQuery Architecture for CBI-V14
Uses OpenAI Deep Research to create comprehensive BigQuery setup plan
"""

import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.utils.deep_research import DeepResearcher


def research_bigquery_architecture():
    """Research comprehensive BigQuery architecture for live data feeds and training."""
    
    print("="*80)
    print("RESEARCHING BIGQUERY ARCHITECTURE FOR CBI-V14")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    researcher = DeepResearcher(model="o3-deep-research")  # Use full model for comprehensive plan
    
    # Comprehensive research query
    query = """
Create a comprehensive architecture plan for setting up a quantitative trading system with the following requirements:

SYSTEM OVERVIEW:
- Project: CBI-V14 - Soybean Oil (ZL) futures forecasting
- Data Sources: Databento (futures), Alpha Vantage (technical indicators), FRED (economic), NewsAPI (sentiment)
- Training: Local Mac M4 (TensorFlow Metal, PyTorch MPS)
- Storage: Google BigQuery (us-central1 region)
- Dashboard: Next.js/Vercel reading from BigQuery
- 25+ years of historical data (2000-2025)

ARCHITECTURE REQUIREMENTS:

1. BIGQUERY SETUP:
   - Schema design for time-series futures data
   - Partitioning strategy (by date)
   - Clustering strategy (by symbol, date)
   - Table structure for: raw data, curated features, training exports, predictions
   - Best practices for cost optimization (stay under 1 TB/month queries)
   - Data retention policies

2. LIVE DATA FEEDS:
   - Real-time streaming from Databento to BigQuery
   - Batch ingestion patterns (5-minute intervals)
   - Error handling and retry logic
   - Data validation at ingestion
   - Idempotent pipelines (safe to re-run)
   - Monitoring and alerting

3. TRAINING DATA EXPORT:
   - Efficient export from BigQuery to local Parquet files
   - Export strategies for large datasets (25+ years)
   - Incremental export patterns
   - Data quality validation before export
   - Format optimization for TensorFlow/PyTorch

4. DASHBOARD INTEGRATION:
   - BigQuery → Next.js/Vercel connection patterns
   - Real-time data refresh strategies
   - Query optimization for dashboard performance
   - Caching strategies
   - Cost control (query limits, pagination)

5. DATA PIPELINE ARCHITECTURE:
   - Raw → Curated → Training → Predictions flow
   - Staging and quarantine layers
   - Data lineage tracking
   - Version control for schemas
   - Rollback procedures

6. COST OPTIMIZATION:
   - BigQuery query cost management
   - Storage optimization
   - Partitioning and clustering best practices
   - Query caching strategies
   - Monitoring and alerting for costs

7. SECURITY & COMPLIANCE:
   - API key management (Keychain → BigQuery)
   - IAM roles and permissions
   - Data encryption
   - Access controls

Provide:
- Detailed architecture diagrams (text-based)
- Step-by-step implementation plan
- Code patterns and examples
- Cost estimates
- Best practices from Google Cloud documentation
- Real-world examples from similar systems

Prioritize sources: Google Cloud BigQuery documentation, data engineering best practices, quant finance data pipeline patterns.
Include specific BigQuery SQL examples, Python code patterns, and architecture recommendations.
"""
    
    print("Researching comprehensive BigQuery architecture...")
    print("(This may take several minutes)")
    print()
    
    try:
        response = researcher.research(
            query=query,
            instructions="""
            Create a detailed, actionable architecture plan. Include:
            - Specific BigQuery SQL examples
            - Python code patterns for data ingestion
            - Step-by-step implementation checklist
            - Cost optimization strategies
            - Real-world best practices
            
            Structure the output as a comprehensive implementation plan that can be followed step-by-step.
            """,
            max_tool_calls=80,  # Comprehensive research
            use_code_interpreter=True,  # For code examples
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/research/bigquery_architecture_plan_{timestamp}.json"
        os.makedirs("results/research", exist_ok=True)
        
        result = {
            "timestamp": timestamp,
            "query": query,
            "output": response.output_text,
            "response_id": getattr(response, 'id', None),
        }
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print()
        print("="*80)
        print("RESEARCH COMPLETE")
        print("="*80)
        print()
        print(response.output_text)
        print()
        print("="*80)
        print(f"✅ Full results saved to: {output_file}")
        print("="*80)
        
        # Also save as markdown for easier reading
        md_file = f"docs/plans/BIGQUERY_LIVE_FEEDS_ARCHITECTURE_PLAN.md"
        with open(md_file, 'w') as f:
            f.write(f"# BigQuery Live Feeds Architecture Plan\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Research Model:** o3-deep-research\n\n")
            f.write("---\n\n")
            f.write(response.output_text)
        
        print(f"✅ Markdown version saved to: {md_file}")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = research_bigquery_architecture()
    sys.exit(0 if success else 1)



