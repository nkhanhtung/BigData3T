from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey
from databases.postsql.database import Base
from sqlalchemy.orm import relationship


class MonthlyStockPrice(Base):
    __tablename__ = "monthly_stocks_prices"

    stock_symbol = Column(String(3), ForeignKey("stocks.stock_symbol", ondelete="CASCADE"),primary_key=True)
    date = Column(Date, nullable=False)  
    open_price = Column(Numeric(10,2), nullable=False)
    close_price = Column(Numeric(10,2), nullable=False)
    high_price = Column(Numeric(10,2), nullable=False)
    low_price = Column(Numeric(10,2), nullable=False)
    volumes = Column(Integer, nullable=False)

    monthlies_stock = relationship("Stock", back_populates="stock_monthlies")

