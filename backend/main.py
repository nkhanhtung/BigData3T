
from fastapi import FastAPI
import uvicorn
from routers import user, admin, trading, visualization, realtime
from fastapi.middleware.cors import CORSMiddleware
import logging
from cores.kafka_client import get_kafka_producer_async, close_kafka_producer
from databases.postsql.database import close_db_connection as close_postgres_db, get_db_connection as get_postgres_db_connection
from databases.mongodb.database import close_db_connection as close_mongodb, get_db_connection as get_mongodb_connection
from cores.redis_client import close_redis_connection, get_redis_connection 

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(user.router, prefix="/user", tags=['User Management'])
app.include_router(admin.router, prefix="/admin", tags=["Admin Management"])
app.include_router(trading.router, prefix="/trading", tags=["Trading Operations"])
app.include_router(visualization.router, prefix="/visualization", tags=["Visualize Stocks"])
app.include_router(realtime.router, prefix="/realtime", tags=["Realtime Trading"])

origins = [
    "http://localhost:5173", 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

@app.on_event("startup")
async def startup_event():
    """
    Sự kiện được gọi khi ứng dụng khởi động.
    Khởi tạo tất cả các kết nối cần thiết.
    """
    logger.info("Application starting up...")
    try:
        await get_kafka_producer_async()
        logger.info("Kafka Producer initialized.")

        await get_postgres_db_connection() 
        logger.info("PostgreSQL database connection initialized.")

        await get_mongodb_connection() 
        logger.info("MongoDB database connection initialized.")

        await get_redis_connection()
        logger.info("Redis client initialized.")

    except Exception as e:
        logger.critical(f"Failed to initialize resources during startup: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Sự kiện được gọi khi ứng dụng tắt.
    Đóng tất cả các kết nối và giải phóng tài nguyên.
    """
    logger.info("Application shutting down...")
    
    try:
        close_kafka_producer()
        logger.info("Kafka Producer closed.")
    except Exception as e:
        logger.error(f"Error closing Kafka Producer: {e}")

    try:
        await close_postgres_db() 
        logger.info("PostgreSQL database connection closed.")
    except Exception as e:
        logger.error(f"Error closing PostgreSQL connection: {e}")


    try:
        await close_mongodb()
        logger.info("MongoDB database connection closed.")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")

    try:
        await close_redis_connection()
        logger.info("Redis client closed.")
    except Exception as e:
        logger.error(f"Error closing Redis client: {e}")

    logger.info("Application shutdown complete.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)