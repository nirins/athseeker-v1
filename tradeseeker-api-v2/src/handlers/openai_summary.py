"""
OpenAI summary endpoint handler for TradeSeekerAPI v2.

This module handles GET /openai-summary requests to retrieve
AI-generated stock analysis and news summaries using OpenAI's API
with real-time web search capabilities.
"""

import logging
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import quote

import openai
import requests
from bs4 import BeautifulSoup

from src.validators import validate_openai_summary_params
from src.formatters import success_response, error_response
from src.config import get_openai_api_key

logger = logging.getLogger(__name__)


def handle_openai_summary(query_params: Dict[str, Any]) -> dict:
    """
    Handles GET /openai-summary requests.
    
    Generates AI-powered stock analysis and news summaries using OpenAI's API
    with real-time web search for latest news.
    
    Query parameters:
    - symbol: Stock symbol with market code (e.g., AAPL.US) - required
    - analysis_type: Type of analysis (news, technical, fundamental, all) - optional, default: news
    - model: OpenAI model to use (gpt-4, gpt-3.5-turbo) - optional, default: gpt-4-turbo
    
    Args:
        query_params: Dict with query parameters
        
    Returns:
        Response dict with statusCode and body containing AI analysis
    """
    # Validate query parameters
    validated_params, validation_errors = validate_openai_summary_params(query_params)
    
    if validation_errors:
        logger.warning(f"Validation errors: {validation_errors}")
        return error_response("Invalid parameters", 400, validation_errors)
    
    # Extract validated parameters
    symbol = validated_params['symbol']
    analysis_type = validated_params.get('analysis_type', 'news')
    model = validated_params.get('model', 'gpt-4-turbo')
    
    logger.info(
        f"Processing OpenAI summary request: symbol={symbol}, "
        f"analysis_type={analysis_type}, model={model}"
    )
    
    try:
        # Get OpenAI API key from AWS Secrets Manager
        api_key = get_openai_api_key()
        
        # Set OpenAI API key
        openai.api_key = api_key
        
        # Get real-time news if analysis_type includes news
        news_content = ""
        if analysis_type in ['news', 'all']:
            logger.info(f"Fetching latest news for {symbol}")
            news_content = _fetch_latest_news(symbol)
        
        # Generate prompt based on analysis type
        prompt = _generate_prompt(symbol, analysis_type, news_content)
        
        # Call OpenAI API using the older format
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a financial analyst. Provide concise, factual analysis based on the provided information. Follow the requested format and keep responses brief and focused."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Reduced from 800
            temperature=0.1  # Reduced for faster, more focused responses
        )
        
        # Extract the analysis from the response
        analysis = response.choices[0].message.content
        
        # Prepare response data
        result = {
            "symbol": symbol,
            "analysis_type": analysis_type,
            "model": model,
            "analysis": analysis,
            "news_sources_checked": bool(news_content),
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        logger.info(f"Successfully generated OpenAI summary for {symbol}")
        
        return success_response(result)
        
    except ValueError as e:
        # Handle configuration errors (missing secret, etc.)
        logger.error(f"Configuration error: {e}")
        return error_response("OpenAI service not configured", 500)
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}", exc_info=True)
        return error_response("Failed to generate AI analysis", 500)


def _fetch_latest_news(symbol: str) -> str:
    """
    Fetch latest news about the stock from Google News.
    
    Args:
        symbol: Stock symbol (e.g., AAPL.US)
        
    Returns:
        Formatted news content string
    """
    base_symbol = symbol.split('.')[0]  # Remove market code
    news_items = []
    
    logger.info(f"Fetching news for symbol: {symbol} (base: {base_symbol})")
    
    try:
        # Search Google News for recent articles
        google_news = _search_google_news(base_symbol)
        news_items.extend(google_news)
        logger.info(f"Google News contributed {len(google_news)} articles")
        
        # Format news content
        if news_items:
            formatted_news = "\n".join([
                f"• {item['title']}"
                + (f" - {item['snippet']}" if item.get('snippet') else "")
                + f" ({item['source']}, {item['date']})"
                for item in news_items[:5]  # Limit to top 5 articles for faster processing
            ])
            logger.info(f"Successfully formatted {len(news_items)} news articles for {symbol}")
            return f"Recent news articles found:\n{formatted_news}"
        else:
            logger.warning(f"No news articles found for {symbol} from Google News")
            return f"No recent news articles found for {base_symbol} (AAPL.US)."
            
    except Exception as e:
        logger.error(f"Failed to fetch news for {symbol}: {e}", exc_info=True)
        return "Unable to fetch recent news at this time."


def _search_google_news(symbol: str) -> List[Dict]:
    """
    Search Google News for stock-related articles.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        List of news items
    """
    news_items = []
    
    try:
        # Use the most effective single query instead of multiple queries
        query = f"{symbol} stock news"
        if symbol == "AAPL":
            query = "Apple AAPL stock news"
        elif symbol == "AMZN":
            query = "Amazon AMZN stock news"
        elif symbol == "GOOGL":
            query = "Google GOOGL stock news"
        elif symbol == "MSFT":
            query = "Microsoft MSFT stock news"
        elif symbol == "TSLA":
            query = "Tesla TSLA stock news"
        
        # Google News search URL
        url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Searching Google News with query: {query}")
        response = requests.get(url, headers=headers, timeout=8)  # Reduced timeout
        response.raise_for_status()
        
        # Parse RSS feed with fallback parsers
        try:
            soup = BeautifulSoup(response.content, 'xml')
        except Exception:
            # Fallback to html.parser if xml parser not available
            soup = BeautifulSoup(response.content, 'html.parser')
        
        items = soup.find_all('item')
        logger.info(f"Found {len(items)} items for query: {query}")
        
        for item in items[:6]:  # Get top 6 articles only
            title = item.find('title')
            pub_date = item.find('pubDate')
            source = item.find('source')
            description = item.find('description')
            
            if title and title.text.strip():
                news_item = {
                    'title': title.text.strip(),
                    'snippet': description.text.strip()[:150] + "..." if description and description.text else None,  # Shorter snippets
                    'source': source.text.strip() if source and source.text else 'Google News',
                    'date': _parse_date(pub_date.text if pub_date and pub_date.text else '')
                }
                news_items.append(news_item)
                
    except Exception as e:
        logger.error(f"Google News search failed: {e}")
    
    logger.info(f"Google News returned {len(news_items)} items for {symbol}")
    return news_items




def _parse_date(date_str: str) -> str:
    """
    Parse and format date string.
    
    Args:
        date_str: Raw date string
        
    Returns:
        Formatted date string
    """
    try:
        if not date_str:
            return 'Recent'
        
        # Try to parse common date formats
        for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return 'Recent'
    except Exception:
        return 'Recent'


def _generate_prompt(symbol: str, analysis_type: str, news_content: str = "") -> str:
    """
    Generate appropriate prompt based on symbol, analysis type, and news content.
    
    Args:
        symbol: Stock symbol (e.g., AAPL.US)
        analysis_type: Type of analysis requested
        news_content: Recent news content from web search
        
    Returns:
        Formatted prompt string for OpenAI API
    """
    base_symbol = symbol.split('.')[0]  # Remove market code for readability
    
    prompts = {
        "news": f"""
        Analyze the latest news and developments for {base_symbol} ({symbol}) stock.
        
        {news_content if news_content else "Based on general market knowledge:"}
        
        Please provide:
        1. **Key Development**: Combine recent news summary with how these developments might affect the stock price
        2. **Sentiment**: Combine current investor sentiment with key risks and opportunities investors should watch
        3. **Overall Sentiment Classification**: Classify the overall sentiment as exactly one word: POSITIVE, NEUTRAL, or NEGATIVE
        
        Keep sections 1-2 concise (2-3 sentences each) and focus on actionable insights.
        """,
        
        "technical": f"""
        Provide a technical analysis framework for {base_symbol} ({symbol}) stock:
        
        1. **Key Technical Levels**: Important support and resistance levels to monitor
        2. **Trend Analysis**: Current trend direction and momentum indicators
        3. **Volume Patterns**: What volume trends typically signal for this stock
        4. **Technical Indicators**: Key indicators (RSI, MACD, moving averages) to watch
        5. **Trading Outlook**: Short-term and medium-term technical perspective
        
        Focus on actionable technical analysis insights.
        """,
        
        "fundamental": f"""
        Provide fundamental analysis for {base_symbol} ({symbol}) stock:
        
        1. **Business Model**: Core revenue drivers and competitive advantages
        2. **Financial Health**: Key metrics and ratios to monitor
        3. **Growth Prospects**: Long-term growth drivers and opportunities
        4. **Valuation**: How to assess if the stock is fairly valued
        5. **Risk Factors**: Key business and financial risks
        
        Focus on long-term investment considerations.
        """,
        
        "all": f"""
        Provide comprehensive analysis for {base_symbol} ({symbol}) stock:
        
        **Recent News & Developments:**
        {news_content if news_content else "Based on general market knowledge of this company:"}
        
        **Analysis Framework:**
        1. **News Impact**: How recent developments affect the investment thesis
        2. **Technical Outlook**: Key price levels and trend analysis
        3. **Fundamental Strengths**: Core business drivers and competitive position
        4. **Investment Considerations**: Key factors for investors to monitor
        5. **Risk Assessment**: Primary risks and opportunities
        
        Provide a balanced, comprehensive view for investors.
        """
    }
    
    return prompts.get(analysis_type, prompts["news"])