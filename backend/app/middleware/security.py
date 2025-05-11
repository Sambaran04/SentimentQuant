from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, List
import time
from app.core.config import settings
import re
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
        self.rate_limit_store: Dict[str, List[float]] = {}

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

        # Rate limiting
        client_ip = request.client.host
        current_time = time.time()
        
        if client_ip not in self.rate_limit_store:
            self.rate_limit_store[client_ip] = []
        
        # Remove old timestamps
        self.rate_limit_store[client_ip] = [
            ts for ts in self.rate_limit_store[client_ip]
            if current_time - ts < self.rate_limit_window
        ]
        
        # Check rate limit
        if len(self.rate_limit_store[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # Add current timestamp
        self.rate_limit_store[client_ip].append(current_time)

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