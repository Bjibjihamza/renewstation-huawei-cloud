import pandas as pd
from io import StringIO
import psycopg2
import os

def get_db_connection():
    host = os.getenv("GAUSSDB_HOST")
    if not host or host == "localhost":
        host = os.getenv("POSTGRES_HOST", "postgres")
    return psycopg2.connect(
        host=host,
        port=os.getenv("GAUSSDB_PORT", "5432"),
        database=os.getenv("GAUSSDB_DB_SILVER", "silver"),
        user=os.getenv("GAUSSDB_USER", "postgres"),
        password=os.getenv("GAUSSDB_PASSWORD", "postgres"),
        sslmode=os.getenv("GAUSSDB_SSLMODE", "disable")
    )

def load_weather_forecast_to_db(df: pd.DataFrame):
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
        'Couverture Nuageuse (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
    })

    df_db['forecast_timestamp'] = pd.to_datetime(df_db['forecast_date'] + ' ' + df_db['forecast_time'])
    df_db = df_db.drop(columns=['forecast_date', 'forecast_time'], errors='ignore')
    df_db['forecast_date'] = df_db['forecast_timestamp'].dt.date
    df_db['forecast_time'] = df_db['forecast_timestamp'].dt.time

    cols = [
        'forecast_timestamp', 'forecast_date', 'forecast_time',
        'temperature_c', 'humidity_pct', 'precipitation_mm',
        'precipitation_probability_pct', 'weather_conditions',
        'wind_speed_kmh', 'wind_direction_deg', 'pressure_hpa',
        'cloud_cover_pct', 'solar_radiation_w_m2'
    ]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("CREATE TEMP TABLE temp_forecast (LIKE weather_forecast_hourly INCLUDING ALL) ON COMMIT DROP")
        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False, na_rep='NULL')
        buffer.seek(0)
        cur.copy_expert("COPY temp_forecast FROM STDIN WITH (FORMAT csv, NULL 'NULL')", buffer)

        cur.execute("""
            INSERT INTO weather_forecast_hourly 
            SELECT * FROM temp_forecast
            ON CONFLICT (forecast_timestamp) DO UPDATE SET
                temperature_c = EXCLUDED.temperature_c,
                humidity_pct = EXCLUDED.humidity_pct,
                precipitation_mm = EXCLUDED.precipitation_mm,
                precipitation_probability_pct = EXCLUDED.precipitation_probability_pct,
                weather_conditions = EXCLUDED.weather_conditions,
                wind_speed_kmh = EXCLUDED.wind_speed_kmh,
                wind_direction_deg = EXCLUDED.wind_direction_deg,
                pressure_hpa = EXCLUDED.pressure_hpa,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2
        """)
        conn.commit()
        print(f"SUCCESS: WEATHER FORECAST 7J → {len(df_db)} lignes chargées dans weather_forecast_hourly")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise e
    finally:
        cur.close()
        conn.close()