# src/pipeline/load/predicted_energy_loader.py
from .weather_loader import get_db_connection
from io import StringIO
import pandas as pd

def load_predicted_energy_consumption_to_db(
    df: pd.DataFrame,
    target_table: str = "predicted_energy_consumption_hourly"  # 👈 changé ici
):
    df_db = df.rename(columns={
        'Time': 'time_ts',
        'Building': 'building',
        'Outdoor Temp (°C)': 'outdoor_temp_c',
        'Humidity (%)': 'humidity_pct',
        'Cloud Cover (%)': 'cloud_cover_pct',
        'Solar Radiation (W/m²)': 'solar_radiation_w_m2',
        'Lighting [kW]': 'lighting_kw',
        'HVAC [kW]': 'hvac_kw',
        'Special Equipment [kW]': 'special_equipment_kw',
        'Use [kW]': 'use_kw',
        'Winter': 'winter_flag',
        'Spring': 'spring_flag',
        'Summer': 'summer_flag',
        'Fall': 'fall_flag',
        'Hour': 'hour_of_day',
        'DayOfWeek': 'day_of_week',
        'Month': 'month_num',
        'DayOfYear': 'day_of_year',
        'IsWeekend': 'is_weekend',
        'IsHoliday': 'is_holiday',
        'IsPeakHour': 'is_peak_hour',
    })

    df_db['id'] = df_db['time_ts'].dt.strftime('%Y%m%d%H') + '_' + df_db['building']
    df_db['time_ts'] = pd.to_datetime(df_db['time_ts'])

    cols = [col.lower() for col in [
        'id', 'time_ts', 'building',
        'winter_flag', 'spring_flag', 'summer_flag', 'fall_flag',
        'outdoor_temp_c', 'humidity_pct', 'cloud_cover_pct', 'solar_radiation_w_m2',
        'hour_of_day', 'day_of_week', 'month_num', 'day_of_year',
        'is_weekend', 'is_holiday', 'is_peak_hour',
        'lighting_kw', 'hvac_kw', 'special_equipment_kw', 'use_kw'
    ]]
    df_db = df_db[cols]

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(f"CREATE TEMP TABLE temp_pred (LIKE {target_table} INCLUDING ALL) ON COMMIT DROP")

        buffer = StringIO()
        df_db.to_csv(buffer, index=False, header=False)
        buffer.seek(0)
        cur.copy_expert(f"COPY temp_pred FROM STDIN WITH (FORMAT csv)", buffer)

        cur.execute(f"""
            INSERT INTO {target_table}
            SELECT * FROM temp_pred
            ON CONFLICT (time_ts, building) DO UPDATE SET
                use_kw = EXCLUDED.use_kw,
                lighting_kw = EXCLUDED.lighting_kw,
                hvac_kw = EXCLUDED.hvac_kw,
                special_equipment_kw = EXCLUDED.special_equipment_kw
        """)
        conn.commit()
        print(f"{len(df_db)} lignes insérées dans {target_table}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
