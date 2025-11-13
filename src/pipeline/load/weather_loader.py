# src/pipeline/load/weather_loader.py
import os
from io import StringIO
import pandas as pd
import psycopg2
from dotenv import load_dotenv

if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()

DB_HOST = os.getenv("GAUSSDB_HOST", "postgres")
DB_PORT = int(os.getenv("GAUSSDB_PORT", "5432"))
DB_NAME = os.getenv("GAUSSDB_DB_SILVER", "silver")
DB_USER = os.getenv("GAUSSDB_USER", "postgres")
DB_PASSWORD = os.getenv("GAUSSDB_PASSWORD", "postgres")
DB_SSLMODE = os.getenv("GAUSSDB_SSLMODE", "disable")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD, sslmode=DB_SSLMODE
    )


def upsert_weather_to_archive_and_forecast(df: pd.DataFrame):
    """
    INITIALISATION ONLY → Charge TOUT dans weather_archive_hourly
    (on n'a pas encore weather_forecast_hourly)
    """
    df_db = df.rename(columns={
        'Date': 'forecast_date', 'Heure': 'forecast_time',
        'Temperature (°C)': 'temperature_c', 'Humidité (%)': 'humidity_pct',
        'Précipitation (mm)': 'precipitation_mm',
        'Probabilité Pluie (%)': 'precipitation_probability_pct',
        'Conditions': 'weather_conditions',
        'Vitesse Vent (km/h)': 'wind_speed_kmh',
        'Direction Vent (°)': 'wind_direction_deg',
        'Pression (hPa)': 'pressure_hpa',
        'Couverture Nuageuse (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
    })

    df_db['forecast_timestamp'] = pd.to_datetime(df_db['forecast_date'] + ' ' + df_db['forecast_time'])
    df_db = df_db.drop(columns=['forecast_date', 'forecast_time'])
    df_db['forecast_date'] = df_db['forecast_timestamp'].dt.date
    df_db['forecast_time'] = df_db['forecast_timestamp'].dt.time
    df_db['created_at'] = pd.Timestamp.now()  # obligatoire

    cols = [
        'forecast_timestamp', 'forecast_date', 'forecast_time',
        'temperature_c', 'humidity_pct', 'precipitation_mm',
        'precipitation_probability_pct', 'weather_conditions',
        'wind_speed_kmh', 'wind_direction_deg', 'pressure_hpa',
        'cloud_cover_pct', 'solar_radiation_w_m2',
        'created_at'
    ]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("CREATE TEMP TABLE temp_weather (LIKE weather_archive_hourly INCLUDING ALL)")

        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False)
        buffer.seek(0)
        cur.copy_expert("COPY temp_weather FROM STDIN WITH (FORMAT csv)", buffer)

        # ON CHARGE UNIQUEMENT DANS L'ARCHIVE
        cur.execute("""
            INSERT INTO weather_archive_hourly 
            SELECT * FROM temp_weather
            ON CONFLICT (forecast_timestamp) DO UPDATE SET
                temperature_c = EXCLUDED.temperature_c,
                humidity_pct = EXCLUDED.humidity_pct,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2,
                created_at = EXCLUDED.created_at
        """)

        conn.commit()
        print(f"WEATHER ARCHIVE ONLY → {len(df_db)} rows inserted into weather_archive_hourly")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

        
def load_weather_forecast_to_db(df: pd.DataFrame):
    """Legacy compatibilité"""
    upsert_weather_to_archive_and_forecast(df)