from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class Comment(BaseModel):
    text: str
    score: int
    created_at: datetime

class SocialData(BaseModel):
    symbol: str
    type: str  # 'tweet' or 'post'
    text: str
    title: Optional[str] = None
    created_at: datetime
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str  # 'twitter' or 'reddit'
    metrics: Optional[Dict] = None
    username: Optional[str] = None
    user_metrics: Optional[Dict] = None
    score: Optional[int] = None
    subreddit: Optional[str] = None
    url: Optional[str] = None
    comments: Optional[List[Comment]] = None
    compound_score: float = 0.0
    positive_score: float = 0.0
    neutral_score: float = 0.0
    negative_score: float = 0.0
    comment_sentiments: Optional[List[Dict]] = None

    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "type": "tweet",
                "text": "Apple's new iPhone sales exceed expectations",
                "created_at": "2024-01-01T12:00:00Z",
                "timestamp": "2024-01-01T12:00:00Z",
                "source": "twitter",
                "metrics": {
                    "retweet_count": 100,
                    "reply_count": 50,
                    "like_count": 200,
                    "quote_count": 30
                },
                "username": "trader123",
                "user_metrics": {
                    "followers_count": 1000,
                    "following_count": 500,
                    "tweet_count": 5000
                },
                "compound_score": 0.6369,
                "positive_score": 0.636,
                "neutral_score": 0.364,
                "negative_score": 0.0
            }
        } 