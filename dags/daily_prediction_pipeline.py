from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "hamza",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="daily_prediction_pipeline",
    description="Daily @ 00:00 → Archive J-1 + Weather + Energy + Solar + Battery 7d",
    schedule_interval="0 0 * * *",
    start_date=datetime(2025, 11, 13),
    catchup=False,
    max_active_runs=1,
    tags=["daily", "prediction", "live"],
    default_args=default_args,
) as dag:

    start = EmptyOperator(task_id="start")

    archive_yesterday = BashOperator(
        task_id="archive_yesterday_data",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.archive_yesterday_sync",
        execution_timeout=timedelta(minutes=5),
    )

    battery_real_daily = BashOperator(
        task_id="battery_real_daily",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.battery_real_daily",
        execution_timeout=timedelta(minutes=10),
    )

    fetch_weather_forecast = BashOperator(
        task_id="fetch_weather_forecast_7d",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.weather_forecast_7d",
        execution_timeout=timedelta(minutes=8),
    )

    predict_energy = BashOperator(
        task_id="predict_energy_consumption_7d",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.energy_prediction_7d",
        execution_timeout=timedelta(minutes=15),
    )

    predict_solar = BashOperator(
        task_id="predict_solar_production_7d",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.solar_prediction_7d",
        execution_timeout=timedelta(minutes=10),
    )

    predict_battery = BashOperator(
        task_id="predict_battery_state_7d",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.battery_prediction_7d",
        execution_timeout=timedelta(minutes=10),
    )

    end = EmptyOperator(task_id="end")

    start >> archive_yesterday >> battery_real_daily >> fetch_weather_forecast \
          >> predict_energy >> predict_solar >> predict_battery >> end
