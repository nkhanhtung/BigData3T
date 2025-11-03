from sqlalchemy import Column, Integer, Text, Numeric, DateTime, String, ForeignKey, func
from sqlalchemy.orm import relationship
from databases.postsql.database import Base
import sqlalchemy as sa
import uuid


class OrderHistory(Base):
    __tablename__ = "order_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)  # SERIAL
    order_id = Column(sa.UUID(as_uuid=True),ForeignKey("orders.order_id", onupdate="CASCADE", ondelete="RESTRICT"),nullable=False)

    status_at_event = Column(String(20), nullable=False)
    filled_quantity_at_event = Column(Integer, default=0)
    filled_price_avg_at_event = Column(Numeric(10, 2), default=0)

    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_details = Column(Text)

    histories_order = relationship("Order", back_populates="order_histories")