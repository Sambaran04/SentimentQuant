from typing import Any, Dict, Optional
from pydantic import BaseModel, validator, EmailStr, constr
import re
from datetime import datetime
from app.core.config import settings

class StockDataValidator(BaseModel):
    symbol: constr(min_length=1, max_length=10, regex=r'^[A-Z]+$')
    price: float
    volume: int
    timestamp: datetime

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @validator('volume')
    def validate_volume(cls, v):
        if v < 0:
            raise ValueError('Volume cannot be negative')
        return v

class PortfolioTransactionValidator(BaseModel):
    symbol: constr(min_length=1, max_length=10, regex=r'^[A-Z]+$')
    quantity: int
    price: float
    type: str

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @validator('type')
    def validate_type(cls, v):
        if v not in ['buy', 'sell']:
            raise ValueError('Type must be either "buy" or "sell"')
        return v.lower()

class WatchlistValidator(BaseModel):
    name: constr(min_length=1, max_length=50)
    description: Optional[str] = None
    symbols: list[constr(min_length=1, max_length=10, regex=r'^[A-Z]+$')]

    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError('At least one symbol is required')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate symbols are not allowed')
        return v

def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize input data to prevent SQL injection and XSS attacks"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potentially dangerous characters
            sanitized[key] = re.sub(r'[<>"\']', '', value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item) if isinstance(item, dict)
                else re.sub(r'[<>"\']', '', item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized

def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False
    if len(password) > settings.PASSWORD_MAX_LENGTH:
        return False
    if not re.match(settings.PASSWORD_REGEX, password):
        return False
    return True

def sanitize_email(email: str) -> str:
    """Sanitize email address"""
    return email.lower().strip()

def validate_stock_symbol(symbol: str) -> bool:
    """Validate stock symbol format"""
    return bool(re.match(r'^[A-Z]{1,10}$', symbol)) 