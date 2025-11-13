# 📊 Pipeline de Données - RenewStation

## 🎯 Vue d'ensemble

Le projet RenewStation est une plateforme qui gère la collecte, la génération, et la mise à jour des données météorologiques et énergétiques. Ce pipeline automatisé récupère les données de consommation d'énergie et de prévisions météorologiques en temps réel, et utilise des algorithmes pour prédire la production énergétique et gérer les batteries associées.

## 🛠️ Architecture du Pipeline

```
┌────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE DU PIPELINE                        │
└────────────────────────────────────────────────────────────────────┘

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
├── dags/                             # DAGs Airflow pour orchestrer les pipelines
│   ├── weather_energy_dag.py          # DAG pour la météo et la consommation énergétique
│   └── initialization_pipeline.py    # Pipeline d'initialisation
│
├── src/
│   └── pipeline/
│       ├── generator/                 # Génération des données météo et énergétiques
│       │   ├── weather_forecasting.py  # Historique et prévisions météo
│       │   ├── energy_cons_generator.py # Génération de la consommation énergétique
│       │   └── generate_energy_6h_forecast.py # Prévisions énergétiques 6h
│       └── load/                      # Chargement dans la base de données
│           ├── weather_loader.py      # UPSERT des données météo
│           └── energy_loader.py       # UPSERT des données énergétiques
│
├── databases/                        # Schémas SQL pour les données (bronze, silver, gold)
│   ├── bronze.sql                    # Schéma des données brutes
│   ├── silver.sql                    # Schéma des tables principales
│   └── gold.sql                      # Schéma des agrégations futures
│
├── data/                             # Fichiers de données (CSV, logs)
│   └── energy_consumption.csv        # Export des données énergétiques
│
├── frontend/                         # Code Frontend React
│   ├── src/
│   │   ├── components/               # Composants UI de l'application
│   │   ├── Pages/                    # Pages principales (Dashboard, Battery, etc.)
│   │   └── App.jsx                   # Point d'entrée de l'application
│   ├── public/                       # Fichiers publics (index.html, etc.)
│   └── Dockerfile                    # Dockerfile pour le Frontend
│
├── api/                              # Backend API (Node.js)
│   ├── src/
│   │   ├── config/                   # Configuration API
│   │   ├── controllers/              # Contrôleurs d'API
│   │   └── routes/                   # Routes API
│   ├── Dockerfile                    # Dockerfile pour l'API
│   └── package.json                  # Dépendances du Backend
│
├── logs/                             # Logs Airflow
├── notebooks/                        # Jupyter Notebooks pour l'analyse
├── .gitignore                        # Fichiers à ignorer dans Git
├── .env                               # Variables d'environnement
├── docker-compose.yml                # Configuration Docker Compose
└── README.md                         # Ce fichier README
```

## 🚀 Installation et Démarrage

### 1️⃣ Cloner le Projet

```bash
# Cloner le dépôt
git clone https://github.com/your-repo/renewstation-huawei-cloud.git
cd renewstation-huawei-cloud
```

### 2️⃣ Configurer les Variables d'Environnement

Copiez le fichier `.env.example` et renommez-le en `.env`. Ensuite, modifiez les paramètres de connexion à la base de données PostgreSQL.

```env
GAUSSDB_HOST=postgres
GAUSSDB_PORT=5432
GAUSSDB_DB_SILVER=silver
GAUSSDB_USER=postgres
GAUSSDB_PASSWORD=your_secure_password
GAUSSDB_SSLMODE=disable
```

### 3️⃣ Lancer les Services Docker

```bash
# Lancer les conteneurs Docker
docker-compose up -d --build
# Vérifier que les services sont actifs
docker ps
# Vous devriez voir: postgres, airflow-webserver, airflow-scheduler
```

### 4️⃣ Initialiser la Base de Données

```bash
# Se connecter au conteneur PostgreSQL
docker exec -it renewstation-postgres psql -U postgres

# Créer la base de données Silver
CREATE DATABASE silver;

# Se connecter à la base Silver
\c silver

# Exécuter le script de création des tables
\i /path/to/databases/silver.sql
```

### 5️⃣ Accéder à l'Interface Airflow

Une fois que les services sont en cours d'exécution, vous pouvez accéder à l'interface d'Airflow via :

- **URL** : http://localhost:8080
- **Utilisateur** : airflow
- **Mot de passe** : airflow

## ⚙️ Utilisation du Pipeline

### 🎯 Première Exécution (Initial Load)

1. **Activer le DAG**  
   Dans l'interface Airflow :  
   - Allez dans **DAGs**  
   - Trouvez **unified_weather_energy_pipeline**  
   - Activez le toggle (bouton ON/OFF)

2. **Déclencher le DAG Manuellement**  
   - Cliquez sur le bouton ▶️ **Trigger DAG**  
   - Le pipeline détectera automatiquement qu'il s'agit de la première exécution  
   - **Durée estimée** : 45-60 minutes

3. **Étapes exécutées (Première Exécution)**

   ```
   check_initialization_mode
     └─► initial_load
          ├─► initial_weather_history       (~10-20 min)
          ├─► initial_energy_history        (~20-30 min)
          ├─► initial_weather_forecast_6h   (~1-2 min)
          ├─► initial_energy_forecast_6h    (~2-3 min)
          └─► mark_system_initialized       (~1 sec)
   ```

4. **Vérification du Chargement**

   ```sql
   -- Vérifier les données météo historiques
   SELECT COUNT(*) as total_heures, COUNT(DISTINCT DATE(forecast_timestamp)) as total_jours
   FROM weather_forecast_hourly;

   -- Vérifier la consommation d'énergie
   SELECT building, COUNT(*) as heures, ROUND(AVG(use_kw), 2) as consommation_moyenne_kw
   FROM energy_consumption_hourly
   GROUP BY building;
   ```

### 🔄 Exécutions Automatiques (Updates 6h)

Après la première exécution, le DAG s'exécute automatiquement toutes les 6 heures.  
**Schedule** : `0 */6 * * *`  

**Étapes exécutées** :

```
check_initialization_mode
  └─► regular_update
       ├─► regular_weather_update_6h
       └─► regular_energy_update_6h
```

**Durée totale update** : ~2-3 minutes

## 🏗️ Architecture Détaillée

### 📊 Tables de Données

1. **weather_forecast_hourly (Prévisions Météo)**  
   Données de prévisions météo à l'heure avec des informations telles que la température, l'humidité, la radiation solaire, etc.

2. **energy_consumption_hourly (Consommation d'Énergie)**  
   Données sur la consommation énergétique horaire par bâtiment avec des informations telles que la température extérieure, l'éclairage, l'HVAC, etc.

3. **Solar and Battery Data**  
   Tables pour stocker la production d'énergie solaire et l'état de la batterie avec des prévisions et des données réelles.

### Variables d'Environnement (Fichier `.env`)

```env
# Variables de connexion à la base de données
GAUSSDB_HOST=postgres
GAUSSDB_PORT=5432
GAUSSDB_USER=postgres
GAUSSDB_PASSWORD=your_secure_password
GAUSSDB_DB_SILVER=silver
GAUSSDB_SSLMODE=disable
```

## 🧰 Monitoring et Vérification

### Logs Airflow

- **Localisation des logs** : `/logs/`
- **Commande pour afficher les logs en temps réel** :

  ```bash
  docker logs -f renewstation-airflow-scheduler
  ```