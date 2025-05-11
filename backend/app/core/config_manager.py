from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, Field, validator, PostgresDsn, RedisDsn, AnyHttpUrl
from pydantic_settings import BaseSettings
import os
import json
from pathlib import Path
import secrets
from functools import lru_cache
import hvac
from app.core.logging import logger

class EnvironmentConfig(BaseSettings):
    """Environment-specific configuration"""
    ENV: str = Field(default="development", env="ENV")
    DEBUG: bool = Field(default=False, env="DEBUG")
    TESTING: bool = Field(default=False, env="TESTING")
    
    @validator("ENV")
    def validate_env(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return v

class SecretConfig(BaseSettings):
    """Secret management configuration"""
    VAULT_ADDR: str = Field(default="http://localhost:8200", env="VAULT_ADDR")
    VAULT_TOKEN: str = Field(default="", env="VAULT_TOKEN")
    VAULT_PATH: str = Field(default="secret/sentimentquant", env="VAULT_PATH")
    
    def get_vault_client(self) -> hvac.Client:
        """Get Vault client"""
        client = hvac.Client(url=self.VAULT_ADDR, token=self.VAULT_TOKEN)
        if not client.is_authenticated():
            raise ValueError("Failed to authenticate with Vault")
        return client
    
    def get_secret(self, key: str) -> Any:
        """Get secret from Vault"""
        try:
            client = self.get_vault_client()
            secret = client.secrets.kv.v2.read_secret_version(
                path=f"{self.VAULT_PATH}/{key}"
            )
            return secret["data"]["data"]
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {str(e)}")
            raise

class FeatureFlags(BaseSettings):
    """Feature flags configuration"""
    ENABLE_REAL_TIME_TRADING: bool = Field(default=False, env="ENABLE_REAL_TIME_TRADING")
    ENABLE_SENTIMENT_ANALYSIS: bool = Field(default=True, env="ENABLE_SENTIMENT_ANALYSIS")
    ENABLE_MACHINE_LEARNING: bool = Field(default=False, env="ENABLE_MACHINE_LEARNING")
    ENABLE_SOCIAL_MEDIA_INTEGRATION: bool = Field(default=True, env="ENABLE_SOCIAL_MEDIA_INTEGRATION")
    
    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled"""
        return getattr(self, f"ENABLE_{feature.upper()}", False)

class ServiceDiscovery(BaseSettings):
    """Service discovery configuration"""
    SERVICE_REGISTRY: Dict[str, str] = Field(default_factory=dict)
    SERVICE_HEALTH_CHECK_INTERVAL: int = Field(default=30, env="SERVICE_HEALTH_CHECK_INTERVAL")
    
    def register_service(self, name: str, url: str):
        """Register a service"""
        self.SERVICE_REGISTRY[name] = url
    
    def get_service_url(self, name: str) -> Optional[str]:
        """Get service URL"""
        return self.SERVICE_REGISTRY.get(name)
    
    def get_all_services(self) -> Dict[str, str]:
        """Get all registered services"""
        return self.SERVICE_REGISTRY.copy()

class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    env: EnvironmentConfig = EnvironmentConfig()
    
    # Secrets
    secrets: SecretConfig = SecretConfig()
    
    # Feature flags
    features: FeatureFlags = FeatureFlags()
    
    # Service discovery
    services: ServiceDiscovery = ServiceDiscovery()
    
    # Application
    APP_NAME: str = "SentimentQuant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "sentimentquant"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    
    # Logging
    LOG_DIR: Path = Path("logs")
    LOG_LEVEL: str = "INFO"
    
    # File storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # Trading API
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"
    
    # News API
    NEWS_API_KEY: str = ""
    
    # Twitter API
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    
    # Reddit API
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "SentimentQuant/1.0"
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

class ConfigManager:
    """Configuration manager with validation and caching"""
    
    def __init__(self):
        self._settings = None
        self._config_cache = {}
    
    @lru_cache()
    def get_settings(self) -> Settings:
        """Get application settings with caching"""
        if self._settings is None:
            self._settings = Settings()
        return self._settings
    
    def get_feature_flag(self, feature: str) -> bool:
        """Get feature flag value"""
        settings = self.get_settings()
        return settings.features.is_enabled(feature)
    
    def get_service_url(self, service: str) -> Optional[str]:
        """Get service URL"""
        settings = self.get_settings()
        return settings.services.get_service_url(service)
    
    def get_secret(self, key: str) -> Any:
        """Get secret value"""
        settings = self.get_settings()
        return settings.secrets.get_secret(key)
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        try:
            settings = self.get_settings()
            
            # Validate required settings
            required_settings = [
                "SECRET_KEY",
                "POSTGRES_PASSWORD",
                "ALPACA_API_KEY",
                "ALPACA_SECRET_KEY"
            ]
            
            for setting in required_settings:
                if not getattr(settings, setting):
                    raise ValueError(f"Missing required setting: {setting}")
            
            # Validate service URLs
            for service, url in settings.services.get_all_services().items():
                if not url:
                    raise ValueError(f"Missing URL for service: {service}")
            
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def reload_config(self):
        """Reload configuration"""
        self._settings = None
        self._config_cache.clear()
        return self.get_settings()

# Initialize configuration manager
config_manager = ConfigManager() 