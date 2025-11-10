# src/pipeline/load/energy_loader.py

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


def load_energy_consumption_to_db(df: pd.DataFrame):
    """
    Charge le DataFrame 'energy_consumption' dans la table
    silver.energy_consumption_hourly via COPY FROM STDIN.
    """
    # 1) Renommer les colonnes pour matcher les colonnes SQL
    df_db = df.rename(columns={
        'Time': 'time_ts',
        'Building': 'building',
        'Winter': 'winter_flag',
        'Spring': 'spring_flag',
        'Summer': 'summer_flag',
        'Fall': 'fall_flag',
        'Outdoor Temp (°C)': 'outdoor_temp_c',
        'Humidity (%)': 'humidity_pct',
        'Cloud Cover (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
        'Hour': 'hour_of_day',
        'DayOfWeek': 'day_of_week',
        'Month': 'month_num',
        'DayOfYear': 'day_of_year',
        'IsWeekend': 'is_weekend',
        'IsHoliday': 'is_holiday',
        'IsPeakHour': 'is_peak_hour',
        'Lighting [kW]': 'lighting_kw',
        'HVAC [kW]': 'hvac_kw',
        'Special Equipment [kW]': 'special_equipment_kw',
        'Use [kW]': 'use_kw',
    })

    cols = [
        'time_ts',
        'building',
        'winter_flag',
        'spring_flag',
        'summer_flag',
        'fall_flag',
        'outdoor_temp_c',
        'humidity_pct',
        'cloud_cover_pct',
        'solar_radiation_w_m2',
        'hour_of_day',
        'day_of_week',
        'month_num',
        'day_of_year',
        'is_weekend',
        'is_holiday',
        'is_peak_hour',
        'lighting_kw',
        'hvac_kw',
        'special_equipment_kw',
        'use_kw',
    ]
    df_db = df_db[cols]

    # 2) Convertir en CSV en mémoire (sans header)
    buffer = StringIO()
    df_db.to_csv(buffer, index=False, header=False)
    buffer.seek(0)

    # 3) COPY vers GaussDB
    conn = get_db_connection()
    cur = conn.cursor()

    copy_sql = """
    COPY energy_consumption_hourly (
        time_ts,
        building,
        winter_flag,
        spring_flag,
        summer_flag,
        fall_flag,
        outdoor_temp_c,
        humidity_pct,
        cloud_cover_pct,
        solar_radiation_w_m2,
        hour_of_day,
        day_of_week,
        month_num,
        day_of_year,
        is_weekend,
        is_holiday,
        is_peak_hour,
        lighting_kw,
        hvac_kw,
        special_equipment_kw,
        use_kw
    )
    FROM STDIN WITH (FORMAT csv)
    """

    cur.copy_expert(copy_sql, buffer)
    conn.commit()
    cur.close()
    conn.close()

    print("✅ Chargement terminé dans silver.energy_consumption_hourly")
