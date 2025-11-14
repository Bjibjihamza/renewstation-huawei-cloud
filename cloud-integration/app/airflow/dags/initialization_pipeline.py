# dags/initialization_pipeline.py
from datetime import datetime
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# ✅ On réutilise le même get_db_connection que le reste du projet
from src.pipeline.load.weather_loader import get_db_connection


def initialize_battery_states(**context):
    conn = get_db_connection()
    cur = conn.cursor()

    start_ts = datetime(2024, 1, 1, 0, 0, 0)
    batteries = [
        ("main",   3000.0, f"{start_ts.strftime('%Y%m%d%H')}_main"),
        ("backup", 1000.0, f"{start_ts.strftime('%Y%m%d%H')}_backup")
    ]

    for typ, cap, uid in batteries:
        cur.execute("""
            INSERT INTO battery_state_real VALUES (%s, %s, %s, %s, 100.0, 100.0, %s, 0,0,0,0,0,0,0)
            ON CONFLICT (id) DO UPDATE SET 
                soc_start_pct = 100.0, 
                soc_end_pct = 100.0, 
                energy_stored_kwh = %s
        """, (uid, start_ts, typ, cap, cap, cap))

    conn.commit()
    cur.close()
    conn.close()
    print("BATTERIES INITIALISÉES À 100%")


def mark_initialization_complete(**context):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            key VARCHAR(100) PRIMARY KEY, 
            value TEXT, 
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        INSERT INTO pipeline_metadata (key, value) 
        VALUES ('initialization_complete', 'true')
        ON CONFLICT (key) DO UPDATE 
        SET value = 'true', updated_at = NOW()
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("INITIALISATION TERMINÉE → MARQUÉE")


with DAG(
    dag_id="initialization_pipeline",
    description="INIT COMPLETE → Météo + Énergie + Batteries 100%",
    start_date=datetime(2025, 11, 13),
    schedule_interval=None,
    catchup=False,
    tags=["init", "renewstation"],
    default_args={"retries": 1}
) as dag:

    start = EmptyOperator(task_id="start")

    weather = BashOperator(
        task_id="01_weather_historical",
        bash_command="python -m src.pipeline.generator.weather_forecasting --mode full",
        cwd="/opt/airflow"
    )

    energy = BashOperator(
        task_id="02_energy_historical",
        bash_command="python -m src.pipeline.generator.energy_cons_generator --mode full",
        cwd="/opt/airflow"
    )

    init_batteries = PythonOperator(
        task_id="03_init_batteries",
        python_callable=initialize_battery_states
    )

    mark_done = PythonOperator(
        task_id="04_mark_initialization_done",
        python_callable=mark_initialization_complete
    )

    end = EmptyOperator(task_id="end")

    start >> weather >> energy >> init_batteries >> mark_done >> end
