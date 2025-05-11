from typing import Dict, List
from celery import Task
from app.core.celery_app import celery_app
from app.services.sentiment_aggregator import sentiment_aggregator
from app.core.redis_manager import redis_manager
import json
import logging
from datetime import datetime, timedelta
from celery.exceptions import MaxRetriesExceededError
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

# Rate limiting configuration
ONE_MINUTE = 60
MAX_REQUESTS_PER_MINUTE = 30

class BaseTaskWithRetry(Task):
    """Base task with retry logic and error handling"""
    max_retries = 3
    default_retry_delay = 60  # 1 minute

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {str(exc)}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        logger.warning(f"Task {task_id} retrying: {str(exc)}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

@sleep_and_retry
@limits(calls=MAX_REQUESTS_PER_MINUTE, period=ONE_MINUTE)
def rate_limited_aggregate_sentiment(symbol: str) -> Dict:
    """Rate-limited sentiment aggregation"""
    return sentiment_aggregator.aggregate_sentiment(symbol)

@celery_app.task(
    base=BaseTaskWithRetry,
    bind=True,
    name="analyze_sentiment",
    queue="sentiment"
)
def analyze_sentiment(self, symbol: str) -> Dict:
    """Analyze sentiment for a symbol"""
    try:
        # Check cache first
        cache_key = f"sentiment:{symbol}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        cached_result = redis_manager.cache_get(cache_key)
        
        if cached_result:
            return json.loads(cached_result)
        
        # Perform sentiment analysis
        result = rate_limited_aggregate_sentiment(symbol)
        
        # Cache the result
        redis_manager.cache_set(cache_key, json.dumps(result), expire=3600)
        
        # Publish update to Redis channel
        redis_manager.publish(f"sentiment_updates:{symbol}", json.dumps(result))
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {
                "error": f"Failed to analyze sentiment for {symbol} after {self.max_retries} retries",
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat()
            }

@celery_app.task(
    base=BaseTaskWithRetry,
    bind=True,
    name="batch_analyze_sentiment",
    queue="sentiment"
)
def batch_analyze_sentiment(self, symbols: List[str]) -> Dict[str, Dict]:
    """Analyze sentiment for multiple symbols"""
    results = {}
    for symbol in symbols:
        try:
            results[symbol] = analyze_sentiment.delay(symbol).get(timeout=30)
        except Exception as e:
            logger.error(f"Error in batch analysis for {symbol}: {str(e)}")
            results[symbol] = {
                "error": f"Failed to analyze sentiment for {symbol}",
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat()
            }
    return results

@celery_app.task(
    base=BaseTaskWithRetry,
    bind=True,
    name="update_historical_sentiment",
    queue="sentiment"
)
def update_historical_sentiment(self, symbol: str, days: int = 30) -> Dict:
    """Update historical sentiment data"""
    try:
        # Get historical data
        historical_data = sentiment_aggregator.sentiment_analyzer.calculate_historical_sentiment(
            symbol,
            start_date=datetime.utcnow() - timedelta(days=days),
            end_date=datetime.utcnow()
        )
        
        # Cache the result
        cache_key = f"historical_sentiment:{symbol}:{days}"
        redis_manager.cache_set(cache_key, historical_data.to_json(), expire=3600)
        
        return {
            "symbol": symbol,
            "days": days,
            "data": historical_data.to_dict(orient="records"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating historical sentiment for {symbol}: {str(e)}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            return {
                "error": f"Failed to update historical sentiment for {symbol}",
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat()
            } 