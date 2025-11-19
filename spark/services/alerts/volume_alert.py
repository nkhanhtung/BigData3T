# realtime_volume_alert_kafka.py
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, sum
from spark.consumer_topicKafka import matched_schema
from backend.cores.config import settings_spark, settings_kafka
from kafka import KafkaProducer
import json
from pymongo import MongoClient
from backend.cores.config import settings_mongodb

# ================= Logger =================
logger = logging.getLogger("VolumeAlert")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Starting Spark VolumeAlert...")

# ================= Spark session =================
existing_spark = SparkSession.getActiveSession()
if existing_spark:
    existing_spark.stop()

spark = SparkSession.builder \
    .appName(settings_spark.SPARK_APP_NAME + "_VolumeAlert") \
    .master(f"local[{settings_spark.THREAD_SOLD}]") \
    .getOrCreate()

logger.info("Spark session created")

# ================= Kafka Producer =================
producer = KafkaProducer(
    bootstrap_servers=settings_kafka.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
logger.info("Kafka Producer initialized")

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

# ================= Aggregate volume =================
agg_df = json_df.groupBy(
    window(col("trade_timestamp"), "1 minute"),
    col("stock_symbol")
).agg(
    sum("matched_quantity").alias("total_volume")
)

alerts_df = agg_df.filter(col("total_volume") > settings_spark.VOLUME_THRESHOLD)

# ================= Setting for Mongo sync=================
client = MongoClient(settings_mongodb.MONGO_DATABASE_URL)
db = client[settings_mongodb.MONGO_DB_NAME]
volume_collection = db['volumes_alerts']

# ================= Alert logic =================
def process_volume_batch(batch_df, batch_id):
    volume_msg_list = []
    rows = batch_df.collect()
    for row in rows:
        window_start = row['window']['start']
        window_end = row['window']['end']
        symbol = row['stock_symbol']
        total_volume = row['total_volume']
        msg = {
            "symbol": symbol,
            "total_volume": total_volume,
            "window_start": str(window_start),
            "window_end": str(window_end)
        }

        # Chỉ gửi vào Kafka topic
        producer.send(settings_kafka.KAFKA_TOPIC_VOLUME_ALERTS, msg)
        producer.flush()
        logger.warning(f"⚠️ Volume alert sent to Kafka: {msg}")
        volume_msg_list.append(msg)
        logger.info("Appended msg in volume_msg_list")
    
    if volume_msg_list:
        volume_collection.insert_many(volume_msg_list)
        logger.info("Insert successfully in Mongodb")
    logger.info("Finish volume batch")

# ================= Start streaming =================
query = alerts_df.writeStream \
    .outputMode("update") \
    .foreachBatch(process_volume_batch) \
    .option("checkpointLocation", "/tmp/spark_volume_alert_checkpoint") \
    .start()

logger.info("Streaming query started.")
query.awaitTermination()
