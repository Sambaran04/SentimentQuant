import alpaca_trade_api as tradeapi
from typing import Dict, Optional, List, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.trading import (
    Portfolio, Position, Order, OrderType, OrderSide, OrderStatus,
    RiskLimit, TradingStrategy, BacktestResult
)
from app.core.exceptions import TradingError
import logging
import pandas as pd
import numpy as np
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)

class TradingService:
    def __init__(self, db: Session, market_data_service: MarketDataService):
        self.db = db
        self.market_data = market_data_service
        self.api = tradeapi.REST(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
            settings.ALPACA_BASE_URL,
            api_version='v2'
        )
    
    async def get_account(self) -> Dict:
        """Get account information."""
        account = self.api.get_account()
        return {
            "id": account.id,
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value)
        }
    
    async def get_positions(self) -> Dict:
        """Get current positions."""
        positions = self.api.list_positions()
        return {
            position.symbol: {
                "qty": float(position.qty),
                "avg_entry_price": float(position.avg_entry_price),
                "market_value": float(position.market_value),
                "unrealized_pl": float(position.unrealized_pl)
            }
            for position in positions
        }
    
    async def create_portfolio(self, user_id: int, name: str, initial_balance: float) -> Portfolio:
        """Create a new portfolio for a user"""
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            cash_balance=initial_balance,
            total_value=initial_balance
        )
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    async def place_order(
        self,
        portfolio_id: int,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Order:
        """Place a new order"""
        # Validate portfolio exists
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise TradingError("Portfolio not found")

        # Check risk limits
        await self._validate_risk_limits(portfolio_id, symbol, quantity, price)

        # Create order
        order = Order(
            portfolio_id=portfolio_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Process order based on type
        if order_type == OrderType.MARKET:
            await self._execute_market_order(order)
        elif order_type == OrderType.LIMIT:
            await self._place_limit_order(order)
        elif order_type == OrderType.STOP:
            await self._place_stop_order(order)
        elif order_type == OrderType.STOP_LIMIT:
            await self._place_stop_limit_order(order)

        return order

    async def _execute_market_order(self, order: Order):
        """Execute a market order"""
        current_price = await self.market_data.get_current_price(order.symbol)
        if not current_price:
            raise TradingError(f"Could not get current price for {order.symbol}")

        # Calculate total cost
        total_cost = current_price * order.quantity
        if order.side == OrderSide.BUY:
            if total_cost > order.portfolio.cash_balance:
                raise TradingError("Insufficient funds")
            order.portfolio.cash_balance -= total_cost
        else:
            position = self._get_position(order.portfolio_id, order.symbol)
            if not position or position.quantity < order.quantity:
                raise TradingError("Insufficient position")

        # Update order status
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_fill_price = current_price

        # Update position
        await self._update_position(order)

        self.db.commit()

    async def _update_position(self, order: Order):
        """Update position after order execution"""
        position = self._get_position(order.portfolio_id, order.symbol)
        if not position:
            position = Position(
                portfolio_id=order.portfolio_id,
                symbol=order.symbol,
                quantity=0,
                average_entry_price=0,
                current_price=order.average_fill_price,
                unrealized_pnl=0,
                realized_pnl=0
            )
            self.db.add(position)

        if order.side == OrderSide.BUY:
            new_quantity = position.quantity + order.quantity
            new_cost = (position.quantity * position.average_entry_price +
                       order.quantity * order.average_fill_price)
            position.average_entry_price = new_cost / new_quantity
            position.quantity = new_quantity
        else:
            position.quantity -= order.quantity
            # Calculate realized P&L
            realized_pnl = (order.average_fill_price - position.average_entry_price) * order.quantity
            position.realized_pnl += realized_pnl

        position.current_price = order.average_fill_price
        position.unrealized_pnl = (position.current_price - position.average_entry_price) * position.quantity

    def _get_position(self, portfolio_id: int, symbol: str) -> Optional[Position]:
        """Get position for a symbol in a portfolio"""
        return self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol
        ).first()

    async def _validate_risk_limits(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: float,
        price: Optional[float]
    ):
        """Validate order against risk limits"""
        risk_limits = self.db.query(RiskLimit).filter(
            RiskLimit.portfolio_id == portfolio_id
        ).first()

        if not risk_limits:
            return

        # Calculate position value
        if not price:
            price = await self.market_data.get_current_price(symbol)
        position_value = quantity * price

        # Check position size limit
        if position_value > risk_limits.max_position_size:
            raise TradingError(f"Order exceeds maximum position size of {risk_limits.max_position_size}")

        # Check leverage limit
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if position_value / portfolio.total_value > risk_limits.max_leverage:
            raise TradingError(f"Order exceeds maximum leverage of {risk_limits.max_leverage}")

    async def get_portfolio_summary(self, portfolio_id: int) -> Dict[str, Any]:
        """Get portfolio summary including positions and performance"""
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise TradingError("Portfolio not found")

        positions = self.db.query(Position).filter(Portfolio.id == portfolio_id).all()
        
        # Calculate portfolio metrics
        total_position_value = sum(p.quantity * p.current_price for p in positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        total_realized_pnl = sum(p.realized_pnl for p in positions)
        
        return {
            "portfolio_id": portfolio.id,
            "name": portfolio.name,
            "cash_balance": portfolio.cash_balance,
            "total_position_value": total_position_value,
            "total_value": portfolio.cash_balance + total_position_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "average_entry_price": p.average_entry_price,
                    "current_price": p.current_price,
                    "unrealized_pnl": p.unrealized_pnl,
                    "realized_pnl": p.realized_pnl
                }
                for p in positions
            ]
        }

    async def backtest_strategy(
        self,
        strategy_id: int,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float
    ) -> BacktestResult:
        """Backtest a trading strategy"""
        strategy = self.db.query(TradingStrategy).filter(TradingStrategy.id == strategy_id).first()
        if not strategy:
            raise TradingError("Strategy not found")

        # Get historical data
        historical_data = await self.market_data.get_historical_data(
            strategy.parameters["symbol"],
            start_date,
            end_date
        )

        # Run backtest
        results = self._run_backtest(historical_data, strategy.parameters, initial_capital)

        # Save results
        backtest_result = BacktestResult(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_capital=results["final_capital"],
            total_return=results["total_return"],
            sharpe_ratio=results["sharpe_ratio"],
            max_drawdown=results["max_drawdown"],
            win_rate=results["win_rate"],
            parameters=strategy.parameters
        )
        self.db.add(backtest_result)
        self.db.commit()
        self.db.refresh(backtest_result)

        return backtest_result

    def _run_backtest(
        self,
        data: pd.DataFrame,
        parameters: Dict[str, Any],
        initial_capital: float
    ) -> Dict[str, float]:
        """Run backtest simulation"""
        # Implement strategy logic here
        # This is a placeholder implementation
        returns = data["close"].pct_change()
        cumulative_returns = (1 + returns).cumprod()
        
        return {
            "final_capital": initial_capital * cumulative_returns.iloc[-1],
            "total_return": cumulative_returns.iloc[-1] - 1,
            "sharpe_ratio": returns.mean() / returns.std() * np.sqrt(252),
            "max_drawdown": (cumulative_returns / cumulative_returns.cummax() - 1).min(),
            "win_rate": (returns > 0).mean()
        }

# Create singleton instance
trading_service = TradingService() 