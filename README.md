# RenewStation – Plateforme IA de Prédiction Énergétique

**Précision ±149 Watts · 17 Bâtiments · 7 Jours d'Avance**

---

## 🎯 Vue d'Ensemble

RenewStation est une plateforme complète de gestion et prédiction énergétique utilisant l'Intelligence Artificielle pour anticiper la consommation électrique de 17 bâtiments avec une précision exceptionnelle de ±149 Watts (0.149 kW).

### 💡 Proposition de Valeur

> « Notre IA prédit votre consommation électrique heure par heure, 7 jours à l'avance, avec une erreur moyenne de seulement 149 Watts — l'équivalent d'une ampoule LED. »

---

## 📊 Métriques de Performance

| Métrique | Valeur | Description |
|----------|--------|-------------|
| **MAE** | 0.149 kW | Erreur Absolue Moyenne |
| **RMSE** | 0.285 kW | Racine de l'Erreur Quadratique Moyenne |
| **R²** | 0.9980 | Coefficient de Détermination (99.8%) |
| **Précision Réelle** | 73.0% | Prédictions dans la marge ±0.149 kW |
| **Bâtiments** | 17 | Couverture totale |
| **Horizon** | 168h | 7 jours (prédictions horaires) |
| **Données d'Entraînement** | 278 647 | Points de données réelles |

---

## 🏗️ Architecture Complète

### Stack Technologique

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                        │
│              Dashboard Visualisation Temps Réel             │
│                    Port 80 (Nginx)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─→ HTTP Requests
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  API REST (Node.js/Express)                 │
│        Endpoints: Energy, Weather, Solar, Battery           │
│                    Port 8000                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─→ SQL Queries
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              DATABASE (PostgreSQL 16)                       │
│           9 Tables Silver Layer (Optimisées)                │
│                    Port 5432                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─→ Read/Write
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            AIRFLOW ORCHESTRATION                            │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐           │
│  │ Scheduler  │  │  Webserver │  │   Worker    │           │
│  │  Port 8080 │  │  (UI)      │  │             │           │
│  └────────────┘  └────────────┘  └─────────────┘           │
│                                                              │
│  DAGs:                                                       │
│  • daily_prediction_pipeline (00:00 quotidien)              │
│  • initialization_pipeline (setup initial)                  │
└──────────────────────────────────────────────────────────────┘
                      │
                      ├─→ ML Training & Inference
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  MACHINE LEARNING                           │
│              RandomForest Regressor                         │
│           Model: energy_predictor.pkl                       │
│              (Persisté & Auto-Updated)                      │
└──────────────────────────────────────────────────────────────┘
```

### Composants Docker

```yaml
Services:
├── postgres          # Base de données principale
├── airflow-init      # Initialisation DB Airflow
├── airflow-scheduler # Orchestration DAGs
├── airflow-webserver # Interface Airflow UI
├── api              # Backend Node.js/Express
└── frontend         # Dashboard React/Vite
```

---

## 📁 Structure Complète du Projet

```
renewstation-huawei-cloud/
│
├── 📂 api/                              # Backend REST API
│   ├── src/
│   │   ├── config/
│   │   │   └── database.js             # Configuration PostgreSQL
│   │   ├── controllers/
│   │   │   └── solar.controller.js     # Logique métier (18 endpoints)
│   │   ├── routes/
│   │   │   └── solar.routes.js         # Routes Express
│   │   └── server.js                   # Point d'entrée API
│   ├── Dockerfile                      # Image Node.js API
│   ├── package.json                    # Dépendances npm
│   └── .env.example                    # Template variables
│
├── 📂 frontend/                         # Interface Utilisateur
│   ├── src/
│   │   ├── Pages/
│   │   │   ├── Dashboard.jsx           # Page d'accueil
│   │   │   ├── EnergyPage.jsx          # Consommation énergétique
│   │   │   ├── SolarPage.jsx           # Production solaire
│   │   │   ├── Battery.jsx             # État batterie
│   │   │   ├── WeatherPage.jsx         # Météo & prévisions
│   │   │   └── Overviews.jsx           # Vue d'ensemble
│   │   ├── components/
│   │   │   ├── Overview.tsx            # Composant principal
│   │   │   ├── BatteryStateSection.tsx # Section batterie
│   │   │   ├── BatteryVerticalBar.tsx  # Visualisation batterie
│   │   │   ├── Card.tsx                # Carte générique
│   │   │   └── WeatherMetric.tsx       # Métriques météo
│   │   ├── App.jsx                     # Router principal
│   │   └── main.jsx                    # Point d'entrée React
│   ├── Dockerfile                      # Build multi-stage Vite
│   ├── nginx.conf                      # Configuration Nginx
│   ├── package.json                    # Dépendances React
│   └── vite.config.js                  # Config Vite
│
├── 📂 dags/                             # Airflow DAGs
│   ├── daily_prediction_pipeline.py    # Pipeline quotidien 00:00
│   └── initialization_pipeline.py      # Setup initial (run once)
│
├── 📂 src/                              # Code Pipeline Python
│   ├── pipeline/
│   │   ├── extract/
│   │   │   └── test.py                 # Extraction données
│   │   ├── generator/
│   │   │   ├── energy_cons_generator.py      # Génération consommation
│   │   │   ├── energy_prediction_7d.py       # Prédiction ML 7j
│   │   │   ├── solar_prediction_7d.py        # Prédiction solaire
│   │   │   ├── battery_prediction_7d.py      # Prédiction batterie
│   │   │   ├── weather_forecasting.py        # Météo actuelle
│   │   │   ├── weather_forecast_7d.py        # Météo 7 jours
│   │   │   ├── battery_real_daily.py         # Batterie réelle
│   │   │   ├── battery_utils.py              # Utilitaires batterie
│   │   │   └── archive_yesterday_sync.py     # Archive J-1
│   │   ├── load/
│   │   │   ├── energy_loader.py              # Chargement energy live
│   │   │   ├── predicted_energy_loader.py    # Chargement ML predictions
│   │   │   ├── solar_prediction_loader.py    # Chargement solar pred
│   │   │   ├── battery_loader.py             # Chargement batterie
│   │   │   ├── weather_loader.py             # Chargement météo actuelle
│   │   │   ├── weather_loader_7d.py          # Chargement météo 7j
│   │   │   └── daily_archive_loader.py       # Archivage quotidien
│   │   ├── ml/
│   │   │   └── train_energy_model.py         # Entraînement modèle ML
│   │   └── transform/
│   │       └── (transformations si besoin)
│   ├── helpers/                               # Fonctions utilitaires
│   └── init_silver_data.py                   # Init schéma Silver
│
├── 📂 models/                           # Modèles ML Persistés
│   └── energy_predictor.pkl            # RandomForest 500 arbres
│
├── 📂 notebooks/                        # Jupyter Notebooks
│   ├── ML_VERIFICATION_FINAL.ipynb     # Validation modèle
│   ├── ML.ipynb                        # Expérimentation ML
│   ├── battries_verif.ipynb            # Tests batterie
│   ├── verif_7d.ipynb                  # Vérification prédictions 7j
│   └── prod.ipynb                      # Notebook production
│
├── 📂 databases/                        # Scripts SQL
│   └── silver.sql                      # Schéma complet Silver Layer
│
├── 📂 logs/                             # Logs Airflow
│
├── 📄 docker-compose.yml               # Orchestration complète
├── 📄 Dockerfile                       # Image Airflow
├── 📄 requirements.txt                 # Dépendances Python
├── 📄 .env                             # Variables d'environnement
├── 📄 .gitignore                       # Exclusions Git
└── 📄 README.md                        # Cette documentation
```

---

## 🗄️ Schéma de Base de Données (Silver Layer)

### Tables Principales

#### 1. energy_consumption_hourly_archive (Historique Complet)

Stocke toutes les données historiques de consommation réelle.

```sql
CREATE TABLE energy_consumption_hourly_archive (
    id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL,
    building_name VARCHAR(255),
    time_ts TIMESTAMP NOT NULL,
    consumed_energy_kwh NUMERIC(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** Base d'entraînement ML, analyses historiques

#### 2. energy_consumption_hourly_live (Données Récentes)

Contient les dernières heures de consommation réelle (fenêtre glissante).

```sql
CREATE TABLE energy_consumption_hourly_live (
    id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL,
    building_name VARCHAR(255),
    time_ts TIMESTAMP NOT NULL,
    consumed_energy_kwh NUMERIC(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** Affichage temps réel dashboard, comparaison avec prédictions

#### 3. predicted_energy_consumption_hourly (Prédictions ML)

Prédictions IA pour les 7 prochains jours (168 heures × 17 bâtiments = 2 856 lignes).

```sql
CREATE TABLE predicted_energy_consumption_hourly (
    id SERIAL PRIMARY KEY,
    building_id INTEGER NOT NULL,
    building_name VARCHAR(255),
    time_ts TIMESTAMP NOT NULL,
    predicted_energy_kwh NUMERIC(10, 3),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** Affichage prédictions dashboard, planification énergétique

#### 4. weather_forecast_hourly (Prévisions Météo 7j)

Données météo futures depuis Open-Meteo API.

```sql
CREATE TABLE weather_forecast_hourly (
    id SERIAL PRIMARY KEY,
    forecast_timestamp TIMESTAMP NOT NULL,
    temperature_2m NUMERIC(5, 2),
    relative_humidity_2m INTEGER,
    precipitation NUMERIC(5, 2),
    cloud_cover INTEGER,
    wind_speed_10m NUMERIC(5, 2),
    shortwave_radiation NUMERIC(7, 2),
    direct_radiation NUMERIC(7, 2),
    diffuse_radiation NUMERIC(7, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** Features ML, affichage météo dashboard

#### 5. weather_archive_hourly (Historique Météo)

Archive des prévisions météo passées.

```sql
CREATE TABLE weather_archive_hourly (
    -- Même structure que weather_forecast_hourly
);
```

#### 6. predicted_solar_production (Production Solaire Prédite)

Prédictions de production solaire sur 7 jours.

```sql
CREATE TABLE predicted_solar_production (
    timestamp TIMESTAMP PRIMARY KEY,
    predicted_solar_kwh NUMERIC(10, 3),
    shortwave_radiation NUMERIC(7, 2),
    direct_radiation NUMERIC(7, 2),
    diffuse_radiation NUMERIC(7, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage:** Planification production renouvelable

#### 7. solar_production_archive (Production Solaire Réelle)

Historique de la production solaire réelle.

```sql
CREATE TABLE solar_production_archive (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    actual_solar_kwh NUMERIC(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 8. battery_state_real (État Batterie Réel)

État de charge réel des batteries (J-1).

```sql
CREATE TABLE battery_state_real (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    state_of_charge_percent NUMERIC(5, 2),
    charge_kwh NUMERIC(10, 3),
    discharge_kwh NUMERIC(10, 3),
    net_battery_kwh NUMERIC(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 9. battery_state_predicted (État Batterie Prédit)

Prédictions de l'état de charge sur 7 jours.

```sql
CREATE TABLE battery_state_predicted (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    predicted_soc_percent NUMERIC(5, 2),
    predicted_charge_kwh NUMERIC(10, 3),
    predicted_discharge_kwh NUMERIC(10, 3),
    predicted_net_battery_kwh NUMERIC(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🤖 Machine Learning - Détails Techniques

### Modèle: RandomForest Regressor

**Fichier:** `src/pipeline/ml/train_energy_model.py`

#### Configuration

```python
RandomForestRegressor(
    n_estimators=500,      # 500 arbres de décision
    max_depth=20,          # Profondeur maximale
    min_samples_split=5,   # Minimum échantillons pour split
    min_samples_leaf=2,    # Minimum échantillons par feuille
    random_state=42,       # Reproductibilité
    n_jobs=-1              # Parallélisation
)
```

#### Features Utilisées

```python
features = [
    'hour',                    # Heure de la journée (0-23)
    'day_of_week',            # Jour de la semaine (0-6)
    'month',                  # Mois (1-12)
    'is_weekend',             # Weekend (0/1)
    'building_id',            # ID unique bâtiment
    'temperature_2m',         # Température °C
    'relative_humidity_2m',   # Humidité %
    'precipitation',          # Précipitations mm
    'cloud_cover',           # Couverture nuageuse %
    'wind_speed_10m',        # Vitesse vent km/h
    'shortwave_radiation',   # Radiation W/m²
]
```

#### Métriques de Performance

```
══════════════════════════════════════════════════════════
MODÈLE RÉ-ENTRAÎNÉ - PRÉCISION EXTRÊME DÉTECTÉE
══════════════════════════════════════════════════════════

MAE                    : 0.149 kW
RMSE                   : 0.285 kW
R²                     : 0.9980

PRÉCISION RÉELLE       : 73.0% des prédictions dans ±0.149 kW
                       → Erreur moyenne de seulement 149 Watts !

══════════════════════════════════════════════════════════
Modèle écrasé et mis à jour :
 → /opt/airflow/models/energy_predictor.pkl
 → models/energy_predictor.pkl
```

#### Entraînement

Le modèle est entraîné sur **278 647 points de données réelles** couvrant:

- 17 bâtiments différents
- 10+ jours d'historique
- Toutes les heures de la journée
- Conditions météo variées

#### Ré-entraînement

```bash
# Commande manuelle
docker exec -it renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model

# Automatique via DAG (à programmer si besoin)
```

Le fichier `models/energy_predictor.pkl` est **écrasé automatiquement** à chaque entraînement.

---

## 🔌 API REST - Documentation Complète

### Base URL

```
http://localhost:8000/api/solar
```

### Endpoints Disponibles

#### 🏠 Energy Consumption

**1. GET /energy-consumption-archive**

Récupère l'historique complet de consommation.

Query Parameters:
- `page` (integer, default: 1)
- `limit` (integer, default: 100, max: 1000)

Response:
```json
{
  "count": 278647,
  "results": [
    {
      "id": 1,
      "building_id": 1,
      "building_name": "Hospital",
      "time_ts": "2025-11-13T10:00:00Z",
      "consumed_energy_kwh": 2.456,
      "created_at": "2025-11-13T10:05:00Z"
    }
  ],
  "page": 1,
  "totalPages": 2787
}
```

**2. GET /energy-consumption-archive/:id**

Récupère un enregistrement spécifique.

**3. GET /energy-consumption-live**

Récupère les données récentes (fenêtre glissante).

**4. GET /energy-consumption-live/:id**

Récupère un enregistrement live spécifique.

#### 🌤️ Weather Data

**5. GET /weather-forecast-hourly**

Prévisions météo 7 jours.

Response:
```json
{
  "count": 168,
  "results": [
    {
      "id": 1,
      "forecast_timestamp": "2025-11-14T00:00:00Z",
      "temperature_2m": 18.5,
      "relative_humidity_2m": 65,
      "precipitation": 0.2,
      "cloud_cover": 40,
      "wind_speed_10m": 12.3,
      "shortwave_radiation": 450.2,
      "direct_radiation": 320.5,
      "diffuse_radiation": 129.7
    }
  ],
  "page": 1,
  "totalPages": 2
}
```

**6. GET /weather-forecast-hourly/:timestamp**

Prévision pour un timestamp spécifique.

**7. GET /weather-archive-hourly**

Historique météo.

**8. GET /weather-archive-hourly/:timestamp**

Archive météo pour un timestamp.

#### ⚡ Predicted Energy (ML)

**9. GET /predicted-energy-consumption**

Prédictions IA 7 jours (2 856 prédictions).

Response:
```json
{
  "count": 2856,
  "results": [
    {
      "id": 1,
      "building_id": 1,
      "building_name": "Hospital",
      "time_ts": "2025-11-14T00:00:00Z",
      "predicted_energy_kwh": 2.398,
      "model_version": "energy_predictor.pkl",
      "created_at": "2025-11-13T00:01:00Z"
    }
  ],
  "page": 1,
  "totalPages": 29
}
```

**10. GET /predicted-energy-consumption/:id**

Prédiction spécifique par ID.

#### ☀️ Solar Production

**11. GET /solar-production-archive**

Production solaire historique.

**12. GET /solar-production-archive/:id**

Production pour un ID spécifique.

**13. GET /predicted-solar-production**

Prédictions solaires 7 jours.

Response:
```json
{
  "count": 168,
  "results": [
    {
      "timestamp": "2025-11-14T08:00:00Z",
      "predicted_solar_kwh": 12.456,
      "shortwave_radiation": 780.5,
      "direct_radiation": 620.3,
      "diffuse_radiation": 160.2
    }
  ]
}
```

**14. GET /predicted-solar-production/:timestamp**

Prédiction solaire pour un timestamp.

#### 🔋 Battery State

**15. GET /battery-state-real**

État réel batterie (historique).

Response:
```json
{
  "count": 240,
  "results": [
    {
      "id": 1,
      "timestamp": "2025-11-13T23:00:00Z",
      "state_of_charge_percent": 85.5,
      "charge_kwh": 15.2,
      "discharge_kwh": 8.3,
      "net_battery_kwh": 6.9
    }
  ]
}
```

**16. GET /battery-state-real/:id**

État réel pour un ID spécifique.

**17. GET /battery-state-predicted**

Prédictions batterie 7 jours.

**18. GET /battery-state-predicted/:id**

Prédiction batterie pour un ID.

**19. GET /battery-state?source=all|real|predicted**

Endpoint unifié pour le dashboard.

Query Parameters:
- `source`: all (default), real, predicted

#### 📊 Summary

**20. GET /summary**

Vue d'ensemble de toutes les tables.

Response:
```json
{
  "tables": {
    "energy_consumption_hourly_archive": 278647,
    "energy_consumption_hourly_live": 240,
    "weather_forecast_hourly": 168,
    "weather_archive_hourly": 1200,
    "predicted_energy_consumption_hourly": 2856,
    "solar_production_archive": 500,
    "predicted_solar_production": 168,
    "battery_state_real": 240,
    "battery_state_predicted": 168
  },
  "timestamp": "2025-11-14T00:00:00Z"
}
```

#### 🏥 Health Check

**21. GET /health**

Vérification santé API.

Response:
```json
{
  "status": "OK",
  "uptime": 3600.5,
  "timestamp": "2025-11-14T00:00:00Z"
}
```

---

## 🎨 Frontend Dashboard - React/Vite

### Technologies

- **React 18** - Framework UI
- **Vite** - Build tool ultra-rapide
- **Tailwind CSS** - Styling utility-first
- **Recharts** - Visualisations graphiques
- **Lucide React** - Icônes modernes
- **Nginx** - Serveur web production

### Pages Disponibles

#### 1. Dashboard (/)
Vue d'ensemble générale avec KPIs principaux.

#### 2. Energy Page (/energy)
- Graphiques consommation réelle vs prédite
- Comparaison 17 bâtiments
- Ligne rouge "AUJOURD'HUI"
- 10 jours passés (bleu) + 7 jours futurs (orange)

#### 3. Solar Page (/solar)
- Production solaire historique
- Prédictions 7 jours
- Corrélation avec radiation solaire

#### 4. Battery Page (/battery)
- État de charge (SOC %)
- Charge/Décharge (kWh)
- Prédictions 7 jours
- Visualisation barre verticale

#### 5. Weather Page (/weather)
- Prévisions 7 jours
- Température, humidité, précipitations
- Radiation solaire (shortwave, direct, diffuse)

#### 6. Overviews (/overviews)
Vue consolidée multi-métriques.

### Configuration API

Fichier: `frontend/.env` (ou variables d'environnement Docker)

```bash
VITE_API_URL=http://localhost:8000
```

Le frontend appelle automatiquement:

```javascript
fetch(`${import.meta.env.VITE_API_URL}/api/solar/predicted-energy-consumption`)
```

---

## 🚀 Démarrage Complet - Guide Pas à Pas

### Prérequis

- Docker >= 24.0
- Docker Compose >= 2.20
- Git
- 8 GB RAM minimum (recommandé 16 GB)
- 20 GB espace disque

### Installation Depuis Zéro

#### Étape 1: Cloner le Projet

```bash
git clone https://github.com/Bjibjihamza/renewstation-huawei-cloud.git
cd renewstation-huawei-cloud
```

#### Étape 2: Configuration Variables d'Environnement

```bash
# Créer le fichier .env à la racine
cat > .env << EOF
# PostgreSQL
GAUSSDB_DB_SILVER=silver
GAUSSDB_USER=postgres
GAUSSDB_PASSWORD=postgres

# Airflow
AIRFLOW__CORE__FERNET_KEY=sAsfiDM_fXGu_TD6n2XM5ZiOaO2ul-1UR4lHx4k6u1k=
EOF
```

```bash
# Créer le fichier api/.env
cat > api/.env << EOF
NODE_ENV=production
DB_HOST=postgres
DB_PORT=5432
DB_NAME=silver
DB_USER=postgres
DB_PASSWORD=postgres
PORT=8000
EOF
```

#### Étape 3: Lancer la Stack Complète

```bash
# Build & start tous les services
docker compose up -d --build

# Vérifier les logs
docker compose logs -f
```

**Temps d'attente:** ~2-3 minutes pour l'initialisation complète.

#### Étape 4: Initialiser le Schéma Silver

```bash
# Attendre que PostgreSQL soit prêt
docker exec -it renewstation-postgres pg_isready -U postgres

# Créer les tables
docker exec -i renewstation-postgres psql -U postgres -d silver < databases/silver.sql
```

#### Étape 5: Charger les Données Initiales

```bash
# Lancer le DAG d'initialisation (run once)
docker exec -it renewstation-airflow-scheduler \
  airflow dags trigger initialization_pipeline

# Attendre ~5 minutes, puis vérifier
docker exec -it renewstation-postgres psql -U postgres -d silver -c \
  "SELECT COUNT(*) FROM energy_consumption_hourly_archive;"
```

**Résultat attendu:** ~278 647 lignes

#### Étape 6: Entraîner le Modèle ML

```bash
# Entraînement initial (obligatoire)
docker exec -it renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model
```

**Output attendu:**
```
══════════════════════════════════════════════════════════
MODÈLE RÉ-ENTRAÎNÉ - PRÉCISION EXTRÊME DÉTECTÉE
══════════════════════════════════════════════════════════
MAE: 0.149 kW | RMSE: 0.285 kW | R²: 0.9980
✅ Modèle sauvegardé: models/energy_predictor.pkl
```

#### Étape 7: Lancer le Pipeline Quotidien

```bash
# Génère toutes les prédictions 7 jours
docker exec -it renewstation-airflow-scheduler \
  airflow dags trigger daily_prediction_pipeline

# Vérifier le chargement des prédictions
docker exec -it renewstation-postgres psql -U postgres -d silver -c \
  "SELECT COUNT(*) FROM predicted_energy_consumption_hourly;"
```

**Résultat attendu:** 2 856 prédictions (17 bâtiments × 168 heures)

#### Étape 8: Accéder aux Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost | — |
| **API Swagger (root)** | http://localhost:8000 | — |
| **Airflow UI** | http://localhost:8080 | admin / admin |
| **PostgreSQL** | localhost:5432 | postgres / postgres |

### Vérification de Santé

```bash
# Santé API
curl http://localhost:8000/health

# Santé Frontend
curl http://localhost/health

# Santé Airflow
docker exec renewstation-airflow-scheduler airflow jobs check --job-type SchedulerJob

# Vérification complète base de données
docker exec -it renewstation-postgres psql -U postgres -d silver -c "
SELECT 
  table_name,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns,
  pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;
"
```

---

## 🔄 Pipelines Airflow - DAGs Détaillés

### 1. initialization_pipeline.py (Run Once)

**Description:** Pipeline d'initialisation pour setup initial des données.

**Fréquence:** Manuelle (une seule fois au démarrage)

**Tasks:**
- `check_database_connection` - Vérifie connexion PostgreSQL
- `create_silver_schema` - Crée les tables si inexistantes
- `generate_historical_energy` - Génère données historiques (10 jours)
- `load_historical_energy` - Charge dans energy_consumption_hourly_archive
- `generate_weather_archive` - Récupère météo historique
- `load_weather_archive` - Charge dans weather_archive_hourly
- `verify_initialization` - Vérifie counts

**Commande:**
```bash
docker exec -it renewstation-airflow-scheduler \
  airflow dags trigger initialization_pipeline
```

**Durée:** ~5-8 minutes

---

### 2. daily_prediction_pipeline.py (Quotidien 00:00)

**Description:** Pipeline principal de prédiction, s'exécute chaque jour à minuit.

**Fréquence:** `@daily` (00:00 UTC)

**Tasks (ordre d'exécution):**

#### Phase 1: Archivage (00:00 - 00:05)
```
archive_yesterday_task
  ↓
  Archive les données J-1 depuis live → archive
  Source: energy_consumption_hourly_live
  Destination: energy_consumption_hourly_archive
```

#### Phase 2: Génération Données Réelles (00:05 - 00:10)
```
generate_energy_consumption_task
  ↓
  Génère consommation réelle pour aujourd'hui (24h)
  Destination: energy_consumption_hourly_live

generate_battery_real_task
  ↓
  Calcule état batterie réel (J-1)
  Destination: battery_state_real
```

#### Phase 3: Météo (00:10 - 00:15)
```
generate_weather_current_task
  ↓
  Récupère météo actuelle Open-Meteo
  Destination: weather_archive_hourly

generate_weather_forecast_7d_task
  ↓
  Récupère prévisions 7 jours
  Destination: weather_forecast_hourly
```

#### Phase 4: Prédictions ML (00:15 - 00:20)
```
generate_energy_prediction_7d_task
  ↓
  Utilise energy_predictor.pkl
  Génère 2 856 prédictions (17 buildings × 168h)
  Destination: predicted_energy_consumption_hourly
```

#### Phase 5: Prédictions Solaire & Batterie (00:20 - 00:25)
```
generate_solar_prediction_7d_task
  ↓
  Prédictions production solaire 7j
  Destination: predicted_solar_production

generate_battery_prediction_7d_task
  ↓
  Prédictions état batterie 7j
  Destination: battery_state_predicted
```

#### Phase 6: Chargement en Base (00:25 - 00:30)
```
load_energy_consumption_task → charge energy live
load_predicted_energy_task → charge predictions ML
load_solar_prediction_task → charge solar predictions
load_battery_real_task → charge battery real
load_battery_predicted_task → charge battery predictions
load_weather_current_task → charge weather archive
load_weather_forecast_7d_task → charge weather forecast
```

#### Phase 7: Vérification Finale
```
verify_predictions_task
  ↓
  Vérifie counts et intégrité données
  Log final dans Airflow UI
```

**Visualisation DAG:**
```
archive_yesterday
    ↓
┌───┴───┬────────────┬────────────┐
│       │            │            │
energy  battery   weather      weather
gen     real_gen  current_gen  forecast_7d
│       │            │            │
└───┬───┴────────────┴────────────┘
    ↓
energy_prediction_7d (ML)
    ↓
┌───┴───┬────────────┐
│       │            │
solar   battery     
pred    pred        
│       │           
└───┬───┴───────────┘
    ↓
load_all_data_parallel
    ↓
verify_predictions
```

**Logs en temps réel:**
```bash
# Suivre l'exécution du DAG
docker exec -it renewstation-airflow-scheduler \
  airflow dags list-runs -d daily_prediction_pipeline --state running

# Logs détaillés d'une task
docker exec -it renewstation-airflow-scheduler \
  airflow tasks logs daily_prediction_pipeline generate_energy_prediction_7d_task 2025-11-14
```

---

## 📊 Monitoring & Observabilité

### Métriques Clés à Surveiller

#### 1. Performance ML

```sql
-- Vérifier précision des prédictions (comparaison réel vs prédit)
SELECT 
  DATE_TRUNC('day', a.time_ts) as day,
  AVG(ABS(a.consumed_energy_kwh - p.predicted_energy_kwh)) as mae,
  COUNT(*) as predictions_count
FROM energy_consumption_hourly_archive a
JOIN predicted_energy_consumption_hourly p 
  ON a.building_id = p.building_id 
  AND a.time_ts = p.time_ts
WHERE a.time_ts >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('day', a.time_ts)
ORDER BY day DESC;
```

#### 2. État des Données

```sql
-- Dashboard counts
SELECT 
  'Archive Energy' as table_name, 
  COUNT(*) as count,
  MAX(time_ts) as latest_timestamp
FROM energy_consumption_hourly_archive
UNION ALL
SELECT 
  'Live Energy', 
  COUNT(*),
  MAX(time_ts)
FROM energy_consumption_hourly_live
UNION ALL
SELECT 
  'Predicted Energy', 
  COUNT(*),
  MAX(time_ts)
FROM predicted_energy_consumption_hourly
UNION ALL
SELECT 
  'Weather Forecast', 
  COUNT(*),
  MAX(forecast_timestamp)
FROM weather_forecast_hourly
UNION ALL
SELECT 
  'Solar Predicted', 
  COUNT(*),
  MAX(timestamp)
FROM predicted_solar_production
UNION ALL
SELECT 
  'Battery Real', 
  COUNT(*),
  MAX(timestamp)
FROM battery_state_real
UNION ALL
SELECT 
  'Battery Predicted', 
  COUNT(*),
  MAX(timestamp)
FROM battery_state_predicted;
```

#### 3. Performance API

```bash
# Temps de réponse endpoint predictions
time curl -s http://localhost:8000/api/solar/predicted-energy-consumption?limit=100 > /dev/null

# Nombre de requêtes par minute (logs Nginx)
docker exec renewstation-frontend tail -f /var/log/nginx/access.log | \
  awk '{print $4}' | cut -d: -f2 | uniq -c
```

#### 4. Santé Services

```bash
# Script de monitoring complet
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== RenewStation Health Check ==="
echo ""
echo "1. Docker Services:"
docker compose ps
echo ""
echo "2. API Health:"
curl -s http://localhost:8000/health | jq
echo ""
echo "3. Frontend Health:"
curl -s http://localhost/health
echo ""
echo "4. Database Connection:"
docker exec renewstation-postgres pg_isready -U postgres
echo ""
echo "5. Airflow DAGs Status:"
docker exec renewstation-airflow-scheduler airflow dags list | grep daily_prediction_pipeline
echo ""
echo "6. Recent Predictions Count:"
docker exec renewstation-postgres psql -U postgres -d silver -t -c \
  "SELECT COUNT(*) FROM predicted_energy_consumption_hourly WHERE created_at >= NOW() - INTERVAL '1 day';"
echo ""
echo "7. Model File:"
ls -lh models/energy_predictor.pkl
EOF

chmod +x monitor.sh
./monitor.sh
```

### Alertes Recommandées

**Alertes Critiques:**
- DAG `daily_prediction_pipeline` failed
- PostgreSQL down
- API returning 500 errors
- Model file `energy_predictor.pkl` missing

**Alertes Warning:**
- Predictions count < 2800 (attendu: 2856)
- MAE > 0.200 kW (dégradation modèle)
- Airflow task retry > 3
- Disk usage > 80%

---

## 🛠️ Maintenance & Opérations

### Tâches Quotidiennes

#### 1. Vérifier Exécution DAG

```bash
# Check si le DAG s'est bien exécuté cette nuit
docker exec renewstation-airflow-scheduler \
  airflow dags list-runs -d daily_prediction_pipeline --state success | head -5
```

#### 2. Vérifier Fraîcheur Données

```sql
-- Les prédictions doivent être < 24h
SELECT 
  MAX(created_at) as latest_prediction,
  NOW() - MAX(created_at) as age
FROM predicted_energy_consumption_hourly;
```

**Attendu:** age < 24 hours

### Tâches Hebdomadaires

#### 1. Ré-entraîner le Modèle ML

```bash
# Tous les lundis par exemple
docker exec -it renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model

# Vérifier nouvelle MAE
# Si MAE < 0.149 kW → excellent
# Si MAE > 0.200 kW → investiguer
```

#### 2. Nettoyer Logs Airflow

```bash
# Garder seulement 30 jours de logs
docker exec renewstation-airflow-scheduler \
  find /opt/airflow/logs -type f -mtime +30 -delete
```

#### 3. Vacuum PostgreSQL

```sql
-- Optimiser les tables
VACUUM ANALYZE energy_consumption_hourly_archive;
VACUUM ANALYZE predicted_energy_consumption_hourly;
VACUUM ANALYZE weather_forecast_hourly;
```

### Tâches Mensuelles

#### 1. Backup Base de Données

```bash
# Backup complet
docker exec renewstation-postgres pg_dump -U postgres silver | \
  gzip > backup_silver_$(date +%Y%m%d).sql.gz

# Restauration
gunzip < backup_silver_20251114.sql.gz | \
  docker exec -i renewstation-postgres psql -U postgres silver
```

#### 2. Analyser Croissance Données

```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
  pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
```

#### 3. Audit Sécurité

```bash
# Vérifier versions Docker images
docker images | grep renewstation

# Scanner vulnérabilités
docker scout cves renewstation-api
docker scout cves renewstation-frontend
```

### Procédures d'Urgence

#### Situation 1: API Down

```bash
# 1. Check logs
docker logs renewstation-api --tail 100

# 2. Restart service
docker compose restart api

# 3. Verify health
curl http://localhost:8000/health
```

#### Situation 2: Prédictions Manquantes

```bash
# 1. Vérifier si le modèle existe
ls -lh models/energy_predictor.pkl

# 2. Re-train si manquant
docker exec -it renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model

# 3. Re-run DAG
docker exec -it renewstation-airflow-scheduler \
  airflow dags trigger daily_prediction_pipeline
```

#### Situation 3: PostgreSQL Corruption

```bash
# 1. Stop services
docker compose stop

# 2. Backup volumes
docker run --rm -v renewstation-huawei-cloud_postgres_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# 3. Restore ou recréer
docker compose down -v
docker compose up -d
# Re-run initialization_pipeline
```

#### Situation 4: Disque Plein

```bash
# 1. Identifier gros fichiers
du -h --max-depth=2 | sort -hr | head -20

# 2. Nettoyer logs
rm -rf logs/dag_processor_manager/*
rm -rf logs/scheduler/*

# 3. Nettoyer Docker
docker system prune -a --volumes
```

---

## 🚢 Déploiement Production Huawei Cloud

### Architecture Cloud Recommandée

```
┌─────────────────────────────────────────────────────────────┐
│                    Huawei Cloud ECS                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ELB (Load Balancer)                     │  │
│  │              Port 80/443 (SSL)                       │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │         Frontend (Nginx + React)                     │  │
│  │         Container: renewstation-frontend             │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │         API Backend (Node.js)                        │  │
│  │         Container: renewstation-api                  │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │    PostgreSQL (RDS ou Container)                     │  │
│  │    Database: silver                                  │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │         Airflow (Scheduler + Webserver)              │  │
│  │         ML Pipeline Orchestration                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         OBS (Object Storage)                         │  │
│  │         - ML Models                                  │  │
│  │         - Backups                                    │  │
│  │         - Logs Archive                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Serveur ECS

**Spécifications Recommandées:**
- Type: General Purpose (s6)
- vCPUs: 4
- RAM: 16 GB
- Disque: 100 GB SSD
- OS: Ubuntu 22.04 LTS
- Région: Proche utilisateurs (ex: Europe-Paris)

### Étapes de Déploiement

#### 1. Préparation Serveur

```bash
# Connexion SSH
ssh root@<ECS_PUBLIC_IP>

# Mise à jour système
apt update && apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installation Docker Compose
apt install docker-compose-plugin -y

# Vérification
docker --version
docker compose version
```

#### 2. Configuration Firewall & Sécurité

```bash
# Installer UFW
apt install ufw -y

# Règles firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Désactiver accès direct PostgreSQL/Airflow depuis internet
# (accès uniquement via localhost)
```

**Configuration Huawei Security Group:**
- Inbound: 22, 80, 443
- Outbound: All
- Ne PAS ouvrir 5432, 8080, 8000 publiquement

#### 3. Cloner & Configurer Projet

```bash
# Créer utilisateur dédié
useradd -m -s /bin/bash renewstation
usermod -aG docker renewstation
su - renewstation

# Cloner projet
cd /home/renewstation
git clone https://github.com/Bjibjihamza/renewstation-huawei-cloud.git
cd renewstation-huawei-cloud

# Configuration production
cat > .env << EOF
GAUSSDB_DB_SILVER=silver
GAUSSDB_USER=renewstation_user
GAUSSDB_PASSWORD=$(openssl rand -base64 32)
AIRFLOW__CORE__FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
EOF

# Sécuriser
chmod 600 .env

# API config
cat > api/.env << EOF
NODE_ENV=production
DB_HOST=postgres
DB_PORT=5432
DB_NAME=silver
DB_USER=renewstation_user
DB_PASSWORD=$(grep GAUSSDB_PASSWORD .env | cut -d= -f2)
PORT=8000
EOF
```

#### 4. SSL/TLS avec Let's Encrypt

```bash
# Installer Certbot
apt install certbot python3-certbot-nginx -y

# Obtenir certificat
certbot --nginx -d renewstation.votre-domaine.com

# Auto-renouvellement
systemctl enable certbot.timer
```

**Modifier `frontend/nginx.conf` pour SSL:**

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name renewstation.votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/renewstation.votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/renewstation.votre-domaine.com/privkey.pem;

    # Redirect HTTP to HTTPS
    if ($scheme = http) {
        return 301 https://$server_name$request_uri;
    }

    # ... reste de la config
}
```

#### 5. Démarrage Production

```bash
# Build & start
docker compose up -d --build

# Attendre initialisation
sleep 120

# Créer schéma
docker exec -i renewstation-postgres psql -U renewstation_user -d silver < databases/silver.sql

# Initialization pipeline
docker exec renewstation-airflow-scheduler \
  airflow dags trigger initialization_pipeline

# Attendre fin (~8 min)
docker exec renewstation-airflow-scheduler \
  airflow dags list-runs -d initialization_pipeline

# Train modèle
docker exec renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model

# Premier pipeline quotidien
docker exec renewstation-airflow-scheduler \
  airflow dags trigger daily_prediction_pipeline
```

#### 6. Monitoring Production

**Installer Prometheus + Grafana (optionnel):**

```bash
# Ajouter au docker-compose.yml
# ... prometheus, grafana, node-exporter, postgres-exporter
```

**Setup Logs Centralisés:**

```bash
# Logrotate pour logs Docker
cat > /etc/logrotate.d/renewstation << EOF
/home/renewstation/renewstation-huawei-cloud/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

#### 7. Backup Automatisé

```bash
# Script backup quotidien
cat > /home/renewstation/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/renewstation/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec renewstation-postgres pg_dump -U renewstation_user silver | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup ML model
cp renewstation-huawei-cloud/models/energy_predictor.pkl \
  $BACKUP_DIR/model_$DATE.pkl

# Upload vers Huawei OBS (si configuré)
# obsutil cp $BACKUP_DIR/db_$DATE.sql.gz obs://renewstation-backups/

# Garder seulement 30 derniers backups
ls -t $BACKUP_DIR/db_*.sql.gz | tail -n +31 | xargs rm -f
ls -t $BACKUP_DIR/model_*.pkl | tail -n +31 | xargs rm -f
EOF

chmod +x /home/renewstation/backup.sh

# Cron quotidien 02:00
crontab -e
# Ajouter:
# 0 2 * * * /home/renewstation/backup.sh >> /home/renewstation/backup.log 2>&1
```

#### 8. Systemd Service (auto-restart)

```bash
cat > /etc/systemd/system/renewstation.service << EOF
[Unit]
Description=RenewStation Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/renewstation/renewstation-huawei-cloud
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=renewstation

[Install]
WantedBy=multi-user.target
EOF

systemctl enable renewstation
systemctl start renewstation
```

---

## 🧪 Tests & Validation

### Tests Unitaires API

```bash
# Installer Jest (si pas déjà fait)
cd api
npm install --save-dev jest supertest

# Créer tests
mkdir -p tests
cat > tests/api.test.js << 'EOF'
const request = require('supertest');
const app = require('../src/server');

describe('API Endpoints', () => {
  test('GET /health should return 200', async () => {
    const response = await request(app).get('/health');
    expect(response.statusCode).toBe(200);
    expect(response.body.status).toBe('OK');
  });

  test('GET /api/solar/summary should return counts', async () => {
    const response = await request(app).get('/api/solar/summary');
    expect(response.statusCode).toBe(200);
    expect(response.body.tables).toHaveProperty('predicted_energy_consumption_hourly');
  });
});
EOF

# Run tests
npm test
```

### Tests Integration Pipeline

```bash
# Test complet du pipeline
cat > tests/test_pipeline.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Testing RenewStation Pipeline ==="

# 1. Test database connection
echo "1. Testing database..."
docker exec renewstation-postgres psql -U postgres -d silver -c "SELECT 1;"

# 2. Test data generation
echo "2. Testing energy generation..."
docker exec renewstation-airflow-scheduler \
  python -c "from src.pipeline.generator.energy_cons_generator import generate_energy_consumption; print(len(generate_energy_consumption()))"

# 3. Test ML model
echo "3. Testing ML model..."
docker exec renewstation-airflow-scheduler \
  python -c "import pickle; model=pickle.load(open('/opt/airflow/models/energy_predictor.pkl','rb')); print(type(model))"

# 4. Test API endpoints
echo "4. Testing API..."
curl -f http://localhost:8000/health
curl -f http://localhost:8000/api/solar/summary

# 5. Test frontend
echo "5. Testing frontend..."
curl -f http://localhost/ > /dev/null

echo "✅ All tests passed!"
EOF

chmod +x tests/test_pipeline.sh
./tests/test_pipeline.sh
```

### Validation Prédictions ML

```python
# Notebook: notebooks/ML_VERIFICATION_FINAL.ipynb
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="silver",
    user="postgres",
    password="postgres"
)

# Load real vs predicted
query = """
SELECT 
    a.building_name,
    a.time_ts,
    a.consumed_energy_kwh as real,
    p.predicted_energy_kwh as predicted
FROM energy_consumption_hourly_archive a
JOIN predicted_energy_consumption_hourly p 
  ON a.building_id = p.building_id 
  AND a.time_ts = p.time_ts
WHERE a.time_ts >= NOW() - INTERVAL '7 days'
ORDER BY a.building_name, a.time_ts;
"""

df = pd.read_sql(query, conn)
df['error'] = abs(df['real'] - df['predicted'])

# Calculate metrics
mae = df['error'].mean()
rmse = (df['error'] ** 2).mean() ** 0.5

print(f"MAE: {mae:.3f} kW")
print(f"RMSE: {rmse:.3f} kW")

# Plot per building
for building in df['building_name'].unique():
    building_df = df[df['building_name'] == building]
    plt.figure(figsize=(12, 4))
    plt.plot(building_df['time_ts'], building_df['real'], label='Real', color='blue')
    plt.plot(building_df['time_ts'], building_df['predicted'], label='Predicted', color='orange')
    plt.title(f'{building} - Real vs Predicted')
    plt.legend()
    plt.show()
```

---

## 📚 Documentation Développeurs

### Ajouter un Nouveau Bâtiment

**1. Modifier `src/pipeline/generator/energy_cons_generator.py`:**

```python
BUILDINGS = [
    # ... existants
    {"id": 18, "name": "NewBuilding", "base_load": 2.5, "peak_multiplier": 1.8}
]
```

**2. Re-générer données historiques:**

```bash
docker exec renewstation-airflow-scheduler \
  python -c "from src.pipeline.generator.energy_cons_generator import generate_energy_consumption; generate_energy_consumption()"
```

**3. Re-train modèle:**

```bash
docker exec renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model
```

### Ajouter une Nouvelle Feature ML

**1. Modifier `src/pipeline/ml/train_energy_model.py`:**

```python
# Ajouter feature
df['new_feature'] = df['temperature_2m'] * df['humidity']

# Ajouter dans features list
features = [
    # ... existants
    'new_feature'
]
```

**2. Re-train:**

```bash
docker exec renewstation-airflow-scheduler \
  python -m src.pipeline.ml.train_energy_model
```

### Créer un Nouvel Endpoint API

**1. Ajouter controller dans `api/src/controllers/solar.controller.js`:**

```javascript
exports.getCustomMetric = async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM custom_table');
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch custom metric' });
  }
};
```

**2. Ajouter route dans `api/src/routes/solar.routes.js`:**

```javascript
router.get('/custom-metric', solarController.getCustomMetric);
```

**3. Documenter dans README**

### Créer une Nouvelle Page Dashboard

**1. Créer composant `frontend/src/Pages/CustomPage.jsx`:**

```jsx
import React, { useState, useEffect } from 'react';

function CustomPage() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/solar/custom-metric`)
      .then(res => res.json())
      .then(setData);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Custom Metric</h1>
      {/* Votre visualisation */}
    </div>
  );
}

export default CustomPage;
```

**2. Ajouter route dans `frontend/src/App.jsx`:**

```jsx
import CustomPage from './Pages/CustomPage';

function App() {
  return (
    <Router>
      <Routes>
        {/* ... routes existantes */}
        <Route path="/custom" element={<CustomPage />} />
      </Routes>
    </Router>
  );
}
```

---

## 🔒 Sécurité & Best Practices

### Checklist Sécurité Production

- [ ] Changer tous les mots de passe par défaut
- [ ] Utiliser des secrets externes (Vault, AWS Secrets Manager)
- [ ] Activer SSL/TLS (Let's Encrypt)
- [ ] Firewall restrictif (UFW ou Security Groups)
- [ ] Ne PAS exposer PostgreSQL/Airflow publiquement
- [ ] Limiter rate API (nginx rate limiting)
- [ ] Logs centralisés avec rotation
- [ ] Backups automatisés quotidiens
- [ ] Monitoring avec alertes
- [ ] Updates régulières Docker images
- [ ] Scanner vulnérabilités (Trivy, Snyk)

### Variables Sensibles

**NE JAMAIS commit dans Git:**
- `.env`
- `api/.env`
- `*.pkl` (modèles ML si propriétaires)
- Certificats SSL
- Backups

**Utiliser `.gitignore`:**

```
.env
api/.env
*.pkl
backups/
logs/
*.pem
*.key
```

---



**Dernière mise à jour:** Novembre 2025  
**Version:** 3.0.0