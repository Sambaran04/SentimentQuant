from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Dict, List
from app.core.config import settings
from app.core.redis_manager import redis_manager
import re
import time
import json
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        rate_limit: int = 100,  # requests per minute
        rate_limit_window: int = 60,  # seconds
        max_request_size: int = 1024 * 1024,  # 1MB
        allowed_hosts: List[str] = None,
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
    ):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.rate_limit_window = rate_limit_window
        self.max_request_size = max_request_size
        self.allowed_hosts = allowed_hosts or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Check request size
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_request_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request entity too large"}
                )

        # Check host
        if self.allowed_hosts != ["*"]:
            host = request.headers.get("host", "").split(":")[0]
            if host not in self.allowed_hosts:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid host"}
                )

        # Check method
        if request.method not in self.allowed_methods:
            return JSONResponse(
                status_code=405,
                content={"detail": "Method not allowed"}
            )

        # Rate limiting using Redis
        client_ip = request.client.host
        current_time = time.time()
        redis_key = f"rate_limit:{client_ip}"
        
        # Use Redis Sliding Window Counter algorithm
        # Get the current window data
        window_data = redis_manager.cache_get(redis_key)
        if window_data:
            try:
                window = json.loads(window_data)
                window_start = window.get("start", 0)
                request_count = window.get("count", 0)
                
                # Check if we need to reset the window
                if current_time - window_start >= self.rate_limit_window:
                    # Start a new window
                    window = {
                        "start": current_time,
                        "count": 1
                    }
                else:
                    # Increment counter in existing window
                    window["count"] = request_count + 1
                
                # Check if rate limit exceeded
                if window["count"] > self.rate_limit:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"}
                    )
                
                # Update window in Redis
                redis_manager.cache_set(
                    redis_key, 
                    json.dumps(window), 
                    expire=self.rate_limit_window * 2  # 2x window time to account for overlapping windows
                )
            except (json.JSONDecodeError, TypeError):
                # If data is corrupted, create a new window
                window = {
                    "start": current_time,
                    "count": 1
                }
                redis_manager.cache_set(
                    redis_key, 
                    json.dumps(window), 
                    expire=self.rate_limit_window * 2
                )
        else:
            # First request from this IP
            window = {
                "start": current_time,
                "count": 1
            }
            redis_manager.cache_set(
                redis_key, 
                json.dumps(window), 
                expire=self.rate_limit_window * 2
            )

        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sql_injection_pattern = re.compile(
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b.*\b(FROM|INTO|WHERE|VALUES|TABLE|DATABASE)\b)",
            re.IGNORECASE
        )
        self.xss_pattern = re.compile(
            r"(<script|javascript:|on\w+\s*=)",
            re.IGNORECASE
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Check query parameters
        for param, value in request.query_params.items():
            if self._contains_malicious_content(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid input detected"}
                )

        # Check path parameters
        for param, value in request.path_params.items():
            if self._contains_malicious_content(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid input detected"}
                )

        # Check request body for POST/PUT requests
        if request.method in ["POST", "PUT"]:
            try:
                body = await request.json()
                if self._check_dict_for_malicious_content(body):
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid input detected"}
                    )
            except:
                pass  # Skip if body is not JSON

        return await call_next(request)

    def _contains_malicious_content(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        return bool(
            self.sql_injection_pattern.search(value) or
            self.xss_pattern.search(value)
        )

    def _check_dict_for_malicious_content(self, data: dict) -> bool:
        for key, value in data.items():
            if isinstance(value, str):
                if self._contains_malicious_content(value):
                    return True
            elif isinstance(value, dict):
                if self._check_dict_for_malicious_content(value):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        if self._contains_malicious_content(item):
                            return True
                    elif isinstance(item, dict):
                        if self._check_dict_for_malicious_content(item):
                            return True
        return False 