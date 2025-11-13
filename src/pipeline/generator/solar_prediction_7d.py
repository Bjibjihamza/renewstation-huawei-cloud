import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.pipeline.load.solar_prediction_loader import load_predicted_solar_production
from src.pipeline.load.weather_loader import get_db_connection

# ============================================================================
#  CONFIG CENTRALE PV – DONNÉES RÉELLES 2024
# ============================================================================

# Puissance crête installée (1 455 x 550 W ≈ 800 kWc)
PV_PEAK_POWER_KW = 800.0

# Surface totale des panneaux (m²)
PV_AREA_M2 = 3754.0

# Rendement module @ STC (22,5 %)
MODULE_EFFICIENCY_STC = 0.225

# Rendement onduleur (AC)
INVERTER_EFFICIENCY = 0.97

# Coefficient de température des modules (-0,4 %/°C)
TEMPERATURE_COEFFICIENT = -0.004  # -0.4 % / °C

# NOCT – Nominal Operating Cell Temperature
NOCT = 45.0


def fetch_forecast_weather():
    """
    Récupère la météo horaire forecastée sur 7 jours
    depuis weather_forecast_hourly.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT forecast_timestamp, temperature_c, cloud_cover_pct, solar_radiation_w_m2
            FROM weather_forecast_hourly
            WHERE forecast_timestamp >= NOW()
              AND forecast_timestamp < NOW() + INTERVAL '7 days'
            ORDER BY forecast_timestamp
        """)
        rows = cur.fetchall()
        df = pd.DataFrame(
            rows,
            columns=['timestamp', 'temperature_c', 'cloud_cover_pct', 'solar_radiation_w_m2']
        )

        # Convertir les Decimals en float
        df[['temperature_c', 'cloud_cover_pct', 'solar_radiation_w_m2']] = \
            df[['temperature_c', 'cloud_cover_pct', 'solar_radiation_w_m2']].astype(float)

        return df
    finally:
        cur.close()
        conn.close()

def calculate_solar_production(weather_df: pd.DataFrame) -> pd.DataFrame:
    df = weather_df.copy()

    # Sécuriser les types
    numeric_cols = ['temperature_c', 'cloud_cover_pct', 'solar_radiation_w_m2']
    df[numeric_cols] = df[numeric_cols].astype(float)

    # Extraire l'heure (UTC, à adapter si besoin)
    df['hour'] = df['timestamp'].dt.hour

    # ----------------------------------------------------------------------
    # 1) GHI brut depuis la météo (peut être 0 ou manquant)
    # ----------------------------------------------------------------------
    ghi_raw = df['solar_radiation_w_m2'].astype(float).clip(lower=0)

    # Mask des valeurs manquantes / nulles / égales à 0
    mask_missing = (ghi_raw <= 0) | ghi_raw.isna()
    daytime_mask = df['hour'].between(6, 18)

    # ----------------------------------------------------------------------
    # 2) GHI théorique pour les heures de jour (simple cloche autour de midi)
    # ----------------------------------------------------------------------
    # Cloche : 0 à 6h et 18h, 1 à 12h (max)
    rel = 1 - (df['hour'] - 12).abs() / 6.0
    rel = rel.clip(lower=0.0)  # en dehors de [6, 18] → 0

    # GHI ciel clair (~950 W/m² max à midi)
    ghi_clear = 950.0 * rel

    # Correction nuages (cloud_cover_pct en %)
    ghi_cloud_adjusted = ghi_clear * (1.0 - df['cloud_cover_pct'] / 100.0)

    # ----------------------------------------------------------------------
    # 3) Fusion : on prend la météo si non nulle, sinon notre fallback
    # ----------------------------------------------------------------------
    df['ghi_w_m2'] = ghi_raw  # valeur par défaut = data météo

    # Pour les heures où la météo est 0 mais qu'on est en journée → utiliser modèle PV
    df.loc[mask_missing & daytime_mask, 'ghi_w_m2'] = \
        ghi_cloud_adjusted[mask_missing & daytime_mask]

    # La nuit, même si missing → 0
    df.loc[mask_missing & ~daytime_mask, 'ghi_w_m2'] = 0.0

    # ----------------------------------------------------------------------
    # 4) DNI / DHI (approximations)
    # ----------------------------------------------------------------------
    df['dni_w_m2'] = df['ghi_w_m2'] * 1.1
    df['dhi_w_m2'] = df['ghi_w_m2'] * 0.2

    # ----------------------------------------------------------------------
    # 5) Modèle thermique : température cellule
    # ----------------------------------------------------------------------
    df['cell_temperature_c'] = df['temperature_c'] + (NOCT - 20.0) * (df['ghi_w_m2'] / 800.0)

    # Correction de rendement par température
    temp_loss_factor = 1.0 + TEMPERATURE_COEFFICIENT * (df['cell_temperature_c'] - 25.0)

    # ----------------------------------------------------------------------
    # 6) Puissance DC (kW) basée sur surface & rendement module
    # ----------------------------------------------------------------------
    df['dc_power_kw'] = (
        PV_AREA_M2
        * df['ghi_w_m2']
        * MODULE_EFFICIENCY_STC
        * temp_loss_factor
    ) / 1000.0

    df['dc_power_kw'] = df['dc_power_kw'].clip(lower=0.0)

    # ----------------------------------------------------------------------
    # 7) Puissance AC + limite 800 kW
    # ----------------------------------------------------------------------
    df['ac_power_kw'] = df['dc_power_kw'] * INVERTER_EFFICIENCY
    df['ac_power_kw'] = df['ac_power_kw'].clip(lower=0.0, upper=PV_PEAK_POWER_KW)

    # Production horaire (kWh) = kW sur une heure
    df['predicted_production_kwh'] = df['ac_power_kw']

    # Colonnes météo / compatibilité DB
    df['humidity_pct'] = 50.0
    df['temperature_c'] = df['temperature_c']
    df['cloud_cover_pct'] = df['cloud_cover_pct']
    df['solar_radiation_w_m2'] = df['solar_radiation_w_m2']

    return df

def main():
    print("\n" + "=" * 80)
    print("PRÉDICTION PRODUCTION SOLAIRE 7 JOURS → predicted_solar_production")
    print("=" * 80)

    weather_df = fetch_forecast_weather()
    print(f"{len(weather_df)} heures météo récupérées")

    solar_df = calculate_solar_production(weather_df)
    load_predicted_solar_production(solar_df)

    total_kwh = solar_df['predicted_production_kwh'].sum()
    print(f"PRODUCTION PRÉVUE 7J : {total_kwh:.1f} kWh")
    print("SUCCÈS ! PRÉDICTION SOLAIRE CHARGÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()
