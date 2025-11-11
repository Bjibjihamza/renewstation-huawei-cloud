from datetime import datetime, timedelta
import psycopg2

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator

# ============================================================================
#   DAG AIRFLOW UNIFIÉ - MÉTÉO + ÉNERGIE (INITIAL + FORECAST 6H)
# ============================================================================
# 
# 🎯 CE DAG GÈRE AUTOMATIQUEMENT:
# 
# 1️⃣ PREMIÈRE EXÉCUTION (Initial Load):
#    - Détecte automatiquement si la DB est vide
#    - Charge l'historique complet (1/1/2024 → aujourd'hui)
#    - Génère les données énergétiques historiques
#    - Crée les prévisions initiales (6h)
# 
# 2️⃣ EXÉCUTIONS SUIVANTES (Regular Updates):
#    - Backfill des anciennes prévisions avec données réelles
#    - Récupère les 6 prochaines heures de prévisions
#    - Génère les données énergétiques pour les 6h
#    - S'exécute automatiquement toutes les 6h
# 
# ✅ Avantages:
#    - Vérification directe dans la DB (pas de variable Airflow)
#    - Un seul DAG à gérer
#    - Logique intelligente et robuste
#    - Réinitialisation automatique si DB vidée
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
    Vérifie si des données existent déjà dans la base de données.
    
    Critères pour considérer le système comme "initialisé":
    - weather_forecast_hourly contient des données >= 2024-01-01
    - energy_consumption_hourly contient des données >= 2024-01-01
    
    Returns:
        str: 'initial_load' si DB vide, 'regular_update' si déjà des données
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Vérifier la météo historique
        cur.execute("""
            SELECT COUNT(*) 
            FROM weather_forecast_hourly 
            WHERE forecast_timestamp >= '2024-01-01 00:00:00'
        """)
        weather_count = cur.fetchone()[0]
        
        # Vérifier l'énergie historique
        cur.execute("""
            SELECT COUNT(*) 
            FROM energy_consumption_hourly 
            WHERE time_ts >= '2024-01-01 00:00:00'
        """)
        energy_count = cur.fetchone()[0]
        
        print("=" * 80)
        print("🔍 VÉRIFICATION DE L'INITIALISATION DE LA BASE DE DONNÉES")
        print("=" * 80)
        print(f"📊 Données météo depuis 2024-01-01: {weather_count:,} lignes")
        print(f"⚡ Données énergie depuis 2024-01-01: {energy_count:,} lignes")
        print("=" * 80)
        
        # Critère: au moins 1000 lignes de météo ET 10000 lignes d'énergie
        # (correspond à ~42 jours de données minimales)
        if weather_count >= 1000 and energy_count >= 10000:
            print("✅ Base de données déjà initialisée → Mode REGULAR UPDATE (6h)")
            print("=" * 80)
            return "regular_update"
        else:
            print("🚀 Base de données vide ou incomplète → Mode INITIAL LOAD")
            print("=" * 80)
            return "initial_load"
            
    except Exception as e:
        print("=" * 80)
        print(f"⚠️  Erreur lors de la vérification de la DB: {e}")
        print("🚀 Par défaut → Mode INITIAL LOAD")
        print("=" * 80)
        return "initial_load"
        
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
    dag_id="unified_weather_energy_pipeline",
    description="🔄 Pipeline unifié: Initial Load + Updates 6h automatiques (DB Check)",
    default_args=default_args,
    start_date=datetime(2025, 11, 11),
    schedule_interval="0 */6 * * *",         # Toutes les 6h: 00:00, 06:00, 12:00, 18:00
    catchup=False,
    max_active_runs=1,
    tags=["renewstation", "unified", "weather", "energy", "auto"],
) as dag:

    # ========================================================================
    #   BRANCHEMENT INTELLIGENT: INITIAL vs REGULAR (VÉRIFICATION DB)
    # ========================================================================
    
    check_mode = BranchPythonOperator(
        task_id="check_database_status",
        python_callable=check_database_initialization,
        provide_context=True,
        doc_md="""
        ### 🔍 Détection automatique du mode d'exécution
        
        **Vérifie directement dans la base de données:**
        
        - **Query 1:** `SELECT COUNT(*) FROM weather_forecast_hourly WHERE forecast_timestamp >= '2024-01-01'`
        - **Query 2:** `SELECT COUNT(*) FROM energy_consumption_hourly WHERE time_ts >= '2024-01-01'`
        
        **Critères:**
        - Météo >= 1000 lignes ET Énergie >= 10000 lignes → **REGULAR UPDATE**
        - Sinon → **INITIAL LOAD**
        
        **Avantages:**
        - Pas de dépendance à une variable Airflow
        - Vérification robuste de l'état réel
        - Réinitialisation automatique si DB vidée
        """,
    )

    # ========================================================================
    #   BRANCHE 1: INITIAL LOAD (Première exécution ou DB vide)
    # ========================================================================
    
    initial_load = EmptyOperator(
        task_id="initial_load",
        doc_md="🚀 **Mode: Initial Load** - Chargement historique complet",
    )
    
    # --- Historique Météo Complet ---
    initial_weather_history = BashOperator(
        task_id="initial_weather_history",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting"
        ),
        execution_timeout=timedelta(minutes=30),
        doc_md="""
        ### 📚 Chargement historique météo (1/1/2024 → aujourd'hui)
        
        - **Source:** Open-Meteo Archive API
        - **Durée estimée:** 10-20 minutes
        - **Volume:** ~7500+ heures (selon date actuelle)
        - **Insertion:** UPSERT pour éviter les doublons
        """,
    )
    
    # --- Historique Énergie Complet ---
    initial_energy_history = BashOperator(
        task_id="initial_energy_history",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.energy_cons_generator"
        ),
        execution_timeout=timedelta(minutes=45),
        doc_md="""
        ### ⚡ Génération historique énergie (1/1/2024 → aujourd'hui)
        
        - **Corrélations:** météo réelle + patterns d'occupation
        - **Durée estimée:** 20-30 minutes
        - **Volume:** ~180,000+ lignes (24 bâtiments × 7500+ heures)
        - **Insertion:** UPSERT pour éviter les doublons
        """,
    )
    
    # --- Prévisions Météo Initiales (6h) ---
    initial_weather_forecast = BashOperator(
        task_id="initial_weather_forecast_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting"
        ),
        execution_timeout=timedelta(minutes=10),
        doc_md="""
        ### 🔮 Prévisions météo initiales (6h)
        
        - **Source:** Open-Meteo Forecast API
        - **Volume:** 6 heures de prévisions
        - **Insertion:** UPSERT
        """,
    )
    
    # --- Prévisions Énergie Initiales (6h) ---
    initial_energy_forecast = BashOperator(
        task_id="initial_energy_forecast_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.generate_energy_6h_forecast"
        ),
        execution_timeout=timedelta(minutes=15),
        doc_md="""
        ### ⚡ Prévisions énergie initiales (6h)
        
        - **Volume:** ~144 lignes (24 bâtiments × 6 heures)
        - **Insertion:** UPSERT
        """,
    )

    # ========================================================================
    #   BRANCHE 2: REGULAR UPDATE (Exécutions suivantes - toutes les 6h)
    # ========================================================================
    
    regular_update = EmptyOperator(
        task_id="regular_update",
        doc_md="🔄 **Mode: Regular Update** - Mise à jour 6h",
    )
    
    # --- Météo: Backfill + Forecast 6h ---
    regular_weather_update = BashOperator(
        task_id="regular_weather_update_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.weather_forecasting"
        ),
        execution_timeout=timedelta(minutes=10),
        doc_md="""
        ### 📡 Mise à jour météo (backfill + 6h forecast)
        
        **Étapes:**
        1. **Backfill:** Remplace anciennes prévisions par données réelles
        2. **Forecast:** Récupère 6 prochaines heures
        3. **UPSERT:** Pas de duplication
        
        **Durée:** ~2-5 minutes
        """,
    )
    
    # --- Énergie: Génération 6h ---
    regular_energy_update = BashOperator(
        task_id="regular_energy_update_6h",
        bash_command=(
            "cd /opt/airflow && "
            "PYTHONPATH=/opt/airflow "
            "python -m src.pipeline.generator.generate_energy_6h_forecast"
        ),
        execution_timeout=timedelta(minutes=15),
        doc_md="""
        ### ⚡ Génération énergie (6h forecast)
        
        **Étapes:**
        1. Lit les 6h de météo depuis weather_forecast_hourly
        2. Génère données énergétiques synthétiques corrélées
        3. UPSERT dans energy_consumption_hourly
        
        **Durée:** ~3-5 minutes
        """,
    )

    # ========================================================================
    #   CONVERGENCE: Les deux branches rejoignent ici
    # ========================================================================
    
    pipeline_complete = EmptyOperator(
        task_id="pipeline_complete",
        trigger_rule="none_failed_min_one_success",
        doc_md="""
        ### ✅ Pipeline terminé avec succès
        
        Le pipeline s'est terminé avec succès.
        
        **Prochaine exécution:** Dans 6 heures (automatique)
        
        **Vérifications suggérées:**
        ```sql
        -- Météo
        SELECT COUNT(*), MIN(forecast_timestamp), MAX(forecast_timestamp)
        FROM weather_forecast_hourly;
        
        -- Énergie
        SELECT COUNT(*), COUNT(DISTINCT building), MIN(time_ts), MAX(time_ts)
        FROM energy_consumption_hourly;
        ```
        """,
    )

    # ========================================================================
    #   DÉFINITION DES DÉPENDANCES
    # ========================================================================
    
    # Branchement initial (vérification DB)
    check_mode >> [initial_load, regular_update]
    
    # --- BRANCHE INITIAL LOAD ---
    initial_load >> initial_weather_history
    initial_weather_history >> initial_energy_history
    initial_energy_history >> initial_weather_forecast
    initial_weather_forecast >> initial_energy_forecast
    initial_energy_forecast >> pipeline_complete
    
    # --- BRANCHE REGULAR UPDATE ---
    regular_update >> regular_weather_update
    regular_weather_update >> regular_energy_update
    regular_energy_update >> pipeline_complete


