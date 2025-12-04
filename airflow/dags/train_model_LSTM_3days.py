import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append('/opt/airflow')
from airflow import DAG
from airflow.operators.python import PythonOperator
from trains.train_LSTM import train_model


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}
with DAG(
    'train_model_every_3_days',
    default_args=default_args,
    description='Train lại mô hình mỗi 3 ngày',
    schedule_interval='0 2 */3 * *',   # 02:00 sáng mỗi 3 ngày
    start_date=datetime(2025, 11, 28),
    catchup=False,
    tags=['training', 'model'],
) as dag:

    train_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
    )


