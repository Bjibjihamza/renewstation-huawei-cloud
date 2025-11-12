from datetime import datetime, timedelta
import psycopg2
import os

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

# ============================================================================
#   DAG D'INITIALISATION - EXÉCUTION UNIQUE
# ============================================================================
# 
# 🎯 CE DAG GÈRE L'INITIALISATION COMPLÈTE:
# 
# 1️⃣ Full historical weather (2024-01-01 → NOW)
# 2️⃣ Full historical energy consumption (2024-01-01 → NOW)
# 3️⃣ Marquer la DB comme initialisée
# 
# ⚠️  Ce DAG ne doit s'exécuter qu'UNE SEULE FOIS
# ============================================================================

def get_db_connection():
    """Crée une connexion à la base de données PostgreSQL"""
    # En environnement Docker, utiliser le nom du service, pas localhost
    host = os.getenv("GAUSSDB_HOST")
    if not host or host == "localhost":
        # Essayer le nom du service PostgreSQL dans docker-compose
        # Adapter selon votre configuration
        host = os.getenv("POSTGRES_HOST", "postgres")
    
    return psycopg2.connect(
        host=host,
        port=os.getenv("GAUSSDB_PORT", "5432"),
        database=os.getenv("GAUSSDB_DB_SILVER", "silver"),
        user=os.getenv("GAUSSDB_USER", "postgres"),
        password=os.getenv("GAUSSDB_PASSWORD", "postgres"),
        sslmode=os.getenv("GAUSSDB_SSLMODE", "disable")
    )

def mark_initialization_complete(**context):
    """
    Marque la base de données comme initialisée en créant une table de flag.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        print("=" * 80)
        print("🔗 Connexion à la base de données établie")
        print("=" * 80)
        
        # Créer une table de métadonnées si elle n'existe pas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Marquer comme initialisé
        cur.execute("""
            INSERT INTO pipeline_metadata (key, value, updated_at)
            VALUES ('initialization_complete', 'true', CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE 
            SET value = 'true', updated_at = CURRENT_TIMESTAMP
        """)
        
        conn.commit()
        
        print("=" * 80)
        print("✅ BASE DE DONNÉES MARQUÉE COMME INITIALISÉE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur lors du marquage: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cur.close()
            conn.close()

default_args = {
    "owner": "hamza",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="initialization_pipeline",
    description="Initialisation unique: Weather + Energy historique complet",
    default_args=default_args,
    start_date=datetime(2025, 11, 11),
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    max_active_runs=1,
    tags=["renewstation", "initialization", "one-time"],
) as dag:

    # ========================================================================
    #   ÉTAPE 1: MÉTÉO HISTORIQUE COMPLÈTE
    # ========================================================================
    
    start_init = EmptyOperator(task_id="start_initialization")
    
    full_weather_backfill = BashOperator(
        task_id="full_weather_historical",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting --mode full"
        ),
        execution_timeout=timedelta(minutes=30),
    )
    
    # ========================================================================
    #   ÉTAPE 2: ÉNERGIE HISTORIQUE COMPLÈTE
    # ========================================================================
    
    full_energy_backfill = BashOperator(
        task_id="full_energy_historical",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.energy_cons_generator --mode full"
        ),
        execution_timeout=timedelta(minutes=45),
    )
    
    # ========================================================================
    #   ÉTAPE 3: MARQUER COMME INITIALISÉ
    # ========================================================================
    
    mark_complete = PythonOperator(
        task_id="mark_initialization_complete",
        python_callable=mark_initialization_complete,
        provide_context=True,
    )
    
    init_complete = EmptyOperator(task_id="initialization_complete")
    
    # ========================================================================
    #   DÉPENDANCES
    # ========================================================================
    
    start_init >> full_weather_backfill >> full_energy_backfill >> mark_complete >> init_complete


# ============================================================================
#   NOTES D'UTILISATION
# ============================================================================
# 
# 📋 Pour exécuter ce DAG:
#    1. Aller dans l'interface Airflow
#    2. Trouver "initialization_pipeline"
#    3. Cliquer sur "Trigger DAG"
#    4. Attendre la fin de l'exécution (peut prendre 30-45 minutes)
# 
# ⚠️  Ce DAG ne doit être exécuté qu'UNE SEULE FOIS!
# 
# ✅ Après exécution, le DAG "update_and_prediction_pipeline" pourra fonctionner
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