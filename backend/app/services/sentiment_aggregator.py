from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.services.sentiment_analysis import sentiment_analyzer
from app.services.news_aggregator import news_aggregator
from app.services.social_media_analyzer import social_media_analyzer
import logging

logger = logging.getLogger(__name__)

class SentimentAggregator:
    def __init__(self):
        self.sentiment_analyzer = sentiment_analyzer
        self.news_aggregator = news_aggregator
        self.social_media_analyzer = social_media_analyzer

    async def aggregate_sentiment(self, symbol: str) -> Dict:
        """Aggregate sentiment from all sources"""
        try:
            # Get data from all sources
            news_data = await self.news_aggregator.get_news_summary(symbol)
            social_data = await self.social_media_analyzer.get_social_media_summary(symbol)
            
            # Analyze news sentiment
            news_sentiment = self.sentiment_analyzer.analyze_news(news_data["articles"])
            
            # Analyze social media sentiment
            social_sentiment = self.sentiment_analyzer.analyze_social_media(social_data["latest_posts"])
            
            # Calculate weighted sentiment score
            weights = {
                "news": 0.4,
                "social_media": 0.3,
                "technical": 0.3  # Placeholder for technical analysis
            }
            
            weighted_score = (
                news_sentiment["compound"] * weights["news"] +
                social_sentiment["compound"] * weights["social_media"]
            )
            
            # Calculate sentiment trend
            historical_sentiment = self.sentiment_analyzer.calculate_historical_sentiment(symbol)
            trend = self._calculate_trend(historical_sentiment)
            
            return {
                "symbol": symbol,
                "timestamp": datetime.utcnow(),
                "overall_sentiment": {
                    "score": weighted_score,
                    "trend": trend,
                    "confidence": self._calculate_confidence(news_data, social_data)
                },
                "source_sentiments": {
                    "news": news_sentiment,
                    "social_media": social_sentiment
                },
                "metrics": {
                    "news_volume": len(news_data["articles"]),
                    "social_volume": social_data["total_posts"],
                    "engagement": social_data["total_engagement"]
                },
                "sources": {
                    "news_sources": news_data["sources"],
                    "social_platforms": social_data["platforms"]
                }
            }
        except Exception as e:
            logger.error(f"Error aggregating sentiment for {symbol}: {str(e)}")
            return self._get_error_response(symbol)

    def _calculate_trend(self, historical_data: pd.DataFrame) -> str:
        """Calculate sentiment trend from historical data"""
        if historical_data.empty:
            return "neutral"
            
        recent_sentiment = historical_data["sentiment"].tail(5).mean()
        previous_sentiment = historical_data["sentiment"].tail(10).head(5).mean()
        
        if recent_sentiment > previous_sentiment + 0.1:
            return "bullish"
        elif recent_sentiment < previous_sentiment - 0.1:
            return "bearish"
        return "neutral"

    def _calculate_confidence(self, news_data: Dict, social_data: Dict) -> float:
        """Calculate confidence score based on data volume and quality"""
        confidence_factors = {
            "news_volume": min(len(news_data["articles"]) / 50, 1.0),
            "social_volume": min(social_data["total_posts"] / 100, 1.0),
            "engagement": min(social_data["total_engagement"] / 1000, 1.0)
        }
        
        return sum(confidence_factors.values()) / len(confidence_factors)

    def _get_error_response(self, symbol: str) -> Dict:
        """Return error response when sentiment aggregation fails"""
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow(),
            "error": "Failed to aggregate sentiment data",
            "overall_sentiment": {
                "score": 0.0,
                "trend": "neutral",
                "confidence": 0.0
            },
            "source_sentiments": {},
            "metrics": {
                "news_volume": 0,
                "social_volume": 0,
                "engagement": 0
            },
            "sources": {
                "news_sources": [],
                "social_platforms": {}
            }
        }

sentiment_aggregator = SentimentAggregator() 