# Dockerfile
# =============================================================================
#  RenewStation – Airflow Production Dockerfile
# =============================================================================
FROM apache/airflow:2.10.2-python3.11

# Switch to root for system packages
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

# Back to airflow user
USER airflow

# Upgrade pip once
RUN pip install --upgrade pip wheel setuptools

# Copy and install Python requirements (best caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /opt/airflow

# Default entrypoint stays (used by docker-compose)