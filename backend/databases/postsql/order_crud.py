from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from uuid import UUID

from models.order import Order

async def get_orders_by_user_id_db(db: AsyncSession, user_id: int) -> List[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_timestamp.desc())
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return orders

async def create_order_db(session: AsyncSession, order_data: Dict[str, Any]) -> Order:
    model_data = {k: v for k, v in order_data.items() if hasattr(Order, k)}
    db_order = Order(**model_data)
    session.add(db_order)
    await session.commit()
    await session.refresh(db_order)
    return db_order

async def get_order_by_id_db(session: AsyncSession, order_id: UUID) -> Order | None:
    result = await session.execute(select(Order).filter(Order.order_id == order_id))
    db_order = result.scalar_one_or_none()
    return db_order

async def update_order_status_db(session: AsyncSession, order_id: UUID, new_status: str, **kwargs) -> Order | None:
    result = await session.execute(select(Order).filter(Order.order_id == order_id))
    db_order = result.scalar_one_or_none()
    if db_order:
        db_order.current_status = new_status
        for key, value in kwargs.items():
            if hasattr(db_order, key) and value is not None:
                setattr(db_order, key, value)
        
        await session.commit()
        await session.refresh(db_order)
        return db_order
    return None

async def cancel_order_db(session: AsyncSession, order_id: UUID) -> Order | None:
    return await update_order_status_db(session, order_id, "CANCELLED")