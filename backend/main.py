from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import asyncio
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = FastAPI(title="SentimentQuant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "stock": [],
            "sentiment": [],
            "portfolio": []
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections[client_type].append(websocket)

    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].remove(websocket)

    async def broadcast(self, message: str, client_type: str):
        for connection in self.active_connections[client_type]:
            await connection.send_text(message)

manager = ConnectionManager()

# Models
class StockData(BaseModel):
    symbol: str
    price: float
    change: float
    volume: int
    timestamp: datetime

class SentimentData(BaseModel):
    symbol: str
    score: float
    magnitude: float
    timestamp: datetime

class PortfolioPosition(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    profit_loss: float
    profit_loss_percentage: float

class PortfolioSummary(BaseModel):
    total_value: float
    total_profit_loss: float
    total_profit_loss_percentage: float
    positions: List[PortfolioPosition]

# Helper functions
def get_stock_data(symbol: str, timeframe: str = "1d") -> pd.DataFrame:
    """Fetch stock data from Yahoo Finance"""
    stock = yf.Ticker(symbol)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Default to 30 days of data
    df = stock.history(start=start_date, end=end_date, interval=timeframe)
    return df

def calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    """Calculate technical indicators"""
    # Simple Moving Averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df.to_dict('records')

# API Endpoints
@app.get("/api/v1/stocks/search")
async def search_stocks(query: str):
    """Search for stocks by symbol or name"""
    try:
        # Use yfinance to search for stocks
        tickers = yf.Tickers(query)
        results = []
        for symbol in tickers.tickers:
            info = tickers.tickers[symbol].info
            results.append({
                "symbol": symbol,
                "name": info.get("longName", ""),
                "exchange": info.get("exchange", ""),
                "type": info.get("quoteType", "")
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/prices")
async def get_prices(symbol: str, timeframe: str = "1d"):
    """Get historical price data"""
    try:
        df = get_stock_data(symbol, timeframe)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/sentiment")
async def get_sentiment(symbol: str):
    """Get sentiment data for a stock"""
    # This is a mock implementation. In production, integrate with a real sentiment analysis service
    return {
        "symbol": symbol,
        "score": np.random.uniform(-1, 1),
        "magnitude": np.random.uniform(0, 1),
        "timestamp": datetime.now()
    }

@app.get("/api/v1/news")
async def get_news(symbol: str):
    """Get news articles for a stock"""
    try:
        stock = yf.Ticker(symbol)
        news = stock.news
        return news
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/correlation")
async def get_correlation(symbols: str, timeframe: str = "1d"):
    """Calculate correlation between stocks"""
    try:
        symbol_list = symbols.split(',')
        dfs = {}
        for symbol in symbol_list:
            df = get_stock_data(symbol, timeframe)
            dfs[symbol] = df['Close']
        
        # Calculate correlation matrix
        corr_matrix = pd.DataFrame(dfs).corr()
        return corr_matrix.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/portfolio")
async def get_portfolio():
    """Get portfolio summary"""
    # This is a mock implementation. In production, integrate with a real portfolio management system
    return {
        "total_value": 100000.0,
        "total_profit_loss": 5000.0,
        "total_profit_loss_percentage": 5.0,
        "positions": [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "average_price": 150.0,
                "current_price": 155.0,
                "profit_loss": 500.0,
                "profit_loss_percentage": 3.33
            }
        ]
    }

@app.get("/api/v1/watchlist")
async def get_watchlist():
    """Get user's watchlist"""
    # This is a mock implementation. In production, integrate with a real database
    return [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "price": 155.0,
            "change": 1.5,
            "sentiment": 0.8
        }
    ]

# WebSocket endpoints
@app.websocket("/ws/stock/{symbol}")
async def websocket_stock_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, "stock")
    try:
        while True:
            # Get real-time stock data
            stock = yf.Ticker(symbol)
            data = {
                "symbol": symbol,
                "price": stock.info.get("regularMarketPrice", 0),
                "change": stock.info.get("regularMarketChangePercent", 0),
                "volume": stock.info.get("regularMarketVolume", 0),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)  # Update every second
    except WebSocketDisconnect:
        manager.disconnect(websocket, "stock")

@app.websocket("/ws/sentiment/{symbol}")
async def websocket_sentiment_endpoint(websocket: WebSocket, symbol: str):
    await manager.connect(websocket, "sentiment")
    try:
        while True:
            # Get real-time sentiment data
            data = {
                "symbol": symbol,
                "score": np.random.uniform(-1, 1),
                "magnitude": np.random.uniform(0, 1),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket, "sentiment")

@app.websocket("/ws/portfolio")
async def websocket_portfolio_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "portfolio")
    try:
        while True:
            # Get real-time portfolio updates
            data = {
                "total_value": 100000.0,
                "total_profit_loss": 5000.0,
                "total_profit_loss_percentage": 5.0,
                "positions": [
                    {
                        "symbol": "AAPL",
                        "quantity": 100,
                        "average_price": 150.0,
                        "current_price": 155.0,
                        "profit_loss": 500.0,
                        "profit_loss_percentage": 3.33
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(1)  # Update every second
    except WebSocketDisconnect:
        manager.disconnect(websocket, "portfolio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 