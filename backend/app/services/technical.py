import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from app.db.mongodb import get_database
from app.models.technical import TechnicalData

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    def __init__(self):
        self.db = get_database()

    async def get_price_data(self, symbol: str, timeframe: str = '1d', limit: int = 100) -> pd.DataFrame:
        """
        Retrieve price data from the database and convert to pandas DataFrame.
        """
        try:
            collection = self.db.price_data
            cursor = collection.find(
                {'symbol': symbol},
                sort=[('timestamp', -1)],
                limit=limit
            )
            
            data = await cursor.to_list(length=limit)
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df = df.sort_values('timestamp')
            return df
        except Exception as e:
            logger.error(f"Error retrieving price data: {str(e)}")
            return pd.DataFrame()

    async def calculate_indicators(self, symbol: str) -> Dict[str, Dict]:
        """
        Calculate various technical indicators for a symbol.
        """
        try:
            df = await self.get_price_data(symbol)
            if df.empty:
                return {}

            # Convert price data to numpy arrays for talib
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values

            # Calculate indicators
            indicators = {
                'RSI': {
                    'value': talib.RSI(close)[-1],
                    'signal': self._get_rsi_signal(talib.RSI(close)[-1])
                },
                'MACD': {
                    'value': self._calculate_macd(close),
                    'signal': self._get_macd_signal(close)
                },
                'Bollinger Bands': {
                    'value': self._calculate_bollinger_bands(close),
                    'signal': self._get_bb_signal(close)
                },
                'Moving Averages': {
                    'value': self._calculate_moving_averages(close),
                    'signal': self._get_ma_signal(close)
                },
                'Volume': {
                    'value': self._calculate_volume_indicators(close, volume),
                    'signal': self._get_volume_signal(volume)
                }
            }

            # Store the results
            await self.store_technical_data(symbol, indicators)

            return indicators
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return {}

    def _get_rsi_signal(self, rsi: float) -> str:
        """Determine RSI signal."""
        if rsi > 70:
            return 'sell'
        elif rsi < 30:
            return 'buy'
        return 'neutral'

    def _calculate_macd(self, close: np.ndarray) -> Dict[str, float]:
        """Calculate MACD values."""
        macd, signal, hist = talib.MACD(close)
        return {
            'macd': macd[-1],
            'signal': signal[-1],
            'histogram': hist[-1]
        }

    def _get_macd_signal(self, close: np.ndarray) -> str:
        """Determine MACD signal."""
        macd, signal, _ = talib.MACD(close)
        if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
            return 'buy'
        elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
            return 'sell'
        return 'neutral'

    def _calculate_bollinger_bands(self, close: np.ndarray) -> Dict[str, float]:
        """Calculate Bollinger Bands."""
        upper, middle, lower = talib.BBANDS(close)
        return {
            'upper': upper[-1],
            'middle': middle[-1],
            'lower': lower[-1]
        }

    def _get_bb_signal(self, close: np.ndarray) -> str:
        """Determine Bollinger Bands signal."""
        upper, middle, lower = talib.BBANDS(close)
        if close[-1] < lower[-1]:
            return 'buy'
        elif close[-1] > upper[-1]:
            return 'sell'
        return 'neutral'

    def _calculate_moving_averages(self, close: np.ndarray) -> Dict[str, float]:
        """Calculate various moving averages."""
        return {
            'sma_20': talib.SMA(close, timeperiod=20)[-1],
            'sma_50': talib.SMA(close, timeperiod=50)[-1],
            'sma_200': talib.SMA(close, timeperiod=200)[-1],
            'ema_20': talib.EMA(close, timeperiod=20)[-1]
        }

    def _get_ma_signal(self, close: np.ndarray) -> str:
        """Determine Moving Average signal."""
        sma_20 = talib.SMA(close, timeperiod=20)
        sma_50 = talib.SMA(close, timeperiod=50)
        
        if sma_20[-1] > sma_50[-1] and sma_20[-2] <= sma_50[-2]:
            return 'buy'
        elif sma_20[-1] < sma_50[-1] and sma_20[-2] >= sma_50[-2]:
            return 'sell'
        return 'neutral'

    def _calculate_volume_indicators(self, close: np.ndarray, volume: np.ndarray) -> Dict[str, float]:
        """Calculate volume-based indicators."""
        return {
            'obv': talib.OBV(close, volume)[-1],
            'volume_sma': talib.SMA(volume, timeperiod=20)[-1]
        }

    def _get_volume_signal(self, volume: np.ndarray) -> str:
        """Determine volume signal."""
        volume_sma = talib.SMA(volume, timeperiod=20)
        if volume[-1] > volume_sma[-1] * 1.5:
            return 'strong'
        elif volume[-1] < volume_sma[-1] * 0.5:
            return 'weak'
        return 'normal'

    async def store_technical_data(self, symbol: str, indicators: Dict[str, Dict]) -> Optional[TechnicalData]:
        """
        Store technical analysis results in the database.
        """
        try:
            technical_data = TechnicalData(
                symbol=symbol,
                indicators=indicators,
                timestamp=datetime.utcnow()
            )
            
            collection = self.db.technical_data
            await collection.insert_one(technical_data.dict())
            
            return technical_data
        except Exception as e:
            logger.error(f"Error storing technical data: {str(e)}")
            return None

    async def get_technical_history(self, symbol: str, days: int = 30) -> List[TechnicalData]:
        """
        Retrieve technical analysis history for a symbol.
        """
        try:
            collection = self.db.technical_data
            start_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = collection.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', -1)
            
            return [TechnicalData(**doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Error retrieving technical history: {str(e)}")
            return []

technical_analyzer = TechnicalAnalyzer() 