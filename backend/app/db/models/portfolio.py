from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base

class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    cash_balance = Column(Float, default=0)
    total_value = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")
    transactions = relationship("Transaction", back_populates="portfolio")
    risk_limits = relationship("RiskLimit", back_populates="portfolio")
    trading_strategies = relationship("TradingStrategy", back_populates="portfolio")

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    realized_pnl = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    orders = relationship("Order", back_populates="position")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    notes = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")

class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    max_position_size = Column(Float)
    max_drawdown = Column(Float)
    max_leverage = Column(Float)
    stop_loss_percentage = Column(Float)
    take_profit_percentage = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="risk_limits")

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trading_strategies")
    backtest_results = relationship("BacktestResult", back_populates="strategy")

class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    parameters = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy = relationship("TradingStrategy", back_populates="backtest_results") 