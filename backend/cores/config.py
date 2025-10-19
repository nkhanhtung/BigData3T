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
    KAFKA_TOPIC_PENDING_ORDERS: str = "pending_orders"
    KAFKA_TOPIC_MATCHED_ORDERS: str = "matched_orders"
    KAFKA_TOPIC_ORDER_COMMANDS: str = "order_commands" 
    KAFKA_TOPIC_ORDER_STATUS_UPDATES: str = "order_status_updates"
    KAFKA_TOPIC_MARKET_DATA: str = "market_data" 

    class Config:
        env_file = ".env"
        case_sensitive = True

settings_kafka = SettingsKafka()

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

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

settings_redis = SettingsRedis()

class SettingsMongoDB(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_USERNAME: Optional[str] = None
    MONGODB_PASSWORD: Optional[str] = None
    MONGODB_DATABASE: str = "trading_app_db" 
    MONGODB_AUTHSOURCE: Optional[str] = None

    @property
    def MONGODB_URL(self) -> str:
        if self.MONGODB_USERNAME and self.MONGODB_PASSWORD:
            if self.MONGODB_AUTHSOURCE:
                 return f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}?authSource={self.MONGODB_AUTHSOURCE}"
            return f"mongodb://{self.MONGODB_USERNAME}:{self.MONGODB_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}"
        return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DATABASE}"

settings_mongodb = SettingsMongoDB()