from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.websockets.manager import websocket_manager
from app.core.auth import get_current_user
from app.models.user import User
from typing import Optional
import logging
import uuid
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws/sentiment/{symbol}")
async def sentiment_websocket(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time sentiment updates for a specific symbol
    """
    client_id = f"sentiment_{symbol}_{uuid.uuid4()}"
    logger.info(f"New sentiment connection for symbol {symbol} with ID {client_id}")

    async with websocket_manager.websocket_session(websocket, "sentiment", symbol):
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            # You can implement custom message handling here
            logger.debug(f"Received data from {client_id}: {data[:100]}...")


@router.websocket("/ws/sentiment")
async def authenticated_sentiment_websocket(
        websocket: WebSocket,
        current_user: User = Depends(get_current_user)
):
    """
    Authenticated WebSocket endpoint for real-time sentiment updates
    """
    client_id = str(current_user.id)
    logger.info(f"New authenticated sentiment connection for user {client_id}")

    try:
        await websocket_manager.handle_websocket(websocket, client_id)
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}")
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/trading/{symbol}")
async def trading_websocket(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time trading data for a specific symbol
    """
    client_id = f"trading_{symbol}_{uuid.uuid4()}"
    logger.info(f"New trading connection for symbol {symbol} with ID {client_id}")

    async with websocket_manager.websocket_session(websocket, "trading", symbol):
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received trading data from {client_id}: {data[:100]}...")
            # Process trading-specific messages here


@router.websocket("/ws/portfolio")
async def portfolio_websocket(
        websocket: WebSocket,
        current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint for real-time portfolio updates
    Requires authentication
    """
    user_id = str(current_user.id)
    logger.info(f"New portfolio connection for user {user_id}")

    async with websocket_manager.websocket_session(websocket, "portfolio", "user_portfolio", user_id):
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received portfolio data from user {user_id}: {data[:100]}...")
            # Process portfolio-specific messages here
            try:
                # Parse JSON data from client
                json_data = json.loads(data)
                # Handle client events
                await websocket_manager.process_event(websocket, json_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from user {user_id}: {data[:100]}...")


@router.websocket("/ws/combined/{symbol}")
async def combined_data_websocket(
        websocket: WebSocket,
        symbol: str,
        current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint that combines sentiment and trading data for a symbol
    Requires authentication
    """
    user_id = str(current_user.id)
    logger.info(f"New combined data connection for symbol {symbol} from user {user_id}")

    async with websocket_manager.websocket_session(websocket, "combined", symbol, user_id):
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received combined data request from user {user_id} for {symbol}: {data[:100]}...")
            try:
                # Parse JSON data from client
                json_data = json.loads(data)
                
                # Forward the request to the appropriate handler based on data type
                data_type = json_data.get("type")
                if data_type == "sentiment":
                    # Process sentiment-specific request
                    await websocket_manager.broadcast_sentiment(symbol, json_data.get("data", {}))
                elif data_type == "trading":
                    # Process trading-specific request
                    await websocket_manager.broadcast_trading_signal(symbol, json_data.get("data", {}))
                else:
                    # Handle custom event
                    await websocket_manager.process_event(websocket, json_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from user {user_id}: {data[:100]}...")