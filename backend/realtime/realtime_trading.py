import os
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from fastapi import WebSocket
from cores.config import settings_kafka

# ================= Logger =================
logger = logging.getLogger("RealtimeConsumer")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# ================= consumer matched_order for realtime =================
async def stream_matched_orders(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected: matched_orders")

    consumer = AIOKafkaConsumer(
        settings_kafka.KAFKA_TOPIC_MATCHED_ORDERS,
        bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
        group_id="frontend_stream_group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="latest"
    )

    await consumer.start()
    buffer = []

    async def flush():
        while True:
            if buffer:
                await websocket.send_json(buffer.copy())
                logger.info(f"Flushed {len(buffer)} matched orders to WebSocket")
                buffer.clear()
            await asyncio.sleep(5)

    asyncio.create_task(flush())

    try:
        async for msg in consumer:
            buffer.append(msg.value)
            logger.debug(f"Received matched order: {msg.value}")
    except Exception as e:
        logger.warning(f"WebSocket disconnected: {e}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped: matched_orders")

# ================= consumer price_alert for realtime =================
async def stream_price_alerts(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected: price_alerts")

    consumer = AIOKafkaConsumer(
        settings_kafka.KAFKA_TOPIC_PRICE_ALERTS,
        bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await websocket.send_json(msg.value)
            logger.info(f"Sent price alert to WebSocket: {msg.value}")
    except Exception as e:
        logger.warning(f"WebSocket disconnected: {e}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped: price_alerts")

# ================= consumer volume_alert for realtime =================
async def stream_volume_alerts(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected: volume_alerts")

    consumer = AIOKafkaConsumer(
        settings_kafka.KAFKA_TOPIC_VOLUME_ALERTS,
        bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await websocket.send_json(msg.value)
            logger.info(f"Sent volume alert to WebSocket: {msg.value}")
    except Exception as e:
        logger.warning(f"WebSocket disconnected: {e}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped: volume_alerts")


# ================= consumer indicator_alert for realtime =================
async def stream_indicator_alerts(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected: indicator_alerts")

    consumer = AIOKafkaConsumer(
        settings_kafka.KAFKA_TOPIC_INDICATOR_ALERTS,
        bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )
    await consumer.start()
    try:
        async for msg in consumer:
            await websocket.send_json(msg.value)
            logger.info(f"Sent indicator alert to WebSocket: {msg.value}")
    except Exception as e:
        logger.warning(f"WebSocket disconnected: {e}")
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped: indicator_alerts")