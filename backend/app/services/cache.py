import json
from typing import Any, Optional
import aioredis
from datetime import datetime, timedelta
from app.core.config import settings

class RedisCache:
    def __init__(self):
        self.redis = None
        self.default_ttl = 3600  # 1 hour default TTL

    async def connect(self):
        """Connect to Redis server."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        await self.connect()
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache with optional TTL."""
        await self.connect()
        await self.redis.set(
            key,
            json.dumps(value),
            ex=ttl or self.default_ttl
        )

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        await self.connect()
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        await self.connect()
        return bool(await self.redis.exists(key))

    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments."""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"

    # Specific cache methods for different data types
    async def get_price_data(self, symbol: str, interval: str) -> Optional[dict]:
        """Get cached price data."""
        key = self._generate_key('price', symbol, interval)
        return await self.get(key)

    async def set_price_data(self, symbol: str, interval: str, data: dict) -> None:
        """Cache price data."""
        key = self._generate_key('price', symbol, interval)
        ttl = 300 if interval == '1min' else 3600  # 5 minutes for 1min data, 1 hour for others
        await self.set(key, data, ttl)

    async def get_news_data(self, symbol: str, days: int) -> Optional[list]:
        """Get cached news data."""
        key = self._generate_key('news', symbol, days)
        return await self.get(key)

    async def set_news_data(self, symbol: str, days: int, data: list) -> None:
        """Cache news data."""
        key = self._generate_key('news', symbol, days)
        await self.set(key, data, 1800)  # 30 minutes TTL

    async def get_social_data(self, symbol: str, source: str) -> Optional[list]:
        """Get cached social media data."""
        key = self._generate_key('social', symbol, source)
        return await self.get(key)

    async def set_social_data(self, symbol: str, source: str, data: list) -> None:
        """Cache social media data."""
        key = self._generate_key('social', symbol, source)
        await self.set(key, data, 1800)  # 30 minutes TTL

    async def get_analytics(self, symbol: str, analysis_type: str) -> Optional[dict]:
        """Get cached analytics data."""
        key = self._generate_key('analytics', symbol, analysis_type)
        return await self.get(key)

    async def set_analytics(self, symbol: str, analysis_type: str, data: dict) -> None:
        """Cache analytics data."""
        key = self._generate_key('analytics', symbol, analysis_type)
        await self.set(key, data, 3600)  # 1 hour TTL

redis_cache = RedisCache() 