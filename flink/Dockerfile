
FROM flink:1.20.2-scala_2.12

USER root

RUN apt-get update --fix-missing && \
    apt-get install -y python3 python3-pip wget curl cmake && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*


RUN pip3 install --no-cache-dir --upgrade apache-flink==1.20.2

RUN mkdir -p /opt/flink-job
COPY . /opt/flink-job

RUN mkdir -p /opt/flink/lib && \
    chown -R root:root /opt/flink/lib && \
    chmod -R 777 /opt/flink/lib


RUN wget -q -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar
RUN wget -q -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.3.0-1.20/flink-connector-jdbc-3.3.0-1.20.jar 
RUN wget -q -P /opt/flink/lib https://repo1.maven.org/maven2/org/postgresql/postgresql/42.6.0/postgresql-42.6.0.jar
RUN wget -q -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar 

RUN wget -q -P /opt/flink/lib https://repo1.maven.org/maven2/org/apache/flink/flink-json/1.20.2/flink-json-1.20.2.jar



RUN chown -R flink:flink /opt/flink/lib /opt/flink-job
USER flink


ENV PYTHONUNBUFFERED=1
ENV FLINK_HOME=/opt/flink
ENV PATH=$FLINK_HOME/bin:$PATH

WORKDIR /opt/flink-job
