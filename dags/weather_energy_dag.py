from datetime import datetime, timedelta
import psycopg2
import os  # For bash args

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator

# ============================================================================
#   DAG AIRFLOW UNIFIÉ - MÉTÉO + ÉNERGIE (HISTORICAL ONLY, NO FUTURE ENERGY)
# ============================================================================
# 
# 🎯 CE DAG GÈRE:
# 
# 1️⃣ INITIAL/BACKFILL (Gaps detected):
#    - Full historical weather (2024-01-01 → NOW) + 1-week forecast
#    - Full historical energy gen (using historical weather)
# 
# 2️⃣ REGULAR (Recent only, every 6h):
#    - Backfill last 6h weather with archive (replace old forecasts)
#    - Gen energy ONLY for last 6h historical (no future)
# 
# ✅ Avantages:
#    - Gap-aware DB check (up to NOW - 6h)
#    - No future energy (historical only)
#    - Efficient regular runs
# ============================================================================

def get_db_connection():
    """Crée une connexion à la base de données PostgreSQL depuis les variables d'environnement"""
    import os
    
    return psycopg2.connect(
        host=os.getenv("GAUSSDB_HOST", "localhost"),
        port=os.getenv("GAUSSDB_PORT", "5432"),
        database=os.getenv("GAUSSDB_DB_SILVER", "silver"),
        user=os.getenv("GAUSSDB_USER", "postgres"),
        password=os.getenv("GAUSSDB_PASSWORD", "postgres"),
        sslmode=os.getenv("GAUSSDB_SSLMODE", "disable")
    )

def check_database_initialization(**context):
    """
    Vérifie la couverture des données de 2024-01-01 à NOW() - 6h.
    
    Returns:
        str: 'initial_backfill' si gaps/missing; 'regular_recent' si couvert.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        now_minus_6h = datetime.now() - timedelta(hours=6)
        start_date = datetime(2024, 1, 1)
        
        # Vérifier météo: count depuis start à now-6h
        cur.execute("""
            SELECT COUNT(*) 
            FROM weather_forecast_hourly 
            WHERE forecast_timestamp >= %s AND forecast_timestamp <= %s
        """, (start_date, now_minus_6h))
        weather_count = cur.fetchone()[0]
        
        # Expected hours: ~ (now_minus_6h - start_date).total_seconds() / 3600
        expected_hours = int((now_minus_6h - start_date).total_seconds() / 3600)
        
        # Vérifier énergie
        cur.execute("""
            SELECT COUNT(*) 
            FROM energy_consumption_hourly 
            WHERE time_ts >= %s AND time_ts <= %s
        """, (start_date, now_minus_6h))
        energy_count = cur.fetchone()[0]
        
        print("=" * 80)
        print("🔍 VÉRIFICATION COUVERTURE (2024-01-01 → NOW-6h)")
        print("=" * 80)
        print(f"📅 Période: {start_date} → {now_minus_6h} (~{expected_hours:,} heures attendues)")
        print(f"📊 Données météo: {weather_count:,} lignes")
        print(f"⚡ Données énergie: {energy_count:,} lignes")
        print("=" * 80)
        
        # Critère: >=95% coverage (tolérance pour petits gaps)
        coverage_pct = (min(weather_count, energy_count) / max(expected_hours, 1)) * 100
        if coverage_pct < 95:
            print("🚀 Gaps détectés → Mode INITIAL/BACKFILL (full)")
            print("=" * 80)
            return "initial_backfill"
        else:
            print("✅ Couverture OK → Mode REGULAR (last 6h only)")
            print("=" * 80)
            return "regular_recent"
            
    except Exception as e:
        print(f"⚠️ Erreur DB check: {e} → Default to full backfill")
        return "initial_backfill"
    finally:
        if conn:
            conn.close()

default_args = {
    "owner": "hamza",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="unified_weather_energy_historical_pipeline",
    description="🔄 Pipeline unifié: Historical only (backfill gaps + recent 6h, NO future energy)",
    default_args=default_args,
    start_date=datetime(2025, 11, 11),
    schedule_interval="0 */6 * * *",  # Every 6h
    catchup=False,
    max_active_runs=1,
    tags=["renewstation", "historical", "no_forecast_energy", "backfill"],
) as dag:

    # ========================================================================
    #   BRANCHEMENT: FULL BACKFILL vs RECENT 6H
    # ========================================================================
    
    check_mode = BranchPythonOperator(
        task_id="check_database_coverage",
        python_callable=check_database_initialization,
        provide_context=True,
    )

    # ========================================================================
    #   BRANCHE 1: INITIAL/BACKFILL (Gaps/First Run)
    # ========================================================================
    
    initial_backfill = EmptyOperator(task_id="initial_backfill")
    
    # Full historical weather (2024-01-01 → NOW) + 1-week forecast
    full_weather_backfill = BashOperator(
        task_id="full_weather_backfill",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode full"
        ),
        execution_timeout=timedelta(minutes=30),
    )
    
    # Full historical energy (using backfilled weather)
    full_energy_backfill = BashOperator(
        task_id="full_energy_backfill",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.energy_cons_generator --mode full"
        ),
        execution_timeout=timedelta(minutes=45),
    )

    # ========================================================================
    #   BRANCHE 2: REGULAR RECENT (Every 6h, Last 6h Only)
    # ========================================================================
    
    regular_recent = EmptyOperator(task_id="regular_recent")
    
    # Backfill last 6h weather with archive (no full fetch)
    recent_weather_backfill = BashOperator(
        task_id="recent_weather_backfill_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode recent"
        ),
        execution_timeout=timedelta(minutes=5),
    )
    
    # Gen energy ONLY for last 6h historical (repurposed script)
    recent_energy_backfill = BashOperator(
        task_id="recent_energy_backfill_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.backfill_energy_last_6h"  # Repurposed from generate_energy_6h.py
        ),
        execution_timeout=timedelta(minutes=10),
    )

    # ========================================================================
    #   CONVERGENCE
    # ========================================================================
    
    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        trigger_rule="none_failed_min_one_success",
    )

    # ========================================================================
    #   DÉPENDANCES
    # ========================================================================
    
    check_mode >> [initial_backfill, regular_recent]
    
    # Initial/Backfill
    initial_backfill >> full_weather_backfill >> full_energy_backfill >> pipeline_complete
    
    # Regular Recent
    regular_recent >> recent_weather_backfill >> recent_energy_backfill >> pipeline_complete