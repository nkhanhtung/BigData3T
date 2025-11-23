
import logging
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from spark.consumer_topicKafka import matched_schema
from backend.cores.config import settings_kafka, settings_spark
from kafka import KafkaProducer
from spark.services.trading.indicator import sma, ema, vwap, rsi, macd, bollinger_bands, generate_trading_signal
from pymongo import MongoClient
from backend.cores.config import settings_mongodb
# ================= Logger =================

logger = logging.getLogger("IndicatorAlert")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Starting Spark IndicatorAlert...")

# ================= Spark session =================
spark = SparkSession.builder \
    .appName(settings_spark.SPARK_APP_NAME + "_IndicatorAlert") \
    .master(f"local[{settings_spark.THREAD_SOLD}]") \
    .getOrCreate()

logger.info("Spark session created.")

# ================= Kafka Producer =================
producer = KafkaProducer(
    bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)
logger.info("Kafka Producer initialized.")

# ================= Streaming DataFrame =================
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", settings_kafka.KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", settings_kafka.KAFKA_TOPIC_MATCHED_ORDERS) \
    .option("startingOffsets", "latest") \
    .load()

json_df = df.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), matched_schema).alias("data")) \
    .select("data.*")

# ================= Setting for Mongo sync=================
client = MongoClient(settings_mongodb.MONGO_DATABASE_URL)
db = client[settings_mongodb.MONGO_DB_NAME]
indicator_collection = db['indicators_alerts']

# ================= Indicator Logic =================
def process_indicators(batch_df, batch_id):
    indicator_msg_list = []
    row_count = batch_df.count()
    logger.info(f"Processing batch_id={batch_id} with {row_count} rows")
    if row_count == 0:
        return

    df_ind = batch_df
    # ---------- Các chỉ báo ----------
    df_ind = sma(df_ind, period=10)
    df_ind = ema(df_ind, period=10)
    df_ind = vwap(df_ind)
    df_ind = rsi(df_ind, period=14)
    df_ind = macd(df_ind, fast=12, slow=26, signal=9)
    df_ind = bollinger_bands(df_ind, period=20, k=2)
    df_ind = generate_trading_signal(df_ind)


    # ---------- Push to Kafka ----------
    for row in df_ind.collect():
        indicator_msg = {
            "symbol": row.stock_symbol,
            "timestamp": str(row.trade_timestamp),
            "price": row.matched_price,
            "quantity": row.matched_quantity,
            "SMA_10": getattr(row, "SMA_10", None),
            "EMA_10": getattr(row, "EMA_10", None),
            "VWAP": getattr(row, "VWAP", None),
            "RSI_14": getattr(row, "RSI", None),
            "MACD_line": getattr(row, "MACD_line", None),
            "MACD_signal": getattr(row, "MACD_signal", None),
            "MACD_hist": getattr(row, "MACD_hist", None),
            "BB_upper": getattr(row, "BB_upper", None),
            "BB_lower": getattr(row, "BB_lower", None),
            "signal": getattr(row, "signal", "HOLD")
        }
        producer.send(settings_kafka.KAFKA_TOPIC_INDICATOR_ALERTS, indicator_msg)
        producer.flush()
        logger.info(f"Indicator sent to Kafka: {indicator_msg}")
        indicator_msg_list.append(indicator_msg)
        logger.info("Appended indicator_msg in Indicator_msg_list")
    if indicator_msg_list:
        indicator_collection.insert_many(indicator_msg_list)
        logger.info("Insert successfully in Mongodb")

# ================= Start streaming =================
query = json_df.writeStream \
    .foreachBatch(process_indicators) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark_indicator_checkpoint") \
    .start()

logger.info("Streaming query started.")
query.awaitTermination()
