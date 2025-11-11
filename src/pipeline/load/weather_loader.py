# src/pipeline/load/weather_loader.py

import os
from io import StringIO

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Charge les variables d'environnement depuis .env à la racine (pour usage local)
if os.path.exists(".env.local"):
    load_dotenv(".env.local")
else:
    load_dotenv()

# Defaults adaptés pour Docker Compose (service "postgres", base "silver")
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


def upsert_weather_forecast_to_db(df: pd.DataFrame):
    """
    UPSERT (UPDATE + INSERT) du DataFrame dans weather_forecast_hourly.

    Logique:
    - Si forecast_timestamp existe déjà → UPDATE
    - Sinon → INSERT

    Permet de mettre à jour les prévisions existantes et d'ajouter les nouvelles heures.
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
        'Couverture Nuageuse (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
    })

    # 2) Créer le timestamp combiné
    df_db['forecast_timestamp'] = pd.to_datetime(
        df_db['forecast_date'] + ' ' + df_db['forecast_time']
    )

    # 3) Colonnes dans l'ordre de la table SQL
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
        'cloud_cover_pct',
        'solar_radiation_w_m2',
    ]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 4) Créer une table temporaire
        print("🔄 Création de la table temporaire...")
        cur.execute("""
            CREATE TEMP TABLE temp_weather_forecast (
                forecast_timestamp TIMESTAMP NOT NULL,
                forecast_date DATE NOT NULL,
                forecast_time TIME NOT NULL,
                temperature_c NUMERIC(5,2),
                humidity_pct NUMERIC(5,2),
                precipitation_mm NUMERIC(6,2),
                precipitation_probability_pct NUMERIC(5,2),
                weather_conditions VARCHAR(100),
                wind_speed_kmh NUMERIC(6,2),
                wind_direction_deg NUMERIC(5,2),
                pressure_hpa NUMERIC(7,2),
                cloud_cover_pct NUMERIC(5,2),
                solar_radiation_w_m2 NUMERIC(8,2)
            )
        """)

        # 5) Charger les données dans la table temporaire via COPY
        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        copy_sql = """
        COPY temp_weather_forecast (
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
            cloud_cover_pct,
            solar_radiation_w_m2
        )
        FROM STDIN WITH (FORMAT csv)
        """

        print("📥 Chargement des données dans la table temporaire...")
        cur.copy_expert(copy_sql, buffer)

        # 6) UPDATE des enregistrements existants
        print("🔄 Mise à jour des prévisions existantes...")
        update_sql = """
        UPDATE weather_forecast_hourly wf
        SET 
            forecast_date = t.forecast_date,
            forecast_time = t.forecast_time,
            temperature_c = t.temperature_c,
            humidity_pct = t.humidity_pct,
            precipitation_mm = t.precipitation_mm,
            precipitation_probability_pct = t.precipitation_probability_pct,
            weather_conditions = t.weather_conditions,
            wind_speed_kmh = t.wind_speed_kmh,
            wind_direction_deg = t.wind_direction_deg,
            pressure_hpa = t.pressure_hpa,
            cloud_cover_pct = t.cloud_cover_pct,
            solar_radiation_w_m2 = t.solar_radiation_w_m2,
            updated_at = CURRENT_TIMESTAMP
        FROM temp_weather_forecast t
        WHERE wf.forecast_timestamp = t.forecast_timestamp
        """
        cur.execute(update_sql)
        updated_count = cur.rowcount

        # 7) INSERT des nouvelles prévisions
        print("➕ Insertion des nouvelles prévisions...")
        insert_sql = """
        INSERT INTO weather_forecast_hourly (
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
            cloud_cover_pct,
            solar_radiation_w_m2
        )
        SELECT 
            t.forecast_timestamp,
            t.forecast_date,
            t.forecast_time,
            t.temperature_c,
            t.humidity_pct,
            t.precipitation_mm,
            t.precipitation_probability_pct,
            t.weather_conditions,
            t.wind_speed_kmh,
            t.wind_direction_deg,
            t.pressure_hpa,
            t.cloud_cover_pct,
            t.solar_radiation_w_m2
        FROM temp_weather_forecast t
        WHERE NOT EXISTS (
            SELECT 1 
            FROM weather_forecast_hourly wf 
            WHERE wf.forecast_timestamp = t.forecast_timestamp
        )
        """
        cur.execute(insert_sql)
        inserted_count = cur.rowcount

        # 8) Commit
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


def load_weather_forecast_to_db(df: pd.DataFrame):
    """
    Fonction legacy conservée pour compatibilité.
    Délègue à upsert_weather_forecast_to_db().
    """
    print("⚠️  Utilisation de la fonction legacy - redirection vers UPSERT")
    upsert_weather_forecast_to_db(df)
