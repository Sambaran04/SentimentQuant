from typing import Dict, List, Optional, Tuple
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        # Initialize NLTK
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.sia = SentimentIntensityAnalyzer()
        
        # Initialize FinBERT
        self.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.finbert_model.eval()

    def analyze_text(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of a single text using both VADER and FinBERT"""
        # VADER analysis
        vader_scores = self.sia.polarity_scores(text)
        
        # FinBERT analysis
        inputs = self.finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.finbert_model(**inputs)
            finbert_scores = torch.softmax(outputs.logits, dim=1)[0].tolist()
        
        # Combine scores
        return {
            "vader": {
                "compound": vader_scores["compound"],
                "pos": vader_scores["pos"],
                "neg": vader_scores["neg"],
                "neu": vader_scores["neu"]
            },
            "finbert": {
                "positive": finbert_scores[0],
                "negative": finbert_scores[1],
                "neutral": finbert_scores[2]
            },
            "combined_score": (vader_scores["compound"] + (finbert_scores[0] - finbert_scores[1])) / 2
        }

    def analyze_news(self, news_items: List[Dict]) -> Dict[str, float]:
        """Analyze sentiment of news articles"""
        if not news_items:
            return {"score": 0.0, "count": 0}
        
        scores = []
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('description', '')}"
            sentiment = self.analyze_text(text)
            scores.append(sentiment["combined_score"])
        
        return {
            "score": sum(scores) / len(scores),
            "count": len(scores),
            "timestamp": datetime.utcnow()
        }

    def analyze_social_media(self, posts: List[Dict]) -> Dict[str, float]:
        """Analyze sentiment of social media posts"""
        if not posts:
            return {"score": 0.0, "count": 0}
        
        scores = []
        for post in posts:
            text = post.get("text", "")
            sentiment = self.analyze_text(text)
            scores.append(sentiment["combined_score"])
        
        return {
            "score": sum(scores) / len(scores),
            "count": len(scores),
            "timestamp": datetime.utcnow()
        }

    def calculate_historical_sentiment(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Calculate historical sentiment scores"""
        # This would typically fetch data from your database
        # For now, we'll return a sample DataFrame
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        return pd.DataFrame({
            'date': dates,
            'news_sentiment': [0.5] * len(dates),  # Replace with actual data
            'social_sentiment': [0.3] * len(dates),  # Replace with actual data
            'combined_sentiment': [0.4] * len(dates)  # Replace with actual data
        })

    def get_sentiment_summary(self, symbol: str) -> Dict:
        """Get a summary of sentiment analysis for a symbol"""
        # This would typically fetch data from your database
        return {
            "symbol": symbol,
            "current_sentiment": {
                "score": 0.5,  # Replace with actual data
                "trend": "neutral",
                "confidence": 0.8
            },
            "historical": {
                "daily": [0.4, 0.5, 0.6],  # Last 3 days
                "weekly": [0.45, 0.5, 0.55],  # Last 3 weeks
                "monthly": [0.48, 0.5, 0.52]  # Last 3 months
            },
            "sources": {
                "news": 0.6,
                "social_media": 0.4,
                "analyst_reports": 0.7
            },
            "timestamp": datetime.utcnow()
        }

sentiment_analyzer = SentimentAnalyzer() 