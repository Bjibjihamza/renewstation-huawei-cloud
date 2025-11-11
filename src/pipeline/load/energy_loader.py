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

DB_HOST = os.getenv("GAUSSDB_HOST", "postgres")
DB_PORT = int(os.getenv("GAUSSDB_PORT", "5432"))
DB_NAME = os.getenv("GAUSSDB_DB_SILVER", "silver")
DB_USER = os.getenv("GAUSSDB_USER", "postgres")
DB_PASSWORD = os.getenv("GAUSSDB_PASSWORD", "postgres")
DB_SSLMODE = os.getenv("GAUSSDB_SSLMODE", "disable")


def get_db_connection():
    """Ouvre une connexion à Postgres (base SILVER)."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=DB_SSLMODE,
    )


def upsert_energy_consumption_to_db(df: pd.DataFrame):
    """
    UPSERT (UPDATE + INSERT) du DataFrame dans energy_consumption_hourly.
    
    Logique:
    - Si (time_ts, building) existe déjà → UPDATE
    - Sinon → INSERT
    
    Permet de mettre à jour les données existantes et d'ajouter les nouvelles.
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

    # 2) Colonnes dans l'ordre de la table SQL
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

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 3) Créer une table temporaire
        print("🔄 Création de la table temporaire...")
        cur.execute("""
            CREATE TEMP TABLE temp_energy_consumption (
                time_ts                TIMESTAMP      NOT NULL,
                building               VARCHAR(50)    NOT NULL,
                winter_flag            SMALLINT       NOT NULL,
                spring_flag            SMALLINT       NOT NULL,
                summer_flag            SMALLINT       NOT NULL,
                fall_flag              SMALLINT       NOT NULL,
                outdoor_temp_c         NUMERIC(5,2),
                humidity_pct           NUMERIC(5,2),
                cloud_cover_pct        NUMERIC(5,2),
                solar_radiation_w_m2   NUMERIC(8,2),
                hour_of_day            SMALLINT       NOT NULL,
                day_of_week            SMALLINT       NOT NULL,
                month_num              SMALLINT       NOT NULL,
                day_of_year            SMALLINT       NOT NULL,
                is_weekend             SMALLINT       NOT NULL,
                is_holiday             SMALLINT       NOT NULL,
                is_peak_hour           SMALLINT       NOT NULL,
                lighting_kw            NUMERIC(10,4),
                hvac_kw                NUMERIC(10,4),
                special_equipment_kw   NUMERIC(10,4),
                use_kw                 NUMERIC(10,4)
            )
        """)

        # 4) Charger les données dans la table temporaire via COPY
        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        copy_sql = """
        COPY temp_energy_consumption (
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

        print("📥 Chargement des données dans la table temporaire...")
        cur.copy_expert(copy_sql, buffer)

        # 5) UPDATE des enregistrements existants
        print("🔄 Mise à jour des enregistrements existants...")
        update_sql = """
        UPDATE energy_consumption_hourly ec
        SET 
            winter_flag = t.winter_flag,
            spring_flag = t.spring_flag,
            summer_flag = t.summer_flag,
            fall_flag = t.fall_flag,
            outdoor_temp_c = t.outdoor_temp_c,
            humidity_pct = t.humidity_pct,
            cloud_cover_pct = t.cloud_cover_pct,
            solar_radiation_w_m2 = t.solar_radiation_w_m2,
            hour_of_day = t.hour_of_day,
            day_of_week = t.day_of_week,
            month_num = t.month_num,
            day_of_year = t.day_of_year,
            is_weekend = t.is_weekend,
            is_holiday = t.is_holiday,
            is_peak_hour = t.is_peak_hour,
            lighting_kw = t.lighting_kw,
            hvac_kw = t.hvac_kw,
            special_equipment_kw = t.special_equipment_kw,
            use_kw = t.use_kw
        FROM temp_energy_consumption t
        WHERE ec.time_ts = t.time_ts 
          AND ec.building = t.building
        """
        cur.execute(update_sql)
        updated_count = cur.rowcount

        # 6) INSERT des nouveaux enregistrements
        print("➕ Insertion des nouveaux enregistrements...")
        insert_sql = """
        INSERT INTO energy_consumption_hourly (
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
        SELECT 
            t.time_ts,
            t.building,
            t.winter_flag,
            t.spring_flag,
            t.summer_flag,
            t.fall_flag,
            t.outdoor_temp_c,
            t.humidity_pct,
            t.cloud_cover_pct,
            t.solar_radiation_w_m2,
            t.hour_of_day,
            t.day_of_week,
            t.month_num,
            t.day_of_year,
            t.is_weekend,
            t.is_holiday,
            t.is_peak_hour,
            t.lighting_kw,
            t.hvac_kw,
            t.special_equipment_kw,
            t.use_kw
        FROM temp_energy_consumption t
        WHERE NOT EXISTS (
            SELECT 1 
            FROM energy_consumption_hourly ec 
            WHERE ec.time_ts = t.time_ts 
              AND ec.building = t.building
        )
        """
        cur.execute(insert_sql)
        inserted_count = cur.rowcount

        # 7) Commit
        conn.commit()

        print("\n" + "=" * 80)
        print("✅ UPSERT TERMINÉ")
        print(f"🔄 Lignes mises à jour: {updated_count}")
        print(f"➕ Nouvelles lignes insérées: {inserted_count}")
        print(f"📊 Total traité: {len(df_db)} lignes")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERREUR lors de l'UPSERT: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def load_energy_consumption_to_db(df: pd.DataFrame):
    """
    Fonction legacy conservée pour compatibilité.
    Délègue à upsert_energy_consumption_to_db().
    """
    print("⚠️  Utilisation de la fonction legacy - redirection vers UPSERT")
    upsert_energy_consumption_to_db(df)