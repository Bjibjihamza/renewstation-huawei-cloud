from datetime import datetime, timedelta
import psycopg2
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# ============================================================================
#   CONNEXION DB
# ============================================================================

def get_db_connection():
    host = os.getenv("GAUSSDB_HOST")
    if not host or host == "localhost":
        host = os.getenv("POSTGRES_HOST", "postgres")
    
    return psycopg2.connect(
        host=host,
        port=os.getenv("GAUSSDB_PORT", "5432"),
        database=os.getenv("GAUSSDB_DB_SILVER", "silver"),
        user=os.getenv("GAUSSDB_USER", "postgres"),
        password=os.getenv("GAUSSDB_PASSWORD", "postgres"),
        sslmode=os.getenv("GAUSSDB_SSLMODE", "disable")
    )

# ============================================================================
#   1. INITIALISATION BATTERIES À 100%
# ============================================================================

def initialize_battery_states(**context):
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("INITIALISATION BATTERIES → 100% SOC (2024-01-01 00:00)")
    print("=" * 80)
    
    start_ts = datetime(2024, 1, 1, 0, 0, 0)
    
    batteries = [
        ("main",   3000.0, f"{start_ts.strftime('%Y%m%d%H')}_main"),
        ("backup", 1000.0, f"{start_ts.strftime('%Y%m%d%H')}_backup")
    ]
    
    for typ, cap, uid in batteries:
        cur.execute("""
            INSERT INTO battery_state_real (
                id, timestamp, battery_type, battery_capacity_kwh,
                soc_start_pct, soc_end_pct, energy_stored_kwh,
                solar_production_kwh, consumption_kwh, net_energy_kwh,
                battery_charge_kwh, battery_discharge_kwh,
                grid_import_kwh, grid_export_kwh
            ) VALUES (%s, %s, %s, %s, 100.0, 100.0, %s, 0,0,0,0,0,0,0)
            ON CONFLICT (id) DO UPDATE SET
                soc_start_pct = 100.0,
                soc_end_pct = 100.0,
                energy_stored_kwh = %s,
                battery_capacity_kwh = %s
        """, (uid, start_ts, typ, cap, cap, cap, cap))
    
    conn.commit()
    cur.close()
    conn.close()
    print("BATTERIES INITIALISÉES (Main: 3000 kWh | Backup: 1000 kWh)")

# ============================================================================
#   2. MARQUER INITIALISATION TERMINÉE
# ============================================================================

def mark_initialization_complete(**context):
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("MARQUAGE INITIALISATION TERMINÉE")
    print("=" * 80)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_metadata (
            key VARCHAR(100) PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        INSERT INTO pipeline_metadata (key, value) 
        VALUES ('initialization_complete', 'true')
        ON CONFLICT (key) DO UPDATE SET value = 'true', updated_at = NOW()
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("INITIALISATION MARQUÉE COMME TERMINÉE DANS pipeline_metadata")

# ============================================================================
#   DAG MINIMAL
# ============================================================================

with DAG(
    dag_id="initialization_pipeline",
    description="INITIALISATION MINIMALE → Météo + Énergie + Batteries 100%",
    start_date=datetime(2025, 11, 11),
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["init", "minimal"],
    default_args={"owner": "hamza", "retries": 1, "retry_delay": timedelta(minutes=3)}
) as dag:

    start = EmptyOperator(task_id="start")

    # 1. Météo historique (archive only)
    weather = BashOperator(
        task_id="weather_historical",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.weather_forecasting --mode full",
        execution_timeout=timedelta(minutes=30)
    )

    # 2. Énergie historique
    energy = BashOperator(
        task_id="energy_historical",
        bash_command="cd /opt/airflow && PYTHONPATH=/opt/airflow python -m src.pipeline.generator.energy_cons_generator --mode full",
        execution_timeout=timedelta(minutes=40)
    )

    # 3. Batteries à 100%
    init_batteries = PythonOperator(
        task_id="init_batteries",
        python_callable=initialize_battery_states
    )

    # 4. Marquer terminé
    mark_done = PythonOperator(
        task_id="mark_done",
        python_callable=mark_initialization_complete
    )

    end = EmptyOperator(task_id="end")

    # FLUX
    start >> [weather, energy] >> init_batteries >> mark_done >> end