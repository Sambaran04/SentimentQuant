from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
import time
import logging
import json
from typing import Callable
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request started - ID: {request_id} - "
            f"Method: {request.method} - "
            f"Path: {request.url.path} - "
            f"Client: {request.client.host if request.client else 'Unknown'}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed - ID: {request_id} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.2f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            # Log error
            logger.error(
                f"Request failed - ID: {request_id} - "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # Log error
            logger.error(
                f"Unhandled error - ID: {getattr(request.state, 'request_id', 'Unknown')} - "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": getattr(request.state, 'request_id', 'Unknown'),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Validate request headers
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=415,
                    content={
                        "error": "Unsupported media type",
                        "request_id": getattr(request.state, 'request_id', 'Unknown'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        
        return await call_next(request)

class ResponseFormattingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        
        # Only format JSON responses
        if isinstance(response, JSONResponse):
            try:
                content = response.body.decode()
                data = json.loads(content)
                
                # Format response
                formatted_response = {
                    "data": data,
                    "meta": {
                        "request_id": getattr(request.state, 'request_id', 'Unknown'),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                return JSONResponse(
                    content=formatted_response,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            except:
                pass
        
        return response 