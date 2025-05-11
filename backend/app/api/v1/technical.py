from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.services.technical import technical_analyzer
from app.models.technical import TechnicalData
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/analyze/{symbol}", response_model=Dict)
async def analyze_technical(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate technical indicators for a symbol.
    """
    try:
        indicators = await technical_analyzer.calculate_indicators(symbol)
        if not indicators:
            raise HTTPException(status_code=404, detail="No data available for symbol")
        return indicators
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}", response_model=List[TechnicalData])
async def get_technical_history(
    symbol: str,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get technical analysis history for a symbol.
    """
    try:
        history = await technical_analyzer.get_technical_history(symbol, days)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/price/{symbol}", response_model=Dict)
async def get_price_data(
    symbol: str,
    timeframe: str = '1d',
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Get price data for a symbol.
    """
    try:
        df = await technical_analyzer.get_price_data(symbol, timeframe, limit)
        if df.empty:
            raise HTTPException(status_code=404, detail="No price data available for symbol")
        
        # Convert DataFrame to dict format
        data = {
            'timestamp': df['timestamp'].tolist(),
            'open': df['open'].tolist(),
            'high': df['high'].tolist(),
            'low': df['low'].tolist(),
            'close': df['close'].tolist(),
            'volume': df['volume'].tolist()
        }
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/{symbol}", response_model=Dict)
async def get_trading_signals(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get trading signals based on technical indicators.
    """
    try:
        indicators = await technical_analyzer.calculate_indicators(symbol)
        if not indicators:
            raise HTTPException(status_code=404, detail="No signals available for symbol")
        
        # Extract signals from indicators
        signals = {
            indicator: data['signal']
            for indicator, data in indicators.items()
        }
        
        # Calculate overall signal
        buy_signals = sum(1 for signal in signals.values() if signal == 'buy')
        sell_signals = sum(1 for signal in signals.values() if signal == 'sell')
        
        if buy_signals > sell_signals:
            overall_signal = 'buy'
        elif sell_signals > buy_signals:
            overall_signal = 'sell'
        else:
            overall_signal = 'neutral'
        
        return {
            'signals': signals,
            'overall_signal': overall_signal,
            'buy_count': buy_signals,
            'sell_count': sell_signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 