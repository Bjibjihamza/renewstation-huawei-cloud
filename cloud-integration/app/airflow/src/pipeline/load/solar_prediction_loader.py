import pandas as pd
from io import StringIO
from .weather_loader import get_db_connection

def load_predicted_solar_production(df: pd.DataFrame):
    """
    Charge les prédictions solaires 7j dans predicted_solar_production
    UPSERT sur timestamp
    """
    df_db = df.copy()
    df_db['timestamp'] = pd.to_datetime(df_db['timestamp'])

    cols = [
        'timestamp', 'temperature_c', 'humidity_pct', 'cloud_cover_pct',
        'solar_radiation_w_m2', 'ghi_w_m2', 'dni_w_m2', 'dhi_w_m2',
        'cell_temperature_c', 'dc_power_kw', 'ac_power_kw', 'predicted_production_kwh'
    ]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # ✅ Ensure target table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predicted_solar_production (
                timestamp                TIMESTAMPTZ PRIMARY KEY,
                temperature_c            DOUBLE PRECISION,
                humidity_pct             DOUBLE PRECISION,
                cloud_cover_pct          DOUBLE PRECISION,
                solar_radiation_w_m2     DOUBLE PRECISION,
                ghi_w_m2                 DOUBLE PRECISION,
                dni_w_m2                 DOUBLE PRECISION,
                dhi_w_m2                 DOUBLE PRECISION,
                cell_temperature_c       DOUBLE PRECISION,
                dc_power_kw              DOUBLE PRECISION,
                ac_power_kw              DOUBLE PRECISION,
                predicted_production_kwh DOUBLE PRECISION
            )
        """)

        # Temp table with same structure
        cur.execute(
            "CREATE TEMP TABLE temp_solar (LIKE predicted_solar_production INCLUDING ALL) ON COMMIT DROP"
        )

        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False, na_rep='NULL')
        buffer.seek(0)
        cur.copy_expert("COPY temp_solar FROM STDIN WITH (FORMAT csv, NULL 'NULL')", buffer)

        cur.execute("""
            INSERT INTO predicted_solar_production
            SELECT * FROM temp_solar
            ON CONFLICT (timestamp) DO UPDATE SET
                temperature_c            = EXCLUDED.temperature_c,
                humidity_pct             = EXCLUDED.humidity_pct,
                cloud_cover_pct          = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2     = EXCLUDED.solar_radiation_w_m2,
                ghi_w_m2                 = EXCLUDED.ghi_w_m2,
                dni_w_m2                 = EXCLUDED.dni_w_m2,
                dhi_w_m2                 = EXCLUDED.dhi_w_m2,
                cell_temperature_c       = EXCLUDED.cell_temperature_c,
                dc_power_kw              = EXCLUDED.dc_power_kw,
                ac_power_kw              = EXCLUDED.ac_power_kw,
                predicted_production_kwh = EXCLUDED.predicted_production_kwh
        """)

        conn.commit()
        print(f"SUCCESS: SOLAR PREDICTION 7J → {len(df_db)} lignes chargées dans predicted_solar_production")
    except Exception as e:
        conn.rollback()
        print(f"ERROR SOLAR: {e}")
        raise e
    finally:
        cur.close()
        conn.close()
