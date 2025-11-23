# ============================================
# Stage 1: Build Python deps
# ============================================
FROM python:3.10-slim-bullseye AS builder
WORKDIR /app

RUN pip install --upgrade pip

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ============================================
# Stage 2: Runtime + Spark Kafka Connectors
# ============================================
FROM python:3.10-slim-bullseye
WORKDIR /app

# ===== Install Java (for Spark) + tools =====
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    wget \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# ===== Copy Python dependencies from builder =====
COPY --from=builder /install /usr/local

# ============================================
# Install Spark Kafka connectors (giống file mẫu)
# ============================================
ENV SPARK_VERSION=3.5.1
ENV SCALA_VERSION=2.12

RUN mkdir -p /opt/spark/jars

# Spark SQL Kafka connector
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_${SCALA_VERSION}/${SPARK_VERSION}/spark-sql-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar

# Kafka clients (bắt buộc)
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.6.1/kafka-clients-3.6.1.jar

# Spark token provider (Spark 3.5+ yêu cầu)
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_${SCALA_VERSION}/${SPARK_VERSION}/spark-token-provider-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar

# Commons-pool2 (được Spark Kafka dùng)
RUN wget -q -P /opt/spark/jars \
    https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar


# ============================================
# Set Spark submit args để load Kafka JARs
# ============================================
ENV PYSPARK_SUBMIT_ARGS="--jars \
/opt/spark/jars/spark-sql-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar,\
/opt/spark/jars/kafka-clients-3.6.1.jar,\
/opt/spark/jars/spark-token-provider-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar,\
/opt/spark/jars/commons-pool2-2.11.1.jar \
pyspark-shell"


# ============================================
# Copy project code
# ============================================
COPY backend /app/backend
COPY spark /app/spark

ENV CUDA_VISIBLE_DEVICES=-1
ENV PYTHONPATH=/app

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 
