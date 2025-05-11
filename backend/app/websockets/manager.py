from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "sentiment": [],
            "trading": [],
            "portfolio": []
        }
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_type: str, user_id: str = None):
        await websocket.accept()
        self.active_connections[client_type].append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, client_type: str, user_id: str = None):
        self.active_connections[client_type].remove(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]

    async def broadcast_sentiment(self, symbol: str, data: dict):
        message = {
            "type": "sentiment",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        for connection in self.active_connections["sentiment"]:
            try:
                await connection.send_json(message)
            except:
                await self.disconnect(connection, "sentiment")

    async def broadcast_trading_signal(self, symbol: str, signal: dict):
        message = {
            "type": "trading_signal",
            "symbol": symbol,
            "data": signal,
            "timestamp": datetime.utcnow().isoformat()
        }
        for connection in self.active_connections["trading"]:
            try:
                await connection.send_json(message)
            except:
                await self.disconnect(connection, "trading")

    async def send_portfolio_update(self, user_id: str, data: dict):
        message = {
            "type": "portfolio_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except:
                await self.disconnect(self.user_connections[user_id], "portfolio", user_id)

manager = ConnectionManager() 