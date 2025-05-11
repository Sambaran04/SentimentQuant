from typing import List, Dict, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class NewsAggregator:
    def __init__(self):
        self.news_api_key = settings.NEWS_API_KEY
        self.alpha_vantage_key = settings.ALPHA_VANTAGE_API_KEY

    async def fetch_news_api_articles(self, symbol: str) -> List[Dict]:
        """Fetch news articles from News API"""
        url = f"https://newsapi.org/v2/everything"
        params = {
            "q": symbol,
            "apiKey": self.news_api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 100
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("articles", [])
                    else:
                        logger.error(f"News API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching news: {str(e)}")
                return []

    async def fetch_alpha_vantage_news(self, symbol: str) -> List[Dict]:
        """Fetch news from Alpha Vantage"""
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "apikey": self.alpha_vantage_key
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("feed", [])
                    else:
                        logger.error(f"Alpha Vantage error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching Alpha Vantage news: {str(e)}")
                return []

    async def get_company_news(self, symbol: str) -> List[Dict]:
        """Get news from multiple sources"""
        tasks = [
            self.fetch_news_api_articles(symbol),
            self.fetch_alpha_vantage_news(symbol)
        ]
        
        results = await asyncio.gather(*tasks)
        all_news = []
        
        # Process News API results
        for article in results[0]:
            all_news.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "source": article.get("source", {}).get("name"),
                "published_at": article.get("publishedAt"),
                "content": article.get("content")
            })
        
        # Process Alpha Vantage results
        for article in results[1]:
            all_news.append({
                "title": article.get("title"),
                "description": article.get("summary"),
                "url": article.get("url"),
                "source": article.get("source"),
                "published_at": article.get("time_published"),
                "content": article.get("summary")
            })
        
        # Sort by published date
        all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        return all_news

    async def get_news_summary(self, symbol: str) -> Dict:
        """Get a summary of news for a symbol"""
        news = await self.get_company_news(symbol)
        
        return {
            "symbol": symbol,
            "total_articles": len(news),
            "latest_news": news[:5] if news else [],
            "sources": list(set(article["source"] for article in news if article.get("source"))),
            "timestamp": datetime.utcnow()
        }

news_aggregator = NewsAggregator() 