from datetime import datetime, timedelta
import psycopg2
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator

# ============================================================================
#   DAG AIRFLOW COMPLET - MÉTÉO + ÉNERGIE + SOLAIRE + BATTERIES
# ============================================================================
# 
# 🎯 CE DAG GÈRE:
# 
# 1️⃣ INITIAL/BACKFILL (Gaps detected):
#    - Full historical weather (2024-01-01 → NOW) + 7-day forecast
#    - Full historical energy consumption
#    - Full historical solar production
#    - Prepare prediction data (energy + solar + batteries) for next 7 days
# 
# 2️⃣ REGULAR (Recent only, every 6h):
#    - Backfill last 6h weather with archive
#    - Gen energy ONLY for last 6h historical
#    - Update historical solar production (last 6h)
#    - Update prediction data for next 7 days (weather + solar + batteries)
# 
# ✅ Nouveautés:
#    - Production solaire (pvlib) intégrée
#    - État batteries (Main 2500 kWh + Backup 700 kWh)
#    - Historical vs Predicted modes
# ============================================================================

def get_db_connection():
    """Crée une connexion à la base de données PostgreSQL depuis les variables d'environnement"""
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
        
        # Vérifier météo
        cur.execute("""
            SELECT COUNT(*) 
            FROM weather_forecast_hourly 
            WHERE forecast_timestamp >= %s AND forecast_timestamp <= %s
        """, (start_date, now_minus_6h))
        weather_count = cur.fetchone()[0]
        
        expected_hours = int((now_minus_6h - start_date).total_seconds() / 3600)
        
        # Vérifier énergie
        cur.execute("""
            SELECT COUNT(*) 
            FROM energy_consumption_hourly 
            WHERE time_ts >= %s AND time_ts <= %s
        """, (start_date, now_minus_6h))
        energy_count = cur.fetchone()[0]
        
        # Vérifier production solaire historique
        cur.execute("""
            SELECT COUNT(*) 
            FROM historical_solar_production 
            WHERE production_timestamp >= %s AND production_timestamp <= %s
        """, (start_date, now_minus_6h))
        solar_count = cur.fetchone()[0]
        
        print("=" * 80)
        print("🔍 VÉRIFICATION COUVERTURE (2024-01-01 → NOW-6h)")
        print("=" * 80)
        print(f"📅 Période: {start_date} → {now_minus_6h} (~{expected_hours:,} heures attendues)")
        print(f"📊 Données météo: {weather_count:,} lignes")
        print(f"⚡ Données énergie: {energy_count:,} lignes")
        print(f"☀️ Production solaire: {solar_count:,} lignes")
        print("=" * 80)
        
        # Critère: >=95% coverage pour météo ET énergie
        min_coverage = min(weather_count, energy_count)
        coverage_pct = (min_coverage / max(expected_hours, 1)) * 100
        
        if coverage_pct < 95 or solar_count < (expected_hours * 0.9):
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
    dag_id="weather_energy_solar_battery_pipeline",
    description="Pipeline complet: Weather + Energy + Solar Production + Battery State",
    default_args=default_args,
    start_date=datetime(2025, 11, 11),
    schedule_interval="0 */6 * * *",  # Every 6h
    catchup=False,
    max_active_runs=1,
    tags=["renewstation", "complete_pipeline", "solar", "batteries"],
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
    #   BRANCHE 1: INITIAL/BACKFILL (Gaps detected)
    # ========================================================================
    
    initial_backfill = EmptyOperator(task_id="initial_backfill")
    
    # 1. Full historical weather (2024-01-01 → NOW) + 7-day forecast
    full_weather_backfill = BashOperator(
        task_id="full_weather_backfill",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode full"
        ),
        execution_timeout=timedelta(minutes=30),
    )
    
    # 2. Full historical energy consumption
    full_energy_backfill = BashOperator(
        task_id="full_energy_backfill",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.energy_cons_generator --mode full"
        ),
        execution_timeout=timedelta(minutes=45),
    )
    
    # 3. Full historical solar production
    full_solar_historical = BashOperator(
        task_id="full_solar_production_historical",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.solar_battery --mode historical"
        ),
        execution_timeout=timedelta(minutes=30),
    )
    
    # 4. Prepare prediction data (energy consumption for next 7 days)
    full_prepare_energy_predictions = BashOperator(
        task_id="full_prepare_energy_predictions",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.prediction"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    # 5. Calculate predicted solar production & battery state (next 7 days)
    full_solar_battery_predicted = BashOperator(
        task_id="full_solar_battery_predicted",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.solar_battery --mode predicted"
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ========================================================================
    #   BRANCHE 2: REGULAR RECENT (Every 6h, Last 6h Only)
    # ========================================================================
    
    regular_recent = EmptyOperator(task_id="regular_recent")
    
    # 1. Backfill last 6h weather with archive
    recent_weather_backfill = BashOperator(
        task_id="recent_weather_backfill_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode recent"
        ),
        execution_timeout=timedelta(minutes=5),
    )
    
    # 2. Gen energy ONLY for last 6h historical
    recent_energy_backfill = BashOperator(
        task_id="recent_energy_backfill_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.backfill_energy_last_6h"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    # 3. Update historical solar production (last 6h)
    recent_solar_historical = BashOperator(
        task_id="recent_solar_production_historical_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.solar_battery --mode historical"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    # 4. Update prediction data (energy consumption for next 7 days)
    recent_prepare_energy_predictions = BashOperator(
        task_id="recent_prepare_energy_predictions",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.prediction"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    # 5. Update predicted solar production & battery state (next 7 days)
    recent_solar_battery_predicted = BashOperator(
        task_id="recent_solar_battery_predicted",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.solar_battery --mode predicted"
        ),
        execution_timeout=timedelta(minutes=15),
    )

    # ========================================================================
    #   CONVERGENCE
    # ========================================================================
    
    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        trigger_rule="none_failed_min_one_success",
    )

    # ========================================================================
    #   DÉPENDANCES - BRANCHE 1: INITIAL/BACKFILL
    # ========================================================================
    
    # Weather doit être fait en premier (tout dépend de lui)
    initial_backfill >> full_weather_backfill
    
    # Une fois weather OK, on peut faire en parallèle:
    # - Energy historical (dépend de weather)
    # - Solar historical (dépend de weather)
    # - Energy predictions (dépend de weather forecast)
    full_weather_backfill >> [
        full_energy_backfill,
        full_solar_historical,
        full_prepare_energy_predictions
    ]
    
    # Une fois energy predictions prêtes, on peut faire solar+battery predictions
    full_prepare_energy_predictions >> full_solar_battery_predicted
    
    # Tous convergent vers completion
    [
        full_energy_backfill,
        full_solar_historical,
        full_solar_battery_predicted
    ] >> pipeline_complete

    # ========================================================================
    #   DÉPENDANCES - BRANCHE 2: REGULAR RECENT
    # ========================================================================
    
    # Weather en premier
    regular_recent >> recent_weather_backfill
    
    # Parallèle après weather:
    # - Energy historical 6h
    # - Solar historical 6h
    # - Energy predictions update
    recent_weather_backfill >> [
        recent_energy_backfill,
        recent_solar_historical,
        recent_prepare_energy_predictions
    ]
    
    # Une fois energy predictions updated, faire solar+battery predictions
    recent_prepare_energy_predictions >> recent_solar_battery_predicted
    
    # Convergence
    [
        recent_energy_backfill,
        recent_solar_historical,
        recent_solar_battery_predicted
    ] >> pipeline_complete

    # ========================================================================
    #   BRANCHEMENT INITIAL
    # ========================================================================
    
    check_mode >> [initial_backfill, regular_recent]


# ============================================================================
#   NOTES D'IMPLÉMENTATION
# ============================================================================
# 
# 📁 Structure fichiers attendue:
#    src/pipeline/generator/
#    ├── weather_forecasting.py          (existe)
#    ├── energy_cons_generator.py        (existe)
#    ├── backfill_energy_last_6h.py      (existe)
#    ├── prediction.py                   (existe)
#    └── solar_battery.py     (NOUVEAU - à créer)
# 
# 🔋 Tables créées:
#    - predicted_solar_production         (7 jours futurs)
#    - historical_solar_production        (passé réel)
#    - predicted_battery_state            (7 jours futurs - main + backup)
#    - historical_battery_state           (passé réel - main + backup)
# 
# ⚡ Flux de données:
#    weather_forecast_hourly
#         ↓
#    [pvlib calculation]
#         ↓
#    predicted_solar_production → predicted_battery_state
#    historical_solar_production → historical_battery_state
#         ↑
#    predicted_energy_consumption (sum all buildings)
#    energy_consumption_hourly (sum all buildings)
# 
# ============================================================================