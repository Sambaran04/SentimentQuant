from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SentimentData(BaseModel):
    symbol: str
    text: str
    source: str
    compound_score: float
    positive_score: float
    neutral_score: float
    negative_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "text": "Apple's new iPhone sales exceed expectations",
                "source": "news",
                "compound_score": 0.6369,
                "positive_score": 0.636,
                "neutral_score": 0.364,
                "negative_score": 0.0,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        } 