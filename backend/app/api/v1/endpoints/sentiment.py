from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from app.services.sentiment_analysis import sentiment_analyzer
from app.models.sentiment import SentimentData
from app.core.auth import get_current_user
from app.models.user import User
from app.db.mongodb import get_database
from app.services.sentiment_aggregator import sentiment_aggregator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=SentimentData)
async def analyze_sentiment(
        text: str,
        symbol: str,
        source: str,
        model: str = "vader",
        current_user: User = Depends(get_current_user)
):
    """
    Analyze the sentiment of a given text for a specific symbol.
    """
    try:
        result = await sentiment_analyzer.store_sentiment_data(symbol, text, source)

        # Store in MongoDB
        sentiment_data = SentimentData(
            ticker=symbol,
            date=datetime.now(),
            sentiment_score=result.score,
            source=source,
            text=text,
            confidence=result.confidence,
            model=model
        )
        db = await get_database()
        await db.sentiments.insert_one(sentiment_data.dict())

        return result
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/simple")
async def analyze_sentiment_simple(
        text: str,
        model: str = "vader",
        ticker: Optional[str] = None
) -> dict:
    """Analyze sentiment of given text without authentication."""
    try:
        result = sentiment_analyzer.analyze(text, model)

        # Store in MongoDB if ticker is provided
        if ticker:
            sentiment_data = SentimentData(
                ticker=ticker,
                date=datetime.now(),
                sentiment_score=result["compound"],
                source="api",
                text=text,
                confidence=result["confidence"],
                model=model
            )
            db = await get_database()
            await db.sentiments.insert_one(sentiment_data.dict())

        return result
    except Exception as e:
        logger.error(f"Error analyzing simple sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[Dict])
async def analyze_batch(
        texts: List[str],
        current_user: User = Depends(get_current_user)
):
    """
    Analyze a batch of texts and return their sentiment scores.
    """
    try:
        results = await sentiment_analyzer.analyze_batch(texts)
        return results
    except Exception as e:
        logger.error(f"Error analyzing batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{symbol}", response_model=List[SentimentData])
async def get_sentiment_history(
        symbol: str,
        days: int = 30,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        current_user: User = Depends(get_current_user)
):
    """
    Get sentiment history for a symbol.
    """
    try:
        if start_date or end_date:
            # Use database query for custom date ranges
            db = await get_database()
            query = {"ticker": symbol}

            if start_date or end_date:
                query["date"] = {}
                if start_date:
                    query["date"]["$gte"] = start_date
                if end_date:
                    query["date"]["$lte"] = end_date

            cursor = db.sentiments.find(query).sort("date", -1).limit(limit)
            results = await cursor.to_list(length=limit)
            return results
        else:
            # Use existing service function for days-based queries
            history = await sentiment_analyzer.get_sentiment_history(symbol, days)
            return history
    except Exception as e:
        logger.error(f"Error getting sentiment history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aggregate/{symbol}", response_model=Dict)
async def get_aggregate_sentiment(
        symbol: str,
        days: int = 1,
        current_user: User = Depends(get_current_user)
):
    """
    Get aggregate sentiment scores for a symbol over a given period.
    """
    try:
        aggregate = await sentiment_analyzer.calculate_aggregate_sentiment(symbol, days)
        return aggregate
    except Exception as e:
        logger.error(f"Error getting aggregate sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{ticker}")
async def get_sentiment_summary(
        ticker: str,
        period: str = "1d"
) -> dict:
    """Get sentiment summary for a ticker without authentication."""
    try:
        db = await get_database()

        # Calculate time range based on period
        end_date = datetime.now()
        if period == "1d":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "1w":
            start_date = end_date - timedelta(days=7)
        elif period == "1m":
            start_date = end_date.replace(month=end_date.month - 1 if end_date.month > 1 else 12,
                                          year=end_date.year if end_date.month > 1 else end_date.year - 1)
        else:
            raise HTTPException(status_code=400, detail="Invalid period")

        # Aggregate sentiment scores
        pipeline = [
            {
                "$match": {
                    "ticker": ticker,
                    "date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_sentiment": {"$avg": "$sentiment_score"},
                    "count": {"$sum": 1},
                    "max_sentiment": {"$max": "$sentiment_score"},
                    "min_sentiment": {"$min": "$sentiment_score"}
                }
            }
        ]

        result = await db.sentiments.aggregate(pipeline).to_list(length=1)

        if not result:
            return {
                "ticker": ticker,
                "period": period,
                "avg_sentiment": 0,
                "count": 0,
                "max_sentiment": 0,
                "min_sentiment": 0
            }

        return {
            "ticker": ticker,
            "period": period,
            **{k: v for k, v in result[0].items() if k != "_id"}
        }
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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