from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.core.redis_manager import redis_manager
import json
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.rate_limits: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.max_requests_per_minute = 60
        self.redis_subscriptions = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id].add(websocket)
        logger.info(f"Client {client_id} connected")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """Disconnect a WebSocket client"""
        self.active_connections[client_id].remove(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected")

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = time.time()
        client_limits = self.rate_limits[client_id]
        
        # Remove old timestamps
        client_limits = {ts: count for ts, count in client_limits.items() 
                        if now - float(ts) < 60}
        
        # Check if limit exceeded
        if sum(client_limits.values()) >= self.max_requests_per_minute:
            return False
        
        # Add new request
        client_limits[str(now)] = 1
        self.rate_limits[client_id] = client_limits
        return True

    async def subscribe_to_symbol(self, websocket: WebSocket, client_id: str, symbol: str):
        """Subscribe to Redis channel for a symbol"""
        channel = f"sentiment_updates:{symbol}"
        
        # Subscribe to Redis channel if not already subscribed
        if channel not in self.redis_subscriptions:
            redis_manager.subscribe(channel)
            self.redis_subscriptions[channel] = True
            
            # Start background task to forward messages
            asyncio.create_task(self._forward_messages(channel))

    async def _forward_messages(self, channel: str):
        """Forward messages from Redis to WebSocket clients"""
        while True:
            try:
                message = redis_manager.get_message(timeout=1)
                if message and message["type"] == "message":
                    data = message["data"]
                    # Forward to all clients subscribed to this symbol
                    symbol = channel.split(":")[1]
                    for client_id, connections in self.active_connections.items():
                        for connection in connections:
                            try:
                                await connection.send_text(data)
                            except WebSocketDisconnect:
                                self.disconnect(connection, client_id)
                            except Exception as e:
                                logger.error(f"Error sending message to client {client_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error in message forwarding: {str(e)}")
                await asyncio.sleep(1)

    async def broadcast(self, message: str, client_id: str):
        """Broadcast message to all connections of a client"""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(message)
                except WebSocketDisconnect:
                    self.disconnect(connection, client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {str(e)}")

    async def handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connection"""
        await self.connect(websocket, client_id)
        try:
            while True:
                # Check rate limit
                if not self.check_rate_limit(client_id):
                    await websocket.send_json({
                        "error": "Rate limit exceeded",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    await asyncio.sleep(1)
                    continue

                # Receive message
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle subscription request
                    if message.get("type") == "subscribe":
                        symbol = message.get("symbol")
                        if symbol:
                            await self.subscribe_to_symbol(websocket, client_id, symbol)
                            await websocket.send_json({
                                "type": "subscribed",
                                "symbol": symbol,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "error": "Invalid JSON format",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    await websocket.send_json({
                        "error": "Internal server error",
                        "timestamp": datetime.utcnow().isoformat()
                    })

        except WebSocketDisconnect:
            self.disconnect(websocket, client_id)
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            self.disconnect(websocket, client_id)

websocket_manager = ConnectionManager() 