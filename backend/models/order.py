from sqlalchemy import Column, Integer, Text, Numeric, DateTime, String, ForeignKey, func
from sqlalchemy.orm import relationship
from databases.postsql.database import Base
import sqlalchemy as sa
import uuid

class Order(Base):
    __tablename__ = "orders"

    order_id = sa.Column(sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.user_id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    stock_symbol = Column(String(3), ForeignKey("stocks.stock_symbol", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    order_type = Column(String(20), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    filled_quantity = Column(Integer, default=0)
    filled_price_avg = Column(Numeric(10, 2), default=0)

    status = Column(String(20), nullable=False, default='PENDING')
    created_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    orders_user = relationship("User", back_populates="user_orders")
    orders_stock = relationship("Stock", back_populates="stock_orders")
    order_histories = relationship("OrderHistory", back_populates="histories_order")