from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, PostgresDsn
import secrets
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "SentimentQuant"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend development
        "http://localhost:8000",  # Backend development
    ]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100  # Number of requests
    RATE_LIMIT_WINDOW: int = 60     # Time window in seconds
    
    # API Key settings
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_QUERY: str = "api_key"
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/sentimentquant"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Logging settings
    LOG_DIR: Path = Path("logs")
    LOG_LEVEL: str = "INFO"
    
    # File storage settings
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # Security headers
    SECURITY_HEADERS: dict = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'"
    }
    
    # Input validation
    MAX_STRING_LENGTH: int = 1000
    MIN_PASSWORD_LENGTH: int = 8
    MAX_PASSWORD_LENGTH: int = 100
    
    # Session settings
    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    
    # API Settings
    PROJECT_NAME: str = "SentimentQuant"
    
    # CORS Settings
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "sentimentquant"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "sentimentquant"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis Settings
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # JWT Settings
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 60
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Security Settings
    RATE_LIMIT_PER_MINUTE: int = 100
    MAX_REQUEST_SIZE: int = 1024 * 1024  # 1MB
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    PASSWORD_REGEX: str = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"

    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    EMAILS_FROM_NAME: str = PROJECT_NAME
    FRONTEND_URL: str = "http://localhost:3000"

    # Trading API Settings
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # News API Settings
    NEWS_API_KEY: str = "your-news-api-key"

    # Twitter API Settings
    TWITTER_BEARER_TOKEN: str = "your-twitter-bearer-token"
    TWITTER_API_KEY: str = "your-twitter-api-key"
    TWITTER_API_SECRET: str = "your-twitter-api-secret"
    TWITTER_ACCESS_TOKEN: str = "your-twitter-access-token"
    TWITTER_ACCESS_TOKEN_SECRET: str = "your-twitter-access-token-secret"

    # Reddit API Settings
    REDDIT_CLIENT_ID: str = "your-reddit-client-id"
    REDDIT_CLIENT_SECRET: str = "your-reddit-client-secret"
    REDDIT_USER_AGENT: str = "SentimentQuant/1.0"

    # Alpha Vantage API Settings
    ALPHA_VANTAGE_API_KEY: str = "your-alpha-vantage-api-key"

    # Telegram Settings
    TELEGRAM_BOT_TOKEN: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 