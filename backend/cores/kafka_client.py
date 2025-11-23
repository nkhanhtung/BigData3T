from kafka import KafkaProducer, KafkaConsumer
import json
from .config import settings_kafka
import logging
import asyncio 
from concurrent.futures import ThreadPoolExecutor 
from typing import Optional
import uuid
from datetime import datetime
from decimal import Decimal


logger = logging.getLogger(__name__)

def json_serializer(obj):
    """Custom JSON serializer for UUID, datetime, and Decimal."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def get_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=json_serializer).encode('utf-8'),
            retries=5,
            linger_ms=10
        )
        logger.info(f"Kafka Producer connected to {settings_kafka.KAFKA_BOOTSTRAP_SERVERS}")
        return producer
    except Exception as e:
        logger.error(f"Failed to connect Kafka Producer: {e}")
        raise

def get_kafka_consumer(topic: str, group_id: str, auto_offset_reset: str = 'earliest'):
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            enable_auto_commit=True,
            auto_commit_interval_ms=5000
        )
        logger.info(f"Kafka Consumer for topic '{topic}' with group_id '{group_id}' connected to {settings_kafka.KAFKA_BOOTSTRAP_SERVERS}")
        return consumer
    except Exception as e:
        logger.error(f"Failed to connect Kafka Consumer for topic '{topic}': {e}")
        raise

kafka_producer_instance: Optional[KafkaProducer] = None
_thread_pool_executor = ThreadPoolExecutor(max_workers=1) 

def initialize_kafka_producer():
    global kafka_producer_instance
    if kafka_producer_instance is None:
        kafka_producer_instance = get_kafka_producer()
    return kafka_producer_instance

async def get_kafka_producer_async():
    """Returns the initialized Kafka producer instance. For use with FastAPI startup events."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_thread_pool_executor, initialize_kafka_producer)


async def send_message_to_kafka_sync_in_thread(producer: KafkaProducer, topic: str, message: dict):
    """
    Sends a message to Kafka using the synchronous producer in a separate thread.
    This avoids blocking the event loop.
    """
    future = producer.send(topic, message)
    record_metadata = await asyncio.get_event_loop().run_in_executor(
        _thread_pool_executor, future.get
    )
    return record_metadata

async def send_order_to_kafka(topic: str, order_data: dict):
    """
    Asynchronously sends order data to a Kafka topic.
    Initializes the producer if not already initialized.
    """
    try:
        producer = await get_kafka_producer_async()
        record_metadata = await send_message_to_kafka_sync_in_thread(producer, topic, order_data)
        logger.info(f"Message sent to topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
    except Exception as e:
        logger.error(f"Error sending message to Kafka topic {topic}: {e}")
        raise

def close_kafka_producer():
    global kafka_producer_instance
    if kafka_producer_instance:
        kafka_producer_instance.flush()
        kafka_producer_instance.close()
        logger.info("Kafka Producer closed.")
        _thread_pool_executor.shutdown(wait=True) 
        logger.info("Thread pool executor shut down.")

async def send_message(topic: str, message: dict):
    """Gửi message một cách bất đồng bộ. Đây là hàm mà router sẽ gọi."""
    loop = asyncio.get_event_loop()
    try:
        producer = await get_kafka_producer_async()
        future = producer.send(topic, message)
        record_metadata = await loop.run_in_executor(_thread_pool_executor, future.get, 30)
        logger.info(f"Message sent to topic '{record_metadata.topic}' partition {record_metadata.partition}")
    except Exception as e:
        logger.error(f"Error sending message to Kafka topic {topic}: {e}", exc_info=True)
        raise
