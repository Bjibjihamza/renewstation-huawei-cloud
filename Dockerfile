# Utiliser l'image officielle Airflow comme base
FROM apache/airflow:2.10.2

# Passer en mode root pour installer les packages système
USER root

# Installer les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Repasser en utilisateur airflow
USER airflow

# Installer les dépendances Python
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    requests==2.31.0 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0

# Le reste est géré par docker-compose (volumes, env vars, etc.)