from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from app.core.logging import logger

class TradingError(Exception):
    """Base exception for trading-related errors"""
    def __init__(
        self,
        message: str,
        code: str = "TRADING_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class InsufficientFundsError(TradingError):
    """Exception for insufficient funds"""
    def __init__(self, message: str = "Insufficient funds", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INSUFFICIENT_FUNDS",
            status_code=400,
            details=details
        )

class InvalidOrderError(TradingError):
    """Exception for invalid orders"""
    def __init__(self, message: str = "Invalid order", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_ORDER",
            status_code=400,
            details=details
        )

class RiskLimitExceededError(TradingError):
    """Exception for exceeded risk limits"""
    def __init__(self, message: str = "Risk limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RISK_LIMIT_EXCEEDED",
            status_code=400,
            details=details
        )

class MarketDataError(TradingError):
    """Exception for market data errors"""
    def __init__(self, message: str = "Market data error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="MARKET_DATA_ERROR",
            status_code=500,
            details=details
        )

class DatabaseError(TradingError):
    """Exception for database errors"""
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details
        )

class AuthenticationError(HTTPException):
    """Base authentication error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class TokenError(HTTPException):
    """Token-related error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class PermissionError(HTTPException):
    """Permission-related error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ValidationError(HTTPException):
    """Validation error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

class NotFoundError(HTTPException):
    """Resource not found error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class ConflictError(HTTPException):
    """Resource conflict error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

class RateLimitError(HTTPException):
    """Rate limit exceeded error"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )

async def trading_exception_handler(request: Request, exc: TradingError) -> JSONResponse:
    """Handle trading-related exceptions"""
    # Log error
    logger.error(
        "Trading error occurred",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "error_code": exc.code,
            "error_message": exc.message,
            "error_details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            },
            "meta": {
                "request_id": getattr(request.state, "request_id", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    # Log error
    logger.error(
        "HTTP error occurred",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Return error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            },
            "meta": {
                "request_id": getattr(request.state, "request_id", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    # Log error
    logger.error(
        "Unexpected error occurred",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Return error response
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            },
            "meta": {
                "request_id": getattr(request.state, "request_id", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    ) 