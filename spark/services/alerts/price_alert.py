import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from spark.consumer_topicKafka import matched_schema
from backend.cores.config import settings_kafka, settings_spark
from kafka import KafkaProducer
import json

# ================= Logger =================
logger = logging.getLogger("PriceAlert")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Starting Spark PriceAlert...")

# ================= Spark session =================
spark = SparkSession.builder \
    .appName(settings_spark.SPARK_APP_NAME + "_PriceAlert") \
    .master(f"local[{settings_spark.THREAD_SOLD}]") \
    .getOrCreate()

logger.info("Spark session created.")

# ================= Kafka Producer =================
producer = KafkaProducer(
    bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
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

# ================= Alert Logic =================
last_prices = {}

def process_batch(batch_df, batch_id):
    row_count = batch_df.count()
    logger.info(f"Processing batch_id={batch_id} with {row_count} rows")
    
    if row_count == 0:
        return

    rows = batch_df.collect()
    for row in rows:
        symbol = row.stock_symbol
        prev_price = last_prices.get(symbol)
        last_prices[symbol] = row.matched_price
        logger.info(f"Received row: {symbol} -> {row.matched_price}")

        if prev_price is not None:
            change_pct = (row.matched_price - prev_price) / prev_price * 100
            if abs(change_pct) > settings_spark.PRICE_MOVE_THRESHOLD:
                alert = {
                    "symbol": symbol,
                    "prev_price": prev_price,
                    "current_price": row.matched_price,
                    "change_pct": change_pct
                }
                # Chỉ gửi vào Kafka topic
                producer.send(settings_kafka.KAFKA_TOPIC_PRICE_ALERTS, alert)
                producer.flush()
                logger.warning(f"⚠️ Price alert sent to Kafka: {alert}")

    logger.info(f"Updated last_prices: {last_prices}")

# ================= Start streaming =================
query = json_df.writeStream \
    .foreachBatch(process_batch) \
    .outputMode("append") \
    .option("checkpointLocation", "/tmp/spark_price_alert_checkpoint") \
    .start()

logger.info("Streaming query started.")
query.awaitTermination()
