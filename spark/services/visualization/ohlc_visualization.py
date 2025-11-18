import logging
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, min, max, sum, struct, to_timestamp
from spark.consumer_topicKafka import matched_schema
from backend.cores.config import settings_kafka, settings_spark
from kafka import KafkaProducer

# ================= Logger =================
logger = logging.getLogger("Visualize: OHLC")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.info("Starting Spark Visualize: OHLC...")

# ================= Spark session =================
spark = SparkSession.builder \
    .appName(f"{settings_spark.SPARK_APP_NAME}_Visualize_OHLC") \
    .master(f"local[{settings_spark.THREAD_SOLD}]") \
    .config("spark.sql.streaming.schemaInference", "true") \
    .config("spark.sql.shuffle.partitions", "4")  \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
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

# ================= Parse JSON và timestamp =================
parsed_df = df.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), matched_schema).alias("data")) \
    .select("data.*") \
    .withColumn("event_time", to_timestamp(col("trade_timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))

# ================= Logic: Realtime OHLC =================
ohlc_df = parsed_df \
    .withWatermark("event_time", f"{settings_spark.WATERMARK_DELAY_SEC} seconds") \
    .groupBy(
        window(col("event_time"), f"{settings_spark.BATCH_DURATION_SEC} seconds"),
        col("stock_symbol")
    ) \
    .agg(
        min(struct(col("event_time"), col("matched_price"))).alias("open_struct"),
        max(struct(col("event_time"), col("matched_price"))).alias("close_struct"),
        max("matched_price").alias("high"),
        min("matched_price").alias("low"),
        sum("matched_quantity").alias("volume")
    )

final_output = ohlc_df.select(
    col("stock_symbol"),
    col("window.start").alias("start_time"),
    col("window.end").alias("end_time"),
    col("open_struct.matched_price").alias("open"),
    col("high"),
    col("low"),
    col("close_struct.matched_price").alias("close"),
    col("volume")
)

# ================= Output Sink =================
def send_to_kafka(batch_df, batch_id):
    """
    Gửi dữ liệu nến sang Kafka Topic Visualization.
    Dùng toLocalIterator() thay vì collect() để giảm tải driver.
    """
    if batch_df.isEmpty():
        return

    count = 0
    for row in batch_df.toLocalIterator():
        try:
            message = row.asDict()
            message['start_time'] = str(message['start_time'])
            message['end_time'] = str(message['end_time'])
            producer.send(settings_kafka.KAFKA_TOPIC_OHLC_VISUALIZATION, message)
            count += 1
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    producer.flush()
    logger.info(f"Batch {batch_id}: Sent {count} candles to topic '{settings_kafka.KAFKA_TOPIC_OHLC_VISUALIZATION}'")

# ================= Run Stream =================
query = final_output.writeStream \
    .outputMode("update") \
    .foreachBatch(send_to_kafka) \
    .trigger(processingTime=f"{settings_spark.BATCH_DURATION_SEC} seconds") \
    .option("checkpointLocation", "checkpoint_ohlc_viz") \
    .start()

logger.info("Streaming to topic 'ohlc_visualization' started...")
query.awaitTermination()
