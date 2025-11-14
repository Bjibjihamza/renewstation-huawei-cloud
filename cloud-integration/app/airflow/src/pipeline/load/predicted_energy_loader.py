# src/pipeline/load/predicted_energy_loader.py
from .weather_loader import get_db_connection
from io import StringIO
import pandas as pd

def load_predicted_energy_consumption_to_db(
    df: pd.DataFrame,
    target_table: str = "predicted_energy_consumption_hourly"
):
    """
    Version compatible avec le modèle ML (energy_prediction_7d.py)
    Le DataFrame contient maintenant :
    - time_ts
    - building
    - use_kw
    - toutes les features (temp, humidity, etc.)
    → Plus de colonnes lighting_kw, hvac_kw, special_equipment_kw
    """
    # Colonnes attendues par la table
    expected_cols = [
        'time_ts', 'building', 'use_kw',
        'outdoor_temp_c', 'humidity_pct', 'cloud_cover_pct', 'solar_radiation_w_m2',
        'hour_of_day', 'day_of_week', 'month_num', 'day_of_year',
        'is_weekend', 'is_holiday', 'is_peak_hour',
        'winter_flag', 'spring_flag', 'summer_flag', 'fall_flag'
    ]

    # On garde seulement les colonnes présentes
    df_db = df.copy()
    df_db['time_ts'] = pd.to_datetime(df_db['time_ts'])

    # Créer l'ID unique
    df_db['id'] = df_db['time_ts'].dt.strftime('%Y%m%d%H') + '_' + df_db['building']

    # Remplir les colonnes manquantes avec NULL (ex: lighting_kw, hvac_kw → plus calculées)
    # → La table accepte NULL sur ces colonnes
    missing_cols = ['lighting_kw', 'hvac_kw', 'special_equipment_kw']
    for col in missing_cols:
        if col not in df_db.columns:
            df_db[col] = None

    # Ordre final exact
    final_cols = [
        'id', 'time_ts', 'building',
        'winter_flag', 'spring_flag', 'summer_flag', 'fall_flag',
        'outdoor_temp_c', 'humidity_pct', 'cloud_cover_pct', 'solar_radiation_w_m2',
        'hour_of_day', 'day_of_week', 'month_num', 'day_of_year',
        'is_weekend', 'is_holiday', 'is_peak_hour',
        'lighting_kw', 'hvac_kw', 'special_equipment_kw', 'use_kw'
    ]

    # Réorganiser
    df_db = df_db[final_cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"CREATE TEMP TABLE temp_pred (LIKE {target_table} INCLUDING ALL) ON COMMIT DROP")

        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False, na_rep='NULL')
        buffer.seek(0)

        cur.copy_expert(f"COPY temp_pred FROM STDIN WITH (FORMAT csv, NULL 'NULL')", buffer)

        cur.execute(f"""
            INSERT INTO {target_table}
            SELECT * FROM temp_pred
            ON CONFLICT (time_ts, building) DO UPDATE SET
                use_kw = EXCLUDED.use_kw,
                outdoor_temp_c = EXCLUDED.outdoor_temp_c,
                humidity_pct = EXCLUDED.humidity_pct,
                cloud_cover_pct = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2
        """)
        conn.commit()
        print(f"{len(df_db)} prédictions ML chargées dans {target_table} (IA ±149 W)")
    except Exception as e:
        conn.rollback()
        print(f"ERREUR lors du chargement : {e}")
        raise e
    finally:
        cur.close()
        conn.close()