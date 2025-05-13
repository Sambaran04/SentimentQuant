from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from app.api.models import ErrorResponse, MetaData
from app.core.auth import get_current_user
from app.models.user import User
from typing import Optional, Callable, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAPIRouter(APIRouter):
    """Base API router with common dependencies and error handlers"""
    
    def __init__(
        self,
        *args,
        require_auth: bool = True,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.require_auth = require_auth
        
        # Add common dependencies
        if require_auth:
            self.dependencies = [Depends(get_current_user)]
        
        # Add error handlers
        self.add_exception_handler(HTTPException, self.http_exception_handler)
        self.add_exception_handler(Exception, self.generic_exception_handler)
    
    async def http_exception_handler(self, request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        error_response = ErrorResponse(
            error={
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            },
            meta=MetaData(
                request_id=getattr(request.state, 'request_id', 'Unknown'),
                timestamp=datetime.utcnow()
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )
    
    async def generic_exception_handler(self, request: Request, exc: Exception):
        """Handle generic exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        error_response = ErrorResponse(
            error={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            },
            meta=MetaData(
                request_id=getattr(request.state, 'request_id', 'Unknown'),
                timestamp=datetime.utcnow()
            )
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )
    
    def get_current_user_optional(self) -> Optional[User]:
        """Get current user if available"""
        try:
            return get_current_user()
        except:
            return None

# Create base router instance
base_router = BaseAPIRouter(
    prefix="/api/v1",
    tags=["api"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
) 