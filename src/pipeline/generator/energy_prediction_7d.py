# src/pipeline/generator/energy_prediction_7d.py
import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.load.predicted_energy_loader import load_predicted_energy_consumption_to_db
from src.pipeline.load.weather_loader import get_db_connection

# ============================================================================
#   CONFIGURATION
# ============================================================================

random.seed(42)
np.random.seed(42)

building_counts = {
    "Hospital": 1,
    "House": 10,
    "Industry": 2,
    "Office": 3,
    "School": 1,
}

special_equipment_range = {
    "Hospital": (2.5, 8), "House": (0.15, 0.8), "Industry": (5, 18),
    "School": (0.8, 3.5), "Office": (0.8, 4.5),
}
lighting_range = {
    "Hospital": (1.2, 3.5), "House": (0.08, 0.4), "Industry": (1, 4),
    "School": (0.3, 1.8), "Office": (0.4, 2.2),
}
hvac_range = {
    "Hospital": (2.5, 7), "House": (0.2, 1.3), "Industry": (1.5, 6),
    "School": (0.6, 3), "Office": (0.7, 3.5),
}
occupancy_range = {
    "Hospital": (50, 200), "House": (1, 4), "Industry": (10, 100),
    "School": (50, 500), "Office": (5, 50),
}

# ============================================================================
#   RÉCUPÉRATION MÉTÉO PRÉVUE
# ============================================================================

def fetch_forecast_weather_data():
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    print(f"\nRÉCUPÉRATION MÉTÉO PRÉVUE du {start_date.date()} au {end_date.date()}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                forecast_timestamp,
                temperature_c,
                humidity_pct,
                cloud_cover_pct,
                solar_radiation_w_m2
            FROM weather_forecast_hourly
            WHERE forecast_timestamp >= %s AND forecast_timestamp < %s
            ORDER BY forecast_timestamp
        """, (start_date, end_date))
        
        rows = cur.fetchall()
        if not rows:
            raise ValueError("Aucune donnée météo prévue trouvée !")
        
        df = pd.DataFrame(rows, columns=[
            'Time', 'Outdoor Temp (°C)', 'Humidity (%)', 'Cloud Cover (%)', 'Solar Radiation (W/m²)'
        ])
        df['Time'] = pd.to_datetime(df['Time'])
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        print(f"{len(df)} heures récupérées → {df['Time'].min()} → {df['Time'].max()}")
        return df
    finally:
        cur.close()
        conn.close()

# ============================================================================
#   PROFILS MAISON
# ============================================================================

def generate_house_profile(house_id):
    np.random.seed(1000 + house_id)
    profiles = {
        'summer_vacation': {'vacation_months': [7, 8], 'has_ac': True, 'heating_type': 'electric', 'energy_conscious': False},
        'winter_vacation': {'vacation_months': [12], 'has_ac': False, 'heating_type': 'gas', 'energy_conscious': True},
        'always_home_ac': {'vacation_months': [], 'has_ac': True, 'heating_type': 'electric', 'energy_conscious': False},
        'always_home_no_ac': {'vacation_months': [], 'has_ac': False, 'heating_type': 'electric', 'energy_conscious': True},
        'work_from_home': {'vacation_months': [8], 'has_ac': True, 'heating_type': 'heatpump', 'energy_conscious': True, 'high_daytime_usage': True},
        'student_house': {'vacation_months': [7, 8, 12], 'has_ac': False, 'heating_type': 'gas', 'energy_conscious': True, 'low_equipment': True},
        'large_family': {'vacation_months': [7], 'has_ac': True, 'heating_type': 'electric', 'energy_conscious': False, 'high_equipment': True},
    }
    distribution = [
        'summer_vacation', 'summer_vacation', 'winter_vacation', 'always_home_ac', 'always_home_ac',
        'always_home_no_ac', 'always_home_no_ac', 'work_from_home', 'work_from_home', 'work_from_home',
        'student_house', 'student_house', 'large_family', 'large_family', 'large_family'
    ]
    name = distribution[(house_id - 1) % len(distribution)]
    profile = profiles[name].copy()
    profile['name'] = name
    return profile

# ============================================================================
#   FEATURES TEMPORELLES
# ============================================================================

def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    df["Hour"] = df["Time"].dt.hour
    df["DayOfWeek"] = df["Time"].dt.dayofweek
    df["Month"] = df["Time"].dt.month
    df["DayOfYear"] = df["Time"].dt.dayofyear
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6]).astype(int)

    df["IsHoliday"] = (
        ((df["Time"].dt.month == 12) & (df["Time"].dt.day.between(24, 31))) |
        ((df["Time"].dt.month == 1) & (df["Time"].dt.day == 1)) |
        ((df["Time"].dt.month == 7) & (df["Time"].dt.day == 4)) |
        ((df["Time"].dt.month == 11) & (df["Time"].dt.day.between(22, 28))) |
        ((df["Time"].dt.month == 3) & (df["Time"].dt.day.between(15, 22)))
    ).astype(int)

    df["IsSchoolVacation"] = df["Month"].isin([6, 7, 8]).astype(int)
    df["IsPeakHour"] = df["Hour"].isin([7, 8, 9, 17, 18, 19, 20]).astype(int)

    df["Winter"] = df["Month"].isin([12, 1, 2]).astype(int)
    df["Spring"] = df["Month"].isin([3, 4, 5]).astype(int)
    df["Summer"] = df["Month"].isin([6, 7, 8]).astype(int)
    df["Fall"] = df["Month"].isin([9, 10, 11]).astype(int)

    return df

# ============================================================================
#   OCCUPATION, ÉCLAIRAGE, HVAC, ÉQUIPEMENT
# ============================================================================

def generate_realistic_occupancy(df, building_type, size_factor, building_id=0, profile=None):
    occupancy = []
    base_min, base_max = occupancy_range[building_type]
    base_min = int(base_min * size_factor)
    base_max = int(base_max * size_factor)
    prev = 0.5
    noise = np.random.normal(0, 0.05, len(df))

    for idx, row in df.iterrows():
        h, dow, weekend, holiday, school_vac, month = row["Hour"], row["DayOfWeek"], row["IsWeekend"], row["IsHoliday"], row.get("IsSchoolVacation", 0), row["Month"]
        
        if building_type == "House" and profile and month in profile['vacation_months']:
            target = 0.05
        elif building_type == "Hospital":
            target = 0.9 if 7 <= h <= 23 else 0.6
        elif building_type == "School":
            target = 0.05 if school_vac else (0.95 if 9 <= h <= 14 else 0.1)
        elif building_type == "Office":
            target = 0.05 if weekend else (0.88 if 10 <= h <= 16 else 0.2)
        elif building_type == "Industry":
            target = 0.85 if not weekend else 0.6
        else:
            target = 0.5

        level = 0.7 * prev + 0.3 * target + noise[idx]
        level = np.clip(level, 0, 1)
        prev = level
        occupancy.append(int(base_min + (base_max - base_min) * level))
    return occupancy

def generate_realistic_lighting(df, building_type, efficiency, occupancy, profile=None):
    lighting = []
    base_min, base_max = lighting_range[building_type]
    base_max *= efficiency
    noise = np.random.normal(0, 0.08, len(df))

    for idx, row in df.iterrows():
        solar = row["Solar Radiation (W/m²)"]
        occ = occupancy[idx]
        max_occ = occupancy_range[building_type][1]
        occ_factor = occ / max_occ if max_occ > 0 else 0
        natural = solar / 950

        need = (1 - natural * 0.75) * occ_factor
        if building_type in ["Office", "School"] and occ_factor < 0.3:
            need *= 0.6
        if building_type == "House" and profile and row["Month"] in profile['vacation_months']:
            need = 0.02

        load = base_min + (base_max - base_min) * np.clip(need, 0, 1)
        lighting.append(max(0, load * (1 + noise[idx])))
    return lighting

def generate_realistic_hvac(df, building_type, insulation, occupancy, profile=None):
    hvac = []
    base_min, base_max = hvac_range[building_type]
    comfort = 21
    indoor = comfort
    noise = np.random.normal(0, 0.06, len(df))

    for idx, row in df.iterrows():
        temp = row["Outdoor Temp (°C)"]
        solar = row["Solar Radiation (W/m²)"]
        occ = occupancy[idx]
        max_occ = occupancy_range[building_type][1]
        occ_factor = occ / max_occ if max_occ > 0 else 0
        month = row["Month"]

        indoor = 0.88 * indoor + 0.12 * (temp + noise[idx])
        indoor += solar / 48000 + occ_factor * 1.3

        if building_type == "House" and profile and month in profile['vacation_months']:
            need = 0.05
        elif temp < 15:
            need = max(comfort - indoor, 0) / (18 * insulation)
            if building_type == "House" and profile:
                need *= 1.2 if profile['heating_type'] == 'electric' else 0.65 if profile['heating_type'] == 'heatpump' else 0.3
        elif temp > 28:
            need = max(indoor - comfort, 0) / (16 * insulation)
            if building_type == "House" and profile:
                need *= 1.5 if profile['has_ac'] else 0.25
        else:
            need = abs(indoor - comfort) / (20 * insulation) * occ_factor * 0.6

        time_factor = 1.08 if row["IsPeakHour"] and occ_factor > 0.5 else 0.95
        load = base_min + (base_max - base_min) * np.clip(need * time_factor, 0, 1.6)
        hvac.append(max(0, load * (1 + noise[idx])))
    return hvac

def generate_realistic_equipment(df, building_type, modernity, occupancy, profile=None):
    equipment = []
    base_min, base_max = special_equipment_range[building_type]
    if building_type == "House" and profile:
        if profile.get('high_equipment'): base_max *= 1.4
        if profile.get('low_equipment'): base_max *= 0.6
    base_max *= modernity
    noise = np.random.normal(0, 0.04, len(df))

    for idx, row in df.iterrows():
        occ = occupancy[idx]
        max_occ = occupancy_range[building_type][1]
        occ_factor = occ / max_occ if max_occ > 0 else 0
        month = row["Month"]

        base = 0.05 if (building_type == "House" and profile and month in profile['vacation_months']) else 0.35
        variable = occ_factor if building_type not in ["Hospital", "Industry"] else 0.85
        factor = base + variable * 0.65
        load = base_min + (base_max - base_min) * factor
        equipment.append(max(0, load * (1 + noise[idx])))
    return equipment

# ============================================================================
#   GÉNÉRATION PAR BÂTIMENT
# ============================================================================

def generate_building_data(weather_df, building_type, building_number):
    np.random.seed(42 + building_number)
    size_factor = np.random.uniform(0.7, 1.3)
    if building_type == "Industry":
        size_factor = np.random.uniform(1.1, 1.3) if building_number == 1 else np.random.uniform(0.5, 0.9)
    
    efficiency = np.random.uniform(0.75, 1.25)
    insulation = np.random.uniform(0.7, 1.3)
    modernity = np.random.uniform(0.85, 1.15)

    profile = generate_house_profile(building_number) if building_type == "House" else None

    df = weather_df.copy()
    df = add_temporal_features(df)
    occ = generate_realistic_occupancy(df, building_type, size_factor, building_number, profile)

    df["Lighting [kW]"] = generate_realistic_lighting(df, building_type, efficiency, occ, profile)
    df["HVAC [kW]"] = generate_realistic_hvac(df, building_type, insulation, occ, profile)
    df["Special Equipment [kW]"] = generate_realistic_equipment(df, building_type, modernity, occ, profile)
    df["Use [kW]"] = df[["Lighting [kW]", "HVAC [kW]", "Special Equipment [kW]"]].sum(axis=1) * (1 + np.random.normal(0, 0.012, len(df)))
    df["Use [kW]"] = df["Use [kW]"].clip(lower=0)

    df = df.drop(columns=["IsSchoolVacation"], errors="ignore")
    return df, profile

# ============================================================================
#   MAIN
# ============================================================================

def main():
    print("\n" + "="*80)
    print("PRÉDICTION CONSOMMATION ÉNERGIE 7 JOURS → predicted_energy_consumption_hourly")
    print("="*80)

    weather_df = fetch_forecast_weather_data()
    all_data = []
    total = 0

    for btype, count in building_counts.items():
        print(f"\nPrédiction {btype} × {count}")
        for i in range(1, count + 1):
            df, profile = generate_building_data(weather_df, btype, total + i)
            name = f"{btype}{i}" if count > 1 else btype
            df["Building"] = name
            all_data.append(df)
            avg = df["Use [kW]"].mean()
            profile_str = f" | {profile['name']}" if profile else ""
            print(f"  → {name:15} | Moyenne: {avg:6.2f} kW{profile_str}")
        total += count

    combined_df = pd.concat(all_data, ignore_index=True)
    cols = combined_df.columns.tolist()
    cols.remove("Building")
    cols.insert(1, "Building")
    combined_df = combined_df[cols]

    print(f"\nCHARGEMENT DE {len(combined_df):,} LIGNES DANS predicted_energy_consumption_hourly")

    # 👇 ici on laisse le paramètre par défaut (table de prévision)
    load_predicted_energy_consumption_to_db(combined_df)

    print("SUCCÈS ! PRÉDICTIONS 7J CHARGÉES")

    print("\n" + "="*80)
    print("TERMINÉ")
    print("="*80)

if __name__ == "__main__":
    main()