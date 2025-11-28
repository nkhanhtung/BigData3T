import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append('/opt/airflow')
from airflow import DAG
from airflow.operators.python import PythonOperator


from crawlers.crawler import incremental_update_daily, incremental_update_intraday

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'daily_stock_crawl',
    default_args=default_args,
    description='Crawl dữ liệu cuối ngày',
    schedule_interval='0 16 * * 1-5',  # 16:00 Mon-Fri
    start_date=datetime(2025, 11, 28),
    catchup=False,
    tags=['crawler', 'daily'],
) as dag:

    run_daily = PythonOperator(
        task_id='incremental_update_daily',
        python_callable=incremental_update_daily,
    )
