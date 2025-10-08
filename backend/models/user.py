from sqlalchemy import Column, Integer, Text, Numeric, DateTime, String, BigInteger, func
from sqlalchemy.orm import relationship
from databases.postsql.database import Base

class User(Base):
    __tablename__ = "users" 
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(Text, nullable=False)
    user_email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)

    balance = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_stocks = relationship("UserStock", back_populates="user")
    user_orders = relationship("Order", back_populates="orders_user")
