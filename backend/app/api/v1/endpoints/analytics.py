from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from app.services.analytics import analytics_service
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/sentiment-trends/{symbol}")
async def get_sentiment_trends(
    symbol: str,
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Get sentiment trends analysis for a symbol.
    """
    try:
        trends = await analytics_service.analyze_sentiment_trends(symbol, days)
        if not trends:
            raise HTTPException(status_code=404, detail="No sentiment data available")
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/social-impact/{symbol}")
async def get_social_impact(
    symbol: str,
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Get social media impact analysis for a symbol.
    """
    try:
        impact = await analytics_service.analyze_social_impact(symbol, days)
        if not impact:
            raise HTTPException(status_code=404, detail="No social media data available")
        return impact
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-correlation/{symbol}")
async def get_market_correlation(
    symbol: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get market correlation analysis for a symbol.
    """
    try:
        correlation = await analytics_service.analyze_market_correlation(symbol, days)
        if not correlation:
            raise HTTPException(status_code=404, detail="No data available for correlation analysis")
        return correlation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 