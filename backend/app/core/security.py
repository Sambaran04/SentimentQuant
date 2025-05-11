from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config_manager import config_manager
from fastapi import Request, HTTPException, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional, Callable
import time
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db

settings = config_manager.get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# API Key security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security checks"""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ):
        # Validate request headers
        if not self._validate_headers(request):
            raise HTTPException(status_code=400, detail="Invalid request headers")
        
        # Check rate limit
        if not self._check_rate_limit(request):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Sanitize request body
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._sanitize_request_body(request)
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
    
    def _validate_headers(self, request: Request) -> bool:
        """Validate request headers"""
        # Check content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return False
        
        # Check for required headers
        required_headers = ["user-agent", "accept"]
        for header in required_headers:
            if header not in request.headers:
                return False
        
        return True
    
    def _check_rate_limit(self, request: Request) -> bool:
        """Check if request exceeds rate limit"""
        client_ip = request.client.host
        current_time = time.time()
        
        # Get rate limit settings
        rate_limit = settings.RATE_LIMIT_REQUESTS
        rate_limit_window = settings.RATE_LIMIT_WINDOW
        
        # Check rate limit in Redis
        key = f"rate_limit:{client_ip}"
        current = request.app.state.redis.get(key)
        
        if current is None:
            # First request
            request.app.state.redis.setex(
                key,
                rate_limit_window,
                1
            )
            return True
        
        current = int(current)
        if current >= rate_limit:
            return False
        
        # Increment counter
        request.app.state.redis.incr(key)
        return True
    
    async def _sanitize_request_body(self, request: Request):
        """Sanitize request body to prevent XSS"""
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                # Decode and sanitize body
                body_str = body.decode()
                sanitized = self._sanitize_string(body_str)
                request._body = sanitized.encode()
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string to prevent XSS"""
        # Remove potentially dangerous characters
        value = re.sub(r'[<>]', '', value)
        # Escape special characters
        value = value.replace('&', '&amp;')
        value = value.replace('"', '&quot;')
        value = value.replace("'", '&#x27;')
        value = value.replace('/', '&#x2F;')
        return value

class SQLInjectionProtection:
    """SQL injection protection for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize SQL query"""
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Remove multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        # Remove potentially dangerous keywords
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT',
            'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE'
        ]
        for keyword in dangerous_keywords:
            query = re.sub(
                rf'\b{keyword}\b',
                '',
                query,
                flags=re.IGNORECASE
            )
        
        return query.strip()
    
    def execute_safe_query(self, query: str, params: dict = None):
        """Execute query with SQL injection protection"""
        # Sanitize query
        safe_query = self.sanitize_query(query)
        
        # Execute query with parameters
        return self.db.execute(text(safe_query), params or {})

async def validate_api_key(
    api_key_header: Optional[str] = Depends(api_key_header),
    api_key_query: Optional[str] = Depends(api_key_query),
    db: Session = Depends(get_db)
) -> str:
    """Validate API key"""
    api_key = api_key_header or api_key_query
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is missing"
        )
    
    # Check if API key exists and is valid
    result = db.execute(
        text("SELECT * FROM api_keys WHERE key = :key AND is_active = true"),
        {"key": api_key}
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return api_key

def get_cors_middleware() -> CORSMiddleware:
    """Get CORS middleware configuration"""
    return CORSMiddleware(
        app=settings.APP,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Request-ID"
        ],
        expose_headers=["X-Request-ID"],
        max_age=3600
    )

# Input validation patterns
PATTERNS = {
    "symbol": r'^[A-Z]{1,5}$',  # Stock symbols
    "price": r'^\d+(\.\d{1,2})?$',  # Price with up to 2 decimal places
    "quantity": r'^\d+(\.\d{1,4})?$',  # Quantity with up to 4 decimal places
    "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "username": r'^[a-zA-Z0-9_-]{3,20}$',
    "password": r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$'
}

def validate_input(value: str, pattern_name: str) -> bool:
    """Validate input against pattern"""
    if pattern_name not in PATTERNS:
        raise ValueError(f"Unknown pattern: {pattern_name}")
    
    return bool(re.match(PATTERNS[pattern_name], value)) 