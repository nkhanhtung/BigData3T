#!/bin/bash

KAFKA_TOPICS_CMD="/usr/bin/kafka-topics"  # <-- sửa thành đường dẫn này
KAFKA_BROKER="kafka:29092"
PARTITIONS=3
REPLICATION_FACTOR=1

TOPICS=("orders_raw" "order_updates" "matched_orders" "market_data")

# Chờ Kafka sẵn sàng
MAX_RETRIES=30
RETRY_COUNT=0
until nc -z -w 5 ${KAFKA_BROKER%:*} ${KAFKA_BROKER#*:} || [ $RETRY_COUNT -ge $MAX_RETRIES ]; do
  echo "Kafka not yet available at $KAFKA_BROKER. Waiting 5 seconds..."
  sleep 5
  RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
  echo "Kafka did not become available after multiple retries. Exiting."
  exit 1
fi

echo "Kafka is up!"

# Tạo các topic
for topic in "${TOPICS[@]}"; do
  echo "Creating Kafka topic: $topic"
  $KAFKA_TOPICS_CMD --create --topic "$topic" \
                    --bootstrap-server "$KAFKA_BROKER" \
                    --partitions "$PARTITIONS" \
                    --replication-factor "$REPLICATION_FACTOR" \
                    --if-not-exists
done

echo "Kafka topic initialization complete."
