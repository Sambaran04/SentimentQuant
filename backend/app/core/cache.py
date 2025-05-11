from typing import Any, Optional, Union
import json
from datetime import datetime, timedelta
import aioredis
from app.core.config import settings
from app.core.logging import logger

class CacheManager:
    """Redis-based cache manager with async support"""
    
    def __init__(self):
        self.redis = None
        self.default_ttl = 3600  # 1 hour default TTL
    
    async def init(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {str(e)}")
            raise
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            serialized = json.dumps(value)
            ttl = ttl or self.default_ttl
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None
    
    async def get_or_set(
        self,
        key: str,
        getter_func,
        ttl: Optional[int] = None
    ) -> Any:
        """Get value from cache or set if not exists"""
        value = await self.get(key)
        if value is None:
            value = await getter_func()
            await self.set(key, value, ttl)
        return value

# Cache decorator
def cache(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_builder: Optional[callable] = None
):
    """Cache decorator for functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key building
                key_parts = [key_prefix, func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cache_manager = CacheManager()
            await cache_manager.init()
            cached_value = await cache_manager.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Get fresh value
            value = await func(*args, **kwargs)
            
            # Cache the value
            await cache_manager.set(cache_key, value, ttl)
            
            return value
        return wrapper
    return decorator

# Initialize cache manager
cache_manager = CacheManager() 