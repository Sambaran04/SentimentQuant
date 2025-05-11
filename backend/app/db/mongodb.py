from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.config import settings

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    async def connect_to_database(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]

    async def close_database_connection(self):
        if self.client:
            self.client.close()

    async def insert_market_data(self, symbol: str, data: Dict[str, Any]):
        """Insert real-time market data"""
        collection = self.db.market_data
        document = {
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        await collection.insert_one(document)

    async def get_latest_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest market data for a symbol"""
        collection = self.db.market_data
        document = await collection.find_one(
            {"symbol": symbol},
            sort=[("timestamp", -1)]
        )
        return document

    async def insert_sentiment_data(self, symbol: str, data: Dict[str, Any]):
        """Insert sentiment analysis data"""
        collection = self.db.sentiment_data
        document = {
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        await collection.insert_one(document)

    async def get_latest_sentiment_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest sentiment data for a symbol"""
        collection = self.db.sentiment_data
        document = await collection.find_one(
            {"symbol": symbol},
            sort=[("timestamp", -1)]
        )
        return document

    async def create_indexes(self):
        """Create indexes for better query performance"""
        # Market data indexes
        await self.db.market_data.create_index([("symbol", 1), ("timestamp", -1)])
        await self.db.market_data.create_index([("timestamp", -1)])
        
        # Sentiment data indexes
        await self.db.sentiment_data.create_index([("symbol", 1), ("timestamp", -1)])
        await self.db.sentiment_data.create_index([("timestamp", -1)])

mongodb = MongoDB() 