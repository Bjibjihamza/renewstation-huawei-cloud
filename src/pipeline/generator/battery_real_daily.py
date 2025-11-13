# src/pipeline/generator/battery_real_daily.py
import pandas as pd
from datetime import datetime, timedelta, timezone

from src.pipeline.load.weather_loader import get_db_connection
from src.pipeline.load.battery_loader import load_battery_states
from src.pipeline.generator.battery_utils import BatteryConfig, simulate_battery_series
from src.pipeline.generator.solar_prediction_7d import calculate_solar_production

MAIN_CAP_KWH = 3000.0
BACKUP_CAP_KWH = 1000.0

MAIN_MAX_CHARGE_KW = 600.0
MAIN_MAX_DISCHARGE_KW = 600.0

BACKUP_MAX_CHARGE_KW = 200.0
BACKUP_MAX_DISCHARGE_KW = 200.0


def _get_yesterday_bounds():
    today = datetime.now(timezone.utc).date()
    yday = today - timedelta(days=1)

    start_ts = datetime(yday.year, yday.month, yday.day, 0, 0, 0)
    end_ts = start_ts + timedelta(days=1)
    return yday, start_ts, end_ts


def fetch_archived_energy(start_ts, end_ts) -> pd.DataFrame:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT time_ts, SUM(use_kw) AS consumption_kwh
            FROM energy_consumption_hourly_archive
            WHERE time_ts >= %s AND time_ts < %s
            GROUP BY time_ts
            ORDER BY time_ts
            """,
            (start_ts, end_ts),
        )
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=["timestamp", "consumption_kwh"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    finally:
        cur.close()
        conn.close()


def fetch_archived_weather(start_ts, end_ts) -> pd.DataFrame:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT forecast_timestamp, temperature_c, cloud_cover_pct, solar_radiation_w_m2
            FROM weather_archive_hourly
            WHERE forecast_timestamp >= %s AND forecast_timestamp < %s
            ORDER BY forecast_timestamp
            """,
            (start_ts, end_ts),
        )
        rows = cur.fetchall()
        df = pd.DataFrame(
            rows,
            columns=[
                "timestamp",
                "temperature_c",
                "cloud_cover_pct",
                "solar_radiation_w_m2",
            ],
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        solar_df = calculate_solar_production(df)
        out = solar_df[["timestamp", "predicted_production_kwh"]].rename(
            columns={"predicted_production_kwh": "solar_kwh"}
        )
        return out
    finally:
        cur.close()
        conn.close()


def get_last_real_energy_before(start_ts, battery_type: str, default_capacity: float) -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT energy_stored_kwh
            FROM battery_state_real
            WHERE battery_type = %s
              AND timestamp < %s
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (battery_type, start_ts),
        )
        row = cur.fetchone()
        if row is None or row[0] is None:
            return default_capacity
        return float(row[0])
    finally:
        cur.close()
        conn.close()


def _delete_existing_real_states(start_ts, end_ts):
    """Supprime les états réels d'une journée avant recalcul."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            DELETE FROM battery_state_real
            WHERE timestamp >= %s AND timestamp < %s
            """,
            (start_ts, end_ts),
        )
        deleted = cur.rowcount
        conn.commit()
        print(f"🧹 {deleted} lignes supprimées dans battery_state_real pour {start_ts}..{end_ts}")
    finally:
        cur.close()
        conn.close()


def main():
    print("\n" + "=" * 80)
    print("BATTERY REAL DAILY → battery_state_real (basé sur archives J-1)")
    print("=" * 80)

    yday, start_ts, end_ts = _get_yesterday_bounds()
    print(f"Jour traité : {yday} → {start_ts} .. {end_ts}")

    energy_df = fetch_archived_energy(start_ts, end_ts)
    solar_df = fetch_archived_weather(start_ts, end_ts)

    if energy_df.empty:
        print("⚠️ Aucune énergie dans l'archive pour hier – rien à faire.")
        return

    df = pd.merge(energy_df, solar_df, on="timestamp", how="left")
    df["solar_kwh"] = df["solar_kwh"].fillna(0.0)

    print(f"{len(df)} heures trouvées pour J-1")

    main_init = get_last_real_energy_before(start_ts, "main", MAIN_CAP_KWH)
    backup_init = get_last_real_energy_before(start_ts, "backup", BACKUP_CAP_KWH)

    print(f"Main init:   {main_init:.2f} kWh / {MAIN_CAP_KWH} kWh")
    print(f"Backup init: {backup_init:.2f} kWh / {BACKUP_CAP_KWH} kWh")

    main_cfg = BatteryConfig(
        battery_type="main",
        capacity_kwh=MAIN_CAP_KWH,
        max_charge_kw=MAIN_MAX_CHARGE_KW,
        max_discharge_kw=MAIN_MAX_DISCHARGE_KW,
    )

    backup_cfg = BatteryConfig(
        battery_type="backup",
        capacity_kwh=BACKUP_CAP_KWH,
        max_charge_kw=BACKUP_MAX_CHARGE_KW,
        max_discharge_kw=BACKUP_MAX_DISCHARGE_KW,
    )

    main_df = simulate_battery_series(df, main_cfg, main_init)
    backup_df = simulate_battery_series(df, backup_cfg, backup_init)

    all_df = pd.concat([main_df, backup_df], ignore_index=True)

    # 1) flag obligatoire pour le loader
    all_df["is_predicted"] = False

    # 2) Nettoyer les éventuels anciens calculs J-1
    _delete_existing_real_states(start_ts, end_ts)

    # 3) Upsert via loader (sécurisé)
    load_battery_states(all_df, target_table="battery_state_real")



    print("=" * 80)
    print("BATTERY REAL DAILY TERMINÉ")
    print("=" * 80)


if __name__ == "__main__":
    main()
