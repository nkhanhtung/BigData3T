
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
            MONGO_DATABASE_URL = "mongodb+srv://maiminhtung2005_db_user:ggzaIHwy1EOsEFnC@cluster0.lu0egys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            MONGO_DB_NAME = "BigData" 

            mongo_client = AsyncIOMotorClient(
                MONGO_DATABASE_URL,
                serverSelectionTimeoutMS=5000 
            )
            await mongo_client.admin.command('ping') 
            
            mongo_database = mongo_client[MONGO_DB_NAME]
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