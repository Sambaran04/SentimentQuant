from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import ValidationError
import logging
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenPayload, TokenResponse, UserCreate, UserUpdate
from app.core.exceptions import AuthenticationError, TokenError

# Configure logging
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

class AuthManager:
    """Authentication manager class to handle all auth-related operations"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None,
        scopes: List[str] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "scopes": scopes or [],
            "type": "access"
        }
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise TokenError("Could not create access token")

    @staticmethod
    def create_refresh_token(
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode = {
            "exp": expire,
            "sub": str(subject),
            "type": "refresh"
        }
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise TokenError("Could not create refresh token")

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"Error verifying token: {str(e)}")
            raise TokenError("Invalid token")

    @staticmethod
    async def get_current_user(
        request: Request,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
    ) -> User:
        """Get current authenticated user"""
        try:
            payload = AuthManager.verify_token(token)
            token_data = TokenPayload(**payload)
            
            if datetime.fromtimestamp(token_data.exp) < datetime.now():
                raise TokenError("Token has expired")
            
            user = db.query(User).filter(User.id == token_data.sub).first()
            if not user:
                raise AuthenticationError("User not found")
            
            if not user.is_active:
                raise AuthenticationError("Inactive user")
            
            # Add user to request state for logging/monitoring
            request.state.user = user
            
            return user
            
        except (JWTError, ValidationError) as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise AuthenticationError("Could not validate credentials")

    @staticmethod
    async def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Get current active user"""
        if not current_user.is_active:
            raise AuthenticationError("Inactive user")
        return current_user

    @staticmethod
    async def get_current_superuser(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """Get current superuser"""
        if not current_user.is_superuser:
            raise AuthenticationError("Not enough privileges")
        return current_user

    @staticmethod
    async def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            if not AuthManager.verify_password(password, user.hashed_password):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None

    @staticmethod
    async def create_user(
        db: Session,
        user_in: UserCreate
    ) -> User:
        """Create new user"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.email == user_in.email).first()
            if user:
                raise AuthenticationError("Email already registered")
            
            # Create new user
            user = User(
                email=user_in.email,
                hashed_password=AuthManager.get_password_hash(user_in.password),
                full_name=user_in.full_name,
                is_active=True,
                is_superuser=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise AuthenticationError("Could not create user")

    @staticmethod
    async def update_user(
        db: Session,
        user: User,
        user_in: UserUpdate
    ) -> User:
        """Update user information"""
        try:
            update_data = user_in.dict(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = AuthManager.get_password_hash(
                    update_data.pop("password")
                )
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {str(e)}")
            raise AuthenticationError("Could not update user")

    @staticmethod
    async def change_password(
        db: Session,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        try:
            if not AuthManager.verify_password(current_password, user.hashed_password):
                raise AuthenticationError("Incorrect password")
            
            user.hashed_password = AuthManager.get_password_hash(new_password)
            db.add(user)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error changing password: {str(e)}")
            raise AuthenticationError("Could not change password")

    @staticmethod
    async def create_tokens(user: User) -> TokenResponse:
        """Create access and refresh tokens for user"""
        try:
            access_token = AuthManager.create_access_token(
                subject=user.id,
                scopes=["user"] if not user.is_superuser else ["admin"]
            )
            refresh_token = AuthManager.create_refresh_token(subject=user.id)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
            
        except Exception as e:
            logger.error(f"Error creating tokens: {str(e)}")
            raise TokenError("Could not create tokens")

# Create auth manager instance
auth_manager = AuthManager()

# Export commonly used functions
get_current_user = auth_manager.get_current_user
get_current_active_user = auth_manager.get_current_active_user
get_current_superuser = auth_manager.get_current_superuser
authenticate_user = auth_manager.authenticate_user
create_user = auth_manager.create_user
update_user = auth_manager.update_user
change_password = auth_manager.change_password
create_tokens = auth_manager.create_tokens 