# src/pipeline/load/energy_loader.py
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


def generate_energy_id(timestamp, building):
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    return timestamp.strftime('%Y%m%d%H') + f"_{building}"


def upsert_energy_to_archive_and_live(df: pd.DataFrame):
    """
    Charge les données dans :
    - energy_consumption_hourly_archive (tout l'historique)
    - energy_consumption_hourly_live (seulement les dernières 48h)
    """
    df_db = df.rename(columns={
        'Time': 'time_ts',
        'Building': 'building',
        'Winter': 'winter_flag', 'Spring': 'spring_flag',
        'Summer': 'summer_flag', 'Fall': 'fall_flag',
        'Outdoor Temp (°C)': 'outdoor_temp_c',
        'Humidity (%)': 'humidity_pct',
        'Cloud Cover (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
        'Hour': 'hour_of_day', 'DayOfWeek': 'day_of_week',
        'Month': 'month_num', 'DayOfYear': 'day_of_year',
        'IsWeekend': 'is_weekend', 'IsHoliday': 'is_holiday',
        'IsPeakHour': 'is_peak_hour',
        'Lighting [kW]': 'lighting_kw', 'HVAC [kW]': 'hvac_kw',
        'Special Equipment [kW]': 'special_equipment_kw',
        'Use [kW]': 'use_kw',
    })

    df_db['time_ts'] = pd.to_datetime(df_db['time_ts'])
    df_db['id'] = df_db.apply(lambda row: generate_energy_id(row['time_ts'], row['building']), axis=1)

    cols = [
        'id', 'time_ts', 'building', 'winter_flag', 'spring_flag', 'summer_flag', 'fall_flag',
        'outdoor_temp_c', 'humidity_pct', 'cloud_cover_pct', 'solar_radiation_w_m2',
        'hour_of_day', 'day_of_week', 'month_num', 'day_of_year',
        'is_weekend', 'is_holiday', 'is_peak_hour',
        'lighting_kw', 'hvac_kw', 'special_equipment_kw', 'use_kw'
    ]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Table temporaire
        cur.execute("""
            CREATE TEMP TABLE temp_energy (
                LIKE energy_consumption_hourly_archive INCLUDING ALL
            )
        """)

        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False)
        buffer.seek(0)
        cur.copy_expert("""
            COPY temp_energy FROM STDIN WITH (FORMAT csv)
        """, buffer)

        # UPSERT dans ARCHIVE
        cur.execute("""
            INSERT INTO energy_consumption_hourly_archive
            SELECT * FROM temp_energy
            ON CONFLICT (time_ts, building) DO UPDATE SET
                id = EXCLUDED.id,
                winter_flag = EXCLUDED.winter_flag,
                spring_flag = EXCLUDED.spring_flag,
                summer_flag = EXCLUDED.summer_flag,
                fall_flag = EXCLUDED.fall_flag,
                outdoor_temp_c = EXCLUDED.outdoor_temp_c,
                humidity_pct = EXCLUDED.humidity_pct,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2,
                hour_of_day = EXCLUDED.hour_of_day,
                day_of_week = EXCLUDED.day_of_week,
                month_num = EXCLUDED.month_num,
                day_of_year = EXCLUDED.day_of_year,
                is_weekend = EXCLUDED.is_weekend,
                is_holiday = EXCLUDED.is_holiday,
                is_peak_hour = EXCLUDED.is_peak_hour,
                lighting_kw = EXCLUDED.lighting_kw,
                hvac_kw = EXCLUDED.hvac_kw,
                special_equipment_kw = EXCLUDED.special_equipment_kw,
                use_kw = EXCLUDED.use_kw
        """)

        # UPSERT dans LIVE (seulement dernières 48h)
        cur.execute("""
            INSERT INTO energy_consumption_hourly_live
            SELECT * FROM temp_energy
            WHERE time_ts >= NOW() - INTERVAL '48 hours'
            ON CONFLICT (time_ts, building) DO UPDATE SET
                id = EXCLUDED.id,
                winter_flag = EXCLUDED.winter_flag,
                spring_flag = EXCLUDED.spring_flag,
                summer_flag = EXCLUDED.summer_flag,
                fall_flag = EXCLUDED.fall_flag,
                outdoor_temp_c = EXCLUDED.outdoor_temp_c,
                humidity_pct = EXCLUDED.humidity_pct,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2,
                hour_of_day = EXCLUDED.hour_of_day,
                day_of_week = EXCLUDED.day_of_week,
                month_num = EXCLUDED.month_num,
                day_of_year = EXCLUDED.day_of_year,
                is_weekend = EXCLUDED.is_weekend,
                is_holiday = EXCLUDED.is_holiday,
                is_peak_hour = EXCLUDED.is_peak_hour,
                lighting_kw = EXCLUDED.lighting_kw,
                hvac_kw = EXCLUDED.hvac_kw,
                special_equipment_kw = EXCLUDED.special_equipment_kw,
                use_kw = EXCLUDED.use_kw
        """)

        conn.commit()
        print(f"ENERGY UPSERT DONE → {len(df_db)} rows in archive + live (last 48h)")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def load_energy_consumption_to_db(df: pd.DataFrame):
    """Legacy compatibilité"""
    upsert_energy_to_archive_and_live(df)