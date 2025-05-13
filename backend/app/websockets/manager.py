from fastapi import WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState
from typing import Dict, List, Set, Optional, Any, Callable, Awaitable
import json
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Type alias for WebSocket event handlers
WebSocketEventHandler = Callable[[WebSocket, Any], Awaitable[None]]

class WebSocketManager:
    def __init__(self):
        # Store connections by client type and topic (e.g., symbol)
        self.connections: Dict[str, Dict[str, Set[WebSocket]]] = {
            "sentiment": {},
            "trading": {},
            "portfolio": {}
        }
        # Map websockets to their connection info for quick lookups
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        # Map user IDs to their websockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # Mapping of event types to handlers
        self.event_handlers: Dict[str, WebSocketEventHandler] = {}

    @asynccontextmanager
    async def websocket_session(self, websocket: WebSocket, client_type: str, topic: str, user_id: Optional[str] = None):
        """Context manager for WebSocket connections that handles setup and cleanup"""
        try:
            await self.connect(websocket, client_type, topic, user_id)
            yield
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket disconnected: {e.code}")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        finally:
            await self.disconnect(websocket)

    async def connect(self, websocket: WebSocket, client_type: str, topic: str, user_id: Optional[str] = None):
        """Accept a WebSocket connection and register it"""
        # Ensure client_type is valid
        if client_type not in self.connections:
            raise ValueError(f"Invalid client type: {client_type}")
        
        # Accept the connection
        await websocket.accept()
        
        # Initialize topic dictionary if needed
        if topic not in self.connections[client_type]:
            self.connections[client_type][topic] = set()
        
        # Add to connections
        self.connections[client_type][topic].add(websocket)
        
        # Store connection info for quick lookup
        self.connection_info[websocket] = {
            "client_type": client_type,
            "topic": topic,
            "user_id": user_id,
            "connected_at": datetime.utcnow()
        }
        
        # If user_id provided, store in user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected: {client_type}/{topic}" + (f"/user:{user_id}" if user_id else ""))

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_info:
            info = self.connection_info[websocket]
            client_type = info["client_type"]
            topic = info["topic"]
            user_id = info["user_id"]
            
            # Remove from connections
            if topic in self.connections[client_type]:
                self.connections[client_type][topic].discard(websocket)
                
                # Clean up empty topics
                if not self.connections[client_type][topic]:
                    del self.connections[client_type][topic]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from connection info
            del self.connection_info[websocket]
            
            # Close the connection if still open
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close()
            
            logger.info(f"WebSocket disconnected: {client_type}/{topic}" + (f"/user:{user_id}" if user_id else ""))

    async def broadcast(self, client_type: str, topic: str, message: Any):
        """Broadcast a message to all connections of a client type and topic"""
        if client_type not in self.connections or topic not in self.connections[client_type]:
            return
        
        # Prepare the message
        if not isinstance(message, (str, bytes)):
            message = {
                "type": client_type,
                "topic": topic,
                "data": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get connections
        connections = self.connections[client_type][topic].copy()
        
        # Send to all connections
        for websocket in connections:
            try:
                if isinstance(message, dict):
                    await websocket.send_json(message)
                elif isinstance(message, str):
                    await websocket.send_text(message)
                elif isinstance(message, bytes):
                    await websocket.send_bytes(message)
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")
                await self.disconnect(websocket)

    async def broadcast_sentiment(self, symbol: str, data: dict):
        """Broadcast sentiment data for a symbol"""
        await self.broadcast("sentiment", symbol, data)

    async def broadcast_trading_signal(self, symbol: str, signal: dict):
        """Broadcast trading signal for a symbol"""
        await self.broadcast("trading", symbol, signal)

    async def send_to_user(self, user_id: str, message: Any):
        """Send a message to all connections of a user"""
        if user_id not in self.user_connections:
            return
        
        # Prepare the message if not string/bytes
        if not isinstance(message, (str, bytes)):
            message = {
                "type": "user_message",
                "user_id": user_id,
                "data": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get connections
        connections = self.user_connections[user_id].copy()
        
        # Send to all user connections
        for websocket in connections:
            try:
                if isinstance(message, dict):
                    await websocket.send_json(message)
                elif isinstance(message, str):
                    await websocket.send_text(message)
                elif isinstance(message, bytes):
                    await websocket.send_bytes(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                await self.disconnect(websocket)

    async def send_portfolio_update(self, user_id: str, data: dict):
        """Send portfolio update to a user"""
        message = {
            "type": "portfolio_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_to_user(user_id, message)
    
    def register_event_handler(self, event_type: str, handler: WebSocketEventHandler):
        """Register a handler for a specific event type"""
        self.event_handlers[event_type] = handler
    
    async def process_event(self, websocket: WebSocket, event: dict):
        """Process an event from a client"""
        event_type = event.get("type")
        if event_type in self.event_handlers:
            await self.event_handlers[event_type](websocket, event)
        else:
            logger.warning(f"No handler for event type: {event_type}")
    
    async def handle_client_message(self, websocket: WebSocket):
        """Handle incoming messages from the client"""
        try:
            # Get connection info
            if websocket not in self.connection_info:
                logger.warning("Received message from unregistered WebSocket")
                return
            
            # Receive and process message
            data = await websocket.receive_json()
            if isinstance(data, dict) and "type" in data:
                await self.process_event(websocket, data)
            else:
                logger.warning(f"Invalid message format: {data}")
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error handling client message: {str(e)}")
            await self.disconnect(websocket)

# Singleton instance
websocket_manager = WebSocketManager() 