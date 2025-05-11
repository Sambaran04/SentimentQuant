from typing import TypeVar, Generic, Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')

class MetaData(BaseModel):
    """Metadata for API responses"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    page: Optional[int] = Field(None, description="Current page number for paginated responses")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    total_items: Optional[int] = Field(None, description="Total number of items")

class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: ErrorDetail = Field(..., description="Error details")
    meta: MetaData = Field(..., description="Response metadata")

class SuccessResponse(BaseModel, Generic[T]):
    """Success response model"""
    data: T = Field(..., description="Response data")
    meta: MetaData = Field(..., description="Response metadata")

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model"""
    items: List[T] = Field(..., description="List of items")
    meta: MetaData = Field(..., description="Response metadata")

class EmptyResponse(BaseModel):
    """Empty response model"""
    meta: MetaData = Field(..., description="Response metadata")

# Common response types
class MessageResponse(BaseModel):
    """Message response model"""
    message: str = Field(..., description="Response message")
    meta: MetaData = Field(..., description="Response metadata")

class StatusResponse(BaseModel):
    """Status response model"""
    status: str = Field(..., description="Status message")
    meta: MetaData = Field(..., description="Response metadata")

# Validation error response
class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    errors: List[ErrorDetail] = Field(..., description="List of validation errors")
    meta: MetaData = Field(..., description="Response metadata") 