
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_X3MpLju8nzxi@ep-lingering-pond-a1q4x3j5-pooler.ap-southeast-1.aws.neon.tech:5432/neondb"
async_engine = None
AsyncSessionLocal = None
Base = declarative_base() 

async def get_db_connection():
    global async_engine, AsyncSessionLocal
    if async_engine is None:
        try:
            async_engine = create_async_engine(
                DATABASE_URL,
                echo=True, 
                pool_size=10,
                max_overflow=20 
            )
            AsyncSessionLocal = async_sessionmaker(
                async_engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            
            async with async_engine.connect() as conn:
                await conn.run_sync(Base.metadata.create_all) 
            logger.info("PostgreSQL async engine and session factory initialized.")
            logger.info("Database tables created (if not exist).")
        except Exception as e:
            logger.critical(f"Failed to initialize PostgreSQL async engine: {e}", exc_info=True)
            raise 

    return async_engine

async def close_db_connection():
    global async_engine
    if async_engine:
        logger.info("Disposing PostgreSQL async engine...")
        await async_engine.dispose()
        async_engine = None
        logger.info("PostgreSQL async engine disposed.")

async def get_async_session():
    if AsyncSessionLocal is None:
        logger.warning("AsyncSessionLocal not initialized. Calling get_db_connection().")
        await get_db_connection() 

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()