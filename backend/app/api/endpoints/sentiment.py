from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.services.sentiment_aggregator import sentiment_aggregator
from app.core.auth import get_current_user
from app.models.user import User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/sentiment/{symbol}")
async def get_sentiment(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get sentiment analysis for a stock symbol
    """
    try:
        sentiment_data = await sentiment_aggregator.aggregate_sentiment(symbol)
        return sentiment_data
    except Exception as e:
        logger.error(f"Error getting sentiment for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sentiment data for {symbol}"
        )

@router.get("/sentiment/{symbol}/historical")
async def get_historical_sentiment(
    symbol: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get historical sentiment data for a stock symbol
    """
    try:
        # Get historical sentiment data
        historical_data = sentiment_aggregator.sentiment_analyzer.calculate_historical_sentiment(symbol)
        
        # Filter for requested time period
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filtered_data = historical_data[historical_data.index >= cutoff_date]
        
        return {
            "symbol": symbol,
            "period_days": days,
            "data": filtered_data.to_dict(orient="records"),
            "summary": {
                "mean_sentiment": filtered_data["sentiment"].mean(),
                "std_sentiment": filtered_data["sentiment"].std(),
                "trend": sentiment_aggregator._calculate_trend(filtered_data)
            }
        }
    except Exception as e:
        logger.error(f"Error getting historical sentiment for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get historical sentiment data for {symbol}"
        )

@router.get("/sentiment/{symbol}/sources")
async def get_sentiment_sources(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get sentiment analysis from individual sources
    """
    try:
        # Get news sentiment
        news_data = await sentiment_aggregator.news_aggregator.get_news_summary(symbol)
        news_sentiment = sentiment_aggregator.sentiment_analyzer.analyze_news(news_data["articles"])
        
        # Get social media sentiment
        social_data = await sentiment_aggregator.social_media_analyzer.get_social_media_summary(symbol)
        social_sentiment = sentiment_aggregator.sentiment_analyzer.analyze_social_media(social_data["latest_posts"])
        
        return {
            "symbol": symbol,
            "timestamp": datetime.utcnow(),
            "sources": {
                "news": {
                    "sentiment": news_sentiment,
                    "articles": news_data["articles"][:5]  # Return top 5 articles
                },
                "social_media": {
                    "sentiment": social_sentiment,
                    "posts": social_data["latest_posts"][:5]  # Return top 5 posts
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting sentiment sources for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sentiment source data for {symbol}"
        ) 