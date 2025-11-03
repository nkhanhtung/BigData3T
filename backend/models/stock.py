from sqlalchemy import Column, Integer, Text, Numeric, DateTime, String
from sqlalchemy.orm import relationship
from databases.postsql.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    stock_id = Column(Integer, primary_key=True, autoincrement=True)
    stock_symbol = Column(String(3), nullable=False, unique=True)
    stock_name = Column(Text, nullable=False, unique=True)
    major = Column(Text, nullable=False)
    market_name = Column(Text, nullable=False)

    stock_users = relationship("UserStock", back_populates="stock")
    stock_dailies = relationship("DailyStockPrice", back_populates="dailies_stock")
    stock_orders = relationship("Order", back_populates="orders_stock")
