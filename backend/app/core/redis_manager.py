from typing import Optional
import redis
from redis.exceptions import RedisError
from app.core.config import settings
import logging
import backoff

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.connect()

    @backoff.on_exception(
        backoff.expo,
        (RedisError, ConnectionError),
        max_tries=5,
        max_time=30
    )
    def connect(self) -> None:
        """Establish Redis connection with retry logic"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.pubsub = self.redis_client.pubsub()
            logger.info("Successfully connected to Redis")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if not self.redis_client or not self.redis_client.ping():
            self.connect()
        return self.redis_client

    def get_pubsub(self) -> redis.client.PubSub:
        """Get Redis PubSub instance"""
        if not self.pubsub:
            self.connect()
        return self.pubsub

    def publish(self, channel: str, message: str) -> None:
        """Publish message to Redis channel"""
        try:
            self.get_client().publish(channel, message)
        except RedisError as e:
            logger.error(f"Failed to publish message to {channel}: {str(e)}")
            raise

    def subscribe(self, channel: str) -> None:
        """Subscribe to Redis channel"""
        try:
            self.get_pubsub().subscribe(channel)
        except RedisError as e:
            logger.error(f"Failed to subscribe to {channel}: {str(e)}")
            raise

    def get_message(self, timeout: int = 1) -> Optional[dict]:
        """Get message from subscribed channels"""
        try:
            return self.get_pubsub().get_message(timeout=timeout)
        except RedisError as e:
            logger.error(f"Failed to get message: {str(e)}")
            raise

    def cache_set(self, key: str, value: str, expire: int = 3600) -> None:
        """Set value in Redis cache with expiration"""
        try:
            self.get_client().setex(key, expire, value)
        except RedisError as e:
            logger.error(f"Failed to set cache key {key}: {str(e)}")
            raise

    def cache_get(self, key: str) -> Optional[str]:
        """Get value from Redis cache"""
        try:
            return self.get_client().get(key)
        except RedisError as e:
            logger.error(f"Failed to get cache key {key}: {str(e)}")
            raise

redis_manager = RedisManager() 