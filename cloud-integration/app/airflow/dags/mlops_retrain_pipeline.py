# dags/mlops_retrain_pipeline.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "hamza",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="mlops_retrain_pipeline",
    description="Daily @ 00:00 → Cleanup old models + Retrain energy predictor model",
    schedule_interval=None,
    start_date=datetime(2025, 11, 13),
    catchup=False,
    max_active_runs=1,
    tags=["mlops", "retrain", "daily"],
    default_args=default_args,
) as dag:

    start = EmptyOperator(task_id="start")

    # Cleanup: Delete all existing .pkl files to free storage
    cleanup_old_models = BashOperator(
        task_id="cleanup_old_models",
        bash_command="rm -f /opt/airflow/models/*.pkl",
        execution_timeout=timedelta(minutes=1),
    )

    # Retrain: Run the training script (will save new .pkl)
    retrain_model = BashOperator(
        task_id="retrain_energy_model",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.ml.train_energy_model",
        execution_timeout=timedelta(minutes=15),
    )

    end = EmptyOperator(task_id="end")

    start >> cleanup_old_models >> retrain_model >> end