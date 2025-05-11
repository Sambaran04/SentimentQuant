from datetime import datetime
from pydantic import BaseModel, Field

class NewsData(BaseModel):
    symbol: str
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: datetime
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    compound_score: float = 0.0
    positive_score: float = 0.0
    neutral_score: float = 0.0
    negative_score: float = 0.0

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "title": "Apple Announces New iPhone",
                "description": "Apple has announced its latest iPhone model",
                "content": "Full article content here...",
                "url": "https://example.com/news/1",
                "source": "Tech News",
                "published_at": "2024-01-01T12:00:00Z",
                "timestamp": "2024-01-01T12:00:00Z",
                "compound_score": 0.6369,
                "positive_score": 0.636,
                "neutral_score": 0.364,
                "negative_score": 0.0
            }
        } 