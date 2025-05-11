from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# Association table for watchlist stocks
watchlist_stocks = Table(
    "watchlist_stocks",
    Base.metadata,
    Column("watchlist_id", Integer, ForeignKey("watchlists.id"), primary_key=True),
    Column("stock_id", Integer, ForeignKey("stocks.id"), primary_key=True),
    Column("added_at", DateTime(timezone=True), server_default=func.now())
)

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="watchlists")
    stocks = relationship("Stock", secondary=watchlist_stocks, back_populates="watchlists") 