# src/pipeline/load/daily_archive_loader.py
from datetime import datetime, timedelta, date

import psycopg2
from src.pipeline.load.weather_loader import get_db_connection


def _get_yesterday_bounds() -> tuple[datetime, datetime, date]:
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    start_ts = datetime.combine(yesterday, datetime.min.time())
    end_ts = start_ts + timedelta(days=1)
    return start_ts, end_ts, yesterday


def archive_weather_yesterday():
    """
    Copie la météo d'hier depuis weather_forecast_hourly
    vers weather_archive_hourly (UPSERT sur forecast_timestamp).
    """
    start_ts, end_ts, yday = _get_yesterday_bounds()

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 80)
    print(f"ARCHIVE WEATHER → {yday}  ({start_ts} → {end_ts})")
    print("=" * 80)

    try:
        cur.execute(
            """
            INSERT INTO weather_archive_hourly (
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
                solar_radiation_w_m2,
                created_at
            )
            SELECT
                wf.forecast_timestamp,
                wf.forecast_timestamp::date    AS forecast_date,
                wf.forecast_timestamp::time    AS forecast_time,
                wf.temperature_c,
                wf.humidity_pct,
                wf.precipitation_mm,
                wf.precipitation_probability_pct,
                wf.weather_conditions,
                wf.wind_speed_kmh,
                wf.wind_direction_deg,
                wf.pressure_hpa,
                wf.cloud_cover_pct,
                wf.solar_radiation_w_m2,
                NOW() AS created_at
            FROM weather_forecast_hourly wf
            WHERE wf.forecast_timestamp >= %s
              AND wf.forecast_timestamp < %s
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
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2,
                created_at = EXCLUDED.created_at
            """,
            (start_ts, end_ts),
        )

        print(f"→ {cur.rowcount} lignes météo archivées / mises à jour")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] archive_weather_yesterday: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def archive_energy_yesterday():
    """
    Copie la conso d'hier depuis energy_consumption_hourly_live
    vers energy_consumption_hourly_archive (UPSERT sur (time_ts, building)).
    """
    start_ts, end_ts, yday = _get_yesterday_bounds()

    conn = get_db_connection()
    cur = conn.cursor()

    print("=" * 80)
    print(f"ARCHIVE ENERGY → {yday}  ({start_ts} → {end_ts})")
    print("=" * 80)

    try:
        cur.execute(
            """
            INSERT INTO energy_consumption_hourly_archive (
                id,
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
                e.id,
                e.time_ts,
                e.building,
                e.winter_flag,
                e.spring_flag,
                e.summer_flag,
                e.fall_flag,
                e.outdoor_temp_c,
                e.humidity_pct,
                e.cloud_cover_pct,
                e.solar_radiation_w_m2,
                e.hour_of_day,
                e.day_of_week,
                e.month_num,
                e.day_of_year,
                e.is_weekend,
                e.is_holiday,
                e.is_peak_hour,
                e.lighting_kw,
                e.hvac_kw,
                e.special_equipment_kw,
                e.use_kw
            FROM energy_consumption_hourly_live e
            WHERE e.time_ts >= %s
              AND e.time_ts < %s
            ON CONFLICT (time_ts, building) DO UPDATE SET
                id                   = EXCLUDED.id,
                winter_flag          = EXCLUDED.winter_flag,
                spring_flag          = EXCLUDED.spring_flag,
                summer_flag          = EXCLUDED.summer_flag,
                fall_flag            = EXCLUDED.fall_flag,
                outdoor_temp_c       = EXCLUDED.outdoor_temp_c,
                humidity_pct         = EXCLUDED.humidity_pct,
                cloud_cover_pct      = EXCLUDED.cloud_cover_pct,
                solar_radiation_w_m2 = EXCLUDED.solar_radiation_w_m2,
                hour_of_day          = EXCLUDED.hour_of_day,
                day_of_week          = EXCLUDED.day_of_week,
                month_num            = EXCLUDED.month_num,
                day_of_year          = EXCLUDED.day_of_year,
                is_weekend           = EXCLUDED.is_weekend,
                is_holiday           = EXCLUDED.is_holiday,
                is_peak_hour         = EXCLUDED.is_peak_hour,
                lighting_kw          = EXCLUDED.lighting_kw,
                hvac_kw              = EXCLUDED.hvac_kw,
                special_equipment_kw = EXCLUDED.special_equipment_kw,
                use_kw               = EXCLUDED.use_kw
            """,
            (start_ts, end_ts),
        )

        print(f"→ {cur.rowcount} lignes énergie archivées / mises à jour")

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] archive_energy_yesterday: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def archive_yesterday_all():
    """
    Fonction utilitaire : archive météo + énergie pour la veille.
    À appeler depuis le script ou Airflow.
    """
    archive_weather_yesterday()
    archive_energy_yesterday()
