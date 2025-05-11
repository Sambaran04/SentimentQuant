from fastapi import APIRouter, WebSocket, Depends, HTTPException
from app.websockets.manager import manager
from app.core.auth import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter()

@router.websocket("/ws/sentiment/{symbol}")
async def sentiment_websocket(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, "sentiment")
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            # You can implement custom message handling here
    except:
        manager.disconnect(websocket, "sentiment")

@router.websocket("/ws/trading/{symbol}")
async def trading_websocket(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, "trading")
    try:
        while True:
            data = await websocket.receive_text()
    except:
        manager.disconnect(websocket, "trading")

@router.websocket("/ws/portfolio")
async def portfolio_websocket(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user)
):
    await manager.connect(websocket, "portfolio", str(current_user.id))
    try:
        while True:
            data = await websocket.receive_text()
    except:
        manager.disconnect(websocket, "portfolio", str(current_user.id)) 