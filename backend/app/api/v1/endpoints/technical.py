from fastapi import APIRouter, HTTPException
from app.services.technical_analyzer import technical_analyzer
from typing import Optional

router = APIRouter()

@router.get("/analyze/{ticker}")
async def analyze_technical(
    ticker: str,
    period: Optional[str] = "1y",
    interval: Optional[str] = "1d"
):
    """Get technical indicators and signals for a ticker."""
    try:
        result = await technical_analyzer.analyze(ticker, period, interval)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 