from pydantic import BaseModel, Field, condecimal, constr
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal
from uuid import UUID


ORDER_TYPES = Literal["BUY", "SELL"]
ORDER_STATUSES = Literal["PENDING", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED"]

class OrderBase(BaseModel):
    user_id: int = Field(..., description="ID of the user placing the order")
    stock_symbol: constr(min_length=1, max_length=10) = Field(..., description="Symbol of the stock (e.g., 'AAPL', 'GOOGL')")
    order_type: ORDER_TYPES = Field(..., description="Type of order ('BUY' or 'SELL')")
    
    # Sử dụng condecimal cho kiểu Numeric(10, 2)
    price: condecimal(max_digits=10, decimal_places=2) = Field(..., gt=0, description="Price per share at the time of order")
    quantity: int = Field(..., ge=0, description="Number of shares to trade")

class OrderCreate(OrderBase):
    """Schema for creating a new order."""
    pass

class OrderUpdate(BaseModel):
    """Schema for updating an existing order."""
    """Test API when upload docker remove order_id, action, status"""
    order_id: UUID
    action: str
    quantity: Optional[int] = Field(None, ge=0, description="New quantity of shares to trade")
    price: Optional[condecimal(max_digits=10, decimal_places=2)] = Field(None, gt=0, description="New price per share")
    status: Optional[ORDER_STATUSES] = Field(None, description="New status of the order")
    
    class Config:
        """Allow ORM mode to automatically convert SQLAlchemy models to Pydantic models."""
        orm_mode = True

class OrderInDB(OrderBase):
    """Schema for an order as stored in the database, including system-generated fields."""
    order_id: UUID
    
    filled_quantity: int = Field(0, description="Number of shares that have been filled")
    filled_price_avg: condecimal(max_digits=10, decimal_places=2) = Field(Decimal('0.00'), description="Average price of filled shares")
    
    status: ORDER_STATUSES = Field("PENDING", description="Current status of the order")
    created_timestamp: datetime = Field(..., description="Timestamp of when the order was created")
    last_updated_timestamp: datetime = Field(..., description="Timestamp of when the order was last updated")

    class Config:
        """Allow ORM mode to automatically convert SQLAlchemy models to Pydantic models and handle JSON encoding."""
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + "Z", 
            Decimal: lambda d: str(d) 
        }