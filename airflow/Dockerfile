# Base image Airflow
FROM apache/airflow:2.7.2-python3.10

# Copy requirements
COPY requirements.txt .

# Cài các package Python cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Tùy chọn: set working directory
WORKDIR /opt/airflow

COPY dags/ /opt/airflow/dags/
COPY plugins/ /opt/airflow/plugins/
COPY crawlers/ /opt/airflow/crawlers/
COPY logs/ /opt/airflow/logs/
COPY datasets/ /opt/airflow/datasets/
# Export PYTHONPATH để chắc chắn Airflow tìm được module crawlers
