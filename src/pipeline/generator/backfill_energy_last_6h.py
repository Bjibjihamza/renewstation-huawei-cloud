"""
🔄 BACKFILL ÉNERGIE HISTORIQUE: Dernières 6h seulement

Ce script (repurposed):
1. Récupère les dernières 6h de données météo HISTORIQUES depuis la DB (archive backfilled)
2. Génère des données d'énergie synthétiques UNIQUEMENT pour ces 6h HISTORIQUES
3. Fait un UPSERT dans energy_consumption_hourly

À exécuter après backfill météo récent (toutes les 6h).
NO FUTURE DATA.
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.load.energy_loader import upsert_energy_consumption_to_db
from src.pipeline.load.weather_loader import get_db_connection

# ============================================================================
#   CONSTANTES - IDENTIQUES AU GÉNÉRATEUR PRINCIPAL
# ============================================================================

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Define how many buildings of each type to generate
building_counts = {
    "Hospital": 1,
    "House": 15,
    "Industry": 3,
    "Office": 4,
    "School": 1,
}

# Ranges for equipment (kW)
special_equipment_range = {
    "Hospital": (2.5, 8),
    "House": (0.15, 0.8),
    "Industry": (5, 18),
    "School": (0.8, 3.5),
    "Office": (0.8, 4.5),
}

lighting_range = {
    "Hospital": (1.2, 3.5),
    "House": (0.08, 0.4),
    "Industry": (1, 4),
    "School": (0.3, 1.8),
    "Office": (0.4, 2.2),
}

hvac_range = {
    "Hospital": (2.5, 7),
    "House": (0.2, 1.3),
    "Industry": (1.5, 6),
    "School": (0.6, 3),
    "Office": (0.7, 3.5),
}

occupancy_range = {
    "Hospital": (50, 200),
    "House": (1, 4),
    "Industry": (10, 100),
    "School": (50, 500),
    "Office": (5, 50),
}


# ============================================================================
#   RÉCUPÉRATION DES DONNÉES MÉTÉO DES DERNIÈRES 6 HEURES HISTORIQUES
# ============================================================================

### UPDATED: Changed to fetch LAST 6h historical (not forecast)
def fetch_last_6h_historical_weather():
    """
    Récupère les dernières 6h de données météo HISTORIQUES depuis la base.
    
    Retourne un DataFrame avec les colonnes nécessaires pour la génération.
    """
    print("\n" + "=" * 80)
    print("📡 RÉCUPÉRATION DES DONNÉES MÉTÉO HISTORIQUES (DERNIÈRES 6 HEURES)")
    print("=" * 80)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        now = datetime.now()
        start_time = now - timedelta(hours=6)
        
        query = """
        SELECT 
            forecast_timestamp as time,
            temperature_c,
            humidity_pct,
            cloud_cover_pct,
            solar_radiation_w_m2
        FROM weather_forecast_hourly
        WHERE forecast_timestamp >= %s
          AND forecast_timestamp <= %s
        ORDER BY forecast_timestamp
        """
        
        print(f"🔍 Récupération des données historiques de {start_time} à {now}")
        cur.execute(query, (start_time, now))
        rows = cur.fetchall()
        
        if not rows:
            print("❌ Aucune donnée météo historique trouvée pour les dernières 6h!")
            print("⚠️  Assurez-vous que le backfill météo a été exécuté d'abord")
            return None
        
        # Créer le DataFrame
        df = pd.DataFrame(rows, columns=[
            'Time',
            'Outdoor Temp (°C)',
            'Humidity (%)',
            'Cloud Cover (%)',
            'Solar Radiation (W/m²)'
        ])
        
        # Convertir les Decimal en float
        df['Outdoor Temp (°C)'] = df['Outdoor Temp (°C)'].astype(float)
        df['Humidity (%)'] = df['Humidity (%)'].astype(float)
        df['Cloud Cover (%)'] = df['Cloud Cover (%)'].astype(float)
        df['Solar Radiation (W/m²)'] = df['Solar Radiation (W/m²)'].astype(float)

        print(f"✅ {len(df)} heures de données historiques récupérées")
        print(f"📅 Période: {df['Time'].min()} → {df['Time'].max()}")
        print(f"🌡️  Température: min={df['Outdoor Temp (°C)'].min():.1f}°C, max={df['Outdoor Temp (°C)'].max():.1f}°C")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ============================================================================
#   RÉCUPÉRATION DU DERNIER ÉTAT D'OCCUPATION PAR BÂTIMENT
# ============================================================================

def get_last_occupancy_state(building_name: str):
    """
    Récupère le dernier état d'occupation connu pour un bâtiment.
    Cela permet d'assurer la continuité avec les données passées.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = """
        SELECT 
            use_kw,
            lighting_kw,
            hvac_kw,
            special_equipment_kw
        FROM energy_consumption_hourly
        WHERE building = %s
        ORDER BY time_ts DESC
        LIMIT 1
        """
        
        cur.execute(query, (building_name,))
        row = cur.fetchone()
        
        if row:
            return {
                'last_total_kw': float(row[0]),
                'last_lighting_kw': float(row[1]),
                'last_hvac_kw': float(row[2]),
                'last_equipment_kw': float(row[3]),
            }
        else:
            return None
        
    finally:
        cur.close()
        conn.close()


# ============================================================================
#   FONCTIONS DE GÉNÉRATION (REPRISES DU SCRIPT PRINCIPAL)
# ============================================================================

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add comprehensive temporal features"""
    df["Hour"] = df["Time"].dt.hour
    df["DayOfWeek"] = df["Time"].dt.dayofweek
    df["Month"] = df["Time"].dt.month
    df["DayOfYear"] = df["Time"].dt.dayofyear
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6]).astype(int)

    df["IsHoliday"] = (
        ((df["Time"].dt.month == 12) & (df["Time"].dt.day.between(24, 31)))
        | ((df["Time"].dt.month == 1) & (df["Time"].dt.day == 1))
        | ((df["Time"].dt.month == 7) & (df["Time"].dt.day == 4))
        | ((df["Time"].dt.month == 11) & (df["Time"].dt.day.between(22, 28)))
        | ((df["Time"].dt.month == 3) & (df["Time"].dt.day.between(15, 22)))
    ).astype(int)

    df["IsSchoolVacation"] = df["Month"].isin([6, 7, 8]).astype(int)
    df["IsPeakHour"] = df["Hour"].isin([7, 8, 9, 17, 18, 19, 20]).astype(int)

    # Add season columns
    df["Winter"] = df["Month"].isin([12, 1, 2]).astype(int)
    df["Spring"] = df["Month"].isin([3, 4, 5]).astype(int)
    df["Summer"] = df["Month"].isin([6, 7, 8]).astype(int)
    df["Fall"] = df["Month"].isin([9, 10, 11]).astype(int)

    return df


def generate_realistic_occupancy(df, building_type, building_size_factor, building_id=0, prev_occupancy=0.5):
    """Generate realistic occupancy with continuity"""
    occupancy = []
    base_min, base_max = occupancy_range[building_type]

    base_min = int(base_min * building_size_factor)
    base_max = int(base_max * building_size_factor)

    np.random.seed(200 + building_id)
    if building_type == "House":
        vacation_month = np.random.choice([7, 8, 12, 0])
        weekend_activity = np.random.uniform(0.6, 0.9)
        work_from_home = np.random.choice([True, False])

    for _, row in df.iterrows():
        hour = row["Hour"]
        day_of_week = row["DayOfWeek"]
        is_weekend = row["IsWeekend"]
        is_holiday = row["IsHoliday"]
        is_school_vacation = row.get("IsSchoolVacation", 0)
        month = row["Month"]

        if building_type == "House":
            if vacation_month > 0 and month == vacation_month:
                target_level = 0.15
            elif hour in [6, 7, 8]:
                target_level = 0.85
            elif hour in [9, 10, 11, 12, 13, 14, 15, 16]:
                if work_from_home:
                    target_level = 0.65
                else:
                    target_level = 0.25 if not is_weekend else weekend_activity
            elif hour in [17, 18, 19, 20, 21, 22]:
                target_level = 0.95
            elif hour in [23, 0, 1, 2, 3, 4, 5]:
                target_level = 1.0
            else:
                target_level = 0.5

        elif building_type == "Hospital":
            if hour in [7, 15, 23]:
                target_level = 0.90
            elif hour in [0, 1, 2, 3, 4, 5]:
                target_level = 0.50
            elif hour in [9, 10, 11, 14, 15, 16]:
                target_level = 0.85
            else:
                target_level = 0.70

        elif building_type == "School":
            if is_school_vacation:
                target_level = 0.05
            elif is_weekend or is_holiday:
                target_level = 0.02
            elif hour in [7, 8]:
                target_level = 0.55
            elif hour in [9, 10, 11, 12, 13, 14]:
                target_level = 0.95
            elif hour == 15:
                target_level = 0.45
            elif hour in [16, 17]:
                target_level = 0.25
            else:
                target_level = 0.03

        elif building_type == "Office":
            if is_weekend:
                target_level = 0.05
            elif is_holiday:
                target_level = 0.02
            elif day_of_week == 4:
                if hour < 16:
                    target_level = 0.82
                else:
                    target_level = 0.25
            elif hour in [6, 7]:
                target_level = 0.18
            elif hour in [8, 9]:
                target_level = 0.70
            elif hour in [10, 11, 14, 15, 16]:
                target_level = 0.88
            elif hour in [12, 13]:
                target_level = 0.55
            elif hour in [17, 18]:
                target_level = 0.35
            else:
                target_level = 0.05

        elif building_type == "Industry":
            if is_weekend:
                target_level = 0.55
            elif hour in [6, 7, 14, 15, 22, 23]:
                target_level = 0.92
            elif hour in [8, 9, 10, 11, 12, 13]:
                target_level = 0.88
            elif hour in [16, 17, 18, 19, 20, 21]:
                target_level = 0.75
            else:
                target_level = 0.62
        else:
            target_level = 0.5

        occupancy_level = 0.7 * prev_occupancy + 0.3 * target_level
        prev_occupancy = occupancy_level

        occupancy_level += np.random.normal(0, 0.04)
        occupancy_level = np.clip(occupancy_level, 0, 1)

        occ = int(base_min + (base_max - base_min) * occupancy_level)
        occupancy.append(max(0, occ))

    return occupancy


def generate_realistic_lighting(df, building_type, building_efficiency, occupancy):
    """Generate realistic lighting consumption"""
    lighting = []
    base_min, base_max = lighting_range[building_type]
    base_max = base_max * building_efficiency

    for idx, row in df.iterrows():
        solar = row["Solar Radiation (W/m²)"]
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        is_school_vacation = row.get("IsSchoolVacation", 0)
        hour = row["Hour"]

        natural_light = solar / 950
        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0

        if building_type == "School" and is_school_vacation:
            lighting_need = 0.08
        elif building_type == "Hospital":
            if hour in [0, 1, 2, 3, 4, 5]:
                lighting_need = 0.40 * occupancy_factor
            else:
                lighting_need = (1 - float(natural_light) * 0.7) * occupancy_factor
        elif occupancy_factor < 0.1:
            lighting_need = 0.08 * occupancy_factor
        else:
            lighting_need = (1 - natural_light * 0.75) * occupancy_factor

        if building_type in ["Office", "School"] and occupancy_factor < 0.3:
            lighting_need *= 0.6

        light = base_min + (base_max - base_min) * np.clip(lighting_need, 0, 1)
        lighting.append(max(0, light + np.random.normal(0, 0.025 * light)))

    return lighting


def generate_realistic_hvac(df, building_type, building_insulation, occupancy, initial_indoor_temp=21):
    """Generate realistic HVAC consumption with continuity"""
    hvac = []
    base_min, base_max = hvac_range[building_type]
    comfort_temp = 21
    indoor_temp = initial_indoor_temp

    for idx, row in df.iterrows():
        outdoor_temp = row["Outdoor Temp (°C)"]
        solar = row["Solar Radiation (W/m²)"]
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        hour = row["Hour"]
        is_school_vacation = row.get("IsSchoolVacation", 0)

        indoor_temp = 0.88 * indoor_temp + 0.12 * outdoor_temp

        solar_gain = solar / 48000
        indoor_temp += solar_gain

        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0
        internal_gain = occupancy_factor * 1.3
        indoor_temp += internal_gain

        temp_diff = abs(indoor_temp - comfort_temp)

        if building_type == "School" and is_school_vacation:
            hvac_need = 0.12
        elif building_type == "Hospital":
            if hour in [0, 1, 2, 3, 4, 5]:
                hvac_need = (temp_diff / (18 * building_insulation)) * 0.75
            else:
                hvac_need = (temp_diff / (18 * building_insulation)) * occupancy_factor
        else:
            hvac_need = (temp_diff / (19 * building_insulation)) * occupancy_factor

        if building_type not in ["Hospital"]:
            if occupancy_factor < 0.15:
                hvac_need *= 0.35

        if row["IsPeakHour"] and occupancy_factor > 0.5:
            time_factor = 1.08
        else:
            time_factor = 0.92

        hvac_load = base_min + (base_max - base_min) * np.clip(
            hvac_need * time_factor, 0, 1.4
        )
        hvac.append(max(0, hvac_load + np.random.normal(0, 0.06 * hvac_load)))

    return hvac


def generate_realistic_equipment(df, building_type, building_modernity, occupancy):
    """Generate equipment usage"""
    equipment = []
    base_min, base_max = special_equipment_range[building_type]
    base_max = base_max * building_modernity

    for idx, row in df.iterrows():
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        hour = row["Hour"]
        is_school_vacation = row.get("IsSchoolVacation", 0)

        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0

        if building_type == "School" and is_school_vacation:
            base_equipment = 0.08
        else:
            base_equipment = 0.35

        if building_type == "Hospital":
            if 6 <= hour <= 20:
                variable_load = 0.88
            else:
                variable_load = 0.55
        elif building_type == "Industry":
            variable_load = 0.83 if occupancy_factor > 0.3 else 0.45
        elif building_type == "School":
            if is_school_vacation:
                variable_load = 0.10
            else:
                variable_load = occupancy_factor
        else:
            variable_load = occupancy_factor

        equipment_factor = base_equipment + (variable_load * 0.65)

        equip = base_min + (base_max - base_min) * equipment_factor
        equipment.append(max(0, equip + np.random.normal(0, 0.035 * equip)))

    return equipment


# ============================================================================
#   GÉNÉRATION POUR UN BÂTIMENT (6H HISTORIQUE SEULEMENT)
# ============================================================================

### UPDATED: Renamed and adjusted for historical
def generate_building_last_6h_backfill(weather_df, building_type, building_number, last_state=None):
    """
    Generate last 6h historical backfill for one building using historical weather data
    """

    np.random.seed(42 + building_number)
    random.seed(42 + building_number)

    if building_type == "Industry":
        if building_number == 1:
            building_size_factor = np.random.uniform(1.1, 1.3)
        else:
            building_size_factor = np.random.uniform(0.5, 0.9)
    else:
        building_size_factor = np.random.uniform(0.7, 1.3)

    building_efficiency = np.random.uniform(0.75, 1.25)
    building_insulation = np.random.uniform(0.7, 1.3)
    building_modernity = np.random.uniform(0.85, 1.15)

    # Copier les données météo
    df = weather_df.copy()

    # Ajouter les features temporelles
    df = add_temporal_features(df)

    # Déterminer l'état d'occupation initial
    # (utiliser le dernier état connu si disponible)
    initial_occupancy = 0.5
    if last_state and 'last_total_kw' in last_state:
        # Estimer l'occupation basée sur la consommation passée
        max_possible = (
            lighting_range[building_type][1] +
            hvac_range[building_type][1] +
            special_equipment_range[building_type][1]
        )
        initial_occupancy = min(1.0, last_state['last_total_kw'] / (max_possible * 1.5))

    # Générer l'occupation
    occupancy_internal = generate_realistic_occupancy(
        df, building_type, building_size_factor, building_number, initial_occupancy
    )

    # Générer les consommations
    df["Lighting [kW]"] = generate_realistic_lighting(
        df, building_type, building_efficiency, occupancy_internal
    )
    
    # Pour HVAC, utiliser une température initiale basée sur l'heure actuelle
    initial_indoor_temp = 21  # Température de confort par défaut
    df["HVAC [kW]"] = generate_realistic_hvac(
        df, building_type, building_insulation, occupancy_internal, initial_indoor_temp
    )
    
    df["Special Equipment [kW]"] = generate_realistic_equipment(
        df, building_type, building_modernity, occupancy_internal
    )

    df["Use [kW]"] = (
        df["Special Equipment [kW]"] + df["Lighting [kW]"] + df["HVAC [kW]"]
    ) * (1 + np.random.normal(0, 0.012, len(df)))

    df["Use [kW]"] = df["Use [kW]"].clip(lower=0)

    # Nettoyer les colonnes temporaires
    df = df.drop(columns=["IsSchoolVacation"], errors="ignore")

    return df


# ============================================================================
#   FONCTION PRINCIPALE
# ============================================================================

### UPDATED: Renamed to backfill_last_6h_energy
def backfill_last_6h_energy():
    """
    🔄 FONCTION PRINCIPALE
    
    Génère les données d'énergie synthétiques pour les dernières 6h HISTORIQUES
    et les charge dans la DB (UPSERT).
    """
    print("=" * 80)
    print("🔄 BACKFILL ÉNERGÉTIQUE HISTORIQUE (DERNIÈRES 6 HEURES)")
    print("=" * 80)

    # 1) Récupérer les données météo historiques des dernières 6h
    weather_df = fetch_last_6h_historical_weather()
    
    if weather_df is None or weather_df.empty:
        print("❌ Impossible de générer sans données météo historiques")
        return

    total_buildings = 0
    all_buildings_data = []

    # 2) Générer les données pour chaque bâtiment
    for building_type, count in building_counts.items():
        print(f"\n📊 Backfill de {count} {building_type}(s):")

        for i in range(1, count + 1):
            if count == 1:
                building_name = f"{building_type}"
            else:
                building_name = f"{building_type}{i}"
            
            # Récupérer le dernier état connu pour assurer la continuité
            last_state = get_last_occupancy_state(building_name)
            
            df = generate_building_last_6h_backfill(
                weather_df, building_type, total_buildings + i, last_state
            )

            df["Building"] = building_name
            all_buildings_data.append(df)

            avg_load = df["Use [kW]"].mean()
            print(f"  ✓ {building_name:25s} | Avg Load: {avg_load:7.2f} kW")

        total_buildings += count

    # 3) Combiner et charger dans la DB
    print("\n📦 Préparation du backfill en DB...")
    combined_df = pd.concat(all_buildings_data, ignore_index=True)

    cols = combined_df.columns.tolist()
    cols.remove("Building")
    cols.insert(1, "Building")
    combined_df = combined_df[cols]

    # 4) UPSERT dans la DB
    upsert_energy_consumption_to_db(combined_df)

    print("\n" + "=" * 80)
    print("✅ SUCCÈS! Backfill énergétique historique (6h) généré et chargé")
    print(f"📊 Total: {len(combined_df):,} lignes")
    print(f"📅 Période: {combined_df['Time'].min()} → {combined_df['Time'].max()}")
    print("=" * 80)


if __name__ == "__main__":
    backfill_last_6h_energy()