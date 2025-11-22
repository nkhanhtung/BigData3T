from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import uuid
from uuid import UUID
import logging

from schemas.order import OrderCreate, OrderInDB, OrderUpdate

from databases.postsql.order_crud import (
    create_order_db, 
    get_order_by_id_db, 
    get_orders_by_user_id_db
)
from databases.postsql.database import get_async_session

from cores.kafka_client import send_message
from cores.config import settings_kafka 

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/place", response_model=OrderInDB, status_code=status.HTTP_201_CREATED)
async def place_order(order_data: OrderCreate, db: AsyncSession = Depends(get_async_session)):
    kafka_message = {
        "order_id": str(uuid.uuid4()),
        "user_id": order_data.user_id,
        "stock_symbol": order_data.stock_symbol.upper(),
        "order_type": order_data.order_type.upper(),
        "price": order_data.price,
        "quantity": order_data.quantity,
        "created_timestamp": datetime.utcnow(),
        "action_type": "NEW"
    }

    try:
        db_order = await create_order_db(db, kafka_message)
        await send_message(settings_kafka.KAFKA_TOPIC_ORDERS_RAW, kafka_message)
        return db_order
    except Exception as e:
        logger.error(f"Error placing order: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to place order")
    

@router.get("/user/{user_id}", response_model=List[OrderInDB])
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_async_session)):
    orders = await get_orders_by_user_id_db(db, user_id)
    return orders


@router.put("/{order_id}/update", response_model=OrderInDB)
async def update_order(order_id: uuid.UUID, order_update_data: OrderUpdate, db: AsyncSession = Depends(get_async_session)):
    existing_order = await get_order_by_id_db(db, order_id)
    if not existing_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if existing_order.status not in ["PENDING", "PARTIALLY_FILLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update order with status '{existing_order.status}'"
        )

    kafka_message = {
        "order_id": str(order_id),
        "price": order_update_data.price,
        "quantity": order_update_data.quantity,
        "action_type": "UPDATE",
        "user_id": None, "stock_symbol": None, "order_type": None,
        "created_timestamp": datetime.utcnow().isoformat()
    }

    try:
        await send_message(settings_kafka.KAFKA_TOPIC_ORDERS_RAW, kafka_message)
        logger.info(f"UPDATE command sent to Kafka for order {order_id}")
        return existing_order
    except Exception as e:
        logger.error(f"Error sending UPDATE command to Kafka for order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send order update command")


@router.post("/{order_id}/cancel", response_model=OrderInDB)
async def cancel_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)):
    existing_order = await get_order_by_id_db(db, order_id)
    if not existing_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if existing_order.status not in ["PENDING", "PARTIALLY_FILLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{existing_order.status}'"
        )

    kafka_message = {
        "order_id": str(order_id),
        "action_type": "CANCEL",
        "price": None, "quantity": None, "user_id": None, "stock_symbol": None,
        "order_type": None, "created_timestamp": datetime.utcnow().isoformat()
    }

    try:
        await send_message(settings_kafka.KAFKA_TOPIC_ORDERS_RAW, kafka_message)
        logger.info(f"CANCEL command sent to Kafka for order {order_id}")
        return existing_order
    except Exception as e:
        logger.error(f"Error sending CANCEL command to Kafka for order {order_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send order cancel command")


@router.get("/{order_id}", response_model=OrderInDB)
async def get_order_details(order_id: uuid.UUID, db: AsyncSession = Depends(get_async_session)):
    order = await get_order_by_id_db(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order