from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    stocks,
    portfolios,
    watchlists,
    sentiment,
    websocket
)

api_v1_router = APIRouter()

# Include all endpoint routers
api_v1_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
api_v1_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_v1_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_v1_router.include_router(watchlists.router, prefix="/watchlists", tags=["watchlists"])
api_v1_router.include_router(sentiment.router, prefix="/sentiment", tags=["sentiment"])
api_v1_router.include_router(websocket.router, tags=["websocket"]) 