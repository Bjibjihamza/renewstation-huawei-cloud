# 📊 Pipeline de Données - RenewStation

## 🎯 Vue d'ensemble

Pipeline automatisé pour la collecte, génération et mise à jour des données météo et énergétiques pour la plateforme RenewStation.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE DU PIPELINE                      │
└─────────────────────────────────────────────────────────────────┘

📅 1/1/2024 ──────────────────────────────► Aujourd'hui ──► +6h
    │                                            │            │
    ▼                                            ▼            ▼
┌──────────────────────────────────┐    ┌──────────┐  ┌──────────┐
│  HISTORIQUE (données réelles)    │    │   NOW    │  │ FORECAST │
│  - Météo: API Archive            │    │          │  │ (6h)     │
│  - Énergie: Synthétique corrélé  │    │          │  │          │
└──────────────────────────────────┘    └──────────┘  └──────────┘
                                              ▲            │
                                              │            │
                                              └────────────┘
                                           Backfill auto
                                        (prévisions → réel)
```

## 📂 Structure du Projet

```
renewstation-huawei-cloud/
├── dags/
│   └── weather_energy_dag.py              # DAG unifié (initial + updates)
│
├── src/
│   └── pipeline/
│       ├── generator/
│       │   ├── weather_forecasting.py           # Météo: historique + forecast
│       │   ├── energy_cons_generator.py         # Énergie: historique
│       │   └── generate_energy_6h_forecast.py   # Énergie: forecast 6h
│       │
│       └── load/
│           ├── weather_loader.py                # UPSERT météo
│           └── energy_loader.py                 # UPSERT énergie
│
├── databases/
│   ├── bronze.sql                         # Schéma raw data (non utilisé)
│   ├── silver.sql                         # Schéma tables principales ⭐
│   └── gold.sql                           # Schéma agrégations (futur)
│
├── data/
│   └── energy_consumption.csv             # Export données énergétiques
│
├── logs/                                  # Logs Airflow
├── notebooks/                             # Analyses exploratoires
├── docs/                                  # Documentation Huawei
├── docker-compose.yml                     # Configuration Docker
├── Dockerfile                             # Image Airflow custom
├── .env                                   # Variables d'environnement
└── requirements.txt                       # Dépendances Python
```

## 🚀 Installation et Démarrage

### Prérequis

* Docker Desktop installé et en cours d'exécution
* Python 3.12+ (pour dev local)
* PostgreSQL client (optionnel, pour debug)

### 1️⃣ Configuration Initiale

```bash
# 1. Cloner le projet
cd renewstation-huawei-cloud

# 2. Configurer les variables d'environnement
# Éditer le fichier .env avec vos paramètres
GAUSSDB_HOST=postgres
GAUSSDB_PORT=5432
GAUSSDB_DB_SILVER=silver
GAUSSDB_USER=postgres
GAUSSDB_PASSWORD=your_secure_password
GAUSSDB_SSLMODE=disable

# 3. Lancer les conteneurs Docker
docker-compose up -d --build

# 4. Vérifier que les services sont actifs
docker ps
# Vous devriez voir: postgres, airflow-webserver, airflow-scheduler
```

### 2️⃣ Initialisation de la Base de Données

```bash
# Connexion au conteneur PostgreSQL
docker exec -it renewstation-postgres psql -U postgres

# Créer la base de données SILVER
CREATE DATABASE silver;

# Se connecter à la base silver
\c silver

# Exécuter le script de création des tables
# Copier-coller le contenu de databases/silver.sql
```

**Contenu de `databases/silver.sql` :**

```sql
-- =============================================================================
-- SILVER LAYER – CLEANED / MODELED TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS energy_consumption_hourly (
    time_ts                TIMESTAMP      NOT NULL,
    building               VARCHAR(50)    NOT NULL,
    
    -- Flags saisonniers
    winter_flag            SMALLINT       NOT NULL,
    spring_flag            SMALLINT       NOT NULL,
    summer_flag            SMALLINT       NOT NULL,
    fall_flag              SMALLINT       NOT NULL,
    
    -- Données météo
    outdoor_temp_c         NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),
    
    -- Features temporelles
    hour_of_day            SMALLINT       NOT NULL,
    day_of_week            SMALLINT       NOT NULL,
    month_num              SMALLINT       NOT NULL,
    day_of_year            SMALLINT       NOT NULL,
    is_weekend             SMALLINT       NOT NULL,
    is_holiday             SMALLINT       NOT NULL,
    is_peak_hour           SMALLINT       NOT NULL,
    
    -- Consommation énergétique
    lighting_kw            NUMERIC(10,4),
    hvac_kw                NUMERIC(10,4),
    special_equipment_kw   NUMERIC(10,4),
    use_kw                 NUMERIC(10,4),
    
    CONSTRAINT pk_energy_silver PRIMARY KEY (time_ts, building)
);

CREATE INDEX idx_energy_time ON energy_consumption_hourly(time_ts);
CREATE INDEX idx_energy_building ON energy_consumption_hourly(building);
CREATE INDEX idx_energy_time_building ON energy_consumption_hourly(time_ts, building);
CREATE INDEX idx_energy_temporal ON energy_consumption_hourly(month_num, day_of_week, hour_of_day);

-- =============================================================================

CREATE TABLE IF NOT EXISTS weather_forecast_hourly (
    forecast_timestamp             TIMESTAMP PRIMARY KEY,
    forecast_date                  DATE NOT NULL,
    forecast_time                  TIME NOT NULL,
    
    temperature_c                  NUMERIC(5,2),
    humidity_pct                   NUMERIC(5,2),
    precipitation_mm               NUMERIC(6,2),
    precipitation_probability_pct  NUMERIC(5,2),
    weather_conditions             VARCHAR(100),
    wind_speed_kmh                 NUMERIC(6,2),
    wind_direction_deg             NUMERIC(5,2),
    pressure_hpa                   NUMERIC(7,2),
    cloud_cover_pct                NUMERIC(5,2),
    solar_radiation_w_m2           NUMERIC(8,2),
    
    created_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weather_forecast_date ON weather_forecast_hourly(forecast_date);
CREATE INDEX idx_weather_forecast_timestamp ON weather_forecast_hourly(forecast_timestamp);
CREATE INDEX idx_weather_conditions ON weather_forecast_hourly(weather_conditions);
```

### 3️⃣ Accès à l'Interface Airflow

```
URL: http://localhost:8080
Utilisateur: airflow
Mot de passe: airflow
```

---

## ⚙️ Utilisation du Pipeline

### 🎯 Première Exécution (Initial Load)

Le DAG `unified_weather_energy_pipeline` détecte automatiquement s'il doit charger l'historique complet ou effectuer une mise à jour.

**1. Activer le DAG**

Dans l'interface Airflow :
- Naviguer vers **DAGs**
- Trouver `unified_weather_energy_pipeline`
- Activer le toggle (bouton ON/OFF)

**2. Déclencher manuellement**

- Cliquer sur le bouton **▶️ Trigger DAG**
- Le pipeline détectera automatiquement qu'il s'agit de la première exécution
- Durée estimée : **45-60 minutes**

**3. Étapes exécutées (première fois)**

```
check_initialization_mode
  └─► initial_load
       ├─► initial_weather_history       (~10-20 min)
       ├─► initial_energy_history        (~20-30 min)
       ├─► initial_weather_forecast_6h   (~1-2 min)
       ├─► initial_energy_forecast_6h    (~2-3 min)
       └─► mark_system_initialized       (~1 sec)
```

**4. Vérification du chargement**

```sql
-- Connexion à la base
\c silver

-- Vérifier météo historique
SELECT 
    COUNT(*) as total_heures,
    MIN(forecast_timestamp) as premiere_date,
    MAX(forecast_timestamp) as derniere_date,
    COUNT(DISTINCT DATE(forecast_timestamp)) as total_jours
FROM weather_forecast_hourly;

-- Résultat attendu:
-- total_heures: ~7500+ (du 2024-01-01 à aujourd'hui + 6h)
-- total_jours: ~315+ jours

-- Vérifier énergie historique
SELECT 
    building,
    COUNT(*) as heures,
    MIN(time_ts) as premiere_date,
    MAX(time_ts) as derniere_date,
    ROUND(AVG(use_kw), 2) as consommation_moyenne_kw
FROM energy_consumption_hourly
GROUP BY building
ORDER BY building;

-- Résultat attendu:
-- 24 lignes (un par bâtiment)
-- ~7500+ heures par bâtiment
```

### 🔄 Exécutions Automatiques (Updates 6h)

Après la première exécution, le DAG s'exécute automatiquement toutes les 6 heures.

**Schedule :** `0 */6 * * *` (00:00, 06:00, 12:00, 18:00)

**Étapes exécutées (mode update) :**

```
check_initialization_mode
  └─► regular_update
       ├─► regular_weather_update_6h     (~30 sec - 1 min)
       │    ├─ Backfill: anciennes prévisions → données réelles
       │    └─ Fetch: 6 nouvelles heures de prévisions
       │
       └─► regular_energy_update_6h      (~1-2 min)
            └─ Génère 6h de consommation basée sur météo forecast
```

Durée totale update : ~2-3 minutes

## 🏗️ Architecture Détaillée

### 📊 Tables de Données

#### 1. `weather_forecast_hourly` (Météo)

| Colonne                      | Type          | Description                          |
|------------------------------|---------------|--------------------------------------|
| `forecast_timestamp`         | `TIMESTAMP (PK)` | Horodatage unique de la prévision   |
| `temperature_c`              | `NUMERIC(5,2)` | Température en °C                    |
| `humidity_pct`               | `NUMERIC(5,2)` | Humidité relative en %               |
| `cloud_cover_pct`            | `NUMERIC(5,2)` | Couverture nuageuse en %             |
| `solar_radiation_w_m2`       | `NUMERIC(8,2)` | ☀️ Rayonnement solaire (W/m²)        |
| `wind_speed_kmh`             | `NUMERIC(6,2)` | Vitesse du vent (km/h)               |
| `pressure_hpa`               | `NUMERIC(7,2)` | Pression atmosphérique (hPa)         |
| `precipitation_mm`           | `NUMERIC(6,2)` | Précipitations (mm)                  |
| `weather_conditions`         | `VARCHAR(100)`| Description textuelle                |

**Source :** API Open-Meteo (Archive + Forecast)

#### 2. `energy_consumption_hourly` (Énergie)

| Colonne                  | Type          | Description                          |
|--------------------------|---------------|--------------------------------------|
| `time_ts`                | `TIMESTAMP (PK)` | Horodatage                          |
| `building`               | `VARCHAR(50) (PK)` | Identifiant du bâtiment             |
| `use_kw`                 | `NUMERIC(10,4)` | Consommation totale (kW)            |
| `lighting_kw`            | `NUMERIC(10,4)` | Éclairage (kW)                      |
| `hvac_kw`                | `NUMERIC(10,4)` | Climatisation/Chauffage (kW)        |
| `special_equipment_kw`   | `NUMERIC(10,4)` | Équipements spéciaux (kW)           |
| `outdoor_temp_c`         | `NUMERIC(5,2)` | Température extérieure              |
| `solar_radiation_w_m2`   | `NUMERIC(8,2)` | Rayonnement solaire                 |
| `hour_of_day`            | `SMALLINT`    | Heure (0-23)                        |
| `day_of_week`            | `SMALLINT`    | Jour semaine (0=lundi)              |
| `is_weekend`             | `SMALLINT`    | Weekend ? (0/1)                     |
| `is_holiday`             | `SMALLINT`    | Jour férié ? (0/1)                  |
| `is_peak_hour`           | `SMALLINT`    | Heure de pointe ? (0/1)             |

**Source :** Généré synthétiquement avec corrélations météo réelles

### 🏢 Bâtiments Simulés

| Type      | Quantité | Noms            | Caractéristiques                          |
|-----------|----------|-----------------|-------------------------------------------|
| 🏥 Hospital | 1      | Hospital2       | 24/7, haute consommation stable           |
| 🏠 House   | 15     | House1-15       | Pics matin/soir, weekend élevé            |
| 🏭 Industry| 3      | Industry1-3     | Consommation continue, 3×8                |
| 🏢 Office  | 4      | Office1-4       | 8h-18h, faible weekend                    |
| 🎓 School  | 1      | School          | 8h-17h, vacances scolaires                |
| **TOTAL** | **24**  | -               | Patterns d'occupation uniques             |

**Paramètres individuels par bâtiment :**

* Efficacité énergétique : 0.75 - 1.25 (multiplicateur de base)
* Isolation thermique : 0.7 - 1.3 (impact HVAC)
* Modernité équipements : 0.85 - 1.15 (consommation équipements)

### 🔄 Flux de Données

#### Pipeline Météo (`weather_forecasting.py`)

```python
1. _ensure_history_coverage()
   ├─ Vérifie: 2024-01-01 00:00 → now
   ├─ Détecte gaps dans weather_forecast_hourly
   └─ Backfill via API Archive si manquant
   
2. _backfill_forecast_with_real_data()
   ├─ Cherche prévisions antérieures à now-1h
   ├─ Récupère données réelles pour ces timestamps
   └─ UPDATE weather_forecast_hourly (prévision → réel)
   
3. _fetch_forecast_6h_and_load()
   ├─ API Forecast: now → now+6h
   ├─ Parse réponse JSON
   └─ UPSERT dans weather_forecast_hourly
```

**API utilisée :** https://api.open-meteo.com/v1/

* Archive : `/archive?latitude=33.5731&longitude=-7.5898&...`
* Forecast : `/forecast?latitude=33.5731&longitude=-7.5898&...`

#### Pipeline Énergie

**Historique (initial load) :** (`energy_cons_generator.py`)

```python
1. fetch_real_weather_data()
   └─ SELECT * FROM weather_forecast_hourly
      WHERE forecast_timestamp BETWEEN start_date AND end_date
   
2. generate_building_data()
   Pour chaque bâtiment:
   ├─ Génère patterns d'occupation (jour/nuit, weekend, vacances)
   ├─ Calcule HVAC basé sur température
   │  └─ Plus froid/chaud = plus HVAC
   ├─ Calcule Lighting basé sur solar_radiation
   │  └─ Moins de soleil = plus d'éclairage
   ├─ Calcule Equipment basé sur occupation
   └─ use_kw = lighting + hvac + equipment
   
3. load_energy_consumption_to_db()
   └─ INSERT INTO energy_consumption_hourly
      ON CONFLICT (time_ts, building) DO UPDATE
```

**Forecast 6h (regular updates) :** (`generate_energy_6h_forecast.py`)

```python
1. fetch_6h_weather_forecast()
   └─ SELECT * FROM weather_forecast_hourly
      WHERE forecast_timestamp >= NOW()
      ORDER BY forecast_timestamp
      LIMIT 6
   
2. get_last_occupancy_state()
   └─ Récupère dernier état de chaque bâtiment
      pour assurer continuité des patterns
   
3. generate_building_6h_forecast()
   └─ Même logique que historique, mais 6h seulement
   
4. upsert_energy_consumption_to_db()
   └─ UPSERT (update si existe, insert sinon)
```

## 🔧 Configuration Avancée

### Variables d'Environnement (`.env`)

```bash
# PostgreSQL / GaussDB
GAUSSDB_HOST=postgres
GAUSSDB_PORT=5432
GAUSSDB_DB_SILVER=silver
GAUSSDB_USER=postgres
GAUSSDB_PASSWORD=your_secure_password
GAUSSDB_SSLMODE=disable

# Airflow Core
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
AIRFLOW__CORE__PLUGINS_FOLDER=/opt/airflow/plugins

# Airflow Database
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow

# Airflow Webserver
AIRFLOW__WEBSERVER__EXPOSE_CONFIG=True
AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key_here

# Airflow Scheduler
AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=30
```

### Configuration Docker Compose

**Services principaux :**

1. `postgres` : Base de données (Airflow + Silver)
2. `airflow-webserver` : Interface web (port 8080)
3. `airflow-scheduler` : Orchestrateur des DAGs
4. `airflow-init` : Initialisation DB Airflow

**Volumes montés :**

```yaml
volumes:
  - ./dags:/opt/airflow/dags
  - ./logs:/opt/airflow/logs
  - ./plugins:/opt/airflow/plugins
  - ./src:/opt/airflow/src
  - ./data:/opt/airflow/data
```

### Variables Airflow

**Variable de contrôle :** `renewstation_initialized`

* `false` ou absente → Mode INITIAL LOAD
* `true` → Mode REGULAR UPDATE

**Pour réinitialiser :**

```bash
# Via Airflow CLI
docker exec -it renewstation-airflow-webserver \
  airflow variables delete renewstation_initialized

# Via UI: Admin → Variables → Delete
```

---

## 📊 Monitoring et Vérification

### Logs Airflow

**Localisation :**

```
logs/
├── dag_processor_manager/
│   └── dag_processor_manager.log
└── scheduler/
    └── 2025-11-11/
        ├── initial_data_load.py.log
        ├── weather_energy_dag.py.log
        └── weather_forecasting_dag.py.log
```

**Commandes utiles :**

```bash
# Tail logs en temps réel
docker logs -f renewstation-airflow-scheduler

# Logs d'un DAG spécifique
docker exec -it renewstation-airflow-webserver \
  airflow tasks logs unified_weather_energy_pipeline \
  regular_weather_update_6h 2025-11-11T12:00:00+00:00
```

### Requêtes SQL de Vérification

#### Météo

```sql
-- Statistiques générales
SELECT 
    COUNT(*) as total_heures,
    COUNT(DISTINCT DATE(forecast_timestamp)) as total_jours,
    MIN(forecast_timestamp) as debut,
    MAX(forecast_timestamp) as fin,
    ROUND(AVG(temperature_c), 1) as temp_moy,
    ROUND(AVG(solar_radiation_w_m2), 1) as radiation_moy
FROM weather_forecast_hourly;

-- Prévisions futures (6h)
SELECT 
    forecast_timestamp,
    temperature_c,
    humidity_pct,
    solar_radiation_w_m2,
    weather_conditions
FROM weather_forecast_hourly
WHERE forecast_timestamp >= NOW()
ORDER BY forecast_timestamp;

-- Détection de gaps (heures manquantes)
WITH hours AS (
    SELECT generate_series(
        '2024-01-01 00:00:00'::timestamp,
        NOW(),
        '1 hour'::interval
    ) AS expected_hour
)
SELECT expected_hour
FROM hours
WHERE expected_hour NOT IN (
    SELECT forecast_timestamp FROM weather_forecast_hourly
)
ORDER BY expected_hour;
```

#### Énergie

```sql
-- Vue d'ensemble par bâtiment
SELECT 
    building,
    COUNT(*) as heures,
    MIN(time_ts) as debut,
    MAX(time_ts) as fin,
    ROUND(AVG(use_kw), 2) as conso_moy_kw,
    ROUND(MAX(use_kw), 2) as conso_max_kw,
    ROUND(AVG(lighting_kw), 2) as lighting_moy,
    ROUND(AVG(hvac_kw), 2) as hvac_moy
FROM energy_consumption_hourly
GROUP BY building
ORDER BY AVG(use_kw) DESC;

-- Consommation journalière
SELECT 
    DATE(time_ts) as jour,
    SUM(use_kw) as conso_totale_kw,
    COUNT(DISTINCT building) as nb_batiments
FROM energy_consumption_hourly
WHERE time_ts >= NOW() - INTERVAL '7 days'
GROUP BY DATE(time_ts)
ORDER BY jour DESC;

-- Prévisions 6h
SELECT 
    time_ts,
    building,
    use_kw,
    lighting_kw,
    hvac_kw,
    outdoor_temp_c
FROM energy_consumption_hourly
WHERE time_ts >= NOW()
ORDER BY time_ts, building;

-- Corrélation température / HVAC
SELECT 
    building,
    ROUND(AVG(outdoor_temp_c), 1) as temp_moy,
    ROUND(AVG(hvac_kw), 2) as hvac_moy,
    COUNT(*) as heures
FROM energy_consumption_hourly
WHERE outdoor_temp_c IS NOT NULL
GROUP BY building
ORDER BY building;
```

### Validation Qualité Données

```sql
-- Détection valeurs NULL critiques
SELECT 
    'weather' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN temperature_c IS NULL THEN 1 ELSE 0 END) as null_temp,
    SUM(CASE WHEN solar_radiation_w_m2 IS NULL THEN 1 ELSE 0 END) as null_radiation
FROM weather_forecast_hourly

UNION ALL

SELECT 
    'energy' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN use_kw IS NULL THEN 1 ELSE 0 END) as null_use_kw,
    SUM(CASE WHEN outdoor_temp_c IS NULL THEN 1 ELSE 0 END) as null_temp
FROM energy_consumption_hourly;

-- Valeurs aberrantes
SELECT 
    'temperature' as metric,
    MIN(temperature_c) as min_val,
    MAX(temperature_c) as max_val,
    ROUND(AVG(temperature_c), 2) as avg_val
FROM weather_forecast_hourly
WHERE temperature_c < -20 OR temperature_c > 50

UNION ALL

SELECT 
    'energy_consumption' as metric,
    MIN(use_kw) as min_val,
    MAX(use_kw) as max_val,
    ROUND(AVG(use_kw), 2) as avg_val
FROM energy_consumption_hourly
WHERE use_kw < 0 OR use_kw > 10000;
```