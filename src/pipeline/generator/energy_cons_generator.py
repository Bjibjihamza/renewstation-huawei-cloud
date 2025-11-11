import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta  ### UPDATED: Added timedelta

import numpy as np
import pandas as pd
import argparse  ### UPDATED: Added for mode/end_date

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.load.energy_loader import load_energy_consumption_to_db  ### UPDATED: Uses upsert internally
from src.pipeline.load.weather_loader import get_db_connection

# ============================================================================
#   GÉNÉRATION RÉALISTE DES DONNÉES ÉNERGÉTIQUES AVEC MÉTÉO RÉELLE
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
#   RÉCUPÉRATION DES DONNÉES MÉTÉO RÉELLES DEPUIS LA BASE
# ============================================================================

### UPDATED: Added end_date param for recent mode
def fetch_real_weather_data(end_date=None):
    """
    Récupère les données météo réelles depuis weather_forecast_hourly
    à partir du 2024-01-01 jusqu'à end_date (default: NOW()).
    
    Retourne un DataFrame avec les colonnes nécessaires pour la génération.
    """
    if end_date is None:
        end_date = datetime.now()
    
    print("\n" + "=" * 80)
    print(f"📡 RÉCUPÉRATION DES DONNÉES MÉTÉO RÉELLES DEPUIS LA BASE (jusqu'à {end_date})")
    print("=" * 80)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = """
        SELECT 
            forecast_timestamp as time,
            temperature_c,
            humidity_pct,
            cloud_cover_pct,
            solar_radiation_w_m2
        FROM weather_forecast_hourly
        WHERE forecast_timestamp >= '2024-01-01 00:00:00'
          AND forecast_timestamp <= %s
        ORDER BY forecast_timestamp
        """
        
        print("🔍 Exécution de la requête SQL...")
        cur.execute(query, (end_date,))
        rows = cur.fetchall()
        
        if not rows:
            raise ValueError("❌ Aucune donnée météo trouvée dans la base pour 2024-01-01 à end_date!")
        
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

        print(f"✅ {len(df)} heures de données météo récupérées")
        print(f"📅 Période: {df['Time'].min()} → {df['Time'].max()}")
        print(f"🌡️  Température: min={df['Outdoor Temp (°C)'].min():.1f}°C, max={df['Outdoor Temp (°C)'].max():.1f}°C")
        
        return df
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des données météo: {e}")
        raise
    finally:
        cur.close()
        conn.close()


# ============================================================================
#   PROFILS DE COMPORTEMENT RÉALISTES PAR MAISON
# ============================================================================

def generate_house_profile(house_id):
    """
    Génère un profil unique et réaliste pour chaque maison
    """
    np.random.seed(1000 + house_id)

    profiles = {
        'summer_vacation': { 'vacation_months': [7, 8], 'has_ac': True, 'heating_type': 'electric', 'energy_conscious': False },
        'winter_vacation': { 'vacation_months': [12], 'has_ac': False, 'heating_type': 'gas', 'energy_conscious': True },
        'always_home_ac': { 'vacation_months': [], 'has_ac': True, 'heating_type': 'electric', 'energy_conscious': False },
        'always_home_no_ac': { 'vacation_months': [], 'has_ac': False, 'heating_type': 'electric', 'energy_conscious': True },
        'work_from_home': { 'vacation_months': [8], 'has_ac': True, 'heating_type': 'heatpump', 'energy_conscious': True, 'high_daytime_usage': True },
        'student_house': { 'vacation_months': [7, 8, 12], 'has_ac': False, 'heating_type': 'gas', 'energy_conscious': True, 'low_equipment': True },
        'large_family': { 'vacation_months': [7], 'has_ac': True, 'heating_type': 'electric', 'energy_conscious': False, 'high_equipment': True },
    }

    # Distribution des profils pour un nombre variable de maisons
    profile_distribution = [
        'summer_vacation', 'summer_vacation', 'winter_vacation', 'always_home_ac', 'always_home_ac',
        'always_home_no_ac', 'always_home_no_ac', 'work_from_home', 'work_from_home', 'work_from_home',
        'student_house', 'student_house', 'large_family', 'large_family', 'large_family'
    ]
    
    # Check if house_id is within range, else return a default profile
    if house_id - 1 < len(profile_distribution):
        profile_name = profile_distribution[house_id - 1]
    else:
        print(f"Warning: house_id {house_id} is out of range, using default profile.")
        profile_name = 'summer_vacation'  # Default fallback profile

    profile = profiles[profile_name].copy()
    profile['name'] = profile_name

    return profile



# ============================================================================
#   FONCTIONS POUR AJOUTER LES FEATURES TEMPORELLES
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


# ============================================================================
#   GÉNÉRATION DE L'OCCUPATION RÉALISTE
# ============================================================================

def generate_realistic_occupancy(df, building_type, building_size_factor, building_id=0, profile=None):
    """Generate realistic occupancy with UNIQUE patterns per building"""
    occupancy = []
    base_min, base_max = occupancy_range[building_type]
    prev_occupancy = 0.5

    base_min = int(base_min * building_size_factor)
    base_max = int(base_max * building_size_factor)

    for _, row in df.iterrows():
        hour = row["Hour"]
        day_of_week = row["DayOfWeek"]
        is_weekend = row["IsWeekend"]
        is_holiday = row["IsHoliday"]
        is_school_vacation = row.get("IsSchoolVacation", 0)
        month = row["Month"]

        if building_type == "House" and profile:
            # 🏖️ VACANCES
            if month in profile['vacation_months']:
                target_level = 0.05  # Maison vide
            
            # 🏠 OCCUPATION NORMALE
            elif hour in [6, 7, 8]:  # Matin
                target_level = 0.85
            elif hour in [9, 10, 11, 12, 13, 14, 15, 16]:  # Journée
                if profile.get('high_daytime_usage', False):  # Télétravail
                    target_level = 0.75
                else:
                    target_level = 0.20 if not is_weekend else 0.70
            elif hour in [17, 18, 19, 20, 21, 22]:  # Soirée
                target_level = 0.95
            elif hour in [23, 0, 1, 2, 3, 4, 5]:  # Nuit
                target_level = 1.0
            else:
                target_level = 0.5

        elif building_type == "Hospital":
            # Hôpital 24/7 - PAS de réduction en décembre !
            if hour in [7, 15, 23]:
                target_level = 0.90
            elif hour in [0, 1, 2, 3, 4, 5]:
                target_level = 0.55
            elif hour in [9, 10, 11, 14, 15, 16]:
                target_level = 0.88
            else:
                target_level = 0.75

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
            elif day_of_week == 4:  # Vendredi
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
            # Industrie continue - pas de grosse variation saisonnière
            if is_weekend:
                target_level = 0.60
            elif hour in [6, 7, 14, 15, 22, 23]:
                target_level = 0.92
            elif hour in [8, 9, 10, 11, 12, 13]:
                target_level = 0.90
            elif hour in [16, 17, 18, 19, 20, 21]:
                target_level = 0.78
            else:
                target_level = 0.65
        else:
            target_level = 0.5

        occupancy_level = 0.7 * prev_occupancy + 0.3 * target_level
        prev_occupancy = occupancy_level

        occupancy_level += np.random.normal(0, 0.04)
        occupancy_level = np.clip(occupancy_level, 0, 1)

        occ = int(base_min + (base_max - base_min) * occupancy_level)
        occupancy.append(max(0, occ))

    return occupancy


# ============================================================================
#   GÉNÉRATION DES CONSOMMATIONS CORRÉLÉES AVEC MÉTÉO
# ============================================================================

def generate_realistic_lighting(df, building_type, building_efficiency, occupancy, profile=None):
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
        month = row["Month"]

        natural_light = solar / 950
        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0

        # Maison en vacances
        if building_type == "House" and profile and month in profile['vacation_months']:
            lighting_need = 0.02
        
        elif building_type == "School" and is_school_vacation:
            lighting_need = 0.08
            
        elif building_type == "Hospital":
            if hour in [0, 1, 2, 3, 4, 5]:
                lighting_need = 0.45 * occupancy_factor
            else:
                lighting_need = (1 - float(natural_light) * 0.6) * occupancy_factor
                
        elif occupancy_factor < 0.1:
            lighting_need = 0.08 * occupancy_factor
        else:
            lighting_need = (1 - natural_light * 0.75) * occupancy_factor

        if building_type in ["Office", "School"] and occupancy_factor < 0.3:
            lighting_need *= 0.6

        light = base_min + (base_max - base_min) * np.clip(lighting_need, 0, 1)
        lighting.append(max(0, light + np.random.normal(0, 0.025 * light)))

    return lighting


def generate_realistic_hvac(df, building_type, building_insulation, occupancy, profile=None):
    """
    Generate realistic HVAC consumption with REAL temperature response
    - Clim (AC) when temp > 28°C
    - Heating when temp < 15°C
    - Vacation mode = minimal HVAC
    """
    hvac = []
    base_min, base_max = hvac_range[building_type]
    comfort_temp = 21
    indoor_temp = comfort_temp

    for idx, row in df.iterrows():
        outdoor_temp = row["Outdoor Temp (°C)"]
        solar = row["Solar Radiation (W/m²)"]
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        hour = row["Hour"]
        is_school_vacation = row.get("IsSchoolVacation", 0)
        month = row["Month"]

        # Indoor temperature dynamics
        indoor_temp = 0.88 * indoor_temp + 0.12 * outdoor_temp

        solar_gain = solar / 48000
        indoor_temp += solar_gain

        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0
        internal_gain = occupancy_factor * 1.3
        indoor_temp += internal_gain

        # 🌡️ RÉPONSE RÉALISTE À LA TEMPÉRATURE
        
        # Maison en vacances = mode économie (minimal HVAC)
        if building_type == "House" and profile and month in profile['vacation_months']:
            hvac_need = 0.05
        
        # ❄️ CHAUFFAGE en hiver (temp < 15°C)
        elif outdoor_temp < 15:
            temp_diff = max(comfort_temp - indoor_temp, 0)
            heating_need = (temp_diff / (18 * building_insulation))
            
            if building_type == "House" and profile:
                if profile['heating_type'] == 'gas':
                    # Chauffage au gaz = moins de consommation électrique
                    hvac_need = heating_need * 0.30
                elif profile['heating_type'] == 'heatpump':
                    # Pompe à chaleur = efficace mais électrique
                    hvac_need = heating_need * 0.65
                else:  # electric
                    # Chauffage électrique = haute consommation
                    hvac_need = heating_need * 1.2
            else:
                hvac_need = heating_need * occupancy_factor
        
        # 🔥 CLIMATISATION en été (temp > 28°C)
        elif outdoor_temp > 28:
            temp_diff = max(indoor_temp - comfort_temp, 0)
            cooling_need = (temp_diff / (16 * building_insulation))
            
            if building_type == "House" and profile:
                if profile['has_ac']:
                    # Avec clim = haute consommation quand il fait chaud
                    hvac_need = cooling_need * 1.5
                else:
                    # Sans clim = juste ventilateurs
                    hvac_need = cooling_need * 0.25
            else:
                hvac_need = cooling_need * occupancy_factor
        
        # 🌤️ TEMPÉRATURE MODÉRÉE (15-28°C)
        else:
            temp_diff = abs(indoor_temp - comfort_temp)
            
            if building_type == "School" and is_school_vacation:
                hvac_need = 0.10
            elif building_type == "Hospital":
                # Hôpital = toujours contrôle température
                hvac_need = (temp_diff / (17 * building_insulation)) * 0.85
            else:
                hvac_need = (temp_diff / (20 * building_insulation)) * occupancy_factor * 0.6

        # Peak hour adjustment
        if row["IsPeakHour"] and occupancy_factor > 0.5:
            time_factor = 1.08
        else:
            time_factor = 0.95

        hvac_load = base_min + (base_max - base_min) * np.clip(
            hvac_need * time_factor, 0, 1.6
        )
        hvac.append(max(0, hvac_load + np.random.normal(0, 0.06 * hvac_load)))

    return hvac


def generate_realistic_equipment(df, building_type, building_modernity, occupancy, profile=None):
    """Generate equipment usage"""
    equipment = []
    base_min, base_max = special_equipment_range[building_type]
    
    # Ajustement selon le profil
    if building_type == "House" and profile:
        if profile.get('high_equipment', False):
            base_max = base_max * 1.4  # Famille nombreuse
        elif profile.get('low_equipment', False):
            base_max = base_max * 0.6  # Étudiants
    
    base_max = base_max * building_modernity

    for idx, row in df.iterrows():
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        hour = row["Hour"]
        is_school_vacation = row.get("IsSchoolVacation", 0)
        month = row["Month"]

        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0

        # Maison en vacances
        if building_type == "House" and profile and month in profile['vacation_months']:
            base_equipment = 0.05  # Frigo uniquement
        elif building_type == "School" and is_school_vacation:
            base_equipment = 0.08
        else:
            base_equipment = 0.35

        if building_type == "Hospital":
            # Hôpital = équipements médicaux 24/7
            if 6 <= hour <= 20:
                variable_load = 0.90
            else:
                variable_load = 0.60
        elif building_type == "Industry":
            # Industrie = machines continues
            variable_load = 0.85 if occupancy_factor > 0.3 else 0.50
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
#   GÉNÉRATION D'UN BÂTIMENT
# ============================================================================

def generate_building_data(weather_df, building_type, building_number):
    """Generate highly realistic dataset for one building using real weather data"""

    np.random.seed(42 + building_number)
    random.seed(42 + building_number)

    # Taille du bâtiment
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

    # 🏠 Profil unique pour les maisons
    profile = None
    if building_type == "House":
        profile = generate_house_profile(building_number)
        print(f"      Profile: {profile['name']} | Vacations: {profile['vacation_months']} | AC: {profile['has_ac']} | Heating: {profile['heating_type']}")

    # Copier les données météo réelles
    df = weather_df.copy()

    # Ajouter les features temporelles
    df = add_temporal_features(df)

    # Générer l'occupation
    occupancy_internal = generate_realistic_occupancy(
        df, building_type, building_size_factor, building_number, profile
    )

    # Générer les consommations
    df["Lighting [kW]"] = generate_realistic_lighting(
        df, building_type, building_efficiency, occupancy_internal, profile
    )
    df["HVAC [kW]"] = generate_realistic_hvac(
        df, building_type, building_insulation, occupancy_internal, profile
    )
    df["Special Equipment [kW]"] = generate_realistic_equipment(
        df, building_type, building_modernity, occupancy_internal, profile
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

### UPDATED: Added mode logic
def main(mode="full"):
    end_date = None
    if mode == "recent":
        end_date = datetime.now() - timedelta(hours=6)
        print("🔄 Mode RECENT: Génération seulement pour les dernières 6h historiques")
    else:
        print("🔄 Mode FULL: Génération historique complète")
    
    print("=" * 80)
    print("🚀 GÉNÉRATION RÉALISTE DES DONNÉES ÉNERGÉTIQUES")
    print("=" * 80)

    # 1) Récupérer les données météo réelles (up to end_date)
    weather_df = fetch_real_weather_data(end_date=end_date)

    total_buildings = 0
    all_buildings_data = []

    # 2) Générer les données pour chaque bâtiment
    for building_type, count in building_counts.items():
        print(f"\n📊 Génération de {count} {building_type}(s):")

        for i in range(1, count + 1):
            df = generate_building_data(weather_df, building_type, total_buildings + i)

            if count == 1:
                building_name = f"{building_type}"
            else:
                building_name = f"{building_type}{i}"

            df["Building"] = building_name
            all_buildings_data.append(df)

            # Stats par mois (only if full mode)
            if mode == "full":
                monthly_stats = df.groupby("Month")["Use [kW]"].mean() * 24
                print(f"  ✓ {building_name:25s}")
                print(f"    Jan: {monthly_stats.get(1, 0):6.1f} | "
                      f"Apr: {monthly_stats.get(4, 0):6.1f} | "
                      f"Jul: {monthly_stats.get(7, 0):6.1f} | "
                      f"Oct: {monthly_stats.get(10, 0):6.1f} | "
                      f"Dec: {monthly_stats.get(12, 0):6.1f}")
            else:
                avg_load = df["Use [kW]"].mean()
                print(f"  ✓ {building_name:25s} | Avg Load (6h): {avg_load:7.2f} kW")

        total_buildings += count

    # 3) Combiner et sauvegarder
    print("\n📦 Création du fichier global...")
    combined_df = pd.concat(all_buildings_data, ignore_index=True)

    cols = combined_df.columns.tolist()
    cols.remove("Building")
    cols.insert(1, "Building")
    combined_df = combined_df[cols]

    base_dir = Path(__file__).resolve().parents[3]
    data_dir = base_dir / "data"
    os.makedirs(data_dir, exist_ok=True)

    prefix = "energy_historical_full" if mode == "full" else "energy_recent_6h"
    output_path = data_dir / f"{prefix}.csv"
    combined_df.to_csv(output_path, index=False)
    print(f"  ✓ {output_path} | Total rows: {len(combined_df):,}")

    # 4) Charger dans la DB
    load_energy_consumption_to_db(combined_df)

    print("\n" + "=" * 80)
    print("✅ SUCCÈS! Dataset RÉALISTE généré")
    print(f"📦 Fichier: {output_path}")
    print("=" * 80)

    print("\n🎯 CARACTÉRISTIQUES RÉALISTES:")
    print("  ✓ Hôpital: Consommation stable toute l'année (24/7)")
    print("  ✓ Houses 1-2: Vacances d'été (Jul-Aug) = conso minimale")
    print("  ✓ House 3: Vacances d'hiver (Dec) = conso minimale")
    print("  ✓ Houses 4-5: Toujours occupées avec clim (haute conso en été)")
    print("  ✓ Houses 6-7: Toujours occupées sans clim (économes)")
    print("  ✓ Houses 8-10: Télétravail (haute conso journée)")
    print("  ✓ Houses 11-12: Étudiants (basse conso + vacances longues)")
    print("  ✓ Houses 13-15: Familles nombreuses (haute conso toute l'année)")
    print("  ✓ Temp > 28°C → Clim boost (si équipée)")
    print("  ✓ Temp < 15°C → Chauffage boost (électrique/gaz/pompe)")
    print("  ✓ Industries: Production continue (pas de variations saisonnières)")
    print("  ✓ Bureaux: Réduit week-end/vacances")
    print("  ✓ École: Fermée vacances scolaires (Jun-Jul-Aug)")
    print("=" * 80)


### UPDATED: CLI with argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Energy Consumption Generator")
    parser.add_argument('--mode', default='full', choices=['full', 'recent'], help="Mode: full historical or recent 6h")
    args = parser.parse_args()
    main(mode=args.mode)