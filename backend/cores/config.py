import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str =  "maiminhtung20042005@"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()

class SettingsKafka(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092") 
    KAFKA_TOPIC_ORDERS_RAW: str = "orders_raw"
    KAFKA_TOPIC_MATCHED_ORDERS: str = "matched_orders"
    KAFKA_TOPIC_ORDER_COMMANDS: str = "order_commands" 
    KAFKA_TOPIC_PRICE_ALERTS: str = "price_alerts"
    KAFKA_TOPIC_VOLUME_ALERTS: str = "volume_alerts"
    KAFKA_TOPIC_INDICATOR_ALERTS: str = "indicator_alerts"
    KAFKA_TOPIC_OHLC_VISUALIZATION: str = "ohlc_visualization"
    KAFKA_TOPIC_ORDER_UPDATES: str = 'order_updates'


    class Config:
        env_file = ".env"
        case_sensitive = True

class SettingsRedis(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore' 
    )

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    MAX_FAILED_ATTEMPTS: int = 5           # số lần login sai tối đa
    FAILED_ATTEMPT_TTL_MINUTES: int = 5    # TTL của key failed login, phút
    BLOCK_TIME_MINUTES: int = 5             # Thời gian khóa user sau quá số lần login sai, phút

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def FAILED_ATTEMPT_TTL_SECONDS(self) -> int:
        return self.FAILED_ATTEMPT_TTL_MINUTES * 60

    @property
    def BLOCK_TIME_SECONDS(self) -> int:
        return self.BLOCK_TIME_MINUTES * 60


class SettingsMongoDB(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # Full connection string (MongoDB Atlas)
    MONGO_DATABASE_URL: str = "mongodb+srv://maiminhtung2005_db_user:ggzaIHwy1EOsEFnC@cluster0.lu0egys.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    MONGO_DB_NAME: str = "BigData"


class SettingsSpark(BaseSettings):
    SPARK_APP_NAME: str = "TradingAlerts"
    THREAD_SOLD: int = 4              
    BATCH_DURATION_SEC: int = 60
    WATERMARK_DELAY_SEC: int = 10

    # Threshold cho alert
    VOLUME_THRESHOLD: int = 1000          # tổng lượng giao dịch / window
    PRICE_MOVE_THRESHOLD: float = 1.0     # % biến động giá để cảnh báo


    class Config:
        env_file = ".env"
        case_sensitive = True

settings_spark = SettingsSpark()
settings_redis = SettingsRedis()
settings_mongodb = SettingsMongoDB()
settings_kafka = SettingsKafka()
