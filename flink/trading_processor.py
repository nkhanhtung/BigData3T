import os
import logging
from datetime import datetime

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common import Types, Row
from pyflink.common.watermark_strategy import WatermarkStrategy


from common.schemas import order_raw_type_info, pending_order_type_info, matched_type_info, order_history_type_info
from processors.pending_order_process import PendingOrderProcessFunction, order_update_tag


from pyflink.datastream.connectors.kafka import (
    KafkaSource, KafkaSink, KafkaOffsetsInitializer,
    KafkaRecordSerializationSchema, DeliveryGuarantee
)
from pyflink.datastream.formats.json import (
    JsonRowDeserializationSchema, JsonRowSerializationSchema
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_ORDERS_RAW = os.getenv("KAFKA_TOPIC_ORDERS_RAW", "orders_raw")
KAFKA_TOPIC_MATCHED_ORDERS = os.getenv("KAFKA_TOPIC_MATCHED_ORDERS", "matched_orders")
KAFKA_TOPIC_ORDER_UPDATES = os.getenv("KAFKA_TOPIC_ORDER_UPDATES", "order_updates") # Topic mới cho lịch sử trạng thái


def main():
    logger.info("Starting Flink Trading Processor...")

    env = StreamExecutionEnvironment.get_execution_environment()


    deserialization_schema = (
        JsonRowDeserializationSchema.builder()
        .type_info(order_raw_type_info)
        .ignore_parse_errors() 
        .build()
    )   
    orders_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP_SERVERS)
        .set_topics(KAFKA_TOPIC_ORDERS_RAW)
        .set_group_id("flink_trading_processor_group")
        .set_starting_offsets(KafkaOffsetsInitializer.earliest())
        .set_value_only_deserializer(deserialization_schema)
        .build()
    )
    raw_orders_stream = env.from_source(
        source=orders_source,
        watermark_strategy=WatermarkStrategy.no_watermarks(),
        source_name="OrdersRawKafkaSource",
    )


    def prepare_order(r):
        """Hàm này chuẩn hóa dữ liệu đầu vào để sẵn sàng cho việc xử lý."""
        action_type = r.action_type if hasattr(r, 'action_type') and r.action_type else "NEW"
        

        try:
            timestamp = datetime.strptime(r.created_timestamp, '%Y-%m-%dT%H:%M:%S')
        except (ValueError, TypeError):
            timestamp = datetime.now()

       
        return Row(
            order_id=r.order_id,
            user_id=r.user_id,
            stock_symbol=r.stock_symbol.upper().strip() if r.stock_symbol else None,
            order_type=r.order_type,
            price=r.price,
            quantity=r.quantity,
            created_timestamp=timestamp,
            action_type=action_type,
            status=None, 
            total_filled_quantity=0,
            total_filled_value=0.0
        )

    prepared_stream = raw_orders_stream.map(prepare_order, output_type=pending_order_type_info)

   
    keyed_stream = prepared_stream.key_by(lambda order: order.stock_symbol)

  
    main_stream_matched_orders = keyed_stream.process(
        PendingOrderProcessFunction(),
        output_type=matched_type_info
    )

   
    side_stream_order_updates = main_stream_matched_orders.get_side_output(order_update_tag)

   
    matched_serializer = JsonRowSerializationSchema.builder().with_type_info(matched_type_info).build()
    matched_sink = (
        KafkaSink.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP_SERVERS)
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(KAFKA_TOPIC_MATCHED_ORDERS)
            .set_value_serialization_schema(matched_serializer)
            .build()
        )
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
        .build()
    )
    main_stream_matched_orders.sink_to(matched_sink).name("Matched Orders Sink")
    logger.info(f"✅ Matched orders will be written to Kafka topic '{KAFKA_TOPIC_MATCHED_ORDERS}'")

   
    history_serializer = JsonRowSerializationSchema.builder().with_type_info(order_history_type_info).build()
    updates_sink = (
        KafkaSink.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP_SERVERS)
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(KAFKA_TOPIC_ORDER_UPDATES)
            .set_value_serialization_schema(history_serializer)
            .build()
        )
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
        .build()
    )
    side_stream_order_updates.sink_to(updates_sink).name("Order History Sink")
    logger.info(f"✅ Order history updates will be written to Kafka topic '{KAFKA_TOPIC_ORDER_UPDATES}'")

    env.execute("Trading Processor Job")
    logger.info("Flink Trading Processor Job submitted.")


if __name__ == "__main__":
    main()