import yfinance as yf
import pandas as pd
from finta import TA
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators = {
            "SMA": TA.SMA,
            "EMA": TA.EMA,
            "RSI": TA.RSI,
            "MACD": TA.MACD,
            "BBANDS": TA.BBANDS,
            "STOCH": TA.STOCH,
            "ADX": TA.ADX
        }
    
    async def get_ohlcv_data(self, ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Fetch OHLCV data from yFinance."""
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        return df
    
    def calculate_indicators(self, df: pd.DataFrame, indicators: List[str]) -> Dict[str, pd.DataFrame]:
        """Calculate technical indicators."""
        results = {}
        for indicator in indicators:
            if indicator in self.indicators:
                results[indicator] = self.indicators[indicator](df)
        return results
    
    def generate_signals(self, df: pd.DataFrame, indicators: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Generate trading signals based on technical indicators."""
        signals = {}
        
        # RSI signals
        if "RSI" in indicators:
            rsi = indicators["RSI"].iloc[-1]
            signals["RSI"] = {
                "value": rsi,
                "signal": "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
            }
        
        # MACD signals
        if "MACD" in indicators:
            macd = indicators["MACD"]
            signals["MACD"] = {
                "value": macd["MACD"].iloc[-1],
                "signal": "buy" if macd["MACD"].iloc[-1] > macd["SIGNAL"].iloc[-1] else "sell"
            }
        
        # Bollinger Bands signals
        if "BBANDS" in indicators:
            bb = indicators["BBANDS"]
            current_price = df["Close"].iloc[-1]
            signals["BBANDS"] = {
                "value": current_price,
                "signal": "oversold" if current_price < bb["BB_LOWER"].iloc[-1] else 
                         "overbought" if current_price > bb["BB_UPPER"].iloc[-1] else "neutral"
            }
        
        return signals
    
    async def analyze(self, ticker: str, period: str = "1y", interval: str = "1d") -> Dict:
        """Perform complete technical analysis."""
        # Get OHLCV data
        df = await self.get_ohlcv_data(ticker, period, interval)
        
        # Calculate indicators
        indicators = self.calculate_indicators(df, list(self.indicators.keys()))
        
        # Generate signals
        signals = self.generate_signals(df, indicators)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "price": df["Close"].iloc[-1],
            "signals": signals,
            "indicators": {k: v.iloc[-1].to_dict() for k, v in indicators.items()}
        }

# Create singleton instance
technical_analyzer = TechnicalAnalyzer() 