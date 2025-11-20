#!/usr/bin/env python3
"""
OpenAI Deep Research Integration for CBI-V14
Provides deep research capabilities using o3-deep-research and o4-mini-deep-research models
"""

from openai import OpenAI
from typing import Optional, List, Dict, Any
import json
import logging
import uuid
from src.utils.keychain_manager import get_api_key

logger = logging.getLogger(__name__)


class DeepResearcher:
    """Deep Research client for CBI-V14 research tasks."""
    
    def __init__(self, model: str = "o4-mini-deep-research", timeout: int = 3600):
        """
        Initialize Deep Research client.
        
        Args:
            model: Model to use ('o3-deep-research' or 'o4-mini-deep-research')
            timeout: Request timeout in seconds (default 3600 = 1 hour)
        """
        api_key = get_api_key('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not found in Keychain. "
                "Store it with: security add-generic-password -a default -s cbi-v14.OPENAI_API_KEY -w 'sk-...' -U"
            )
        
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        
    def research(
        self,
        query: str,
        instructions: Optional[str] = None,
        max_tool_calls: int = 50,
        background: bool = True,
        use_web_search: bool = True,
        use_code_interpreter: bool = True,
        vector_store_ids: Optional[List[str]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Conduct deep research on a topic.
        
        Args:
            query: Research question or topic
            instructions: Optional instructions for the research
            max_tool_calls: Maximum number of tool calls (controls cost)
            background: Run in background mode (recommended for long tasks)
            use_web_search: Enable web search tool
            use_code_interpreter: Enable code interpreter for analysis
            vector_store_ids: List of vector store IDs for file search
            mcp_servers: List of MCP server configurations
            
        Returns:
            Response object with output_text and metadata
        """
        tools = []
        
        if use_web_search:
            tools.append({"type": "web_search_preview"})
        
        if vector_store_ids:
            tools.append({
                "type": "file_search",
                "vector_store_ids": vector_store_ids
            })
        
        if mcp_servers:
            for server in mcp_servers:
                tools.append({
                    "type": "mcp",
                    "server_label": server.get("label"),
                    "server_url": server.get("url"),
                    "require_approval": server.get("require_approval", "never"),
                })
        
        if use_code_interpreter:
            tools.append({
                "type": "code_interpreter",
                "container": {"type": "auto"}
            })
        
        if not tools:
            raise ValueError("At least one tool must be enabled for deep research")
        
        logger.info(f"Starting deep research: {query[:100]}...")
        logger.info(f"Model: {self.model}, Max tool calls: {max_tool_calls}")
        
        # Generate unique request ID for tracking (OpenAI best practice)
        request_id = str(uuid.uuid4())
        logger.info(f"Request ID: {request_id}")
        
        try:
            response = self.client.responses.create(
                model=self.model,
                input=query,
                instructions=instructions,
                background=background,
                max_tool_calls=max_tool_calls,
                tools=tools,
                extra_headers={
                    "X-Client-Request-Id": request_id
                }
            )
            
            # Log response metadata if available
            if hasattr(response, 'response_headers'):
                logger.info(f"Response headers: {response.response_headers}")
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API error (Request ID: {request_id}): {e}")
            raise
    
    def research_market_regimes(
        self,
        asset: str = "ZL",
        date_range: str = "2000-2025",
        focus: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Research market regimes for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'ZL', 'ES', 'CL')
            date_range: Date range to analyze
            focus: Optional focus area (e.g., 'Fed policy', 'trade wars', 'weather')
        """
        query = f"""
Research market regimes and regime transitions for {asset} futures from {date_range}.

Do:
- Identify distinct market regimes (trending, ranging, volatile, etc.)
- Analyze regime characteristics (duration, volatility, correlation patterns)
- Identify regime transition triggers (economic events, policy changes, supply shocks)
- Include specific dates, policy changes, and market regime transitions
- Analyze correlation between economic indicators and regime changes
- Include statistical analysis of regime duration and characteristics
- Prioritize sources: FRED data, Fed meeting minutes, academic papers on futures markets, CFTC data
- Include inline citations and return all source metadata

Be analytical, include data-backed reasoning that could inform regime-aware model training.
"""
        
        if focus:
            query += f"\n\nFocus specifically on: {focus}"
        
        return self.research(
            query=query,
            max_tool_calls=50,
            use_code_interpreter=True,
        )
    
    def research_feature_engineering(
        self,
        asset: str = "ZL",
        indicator_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Research best practices for feature engineering.
        
        Args:
            asset: Asset symbol
            indicator_type: Optional specific indicator type (e.g., 'momentum', 'volatility', 'volume')
        """
        query = f"""
Research best practices for technical indicator feature engineering in quantitative 
trading systems, specifically for {asset} futures (agricultural commodities).

Focus on:
- Which technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, etc.) are most predictive for {asset}
- Optimal lookback periods for different market regimes
- Academic research on feature importance in futures markets
- Regime-aware feature selection methodologies
- Feature interaction and combination strategies
- Statistical validation of indicator effectiveness

Prioritize sources: academic papers, quant finance journals, industry research reports, peer-reviewed studies.
Include statistical evidence, correlation analysis, and citations.
"""
        
        if indicator_type:
            query += f"\n\nFocus specifically on {indicator_type} indicators."
        
        return self.research(
            query=query,
            max_tool_calls=40,
            use_code_interpreter=True,
        )
    
    def research_data_sources(
        self,
        data_type: str,
        use_case: str = "futures trading",
    ) -> Dict[str, Any]:
        """
        Research and evaluate data sources.
        
        Args:
            data_type: Type of data (e.g., 'weather', 'economic indicators', 'news sentiment')
            use_case: Intended use case
        """
        query = f"""
Research the reliability, data quality, and cost-effectiveness of {data_type} data sources 
for {use_case}:

For each source:
- Assess data quality and reliability (accuracy, completeness, latency)
- Compare costs and API limitations (rate limits, historical data availability)
- Evaluate integration complexity (API documentation, authentication, data formats)
- Review academic/industry validation studies
- Compare with alternative sources
- Assess suitability for quantitative trading systems

Prioritize peer-reviewed research, industry case studies, and official documentation.
Include specific examples, pricing information, and technical specifications.
"""
        
        return self.research(
            query=query,
            max_tool_calls=35,
        )
    
    def research_economic_impact(
        self,
        topic: str,
        asset: str = "ZL",
        date_range: str = "2000-2025",
    ) -> Dict[str, Any]:
        """
        Research economic impact on asset prices.
        
        Args:
            topic: Economic topic (e.g., 'Fed rate changes', 'trade wars', 'biofuel policy')
            asset: Asset symbol
            date_range: Date range to analyze
        """
        query = f"""
Research the relationship between {topic} and {asset} futures prices from {date_range}.

Do:
- Include specific dates, policy changes, and price movements
- Analyze correlation and causation (not just correlation)
- Include statistical analysis (regression, time series analysis)
- Identify lag effects and transmission mechanisms
- Compare with other similar assets for context
- Prioritize sources: FRED data, Fed meeting minutes, academic papers, regulatory filings
- Include inline citations and return all source metadata

Be analytical, include data-backed reasoning that could inform feature engineering and model training.
"""
        
        return self.research(
            query=query,
            max_tool_calls=50,
            use_code_interpreter=True,
        )


def main():
    """CLI interface for deep research."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deep Research for CBI-V14")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--model", default="o4-mini-deep-research", 
                       choices=["o3-deep-research", "o4-mini-deep-research"],
                       help="Model to use")
    parser.add_argument("--max-calls", type=int, default=50,
                       help="Maximum tool calls")
    parser.add_argument("--no-web", action="store_true",
                       help="Disable web search")
    parser.add_argument("--no-code", action="store_true",
                       help="Disable code interpreter")
    
    args = parser.parse_args()
    
    researcher = DeepResearcher(model=args.model)
    response = researcher.research(
        query=args.query,
        max_tool_calls=args.max_calls,
        use_web_search=not args.no_web,
        use_code_interpreter=not args.no_code,
    )
    
    print("\n" + "="*80)
    print("DEEP RESEARCH RESULTS")
    print("="*80)
    print(response.output_text)
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

