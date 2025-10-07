from sqlalchemy import Column, Integer, Float, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from databases.postsql.database import Base


class UserStock(Base):
    __tablename__ = "users_stocks"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.stock_id", ondelete="CASCADE"), primary_key=True,)
    quantity = Column(Integer, nullable=False)
    mean_price = Column(Numeric(10, 2), nullable=False)

    user = relationship("User", back_populates="user_stocks")
    stock = relationship("Stock", back_populates="stock_users")
