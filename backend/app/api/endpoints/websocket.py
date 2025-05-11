from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websocket_manager import websocket_manager
from app.core.auth import get_current_user
from app.models.user import User
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/sentiment")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user)
):
    """
    WebSocket endpoint for real-time sentiment updates
    """
    client_id = str(current_user.id)
    
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