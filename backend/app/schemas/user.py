from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str

class UserUpdate(UserBase):
    """Schema for updating user information"""
    password: Optional[str] = None

class UserInDBBase(UserBase):
    """Schema for user in database"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    """Schema for user response"""
    pass

class UserInDB(UserInDBBase):
    """Schema for user in database"""
    hashed_password: str 