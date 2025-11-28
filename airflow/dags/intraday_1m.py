import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append('/opt/airflow')
from airflow import DAG
from airflow.operators.python import PythonOperator

from crawlers.crawler import incremental_update_intraday

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'intraday_1m',
    default_args=default_args,
    description='Crawl intraday mỗi 1 phút',
    schedule_interval='* * * * 1-5',  # mỗi phút, Mon-Fri
    start_date=datetime(2025, 11, 28),
    catchup=False,
    tags=['crawler', 'intraday'],
) as dag:

    run_intraday = PythonOperator(
        task_id='incremental_update_intraday_1m',
        python_callable=incremental_update_intraday,
    )
