# ============================================================================
#  RenewStation – Airflow Cloud/ECS Dockerfile
# ============================================================================

FROM apache/airflow:2.10.2-python3.11

# On passe root pour installer les libs système
USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3-dev \
        libpq-dev \
        git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Retour à l'utilisateur airflow
USER airflow

# Upgrade pip & outils Python
RUN pip install --upgrade pip wheel setuptools

# Installer les dépendances Python des DAGs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Répertoire de travail par défaut
WORKDIR /opt/airflow
