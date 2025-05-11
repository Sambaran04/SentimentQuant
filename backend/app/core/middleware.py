from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable, Set, Optional
from app.core.monitoring import usage_tracker, error_tracker
from app.core.logging import logger

class UnifiedMonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[Set[str]] = None,
        exclude_methods: Optional[Set[str]] = None,
        enable_logging: bool = True,
        enable_metrics: bool = True,
        enable_performance: bool = True
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or set()
        self.exclude_methods = exclude_methods or set()
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        self.enable_performance = enable_performance
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip monitoring for excluded paths and methods
        if (
            request.url.path in self.exclude_paths or
            request.method in self.exclude_methods
        ):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Log request if enabled
        if self.enable_logging:
            self._log_request(request)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Track metrics if enabled
            if self.enable_metrics:
                await self._track_metrics(request, response, duration)
            
            # Add performance headers if enabled
            if self.enable_performance:
                response.headers["X-Process-Time"] = f"{duration:.3f}"
            
            # Log response if enabled
            if self.enable_logging:
                self._log_response(request, response)
            
            return response
            
        except Exception as e:
            # Track error if metrics enabled
            if self.enable_metrics:
                await self._track_error(request, e)
            
            # Log error if logging enabled
            if self.enable_logging:
                self._log_error(request, e)
            
            raise
    
    def _log_request(self, request: Request):
        """Log request details"""
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
    
    def _log_response(self, request: Request, response: Response):
        """Log response details"""
        logger.info(
            f"Response: {response.status_code}",
            extra={
                "status_code": response.status_code,
                "method": request.method,
                "path": request.url.path
            }
        )
    
    def _log_error(self, request: Request, error: Exception):
        """Log error details"""
        logger.error(
            f"Error processing request: {str(e)}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(error)
            }
        )
    
    async def _track_metrics(self, request: Request, response: Response, duration: float):
        """Track request metrics"""
        try:
            # Get endpoint path
            path = request.url.path
            
            # Track request
            usage_tracker.track_request(
                path=path,
                method=request.method,
                status_code=response.status_code,
                duration=duration
            )
            
            # Add response headers
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
        except Exception as e:
            logger.error(f"Error tracking metrics: {str(e)}")
    
    async def _track_error(self, request: Request, error: Exception):
        """Track error metrics"""
        try:
            error_tracker.track_error(
                error_type=type(error).__name__,
                message=str(error),
                path=request.url.path,
                method=request.method
            )
        except Exception as e:
            logger.error(f"Error tracking error: {str(e)}") 