# src/pipeline/generator/battery_prediction_7d.py

import pandas as pd
from datetime import datetime, timedelta, timezone

from src.pipeline.load.weather_loader import get_db_connection
from src.pipeline.load.battery_loader import load_battery_states
from src.pipeline.generator.battery_utils import BatteryConfig, simulate_battery_series
from src.pipeline.generator.solar_prediction_7d import calculate_solar_production

# ---------------------------------------------------------------------------
# CONSTANTES BATTERIES
# ---------------------------------------------------------------------------

MAIN_CAP_KWH = 3000.0
BACKUP_CAP_KWH = 1000.0

MAIN_MAX_CHARGE_KW = 600.0
MAIN_MAX_DISCHARGE_KW = 600.0

BACKUP_MAX_CHARGE_KW = 200.0
BACKUP_MAX_DISCHARGE_KW = 200.0


# ---------------------------------------------------------------------------
# FENÊTRE DE PRÉDICTION (7 JOURS FUTURS)
# ---------------------------------------------------------------------------

def _get_prediction_window():
    """
    Retourne:
      - start_ts = demain 00:00 UTC (début horizon)
      - end_ts   = start_ts + 7 jours (exclu)
    """
    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)

    start_ts = datetime(
        tomorrow.year,
        tomorrow.month,
        tomorrow.day,
        0, 0, 0,
        tzinfo=timezone.utc,
    )
    end_ts = start_ts + timedelta(days=7)
    return start_ts, end_ts


# ---------------------------------------------------------------------------
# DATA : CONSOMMATION (PATTERN 30J)
# ---------------------------------------------------------------------------

def _fetch_hourly_pattern_from_archive(days: int = 30) -> pd.DataFrame:
    """
    Va chercher les derniers `days` jours dans energy_consumption_hourly_archive
    et calcule un profil moyen de consommation par heure de la journée (0..23).

    Retourne un DF:
        hour (int), avg_consumption_kwh (float)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        end_ts = datetime.now(timezone.utc)
        start_ts = end_ts - timedelta(days=days)

        cur.execute(
            """
            SELECT time_ts, use_kw
            FROM energy_consumption_hourly_archive
            WHERE time_ts >= %s AND time_ts < %s
            """,
            (start_ts, end_ts),
        )
        rows = cur.fetchall()
        if not rows:
            raise ValueError(
                "❌ Aucune donnée dans energy_consumption_hourly_archive "
                "pour construire le pattern de consommation."
            )

        df = pd.DataFrame(rows, columns=["time_ts", "use_kw"])
        df["time_ts"] = pd.to_datetime(df["time_ts"])
        df["hour"] = df["time_ts"].dt.hour

        pattern = (
            df.groupby("hour")["use_kw"]
            .mean()
            .reset_index()
            .rename(columns={"use_kw": "avg_consumption_kwh"})
        )

        # S'assurer qu'on a bien 24 heures
        all_hours = pd.DataFrame({"hour": list(range(24))})
        pattern = all_hours.merge(pattern, on="hour", how="left")
        pattern["avg_consumption_kwh"] = pattern["avg_consumption_kwh"].fillna(
            pattern["avg_consumption_kwh"].mean()
        )

        return pattern

    finally:
        cur.close()
        conn.close()


def _build_future_energy_forecast(
    start_ts: datetime,
    end_ts: datetime,
    pattern_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Construit une série horaire entre start_ts et end_ts (pas horaire),
    et affecte à chaque heure une consommation = pattern moyen de cette heure.

    Retourne un DF:
        timestamp, consumption_kwh
    """
    rng = pd.date_range(start=start_ts, end=end_ts, freq="H", inclusive="left")
    df = pd.DataFrame({"timestamp": rng})

    # IMPORTANT : enlever le timezone pour matcher les datetime naïfs postgres
    if getattr(df["timestamp"].dt, "tz", None) is not None:
        df["timestamp"] = df["timestamp"].dt.tz_convert(None)

    df["hour"] = df["timestamp"].dt.hour
    df = df.merge(pattern_df, on="hour", how="left")
    df.rename(columns={"avg_consumption_kwh": "consumption_kwh"}, inplace=True)
    df.drop(columns=["hour"], inplace=True)

    df["consumption_kwh"] = df["consumption_kwh"].fillna(0.0)
    return df


# ---------------------------------------------------------------------------
# DATA : MÉTÉO + SOLAIRE (FORECAST 7J)
# ---------------------------------------------------------------------------

def _fetch_forecast_weather(start_ts, end_ts) -> pd.DataFrame:
    """
    Récupère les prévisions météo dans weather_archive_hourly (où le forecast
    est archivé) pour la fenêtre demandée, puis calcule la production solaire
    (kWh) via le modèle PV commun.

    Retourne un DF:
        timestamp, solar_kwh
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT forecast_timestamp,
                   temperature_c,
                   cloud_cover_pct,
                   solar_radiation_w_m2
            FROM weather_archive_hourly
            WHERE forecast_timestamp >= %s AND forecast_timestamp < %s
            ORDER BY forecast_timestamp
            """,
            (start_ts, end_ts),
        )
        rows = cur.fetchall()
        if not rows:
            raise ValueError(
                "❌ Aucune météo forecast trouvée dans weather_archive_hourly "
                "pour la fenêtre demandée."
            )

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

        # Modèle PV commun
        solar_df = calculate_solar_production(df)
        solar_df = solar_df[["timestamp", "predicted_production_kwh"]].rename(
            columns={"predicted_production_kwh": "solar_kwh"}
        )
        return solar_df

    finally:
        cur.close()
        conn.close()


# ---------------------------------------------------------------------------
# DATA : ÉTAT RÉEL FINAL AVANT L'HORIZON
# ---------------------------------------------------------------------------

def _get_last_real_energy_before(
    start_ts,
    battery_type: str,
    default_capacity: float
) -> float:
    """
    Récupère energy_stored_kwh de battery_state_real pour la batterie (main/backup)
    au dernier timestamp < start_ts. Si rien, on considère batterie pleine.
    """
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


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 80)
    print("🔮 BATTERY PREDICTION 7D → battery_state_predicted")
    print("=" * 80)

    # 1) Fenêtre de prédiction
    start_ts, end_ts = _get_prediction_window()
    print(f"Horizon prévision : {start_ts} .. {end_ts} (7 jours)")

    # 2) Pattern de consommation (historique)
    print("📊 Construction du profil de consommation (pattern 30j)...")
    pattern_df = _fetch_hourly_pattern_from_archive(days=30)

    # 3) Série future de consommation (7 jours)
    print("📈 Génération de la série future de consommation (7j)...")
    future_energy_df = _build_future_energy_forecast(start_ts, end_ts, pattern_df)

    # 4) Météo forecast + solaire
    print("☀️ Récupération des prévisions météo + calcul production PV...")
    solar_df = _fetch_forecast_weather(start_ts, end_ts)

    # 5) Fusion énergie + solaire
    df = pd.merge(
        future_energy_df,
        solar_df,
        on="timestamp",
        how="left",
    )
    df["solar_kwh"] = df["solar_kwh"].fillna(0.0)

    print(f"🔢 {len(df)} heures prédites pour la fenêtre 7j")

    # 6) État initial = dernier state réel
    main_init = _get_last_real_energy_before(start_ts, "main", MAIN_CAP_KWH)
    backup_init = _get_last_real_energy_before(start_ts, "backup", BACKUP_CAP_KWH)

    print(f"🔋 Main init:   {main_init:.2f} kWh / {MAIN_CAP_KWH} kWh")
    print(f"🔋 Backup init: {backup_init:.2f} kWh / {BACKUP_CAP_KWH} kWh")

    # 7) Config batteries
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

    # 8) Simulation séries pour 7j (main + backup)
    print("🧮 Simulation batterie MAIN (7j)...")
    main_df = simulate_battery_series(
        df=df,
        cfg=main_cfg,
        energy_stored_kwh_start=main_init,
    )

    print("🧮 Simulation batterie BACKUP (7j)...")
    backup_df = simulate_battery_series(
        df=df,
        cfg=backup_cfg,
        energy_stored_kwh_start=backup_init,
    )

    all_df = pd.concat([main_df, backup_df], ignore_index=True)

    # 9) Flag obligatoire pour le loader (prédictions)
    all_df["is_predicted"] = True

    # 10) Chargement dans la table battery_state_predicted
    print("💾 Insertion dans battery_state_predicted ...")
    load_battery_states(all_df, target_table="battery_state_predicted")

    print("=" * 80)
    print("✅ BATTERY PREDICTION 7D TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()
