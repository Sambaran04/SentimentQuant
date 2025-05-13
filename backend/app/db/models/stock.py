from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    exchange = Column(String)
    sector = Column(String)
    industry = Column(String)
    market_cap = Column(Float)
    last_price = Column(Float)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default={})

    # Relationships
    watchlists = relationship("WatchlistStock", back_populates="stock")
    portfolio_positions = relationship("PortfolioPosition", back_populates="stock") 