from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
from app.core.logging import logger
from app.core.config_manager import config_manager
from app.core.cache import cache_manager

class FeatureFlag:
    """Feature flag definition"""
    
    def __init__(
        self,
        name: str,
        description: str,
        enabled: bool = False,
        percentage: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.enabled = enabled
        self.percentage = min(max(percentage, 0), 100)
        self.start_date = start_date
        self.end_date = end_date
        self.conditions = conditions or {}
    
    def is_active(self) -> bool:
        """Check if feature flag is active"""
        now = datetime.utcnow()
        
        # Check if within date range
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        return self.enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "percentage": self.percentage,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "conditions": self.conditions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlag":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            description=data["description"],
            enabled=data["enabled"],
            percentage=data["percentage"],
            start_date=datetime.fromisoformat(data["start_date"]) if data["start_date"] else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data["end_date"] else None,
            conditions=data["conditions"]
        )

class FeatureFlagManager:
    """Feature flag manager"""
    
    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._cache_key = "feature_flags"
        self._cache_ttl = 300  # 5 minutes
    
    async def init(self):
        """Initialize feature flags"""
        await self._load_flags()
    
    async def _load_flags(self):
        """Load feature flags from cache or config"""
        try:
            # Try to get from cache
            cached_flags = await cache_manager.get(self._cache_key)
            if cached_flags:
                self._flags = {
                    name: FeatureFlag.from_dict(data)
                    for name, data in cached_flags.items()
                }
                return
            
            # Load from config
            settings = config_manager.get_settings()
            for key, value in settings.features.dict().items():
                if key.startswith("ENABLE_"):
                    name = key[7:].lower()
                    self._flags[name] = FeatureFlag(
                        name=name,
                        description=f"Feature flag for {name}",
                        enabled=value
                    )
            
            # Cache the flags
            await self._cache_flags()
        except Exception as e:
            logger.error(f"Failed to load feature flags: {str(e)}")
    
    async def _cache_flags(self):
        """Cache feature flags"""
        try:
            flags_dict = {
                name: flag.to_dict()
                for name, flag in self._flags.items()
            }
            await cache_manager.set(
                self._cache_key,
                flags_dict,
                self._cache_ttl
            )
        except Exception as e:
            logger.error(f"Failed to cache feature flags: {str(e)}")
    
    async def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get feature flag"""
        return self._flags.get(name)
    
    async def set_flag(
        self,
        name: str,
        enabled: bool,
        percentage: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ):
        """Set feature flag"""
        flag = FeatureFlag(
            name=name,
            description=self._flags.get(name, FeatureFlag(name, "")).description,
            enabled=enabled,
            percentage=percentage,
            start_date=start_date,
            end_date=end_date,
            conditions=conditions
        )
        self._flags[name] = flag
        await self._cache_flags()
        logger.info(f"Updated feature flag: {name} -> {enabled}")
    
    async def is_enabled(
        self,
        name: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if feature is enabled"""
        flag = await self.get_flag(name)
        if not flag:
            return False
        
        if not flag.is_active():
            return False
        
        # Check percentage rollout
        if flag.percentage < 100 and user_id:
            # Use user_id to determine if user is in percentage
            user_hash = hash(user_id) % 100
            if user_hash >= flag.percentage:
                return False
        
        # Check conditions
        if flag.conditions and context:
            for key, value in flag.conditions.items():
                if key not in context or context[key] != value:
                    return False
        
        return True
    
    async def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags"""
        return self._flags.copy()
    
    async def delete_flag(self, name: str):
        """Delete feature flag"""
        if name in self._flags:
            del self._flags[name]
            await self._cache_flags()
            logger.info(f"Deleted feature flag: {name}")

# Initialize feature flag manager
feature_flag_manager = FeatureFlagManager() 