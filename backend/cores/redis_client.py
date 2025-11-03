
import aioredis 
import logging
from cores.config import settings_redis 

logger = logging.getLogger(__name__)
r_client: aioredis.Redis = None
async def get_redis_connection():
    global r_client
    if r_client is None:
        try:
            REDIS_URL = f"redis://{settings_redis.REDIS_HOST}:{settings_redis.REDIS_PORT}/{settings_redis.REDIS_DB}"
    
            r_client = aioredis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True 
            )
            await r_client.ping()
            logger.info("Redis client initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to connect to Redis: {e}", exc_info=True)
            raise 
    
    return r_client

async def close_redis_connection():
    global r_client
    if r_client:
        logger.info("Closing Redis client...")
        await r_client.close() 
        r_client = None
        logger.info("Redis client closed.")

async def get_redis_client():
    if r_client is None:
        logger.warning("Redis client not initialized. Calling get_redis_connection().")
        await get_redis_connection() 
    return r_client