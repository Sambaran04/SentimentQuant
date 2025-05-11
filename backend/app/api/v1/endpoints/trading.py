from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.base import BaseAPIRouter
from app.api.models import SuccessResponse, PaginatedResponse
from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.trading import OrderType, OrderSide
from app.services.trading_service import TradingService
from app.services.market_data import MarketDataService
from pydantic import BaseModel

router = BaseAPIRouter(prefix="/trading", tags=["trading"])

# Request/Response Models
class PortfolioCreate(BaseModel):
    name: str
    initial_balance: float

class OrderCreate(BaseModel):
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None

class RiskLimitCreate(BaseModel):
    max_position_size: float
    max_drawdown: float
    max_leverage: float
    stop_loss_percentage: float
    take_profit_percentage: float

class StrategyCreate(BaseModel):
    name: str
    description: str
    parameters: dict
    is_active: bool = True

class BacktestRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    initial_capital: float

# Portfolio Endpoints
@router.post("/portfolios", response_model=SuccessResponse)
async def create_portfolio(
    portfolio: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new portfolio"""
    trading_service = TradingService(db, MarketDataService())
    portfolio = await trading_service.create_portfolio(
        current_user.id,
        portfolio.name,
        portfolio.initial_balance
    )
    return SuccessResponse(data=portfolio)

@router.get("/portfolios/{portfolio_id}", response_model=SuccessResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio summary"""
    trading_service = TradingService(db, MarketDataService())
    portfolio = await trading_service.get_portfolio_summary(portfolio_id)
    return SuccessResponse(data=portfolio)

# Order Endpoints
@router.post("/portfolios/{portfolio_id}/orders", response_model=SuccessResponse)
async def place_order(
    portfolio_id: int,
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place a new order"""
    trading_service = TradingService(db, MarketDataService())
    order = await trading_service.place_order(
        portfolio_id=portfolio_id,
        symbol=order.symbol,
        order_type=order.order_type,
        side=order.side,
        quantity=order.quantity,
        price=order.price,
        stop_price=order.stop_price
    )
    return SuccessResponse(data=order)

# Risk Management Endpoints
@router.post("/portfolios/{portfolio_id}/risk-limits", response_model=SuccessResponse)
async def set_risk_limits(
    portfolio_id: int,
    risk_limits: RiskLimitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set risk limits for a portfolio"""
    trading_service = TradingService(db, MarketDataService())
    risk_limits = await trading_service.set_risk_limits(portfolio_id, risk_limits.dict())
    return SuccessResponse(data=risk_limits)

# Strategy Endpoints
@router.post("/portfolios/{portfolio_id}/strategies", response_model=SuccessResponse)
async def create_strategy(
    portfolio_id: int,
    strategy: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trading strategy"""
    trading_service = TradingService(db, MarketDataService())
    strategy = await trading_service.create_strategy(portfolio_id, strategy.dict())
    return SuccessResponse(data=strategy)

@router.post("/strategies/{strategy_id}/backtest", response_model=SuccessResponse)
async def backtest_strategy(
    strategy_id: int,
    backtest_request: BacktestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Backtest a trading strategy"""
    trading_service = TradingService(db, MarketDataService())
    results = await trading_service.backtest_strategy(
        strategy_id=strategy_id,
        start_date=backtest_request.start_date,
        end_date=backtest_request.end_date,
        initial_capital=backtest_request.initial_capital
    )
    return SuccessResponse(data=results) 