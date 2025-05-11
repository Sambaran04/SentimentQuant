from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional

class TechnicalData(BaseModel):
    symbol: str
    indicators: Dict[str, Dict]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "indicators": {
                    "RSI": {
                        "value": 65.5,
                        "signal": "neutral"
                    },
                    "MACD": {
                        "value": {
                            "macd": 2.5,
                            "signal": 1.8,
                            "histogram": 0.7
                        },
                        "signal": "buy"
                    },
                    "Bollinger Bands": {
                        "value": {
                            "upper": 180.5,
                            "middle": 175.0,
                            "lower": 169.5
                        },
                        "signal": "neutral"
                    },
                    "Moving Averages": {
                        "value": {
                            "sma_20": 175.5,
                            "sma_50": 172.0,
                            "sma_200": 165.0,
                            "ema_20": 176.0
                        },
                        "signal": "buy"
                    },
                    "Volume": {
                        "value": {
                            "obv": 1500000,
                            "volume_sma": 1000000
                        },
                        "signal": "strong"
                    }
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        } 