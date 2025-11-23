# ============================================
# Base Python + Java
# ============================================
FROM python:3.10-slim-bullseye

# Install Java (required for Spark) + wget
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk-headless wget curl procps && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# ============================================
# Install Python packages
# ============================================
COPY spark/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ============================================
# Add Spark Kafka connectors
# ============================================
ENV SPARK_VERSION=3.5.1
ENV SCALA_VERSION=2.12

RUN mkdir -p /opt/spark/jars

# Spark SQL Kafka connector
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_${SCALA_VERSION}/${SPARK_VERSION}/spark-sql-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar

# Kafka clients
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.6.1/kafka-clients-3.6.1.jar

# Spark token provider (bắt buộc cho Spark 3.5+ Kafka streaming)
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_${SCALA_VERSION}/${SPARK_VERSION}/spark-token-provider-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar

RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar
# ============================================
# Copy project code
# ============================================
WORKDIR /app
COPY spark/services /app/spark/
COPY backend/ /app/backend/
ENV PYTHONPATH=/app

# ============================================
# Set Spark submit args để load tất cả JAR
# ============================================
ENV PYSPARK_SUBMIT_ARGS="--jars \
/opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,\
/opt/spark/jars/kafka-clients-3.6.1.jar,\
/opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.1.jar,\
/opt/spark/jars/commons-pool2-2.11.1.jar \
pyspark-shell"


# ============================================
# Command default khi container chạy
# ============================================