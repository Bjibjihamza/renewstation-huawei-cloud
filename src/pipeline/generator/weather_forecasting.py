import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import argparse

from src.pipeline.load.weather_loader import (
    load_weather_forecast_to_db,
    get_db_connection,
)

# ============================================================================
#   CONSTANTES
# ============================================================================

START_HISTORY_DATE = datetime(2024, 1, 1)

LATITUDE = 33.5731
LONGITUDE = -7.5898

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARS = [
    "temperature_2m",
    "relativehumidity_2m",
    "precipitation",
    "precipitation_probability",
    "weathercode",
    "windspeed_10m",
    "winddirection_10m",
    "pressure_msl",
    "cloudcover",
    "shortwave_radiation",
]

TIMEZONE = "Africa/Casablanca"
FORECAST_HORIZON_DAYS = 7  # 7 jours de prévisions

# ============================================================================
#   FONCTIONS UTILITAIRES
# ============================================================================

def _build_dataframe_from_hourly(hourly_data: dict) -> pd.DataFrame:
    """Construit un DataFrame standardisé à partir du bloc hourly d'Open-Meteo."""
    rows = []
    times = hourly_data["time"]
    total_hours = len(times)

    for i in range(total_hours):
        dt = datetime.fromisoformat(times[i])

        row = {
            "Date": dt.strftime("%Y-%m-%d"),
            "Heure": dt.strftime("%H:%M"),
            "Temperature (°C)": hourly_data["temperature_2m"][i],
            "Humidité (%)": hourly_data["relativehumidity_2m"][i],
            "Précipitation (mm)": hourly_data["precipitation"][i],
            "Probabilité Pluie (%)": hourly_data["precipitation_probability"][i] or 0,
            "Conditions": get_weather_description(hourly_data["weathercode"][i]),
            "Vitesse Vent (km/h)": hourly_data["windspeed_10m"][i],
            "Direction Vent (°)": hourly_data["winddirection_10m"][i],
            "Pression (hPa)": hourly_data["pressure_msl"][i],
            "Couverture Nuageuse (%)": hourly_data["cloudcover"][i],
            "Solar Radiation (W/m²)": hourly_data["shortwave_radiation"][i],
        }
        rows.append(row)

    return pd.DataFrame(rows)


def _save_csv(df: pd.DataFrame, prefix: str) -> str:
    """Sauvegarde un DataFrame dans /data avec un préfixe donné et retourne le chemin."""
    base_dir = Path(__file__).resolve().parents[3]
    data_dir = base_dir / "data"
    os.makedirs(data_dir, exist_ok=True)

    filename = data_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    return str(filename)


def _fetch_history_and_load(start_dt: datetime, end_dt: datetime):
    """
    Récupère des données historiques entre start_dt et end_dt (inclus),
    construit un DataFrame et le charge en DB (UPSERT).
    """
    if start_dt > end_dt:
        print(f"⏭️ Aucun historique à récupérer (start > end: {start_dt} > {end_dt})")
        return

    print("\n" + "=" * 80)
    print(f"📚 BACKFILL HISTORIQUE {start_dt} → {end_dt}")
    print("=" * 80)

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_dt.date().isoformat(),
        "end_date": end_dt.date().isoformat(),
        "hourly": HOURLY_VARS,
        "timezone": TIMEZONE,
    }

    response = requests.get(ARCHIVE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    hourly_data = data["hourly"]
    df = _build_dataframe_from_hourly(hourly_data)

    df["__dt"] = pd.to_datetime(df["Date"] + " " + df["Heure"])
    df = df[(df["__dt"] >= start_dt) & (df["__dt"] <= end_dt)].drop(columns="__dt")

    if df.empty:
        print("⚠️ Aucun enregistrement historique renvoyé par l'API pour cette période.")
        return

    filename = _save_csv(df, "meteo_casablanca_historique")
    print(f"📦 Fichier CSV historique créé: {filename}")
    print(f"📊 Nombre total d'heures: {len(df)}")
    print(f"🕐 Période: {df['Date'].min()} {df['Heure'].min()} → {df['Date'].max()} {df['Heure'].max()}")

    load_weather_forecast_to_db(df)


def _fetch_forecast_7d_and_load():
    """
    Récupère les 7 prochains jours de prévisions météo
    et les charge en DB (UPSERT).
    """
    print("\n" + "=" * 80)
    print(f"🔮 PRÉVISIONS MÉTÉO CASABLANCA - {FORECAST_HORIZON_DAYS} jours")
    print("=" * 80)

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": HOURLY_VARS,
        "timezone": TIMEZONE,
        "forecast_days": FORECAST_HORIZON_DAYS,
    }

    response = requests.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()

    hourly_data = data["hourly"]
    df = _build_dataframe_from_hourly(hourly_data)

    now = datetime.now()
    df["__dt"] = pd.to_datetime(df["Date"] + " " + df["Heure"])
    df = df[df["__dt"] >= now].drop(columns="__dt")

    if df.empty:
        print("⚠️ Aucune prévision disponible")
        return

    filename = _save_csv(df, "meteo_casablanca_forecast_7d")
    print(f"\n📦 Fichier CSV prévisions créé: {filename}")
    print(f"📊 Nombre d'heures: {len(df)} heures")
    print(f"🕐 Période: {df['Date'].min()} {df['Heure'].min()} → {df['Date'].max()} {df['Heure'].max()}")

    load_weather_forecast_to_db(df)

    print("\n" + "=" * 80)
    print("✅ SUCCÈS! Prévisions météo (7 jours) récupérées et chargées en DB")
    print("=" * 80)


def _ensure_history_coverage():
    """
    Vérifie que la table weather_archive_hourly contient bien
    toutes les heures entre START_HISTORY_DATE et aujourd'hui.
    Si des trous existent, on les backfill via l'API historique.
    """

    today = datetime.now().date()
    history_end = datetime.combine(today, datetime.max.time()).replace(
        hour=23, minute=0, second=0, microsecond=0
    )

    print("\n" + "=" * 80)
    print(f"🔎 VÉRIFICATION COVERAGE HISTORIQUE {START_HISTORY_DATE} → {history_end}")
    print("=" * 80)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT 
                MIN(forecast_timestamp),
                MAX(forecast_timestamp)
            FROM weather_archive_hourly
            WHERE forecast_timestamp >= %s
              AND forecast_timestamp <= %s
            """,
            (START_HISTORY_DATE, history_end),
        )
        row = cur.fetchone()
        existing_min, existing_max = row[0], row[1]

    finally:
        cur.close()
        conn.close()

    print(f"📉 Existing MIN timestamp: {existing_min}")
    print(f"📈 Existing MAX timestamp: {existing_max}")

    if existing_min is None or existing_max is None:
        print("⚠️ Aucun historique trouvé, backfill complet…")
        _fetch_history_and_load(START_HISTORY_DATE, history_end)
        return

    if existing_min > START_HISTORY_DATE:
        missing_start_end = existing_min - timedelta(hours=1)
        print(f"⚠️ Gap en début: backfill {START_HISTORY_DATE} → {missing_start_end}")
        _fetch_history_and_load(START_HISTORY_DATE, missing_start_end)

    if existing_max < history_end:
        missing_end_start = existing_max + timedelta(hours=1)
        print(f"⚠️ Gap en fin: backfill {missing_end_start} → {history_end}")
        _fetch_history_and_load(missing_end_start, history_end)

    print("✅ Coverage historique vérifié / complété.")


# ============================================================================
#   FONCTION PRINCIPALE
# ============================================================================

def get_hourly_weather_forecast(mode="full"):
    """
    Modes:
    - 'full': Full historical backfill (2024-01-01 → NOW) + 7 jours forecast
    - 'recent': Backfill dernières 24h avec archive (au lieu de 6h)
    - 'forecast': Seulement les 7 jours de prévisions (sans backfill)
    """
    try:
        if mode == "full":
            # 1) S'assurer que l'historique 2024-01-01 → aujourd'hui est complet
            _ensure_history_coverage()

            # 2) Récupérer et charger 7 jours de prévision
            _fetch_forecast_7d_and_load()
            
        elif mode == "forecast":
            # Seulement les prévisions (utilisé dans daily pipeline)
            _fetch_forecast_7d_and_load()
            
        else:  # 'recent'
            # Backfill dernières 24h (au lieu de 6h)
            now_minus_24h = datetime.now() - timedelta(days=1)
            _fetch_history_and_load(now_minus_24h, datetime.now())
            print("✅ Recent backfill (dernières 24h) terminé")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur HTTP lors d'un appel Open-Meteo: {e}")
        raise
    except Exception as e:
        print(f"❌ Erreur générale dans get_hourly_weather_forecast: {e}")
        import traceback
        traceback.print_exc()
        raise


# ============================================================================
#   FONCTIONS UTILITAIRES POUR LA DESCRIPTION MÉTÉO
# ============================================================================

def get_weather_description(code: int) -> str:
    """Retourne la description météo selon le code WMO."""
    weather_codes = {
        0: "Ciel dégagé",
        1: "Principalement dégagé",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine légère",
        53: "Bruine modérée",
        55: "Bruine dense",
        61: "Pluie légère",
        63: "Pluie modérée",
        65: "Pluie forte",
        71: "Chute de neige légère",
        73: "Chute de neige modérée",
        75: "Chute de neige forte",
        77: "Grains de neige",
        80: "Averses de pluie légères",
        81: "Averses de pluie modérées",
        82: "Averses de pluie violentes",
        85: "Averses de neige légères",
        86: "Averses de neige fortes",
        95: "Orage",
        96: "Orage avec grêle légère",
        99: "Orage avec grêle forte",
    }
    return weather_codes.get(code, f"Code: {code}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather Forecasting Pipeline")
    parser.add_argument(
        '--mode', 
        default='full', 
        choices=['full', 'recent', 'forecast'], 
        help="Mode: full (historique+forecast), recent (24h backfill), forecast (7j only)"
    )
    args = parser.parse_args()
    get_hourly_weather_forecast(mode=args.mode)