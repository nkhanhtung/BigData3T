from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

# 1. Spark session
spark = SparkSession.builder \
    .appName("MatchedOrdersConsumer") \
    .getOrCreate()

# 2. Schema tương ứng với matched_type_info
matched_schema = StructType([
    StructField("trade_id", StringType()),
    StructField("stock_symbol", StringType()),
    StructField("buy_order_id", StringType()),
    StructField("sell_order_id", StringType()),
    StructField("buy_user_id", StringType()),
    StructField("sell_user_id", StringType()),
    StructField("matched_price", DoubleType()),
    StructField("matched_quantity", IntegerType()),
    StructField("trade_timestamp", TimestampType())
])
