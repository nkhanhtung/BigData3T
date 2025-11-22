
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging
from cores.config import settings_mongodb 

logger = logging.getLogger(__name__)


mongo_client: AsyncIOMotorClient = None
mongo_database: AsyncIOMotorDatabase = None

async def get_db_connection():
    global mongo_client, mongo_database
    if mongo_client is None:
        try:
            mongo_client = AsyncIOMotorClient(
                settings_mongodb.MONGO_DATABASE_URL,  # ← dùng property ở trên
                serverSelectionTimeoutMS=5000 
            )
            await mongo_client.admin.command('ping') 
            
            mongo_database = mongo_client[settings_mongodb.MONGO_DB_NAME]  # ← dùng database từ config
            logger.info("MongoDB client and database initialized successfully.")
        except Exception as e:
            logger.critical(f"Failed to connect to MongoDB: {e}", exc_info=True)
            raise
    return mongo_database


async def close_db_connection():
    global mongo_client
    if mongo_client:
        logger.info("Closing MongoDB client...")
        mongo_client.close()
        mongo_client = None
        logger.info("MongoDB client closed.")

async def get_mongo_db():
    if mongo_database is None:
        logger.warning("MongoDB database not initialized. Calling get_db_connection().")
        await get_db_connection() 
    
    return mongo_database

async def get_stock_logs_collection():
    db = await get_mongo_db()
    return db['stocks_logs']

async def get_login_user_logs_collection():
    db = await get_mongo_db()
    return db['logins_users']

async def get_logout_user_logs_collection():
    db = await get_mongo_db()
    return db['logouts_users']
