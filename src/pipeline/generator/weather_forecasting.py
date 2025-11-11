import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
import argparse  ### UPDATED: Added for mode handling

from src.pipeline.load.weather_loader import (
    load_weather_forecast_to_db,  ### UPDATED: Uses upsert internally
    get_db_connection,
)

# ============================================================================
#   CONSTANTES
# ============================================================================

# Date de début à garantir en base
START_HISTORY_DATE = datetime(2024, 1, 1)

# Coordonnées Casablanca
LATITUDE = 33.5731
LONGITUDE = -7.5898

# URLs Open-Meteo
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Variables horaires utilisées
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

# ### UPDATED: Changed to 1 week as per req
FORECAST_HORIZON_DAYS = 7  # 1 week

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

    # Filtrer aux bornes exactes (au cas où l'API renvoie plus large)
    df["__dt"] = pd.to_datetime(df["Date"] + " " + df["Heure"])
    df = df[(df["__dt"] >= start_dt) & (df["__dt"] <= end_dt)].drop(columns="__dt")

    if df.empty:
        print("⚠️ Aucun enregistrement historique renvoyé par l'API pour cette période.")
        return

    filename = _save_csv(df, "meteo_casablanca_historique")
    print(f"📦 Fichier CSV historique créé: {filename}")
    print(f"📊 Nombre total d'heures (filtrées): {len(df)}")
    print(f"🕐 Période (effective): {df['Date'].min()} {df['Heure'].min()} → {df['Date'].max()} {df['Heure'].max()}")
    print(f"🌐 Source: Open-Meteo Historical API")

    # Chargement DB (UPSERT)
    load_weather_forecast_to_db(df)


### UPDATED: Renamed and adjusted for 1-week horizon
def _fetch_forecast_1w_and_load():
    """
    Récupère les 7 prochains jours (1 week) de prévisions météo
    et les charge en DB (UPSERT).
    
    Ces données seront plus tard remplacées par des données réelles via backfill.
    """
    print("\n" + "=" * 80)
    print(f"🔮 PRÉVISIONS MÉTÉO CASABLANCA - {FORECAST_HORIZON_DAYS} jours (1 week)")
    print("=" * 80)

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": HOURLY_VARS,
        "timezone": TIMEZONE,
        "forecast_days": FORECAST_HORIZON_DAYS,  ### UPDATED: 7 days
    }

    response = requests.get(FORECAST_URL, params=params)
    response.raise_for_status()
    data = response.json()

    hourly_data = data["hourly"]
    df = _build_dataframe_from_hourly(hourly_data)

    # ### UPDATED: Keep all 1-week data (no filter to 6h)
    now = datetime.now()
    df["__dt"] = pd.to_datetime(df["Date"] + " " + df["Heure"])
    df = df[df["__dt"] >= now].drop(columns="__dt")  # Only future

    if df.empty:
        print("⚠️ Aucune prévision disponible")
        return

    filename = _save_csv(df, "meteo_casablanca_forecast_1w")
    print(f"\n📦 Fichier CSV prévisions créé: {filename}")
    print(f"📊 Nombre d'heures: {len(df)} heures (~{FORECAST_HORIZON_DAYS*24})")
    print(f"🕐 Période: {df['Date'].min()} {df['Heure'].min()} → {df['Date'].max()} {df['Heure'].max()}")
    print(f"🌐 Source: Open-Meteo Forecast API")

    # Chargement DB (UPSERT)
    load_weather_forecast_to_db(df)

    print("\n" + "=" * 80)
    print("✅ SUCCÈS! Prévisions météo (1 week) récupérées et chargées en DB")
    print("⚠️  Ces prévisions seront remplacées par des données réelles plus tard")
    print("=" * 80)


def _backfill_forecast_with_real_data():
    """
    Remplace les prévisions passées par des données réelles.
    
    Logique:
    - Récupère toutes les prévisions dont forecast_timestamp < maintenant
    - Les remplace par des vraies données depuis l'API archive
    """
    print("\n" + "=" * 80)
    print("🔄 BACKFILL DES PRÉVISIONS AVEC DONNÉES RÉELLES")
    print("=" * 80)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Trouver les prévisions qui sont maintenant dans le passé
        now = datetime.now()
        
        cur.execute(
            """
            SELECT 
                MIN(forecast_timestamp) as oldest_forecast,
                MAX(forecast_timestamp) as newest_forecast
            FROM weather_forecast_hourly
            WHERE forecast_timestamp < %s
              AND forecast_timestamp >= %s
            """,
            (now, START_HISTORY_DATE),
        )
        row = cur.fetchone()
        oldest, newest = row[0], row[1]

    finally:
        cur.close()
        conn.close()

    if oldest is None:
        print("✅ Aucune prévision passée à backfill")
        return

    print(f"📍 Prévisions passées trouvées: {oldest} → {newest}")
    print(f"🔄 Remplacement par données réelles...")

    # Récupérer les vraies données pour cette période
    _fetch_history_and_load(oldest, newest)

    print("✅ Backfill des prévisions terminé")


def _ensure_history_coverage():
    """
    Vérifie que la table weather_forecast_hourly contient bien
    toutes les heures entre START_HISTORY_DATE et aujourd'hui (fin de journée).
    Si des trous existent au début ou à la fin, on les backfill via l'API historique.
    """

    # Fin de coverage souhaité = aujourd'hui 23:00
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
            FROM weather_forecast_hourly
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

    # Cas 1: rien en base sur cette période -> backfill complet
    if existing_min is None or existing_max is None:
        print("⚠️ Aucun historique trouvé, backfill complet…")
        _fetch_history_and_load(START_HISTORY_DATE, history_end)
        return

    # Cas 2: trou au début (on n'a pas remonté jusqu'à START_HISTORY_DATE)
    if existing_min > START_HISTORY_DATE:
        missing_start_end = existing_min - timedelta(hours=1)
        print(f"⚠️ Gap en début: backfill {START_HISTORY_DATE} → {missing_start_end}")
        _fetch_history_and_load(START_HISTORY_DATE, missing_start_end)

    # Cas 3: trou à la fin (on n'a pas jusqu'à today)
    if existing_max < history_end:
        missing_end_start = existing_max + timedelta(hours=1)
        print(f"⚠️ Gap en fin: backfill {missing_end_start} → {history_end}")
        _fetch_history_and_load(missing_end_start, history_end)

    print("✅ Coverage historique vérifié / complété.")


# ============================================================================
#   FONCTION PRINCIPALE APPELÉE PAR AIRFLOW
# ============================================================================

def get_hourly_weather_forecast(mode="full"):
    """
    ### UPDATED: Mode-based logic
    
    Modes:
    - 'full': Full historical backfill (2024-01-01 → NOW) + backfill old forecasts + 1-week forecast
    - 'recent': Only backfill last 6h with archive (no forecast fetch)
    """
    try:
        if mode == "full":
            # 1) S'assurer que l'historique 2024-01-01 → aujourd'hui est complet
            _ensure_history_coverage()

            # 2) Backfill des prévisions passées avec données réelles
            _backfill_forecast_with_real_data()

            # 3) Récupérer et charger 1 week de prévision
            _fetch_forecast_1w_and_load()
        else:  # 'recent'
            # Only backfill last 6h historical (no forecast)
            now_minus_6h = datetime.now() - timedelta(hours=6)
            _fetch_history_and_load(now_minus_6h, datetime.now())
            print("✅ Recent backfill (last 6h) terminé - no forecast added")

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


def get_weather_icon(code: int) -> str:
    """Retourne un emoji selon le code météo."""
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "⛅"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "🌧️"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "❄️"
    elif code in [95, 96, 99]:
        return "⛈️"
    else:
        return "🌤️"


### UPDATED: CLI entrypoint with argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weather Forecasting Pipeline")
    parser.add_argument('--mode', default='full', choices=['full', 'recent'], help="Mode: full historical + forecast or recent 6h backfill")
    args = parser.parse_args()
    get_hourly_weather_forecast(mode=args.mode)