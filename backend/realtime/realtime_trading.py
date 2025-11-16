import asyncio
import json
from aiokafka import AIOKafkaConsumer
from fastapi import WebSocket
from cores.config import settings_kafka

async def stream_matched_orders(websocket: WebSocket):
    await websocket.accept()

    consumer = AIOKafkaConsumer(
        "matched_orders",
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
                buffer.clear()
            await asyncio.sleep(5)

    asyncio.create_task(flush())

    try:
        async for msg in consumer:
            buffer.append(msg.value)
    finally:
        await consumer.stop()
