from datetime import datetime, timedelta
import psycopg2
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.operators.empty import EmptyOperator

# ============================================================================
#   DAG DE MISE À JOUR ET PRÉDICTION - EXÉCUTION RÉGULIÈRE
# ============================================================================
# 
# 🎯 CE DAG S'EXÉCUTE TOUTES LES 6 HEURES ET GÈRE:
# 
# 1️⃣ Backfill météo des 6 dernières heures (données réelles)
# 2️⃣ Génération énergie des 6 dernières heures (données historiques)
# 3️⃣ Calcul état RÉEL batteries (6h passées, is_predicted=FALSE)
# 4️⃣ Mise à jour prévisions météo (7 jours futurs)
# 5️⃣ Prédiction consommation énergie (7 jours futurs)
# 6️⃣ Prédiction production solaire + batteries (7 jours futurs, is_predicted=TRUE)
# 
# ⚠️  Ce DAG nécessite que le DAG d'initialisation ait été exécuté
# ============================================================================

def get_db_connection():
    """Crée une connexion à la base de données PostgreSQL"""
    # En environnement Docker, utiliser le nom du service, pas localhost
    host = os.getenv("GAUSSDB_HOST")
    if not host or host == "localhost":
        # Essayer le nom du service PostgreSQL dans docker-compose
        # Adapter selon votre configuration
        host = os.getenv("POSTGRES_HOST", "postgres")
    
    print(f"🔗 Tentative de connexion à: {host}:{os.getenv('GAUSSDB_PORT', '5432')}")
    
    return psycopg2.connect(
        host=host,
        port=os.getenv("GAUSSDB_PORT", "5432"),
        database=os.getenv("GAUSSDB_DB_SILVER", "silver"),
        user=os.getenv("GAUSSDB_USER", "postgres"),
        password=os.getenv("GAUSSDB_PASSWORD", "postgres"),
        sslmode=os.getenv("GAUSSDB_SSLMODE", "disable")
    )

def check_initialization(**context):
    """
    Vérifie que l'initialisation a été complétée.
    Retourne True si initialisé, False sinon (ce qui arrête le DAG).
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("=" * 80)
        print("✅ Connexion à la base de données établie")
        print("=" * 80)
        
        # Vérifier si la table de métadonnées existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'pipeline_metadata'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("=" * 80)
            print("❌ Table pipeline_metadata n'existe pas")
            print("⚠️  Veuillez exécuter le DAG 'initialization_pipeline' d'abord")
            print("=" * 80)
            return False
        
        # Vérifier le flag d'initialisation
        cur.execute("""
            SELECT value FROM pipeline_metadata 
            WHERE key = 'initialization_complete'
        """)
        row = cur.fetchone()
        
        if row and row[0] == 'true':
            print("=" * 80)
            print("✅ BASE DE DONNÉES INITIALISÉE - Exécution du pipeline de mise à jour")
            print("=" * 80)
            return True
        else:
            print("=" * 80)
            print("❌ BASE DE DONNÉES NON INITIALISÉE")
            print("⚠️  Veuillez exécuter le DAG 'initialization_pipeline' d'abord")
            print("=" * 80)
            return False
            
    except Exception as e:
        print("=" * 80)
        print(f"❌ Erreur lors de la vérification: {e}")
        print("⚠️  Veuillez exécuter le DAG 'initialization_pipeline' d'abord")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False
    finally:
        if cur:
            cur.close()
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
    dag_id="update_and_prediction_pipeline",
    description="Mise à jour 6h + Prédictions 7 jours (nécessite initialisation)",
    default_args=default_args,
    start_date=datetime(2025, 11, 11),
    schedule_interval="0 */6 * * *",  # Toutes les 6 heures
    catchup=False,
    max_active_runs=1,
    tags=["renewstation", "update", "prediction", "regular"],
) as dag:

    # ========================================================================
    #   VÉRIFICATION PRÉALABLE
    # ========================================================================
    
    check_init = ShortCircuitOperator(
        task_id="check_initialization",
        python_callable=check_initialization,
        provide_context=True,
    )
    
    start_update = EmptyOperator(task_id="start_update")
    
    # ========================================================================
    #   PARTIE 1: MISE À JOUR DONNÉES HISTORIQUES (6H)
    # ========================================================================
    
    # 1. Backfill météo des 6 dernières heures avec archive
    recent_weather_backfill = BashOperator(
        task_id="weather_backfill_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode recent"
        ),
        execution_timeout=timedelta(minutes=5),
    )
    
    # 2. Génération énergie pour les 6 dernières heures
    recent_energy_backfill = BashOperator(
        task_id="energy_backfill_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.backfill_energy_last_6h"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    # 3. Calcul état RÉEL batteries (6h passées, is_predicted=FALSE)
    recent_solar_battery_real = BashOperator(
        task_id="solar_battery_real_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.solar_battery --mode recent"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    historical_complete = EmptyOperator(
        task_id="historical_update_complete",
        trigger_rule="none_failed",
    )
    
    # ========================================================================
    #   PARTIE 2: PRÉDICTIONS (7 JOURS FUTURS)
    # ========================================================================
    
    # 4. Mise à jour prévisions météo (7 jours futurs)
    update_weather_forecast = BashOperator(
        task_id="weather_forecast_7d",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode full"
        ),
        execution_timeout=timedelta(minutes=5),
    )
    
    # 5. Prédiction consommation énergie (7 jours futurs)
    predict_energy_consumption = BashOperator(
        task_id="predict_energy_7d",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.prediction"
        ),
        execution_timeout=timedelta(minutes=10),
    )
    
    # 6. Prédiction production solaire + batteries (7 jours futurs, is_predicted=TRUE)
    predict_solar_battery = BashOperator(
        task_id="predict_solar_battery_7d",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.solar_battery --mode predicted"
        ),
        execution_timeout=timedelta(minutes=15),
    )
    
    predictions_complete = EmptyOperator(
        task_id="predictions_complete",
        trigger_rule="none_failed",
    )
    
    # ========================================================================
    #   FINALISATION
    # ========================================================================
    
    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        trigger_rule="none_failed_min_one_success",
    )
    
    # ========================================================================
    #   DÉPENDANCES
    # ========================================================================
    
    # Vérification puis démarrage
    check_init >> start_update
    
    # PARTIE 1: Mise à jour historique (parallèle après météo)
    start_update >> recent_weather_backfill
    recent_weather_backfill >> [recent_energy_backfill, recent_solar_battery_real]
    [recent_energy_backfill, recent_solar_battery_real] >> historical_complete
    
    # PARTIE 2: Prédictions (séquentiel)
    historical_complete >> update_weather_forecast
    update_weather_forecast >> predict_energy_consumption
    predict_energy_consumption >> predict_solar_battery
    predict_solar_battery >> predictions_complete
    
    # Finalisation
    predictions_complete >> pipeline_complete


# ============================================================================
#   NOTES D'UTILISATION
# ============================================================================
# 
# 📋 Ce DAG s'exécute automatiquement toutes les 6 heures
# 
# ⚠️  PRÉREQUIS: Le DAG 'initialization_pipeline' doit avoir été exécuté
# 
# 🔄 Flux d'exécution:
#    1. Vérification de l'initialisation
#    2. Si OK: Mise à jour des 6h passées (météo + énergie + batteries réelles)
#    3. Puis: Prédictions pour les 7 jours futurs (météo + énergie + batteries)
#    4. Si KO: Le DAG s'arrête immédiatement
# 
# 📊 Tables mises à jour:
#    - weather_forecast_hourly (backfill 6h + forecast 7j)
#    - energy_consumption_hourly (backfill 6h)
#    - predicted_energy_consumption (forecast 7j)
#    - predicted_solar_production (forecast 7j)
#    - battery_state (backfill 6h avec is_predicted=FALSE + forecast 7j avec is_predicted=TRUE)
#
# 🔧 Configuration requise:
#    Variables d'environnement à définir:
#    - GAUSSDB_HOST ou POSTGRES_HOST (nom du service PostgreSQL)
#    - GAUSSDB_PORT (par défaut: 5432)
#    - GAUSSDB_DB_SILVER (par défaut: silver)
#    - GAUSSDB_USER (par défaut: postgres)
#    - GAUSSDB_PASSWORD (par défaut: postgres)
# 
# ============================================================================