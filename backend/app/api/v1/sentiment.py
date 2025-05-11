from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.services.sentiment import sentiment_analyzer
from app.models.sentiment import SentimentData
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/analyze", response_model=SentimentData)
async def analyze_sentiment(
    text: str,
    symbol: str,
    source: str,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze the sentiment of a given text for a specific symbol.
    """
    try:
        result = await sentiment_analyzer.store_sentiment_data(symbol, text, source)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to analyze sentiment")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}", response_model=List[SentimentData])
async def get_sentiment_history(
    symbol: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get sentiment history for a symbol.
    """
    try:
        history = await sentiment_analyzer.get_sentiment_history(symbol, days)
        return history
    except Exception as e:
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
        raise HTTPException(status_code=500, detail=str(e)) 