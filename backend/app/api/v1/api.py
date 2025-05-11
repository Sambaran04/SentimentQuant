from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, sentiment, technical, trading

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_router.include_router(technical.router, prefix="/technical", tags=["technical"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"]) 