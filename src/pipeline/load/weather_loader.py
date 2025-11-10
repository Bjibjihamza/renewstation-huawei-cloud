# src/pipeline/load/weather_loader.py

import os
from io import StringIO

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Charge les variables d'environnement depuis .env à la racine
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()

DB_HOST = os.getenv("GAUSSDB_HOST")
DB_PORT = int(os.getenv("GAUSSDB_PORT", "8000"))
DB_NAME = os.getenv("GAUSSDB_DB_SILVER", "silver")
DB_USER = os.getenv("GAUSSDB_USER")
DB_PASSWORD = os.getenv("GAUSSDB_PASSWORD")
DB_SSLMODE = os.getenv("GAUSSDB_SSLMODE", "require")


def get_db_connection():
    """Ouvre une connexion à GaussDB (base SILVER)."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=DB_SSLMODE,
    )


def load_weather_forecast_to_db(df: pd.DataFrame):
    """
    Charge le DataFrame 'weather_forecast' dans la table
    silver.weather_forecast_hourly via COPY FROM STDIN.
    """
    # 1) Renommer les colonnes pour matcher les colonnes SQL
    df_db = df.rename(columns={
        'Date': 'forecast_date',
        'Heure': 'forecast_time',
        'Temperature (°C)': 'temperature_c',
        'Humidité (%)': 'humidity_pct',
        'Précipitation (mm)': 'precipitation_mm',
        'Probabilité Pluie (%)': 'precipitation_probability_pct',
        'Conditions': 'weather_conditions',
        'Vitesse Vent (km/h)': 'wind_speed_kmh',
        'Direction Vent (°)': 'wind_direction_deg',
        'Pression (hPa)': 'pressure_hpa',
        'Couverture Nuageuse (%)': 'cloud_cover_pct'
    })

    # 2) Créer le timestamp combiné
    df_db['forecast_timestamp'] = pd.to_datetime(
        df_db['forecast_date'] + ' ' + df_db['forecast_time']
    )

    # 3) Sélectionner les colonnes dans l'ordre de la table
    cols = [
        'forecast_timestamp',
        'forecast_date',
        'forecast_time',
        'temperature_c',
        'humidity_pct',
        'precipitation_mm',
        'precipitation_probability_pct',
        'weather_conditions',
        'wind_speed_kmh',
        'wind_direction_deg',
        'pressure_hpa',
        'cloud_cover_pct'
    ]
    df_db = df_db[cols]

    # 4) Convertir en CSV en mémoire (sans header)
    buffer = StringIO()
    df_db.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    # 5) COPY vers GaussDB
    conn = get_db_connection()
    cur = conn.cursor()

    copy_sql = """
    COPY weather_forecast_hourly (
        forecast_timestamp,
        forecast_date,
        forecast_time,
        temperature_c,
        humidity_pct,
        precipitation_mm,
        precipitation_probability_pct,
        weather_conditions,
        wind_speed_kmh,
        wind_direction_deg,
        pressure_hpa,
        cloud_cover_pct
    )
    FROM STDIN WITH (FORMAT csv)
    """

    cur.copy_expert(copy_sql, buffer)
    conn.commit()
    cur.close()
    conn.close()

    print("✅ Chargement terminé dans silver.weather_forecast_hourly")