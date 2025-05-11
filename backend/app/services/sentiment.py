import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional
import logging
from app.core.config import settings
from app.db.mongodb import get_database
from app.models.sentiment import SentimentData

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.analyzer = SentimentIntensityAnalyzer()
        self.db = get_database()

    async def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze the sentiment of a given text using VADER.
        Returns a dictionary with compound, pos, neu, and neg scores.
        """
        try:
            scores = self.analyzer.polarity_scores(text)
            return {
                'compound': scores['compound'],
                'positive': scores['pos'],
                'neutral': scores['neu'],
                'negative': scores['neg']
            }
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {
                'compound': 0.0,
                'positive': 0.0,
                'neutral': 1.0,
                'negative': 0.0
            }

    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Analyze a batch of texts and return their sentiment scores.
        """
        return [await self.analyze_text(text) for text in texts]

    async def get_sentiment_history(self, symbol: str, days: int = 30) -> List[SentimentData]:
        """
        Retrieve sentiment history for a symbol from the database.
        """
        try:
            collection = self.db.sentiment_data
            start_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = collection.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', -1)
            
            return [SentimentData(**doc) async for doc in cursor]
        except Exception as e:
            logger.error(f"Error retrieving sentiment history: {str(e)}")
            return []

    async def calculate_aggregate_sentiment(self, symbol: str, days: int = 1) -> Dict[str, float]:
        """
        Calculate aggregate sentiment scores for a symbol over a given period.
        """
        try:
            collection = self.db.sentiment_data
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    '$match': {
                        'symbol': symbol,
                        'timestamp': {'$gte': start_date}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'avg_compound': {'$avg': '$compound_score'},
                        'avg_positive': {'$avg': '$positive_score'},
                        'avg_neutral': {'$avg': '$neutral_score'},
                        'avg_negative': {'$avg': '$negative_score'},
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            result = await collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                return {
                    'compound_score': result[0]['avg_compound'],
                    'positive_score': result[0]['avg_positive'],
                    'neutral_score': result[0]['avg_neutral'],
                    'negative_score': result[0]['avg_negative'],
                    'sample_size': result[0]['count']
                }
            return {
                'compound_score': 0.0,
                'positive_score': 0.0,
                'neutral_score': 1.0,
                'negative_score': 0.0,
                'sample_size': 0
            }
        except Exception as e:
            logger.error(f"Error calculating aggregate sentiment: {str(e)}")
            return {
                'compound_score': 0.0,
                'positive_score': 0.0,
                'neutral_score': 1.0,
                'negative_score': 0.0,
                'sample_size': 0
            }

    async def store_sentiment_data(self, symbol: str, text: str, source: str) -> Optional[SentimentData]:
        """
        Analyze text sentiment and store the results in the database.
        """
        try:
            scores = await self.analyze_text(text)
            
            sentiment_data = SentimentData(
                symbol=symbol,
                text=text,
                source=source,
                compound_score=scores['compound'],
                positive_score=scores['positive'],
                neutral_score=scores['neutral'],
                negative_score=scores['negative'],
                timestamp=datetime.utcnow()
            )
            
            collection = self.db.sentiment_data
            await collection.insert_one(sentiment_data.dict())
            
            return sentiment_data
        except Exception as e:
            logger.error(f"Error storing sentiment data: {str(e)}")
            return None

sentiment_analyzer = SentimentAnalyzer() 