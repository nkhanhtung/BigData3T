import os
import logging
import json
import asyncio
import uuid
from datetime import datetime
from dateutil import parser
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Điều chỉnh đường dẫn import cho đúng với vị trí file này
from backend.cores.config import settings_kafka
from backend.databases.postsql.database import get_async_session, get_db_connection, close_db_connection
from backend.models.order import Order
from backend.models.order_history import OrderHistory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

KAFKA_TOPIC_ORDER_UPDATES = os.getenv("KAFKA_TOPIC_ORDER_UPDATES", "order_updates")

async def process_event(event: dict, session: AsyncSession):
    # ... (Toàn bộ logic xử lý message và ghi vào DB như cũ) ...
    # (Nội dung hàm này đã đúng, không cần thay đổi)
    try:
        logger.info(f"Processing event: {event}")
        order_id_str = event.get('order_id')
        if not order_id_str:
            return
        order_id = uuid.UUID(order_id_str)
        history_record = OrderHistory(
            order_id=order_id, 
            status_at_event=event.get('status_at_event'),
            filled_quantity_at_event=event.get('filled_quantity_at_event'),
            filled_price_avg_at_event=Decimal(str(event.get('filled_price_avg_at_event', '0.0'))),
            event_timestamp=parser.isoparse(event.get('event_timestamp')),
            event_details=event.get('event_details')
        )
        session.add(history_record)
        
        stmt_select = select(Order.quantity).where(Order.order_id == order_id)
        result = await session.execute(stmt_select)
        quantity = result.scalar_one_or_none()
        if quantity is not None:
            status = event.get("status_at_event")

            if status == "CANCELED":
                stmt_update = update(Order).where(Order.order_id == order_id).values(
                    status=event.get('status_at_event'), 
                    last_updated_timestamp=parser.isoparse(event.get('event_timestamp')),
                )
                await session.execute(stmt_update)
            else:
                filled_quantity = event.get('filled_quantity_at_event', 0)
                remaining_quantity = quantity - filled_quantity

                stmt_update = update(Order).where(Order.order_id == order_id).values(
                    status=event.get('status_at_event'), 
                    filled_quantity=filled_quantity,
                    filled_price_avg=Decimal(str(event.get('filled_price_avg_at_event', '0.0'))),
                    quantity=remaining_quantity, 
                    last_updated_timestamp=parser.isoparse(event.get('event_timestamp')),
                )
                await session.execute(stmt_update)
        await session.commit()
        logger.info(f"Transaction committed for order_id: {order_id}")
    except Exception as e:
        logger.error(f"Error processing event {event}: {e}", exc_info=True)
        await session.rollback()

async def consume_order_updates():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_ORDER_UPDATES,
        bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
        group_id="persistence_service_group",
        auto_offset_reset="earliest",
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    await get_db_connection()
    await consumer.start()
    logger.info(f"Listening for messages on topic '{KAFKA_TOPIC_ORDER_UPDATES}'...")
    try:
        async for msg in consumer:
            async for session in get_async_session():
                await process_event(msg.value, session)
    finally:
        await consumer.stop()
        await close_db_connection()

def main():
    try:
        asyncio.run(consume_order_updates())
    except KeyboardInterrupt:
        logger.info("Persistence service shutting down.")

if __name__ == "__main__":
    main()