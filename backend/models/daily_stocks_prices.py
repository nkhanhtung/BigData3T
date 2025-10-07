from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from databases.postsql.database import Base
from sqlalchemy.orm import relationship


class DailyStockPrice(Base):
    __tablename__ = "daily_stocks_prices"

    stock_id = Column(Integer, ForeignKey("stocks.stock_id", ondelete="CASCADE"), primary_key=True)
    date = Column(Date, nullable=False)  
    current_price = Column(Numeric(10,2), nullable=False)
    open_price = Column(Numeric(10,2), nullable=False)
    close_price = Column(Numeric(10,2), nullable=False)
    high_price = Column(Numeric(10,2), nullable=False)
    low_price = Column(Numeric(10,2), nullable=False)
    volumes = Column(Integer, nullable=False)

    daily_stocks = relationship("Stock", back_populates="stock_dailies")

