import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.db.mongodb import get_database
from app.services.cache import redis_cache

class AnalyticsService:
    def __init__(self):
        self.db = get_database()

    async def analyze_sentiment_trends(self, symbol: str, days: int = 7) -> Dict:
        """
        Analyze sentiment trends over time.
        """
        try:
            # Try to get from cache first
            cached_data = await redis_cache.get_analytics(symbol, f'sentiment_trends_{days}')
            if cached_data:
                return cached_data

            # Get sentiment data from database
            collection = self.db.sentiment_data
            start_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = collection.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', 1)
            
            data = await cursor.to_list(length=None)
            if not data:
                return {}

            # Convert to DataFrame for analysis
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            
            # Calculate daily averages
            daily_avg = df.groupby('date').agg({
                'compound_score': 'mean',
                'positive_score': 'mean',
                'negative_score': 'mean',
                'neutral_score': 'mean'
            }).reset_index()

            # Calculate trends
            trends = {
                'daily_averages': daily_avg.to_dict('records'),
                'overall_trend': self._calculate_trend(daily_avg['compound_score']),
                'sentiment_volatility': daily_avg['compound_score'].std(),
                'positive_ratio': (daily_avg['positive_score'] > daily_avg['negative_score']).mean(),
                'sentiment_momentum': self._calculate_momentum(daily_avg['compound_score'])
            }

            # Cache the results
            await redis_cache.set_analytics(symbol, f'sentiment_trends_{days}', trends)
            
            return trends

        except Exception as e:
            logger.error(f"Error in analyze_sentiment_trends: {str(e)}")
            return {}

    async def analyze_social_impact(self, symbol: str, days: int = 7) -> Dict:
        """
        Analyze social media impact on sentiment.
        """
        try:
            cached_data = await redis_cache.get_analytics(symbol, f'social_impact_{days}')
            if cached_data:
                return cached_data

            # Get social media data
            collection = self.db.social_data
            start_date = datetime.utcnow() - timedelta(days=days)
            
            cursor = collection.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', 1)
            
            data = await cursor.to_list(length=None)
            if not data:
                return {}

            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['timestamp']).dt.date

            # Analyze by source
            source_analysis = {}
            for source in df['source'].unique():
                source_df = df[df['source'] == source]
                source_analysis[source] = {
                    'volume': len(source_df),
                    'avg_sentiment': source_df['compound_score'].mean(),
                    'sentiment_distribution': {
                        'positive': (source_df['compound_score'] > 0.2).mean(),
                        'neutral': ((source_df['compound_score'] >= -0.2) & 
                                  (source_df['compound_score'] <= 0.2)).mean(),
                        'negative': (source_df['compound_score'] < -0.2).mean()
                    }
                }

            # Calculate engagement metrics
            engagement = {
                'total_mentions': len(df),
                'source_distribution': df['source'].value_counts().to_dict(),
                'engagement_trend': self._calculate_engagement_trend(df),
                'source_analysis': source_analysis
            }

            await redis_cache.set_analytics(symbol, f'social_impact_{days}', engagement)
            return engagement

        except Exception as e:
            logger.error(f"Error in analyze_social_impact: {str(e)}")
            return {}

    async def analyze_market_correlation(self, symbol: str, days: int = 30) -> Dict:
        """
        Analyze correlation between sentiment and price movements.
        """
        try:
            cached_data = await redis_cache.get_analytics(symbol, f'market_correlation_{days}')
            if cached_data:
                return cached_data

            # Get price and sentiment data
            price_collection = self.db.price_data
            sentiment_collection = self.db.sentiment_data
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get price data
            price_cursor = price_collection.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', 1)
            
            price_data = await price_cursor.to_list(length=None)
            if not price_data:
                return {}

            # Get sentiment data
            sentiment_cursor = sentiment_collection.find({
                'symbol': symbol,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', 1)
            
            sentiment_data = await sentiment_cursor.to_list(length=None)
            if not sentiment_data:
                return {}

            # Convert to DataFrames
            price_df = pd.DataFrame(price_data)
            sentiment_df = pd.DataFrame(sentiment_data)

            # Calculate daily returns and sentiment
            price_df['date'] = pd.to_datetime(price_df['timestamp']).dt.date
            price_df['returns'] = price_df['close'].pct_change()
            
            sentiment_df['date'] = pd.to_datetime(sentiment_df['timestamp']).dt.date
            daily_sentiment = sentiment_df.groupby('date')['compound_score'].mean()

            # Calculate correlations
            correlation = price_df.set_index('date')['returns'].corr(daily_sentiment)
            
            # Calculate lead-lag relationship
            lead_lag = self._calculate_lead_lag(price_df['returns'], daily_sentiment)

            analysis = {
                'correlation': correlation,
                'lead_lag_analysis': lead_lag,
                'sentiment_impact': self._calculate_sentiment_impact(price_df, daily_sentiment)
            }

            await redis_cache.set_analytics(symbol, f'market_correlation_{days}', analysis)
            return analysis

        except Exception as e:
            logger.error(f"Error in analyze_market_correlation: {str(e)}")
            return {}

    def _calculate_trend(self, series: pd.Series) -> str:
        """Calculate trend direction."""
        if len(series) < 2:
            return 'neutral'
        
        slope = np.polyfit(range(len(series)), series, 1)[0]
        if slope > 0.01:
            return 'increasing'
        elif slope < -0.01:
            return 'decreasing'
        return 'neutral'

    def _calculate_momentum(self, series: pd.Series) -> float:
        """Calculate momentum indicator."""
        if len(series) < 2:
            return 0.0
        return series.iloc[-1] - series.iloc[0]

    def _calculate_engagement_trend(self, df: pd.DataFrame) -> Dict:
        """Calculate engagement trend over time."""
        daily_volume = df.groupby('date').size()
        return {
            'trend': self._calculate_trend(daily_volume),
            'growth_rate': (daily_volume.iloc[-1] / daily_volume.iloc[0] - 1) 
                          if len(daily_volume) > 1 else 0
        }

    def _calculate_lead_lag(self, returns: pd.Series, sentiment: pd.Series) -> Dict:
        """Calculate lead-lag relationship between returns and sentiment."""
        max_lag = 5
        correlations = []
        
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = returns.corr(sentiment.shift(-lag))
            else:
                corr = returns.shift(lag).corr(sentiment)
            correlations.append({'lag': lag, 'correlation': corr})
        
        return {
            'correlations': correlations,
            'best_lag': max(correlations, key=lambda x: abs(x['correlation']))['lag']
        }

    def _calculate_sentiment_impact(self, price_df: pd.DataFrame, sentiment: pd.Series) -> Dict:
        """Calculate impact of sentiment on price movements."""
        # Group returns by sentiment direction
        sentiment_direction = pd.cut(sentiment, 
                                   bins=[-float('inf'), -0.2, 0.2, float('inf')],
                                   labels=['negative', 'neutral', 'positive'])
        
        returns_by_sentiment = price_df['returns'].groupby(sentiment_direction).agg(['mean', 'std'])
        
        return {
            'returns_by_sentiment': returns_by_sentiment.to_dict(),
            'sentiment_effectiveness': abs(returns_by_sentiment.loc['positive', 'mean'] - 
                                        returns_by_sentiment.loc['negative', 'mean'])
        }

analytics_service = AnalyticsService() 