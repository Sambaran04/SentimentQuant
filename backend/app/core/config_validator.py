from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator, Field
from app.core.logging import logger
import re
import json
from pathlib import Path

class DatabaseConfig(BaseModel):
    """Database configuration validation"""
    host: str
    port: int = Field(ge=1, le=65535)
    database: str
    username: str
    password: str
    
    @validator("host")
    def validate_host(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9.-]+$", v):
            raise ValueError("Invalid host format")
        return v
    
    @validator("database")
    def validate_database(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Invalid database name format")
        return v

class RedisConfig(BaseModel):
    """Redis configuration validation"""
    host: str
    port: int = Field(ge=1, le=65535)
    db: int = Field(ge=0)
    password: Optional[str] = None
    
    @validator("host")
    def validate_host(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9.-]+$", v):
            raise ValueError("Invalid host format")
        return v

class APIConfig(BaseModel):
    """API configuration validation"""
    base_url: str
    api_key: str
    api_secret: Optional[str] = None
    
    @validator("base_url")
    def validate_base_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("Base URL must start with http:// or https://")
        return v

class LoggingConfig(BaseModel):
    """Logging configuration validation"""
    level: str
    format: str
    directory: Path
    
    @validator("level")
    def validate_level(cls, v: str) -> str:
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of {allowed_levels}")
        return v.upper()
    
    @validator("directory")
    def validate_directory(cls, v: Path) -> Path:
        if not v.exists():
            v.mkdir(parents=True)
        return v

class SecurityConfig(BaseModel):
    """Security configuration validation"""
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int = Field(ge=1)
    refresh_token_expire_days: int = Field(ge=1)
    
    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @validator("algorithm")
    def validate_algorithm(cls, v: str) -> str:
        allowed_algorithms = ["HS256", "HS384", "HS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"Algorithm must be one of {allowed_algorithms}")
        return v

class ConfigValidator:
    """Configuration validator"""
    
    @staticmethod
    def validate_database_config(config: Dict[str, Any]) -> bool:
        """Validate database configuration"""
        try:
            DatabaseConfig(**config)
            return True
        except Exception as e:
            logger.error(f"Database configuration validation failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_redis_config(config: Dict[str, Any]) -> bool:
        """Validate Redis configuration"""
        try:
            RedisConfig(**config)
            return True
        except Exception as e:
            logger.error(f"Redis configuration validation failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> bool:
        """Validate API configuration"""
        try:
            APIConfig(**config)
            return True
        except Exception as e:
            logger.error(f"API configuration validation failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_logging_config(config: Dict[str, Any]) -> bool:
        """Validate logging configuration"""
        try:
            LoggingConfig(**config)
            return True
        except Exception as e:
            logger.error(f"Logging configuration validation failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_security_config(config: Dict[str, Any]) -> bool:
        """Validate security configuration"""
        try:
            SecurityConfig(**config)
            return True
        except Exception as e:
            logger.error(f"Security configuration validation failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_config_file(file_path: Path) -> bool:
        """Validate configuration file"""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
            with open(file_path) as f:
                config = json.load(f)
            
            # Validate all sections
            validations = [
                ConfigValidator.validate_database_config(config.get("database", {})),
                ConfigValidator.validate_redis_config(config.get("redis", {})),
                ConfigValidator.validate_api_config(config.get("api", {})),
                ConfigValidator.validate_logging_config(config.get("logging", {})),
                ConfigValidator.validate_security_config(config.get("security", {}))
            ]
            
            return all(validations)
        except Exception as e:
            logger.error(f"Configuration file validation failed: {str(e)}")
            return False

# Initialize configuration validator
config_validator = ConfigValidator() 