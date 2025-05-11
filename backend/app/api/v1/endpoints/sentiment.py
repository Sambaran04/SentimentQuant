from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.services.sentiment_analyzer import sentiment_analyzer
from app.models.sentiment import SentimentData
from app.db.mongodb import get_database
from datetime import datetime

router = APIRouter()

@router.post("/analyze")
async def analyze_sentiment(
    text: str,
    model: str = "vader",
    ticker: Optional[str] = None
) -> dict:
    """Analyze sentiment of given text."""
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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{ticker}")
async def get_sentiment_history(
    ticker: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[dict]:
    """Get sentiment history for a ticker."""
    try:
        db = await get_database()
        query = {"ticker": ticker}
        
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = start_date
            if end_date:
                query["date"]["$lte"] = end_date
        
        cursor = db.sentiments.find(query).sort("date", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{ticker}")
async def get_sentiment_summary(
    ticker: str,
    period: str = "1d"
) -> dict:
    """Get sentiment summary for a ticker."""
    try:
        db = await get_database()
        
        # Calculate time range based on period
        end_date = datetime.now()
        if period == "1d":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "1w":
            start_date = end_date.replace(day=end_date.day-7)
        elif period == "1m":
            start_date = end_date.replace(month=end_date.month-1)
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
            **result[0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 