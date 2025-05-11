from datetime import datetime
from pydantic import BaseModel, Field

class PriceData(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "timestamp": "2024-01-01T12:00:00Z",
                "open": 150.0,
                "high": 152.0,
                "low": 149.0,
                "close": 151.0,
                "volume": 1000000
            }
        } 