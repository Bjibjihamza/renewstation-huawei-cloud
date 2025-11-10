import pandas as pd
import numpy as np
import random
import os

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Constants
hours_per_year = 8760
seasons = ['Winter', 'Spring', 'Summer', 'Fall']

# Define how many buildings of each type to generate
building_counts = {
    'Hospital': 1,
    'House': 15,
    'Industry': 3,
    'Office': 4,
    'School': 1
}

# OBJECTIFS DE CONSOMMATION QUOTIDIENNE RÉALISTES (kWh/jour)
daily_consumption_targets = {
    'Hospital': (150, 500),
    'House': (10, 40),
    'Industry': (300, 1000),
    'School': (50, 200),
    'Office': (50, 250)
}

# Conversion en kW horaires
special_equipment_range = {
    'Hospital': (2.5, 8),
    'House': (0.15, 0.8),
    'Industry': (5, 18),
    'School': (0.8, 3.5),
    'Office': (0.8, 4.5)
}

lighting_range = {
    'Hospital': (1.2, 3.5),
    'House': (0.08, 0.4),
    'Industry': (1, 4),
    'School': (0.3, 1.8),
    'Office': (0.4, 2.2)
}

hvac_range = {
    'Hospital': (2.5, 7),
    'House': (0.2, 1.3),
    'Industry': (1.5, 6),
    'School': (0.6, 3),
    'Office': (0.7, 3.5)
}

occupancy_range = {
    'Hospital': (50, 200),
    'House': (1, 4),
    'Industry': (10, 100),
    'School': (50, 500),
    'Office': (5, 50)
}

def generate_realistic_temperature(hours, location_offset=0, building_type='House', building_id=0):
    """Generate realistic seasonal temperature with UNIQUE patterns per building"""
    temperatures = []
    weather_noise = 0
    
    # CHAQUE BÂTIMENT a son propre pattern saisonnier
    np.random.seed(100 + building_id)
    phase_shift = np.random.uniform(-30, 30)  # Décalage de phase unique
    amplitude_factor = np.random.uniform(0.85, 1.15)  # Amplitude unique
    
    for hour in range(hours):
        day_of_year = hour // 24
        hour_of_day = hour % 24
        
        # Base saisonnière avec variations individuelles
        base_amplitude = 22
        if building_type == 'House':
            seasonal_temp = (17.5 + location_offset) + (base_amplitude * amplitude_factor) * np.sin(2 * np.pi * (day_of_year - 80 + phase_shift) / 365)
        elif building_type == 'Hospital':
            seasonal_temp = (18 + location_offset) + (20 * amplitude_factor) * np.sin(2 * np.pi * (day_of_year - 80 + phase_shift) / 365)
        elif building_type == 'Industry':
            seasonal_temp = (17 + location_offset) + (21 * amplitude_factor) * np.sin(2 * np.pi * (day_of_year - 80 + phase_shift) / 365)
        elif building_type == 'Office':
            seasonal_temp = (18 + location_offset) + (22 * amplitude_factor) * np.sin(2 * np.pi * (day_of_year - 80 + phase_shift) / 365)
        else:
            seasonal_temp = (17.5 + location_offset) + (22 * amplitude_factor) * np.sin(2 * np.pi * (day_of_year - 80 + phase_shift) / 365)
        
        daily_variation = 7 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        weather_noise = 0.92 * weather_noise + 0.08 * np.random.normal(0, 2.5)
        
        if np.random.random() < 0.0008:
            weather_noise += np.random.choice([-8, 8])
        
        temp = seasonal_temp + daily_variation + weather_noise
        temperatures.append(np.clip(temp, -10, 42))
    
    return temperatures

def generate_realistic_humidity(hours, temperatures):
    """Generate humidity with weather patterns"""
    humidity = []
    humidity_noise = 0
    
    for i, temp in enumerate(temperatures):
        day_of_year = i // 24
        base_humidity = 75 - (temp - 10) * 1.1
        seasonal_factor = 8 * np.sin(2 * np.pi * (day_of_year - 120) / 365)
        humidity_noise = 0.9 * humidity_noise + 0.1 * np.random.normal(0, 7)
        
        hum = base_humidity + seasonal_factor + humidity_noise
        humidity.append(np.clip(hum, 35, 95))
    
    return humidity

def generate_realistic_cloud_cover(hours, humidity, temperatures):
    """Generate cloud cover with weather systems"""
    cloud_cover = []
    prev_clouds = 50
    
    for i, (hum, temp) in enumerate(zip(humidity, temperatures)):
        base_clouds = (hum - 35) * 0.9
        temp_factor = -4 * ((temp - 20) / 20) ** 2
        
        clouds = 0.85 * prev_clouds + 0.15 * (base_clouds + temp_factor) + np.random.normal(0, 7)
        clouds = np.clip(clouds, 5, 95)
        
        cloud_cover.append(clouds)
        prev_clouds = clouds
    
    return cloud_cover

def add_temporal_features(df):
    """Add comprehensive temporal features"""
    df['Hour'] = df['Time'].dt.hour
    df['DayOfWeek'] = df['Time'].dt.dayofweek
    df['Month'] = df['Time'].dt.month
    df['DayOfYear'] = df['Time'].dt.dayofyear
    df['IsWeekend'] = df['DayOfWeek'].isin([5, 6]).astype(int)
    
    df['IsHoliday'] = (
        ((df['Time'].dt.month == 12) & (df['Time'].dt.day.between(24, 31))) |
        ((df['Time'].dt.month == 1) & (df['Time'].dt.day == 1)) |
        ((df['Time'].dt.month == 7) & (df['Time'].dt.day == 4)) |
        ((df['Time'].dt.month == 11) & (df['Time'].dt.day.between(22, 28))) |
        ((df['Time'].dt.month == 3) & (df['Time'].dt.day.between(15, 22)))
    ).astype(int)
    
    df['IsSchoolVacation'] = df['Month'].isin([6, 7, 8]).astype(int)
    df['IsPeakHour'] = df['Hour'].isin([7, 8, 9, 17, 18, 19, 20]).astype(int)
    
    return df

def generate_realistic_occupancy(df, building_type, building_size_factor, building_id=0):
    """Generate realistic occupancy with UNIQUE patterns per building"""
    occupancy = []
    base_min, base_max = occupancy_range[building_type]
    prev_occupancy = 0.5
    
    base_min = int(base_min * building_size_factor)
    base_max = int(base_max * building_size_factor)
    
    # PATTERNS UNIQUES pour chaque maison
    np.random.seed(200 + building_id)
    if building_type == 'House':
        # Certaines familles voyagent en été, d'autres en hiver
        vacation_month = np.random.choice([7, 8, 12, 0])  # Juillet, Août, Décembre, ou pas de vacances
        weekend_activity = np.random.uniform(0.6, 0.9)  # Certains sortent plus le weekend
        work_from_home = np.random.choice([True, False])  # Certains en télétravail
    
    for idx, row in df.iterrows():
        hour = row['Hour']
        day_of_week = row['DayOfWeek']
        is_weekend = row['IsWeekend']
        is_holiday = row['IsHoliday']
        is_school_vacation = row.get('IsSchoolVacation', 0)
        month = row['Month']
        
        if building_type == 'House':
            # Pattern unique par maison
            if vacation_month > 0 and month == vacation_month:
                # Famille en vacances ce mois
                target_level = 0.15
            elif hour in [6, 7, 8]:
                target_level = 0.85
            elif hour in [9, 10, 11, 12, 13, 14, 15, 16]:
                if work_from_home:
                    target_level = 0.65  # Télétravail
                else:
                    target_level = 0.25 if not is_weekend else weekend_activity
            elif hour in [17, 18, 19, 20, 21, 22]:
                target_level = 0.95
            elif hour in [23, 0, 1, 2, 3, 4, 5]:
                target_level = 1.0
            else:
                target_level = 0.5
        
        elif building_type == 'Hospital':
            if hour in [7, 15, 23]:
                target_level = 0.90
            elif hour in [0, 1, 2, 3, 4, 5]:
                target_level = 0.50
            elif hour in [9, 10, 11, 14, 15, 16]:
                target_level = 0.85
            else:
                target_level = 0.70
        
        elif building_type == 'School':
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
        
        elif building_type == 'Office':
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
        
        elif building_type == 'Industry':
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

def generate_solar_radiation(hours, cloud_cover):
    """Generate solar radiation"""
    solar = []
    for hour in range(hours):
        hour_of_day = hour % 24
        day_of_year = hour // 24
        clouds = cloud_cover[hour]
        
        seasonal_factor = 0.7 + 0.3 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
        
        if 6 <= hour_of_day <= 18:
            daily_pattern = np.sin(np.pi * (hour_of_day - 6) / 12)
        else:
            daily_pattern = 0
        
        cloud_factor = 1 - (clouds / 140)
        
        solar_radiation = 950 * seasonal_factor * daily_pattern * cloud_factor
        solar.append(max(0, solar_radiation))
    
    return solar

def generate_realistic_lighting(df, building_type, cloud_cover, solar_radiation, building_efficiency, occupancy):
    """Generate realistic lighting consumption"""
    lighting = []
    base_min, base_max = lighting_range[building_type]
    
    base_max = base_max * building_efficiency
    
    for idx, row in df.iterrows():
        hour = row['Hour']
        solar = solar_radiation[idx]
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        is_school_vacation = row.get('IsSchoolVacation', 0)
        
        natural_light = solar / 950
        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0
        
        if building_type == 'School' and is_school_vacation:
            lighting_need = 0.08
        elif building_type == 'Hospital':
            if hour in [0, 1, 2, 3, 4, 5]:
                lighting_need = 0.40 * occupancy_factor
            else:
                lighting_need = (1 - natural_light * 0.7) * occupancy_factor
        elif occupancy_factor < 0.1:
            lighting_need = 0.08 * occupancy_factor
        else:
            lighting_need = (1 - natural_light * 0.75) * occupancy_factor
        
        if building_type in ['Office', 'School'] and occupancy_factor < 0.3:
            lighting_need *= 0.6
        
        light = base_min + (base_max - base_min) * np.clip(lighting_need, 0, 1)
        lighting.append(max(0, light + np.random.normal(0, 0.025 * light)))
    
    return lighting

def generate_realistic_hvac(df, building_type, temperatures, solar_radiation, building_insulation, occupancy):
    """Generate realistic HVAC consumption"""
    hvac = []
    base_min, base_max = hvac_range[building_type]
    comfort_temp = 21
    indoor_temp = comfort_temp
    
    for idx, row in df.iterrows():
        outdoor_temp = temperatures[idx]
        occ = occupancy[idx]
        max_occupancy = occupancy_range[building_type][1]
        hour = row['Hour']
        solar = solar_radiation[idx]
        is_school_vacation = row.get('IsSchoolVacation', 0)
        
        indoor_temp = 0.88 * indoor_temp + 0.12 * outdoor_temp
        
        solar_gain = solar / 48000
        indoor_temp += solar_gain
        
        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0
        internal_gain = occupancy_factor * 1.3
        indoor_temp += internal_gain
        
        temp_diff = abs(indoor_temp - comfort_temp)
        
        if building_type == 'School' and is_school_vacation:
            hvac_need = 0.12
        elif building_type == 'Hospital':
            if hour in [0, 1, 2, 3, 4, 5]:
                hvac_need = (temp_diff / (18 * building_insulation)) * 0.75
            else:
                hvac_need = (temp_diff / (18 * building_insulation)) * occupancy_factor
        else:
            hvac_need = (temp_diff / (19 * building_insulation)) * occupancy_factor
        
        if building_type not in ['Hospital']:
            if occupancy_factor < 0.15:
                hvac_need *= 0.35
        
        if row['IsPeakHour'] and occupancy_factor > 0.5:
            time_factor = 1.08
        else:
            time_factor = 0.92
        
        hvac_load = base_min + (base_max - base_min) * np.clip(hvac_need * time_factor, 0, 1.4)
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
        hour = row['Hour']
        is_school_vacation = row.get('IsSchoolVacation', 0)
        
        occupancy_factor = occ / max_occupancy if max_occupancy > 0 else 0
        
        if building_type == 'School' and is_school_vacation:
            base_equipment = 0.08
        else:
            base_equipment = 0.35
        
        if building_type == 'Hospital':
            if 6 <= hour <= 20:
                variable_load = 0.88
            else:
                variable_load = 0.55
        elif building_type == 'Industry':
            variable_load = 0.83 if occupancy_factor > 0.3 else 0.45
        elif building_type == 'School':
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

def generate_building_data(building_type, building_number):
    """Generate highly realistic dataset for one building"""
    
    np.random.seed(42 + building_number)
    random.seed(42 + building_number)
    
    location_offset = np.random.uniform(-4, 4)
    
    if building_type == 'Industry':
        if building_number == 1:
            building_size_factor = np.random.uniform(1.1, 1.3)
        else:
            building_size_factor = np.random.uniform(0.5, 0.9)
    else:
        building_size_factor = np.random.uniform(0.7, 1.3)
    
    building_efficiency = np.random.uniform(0.75, 1.25)
    building_insulation = np.random.uniform(0.7, 1.3)
    building_modernity = np.random.uniform(0.85, 1.15)
    
    # UNIQUE temperature pattern per building
    temperatures = generate_realistic_temperature(hours_per_year, location_offset, building_type, building_number)
    humidity = generate_realistic_humidity(hours_per_year, temperatures)
    cloud_cover = generate_realistic_cloud_cover(hours_per_year, humidity, temperatures)
    solar_radiation = generate_solar_radiation(hours_per_year, cloud_cover)
    
    df = pd.DataFrame({
        'Time': pd.date_range(start='2023-01-01', periods=hours_per_year, freq='H'),
        'Winter': [1 if (i // (hours_per_year // 4)) % 4 == 0 else 0 for i in range(hours_per_year)],
        'Spring': [1 if (i // (hours_per_year // 4)) % 4 == 1 else 0 for i in range(hours_per_year)],
        'Summer': [1 if (i // (hours_per_year // 4)) % 4 == 2 else 0 for i in range(hours_per_year)],
        'Fall': [1 if (i // (hours_per_year // 4)) % 4 == 3 else 0 for i in range(hours_per_year)],
        'Outdoor Temp (°C)': temperatures,
        'Humidity (%)': humidity,
        'Cloud Cover (%)': cloud_cover,
        'Solar Radiation (W/m²)': solar_radiation,
    })
    
    df = add_temporal_features(df)
    
    # UNIQUE occupancy pattern per building
    occupancy_internal = generate_realistic_occupancy(df, building_type, building_size_factor, building_number)
    
    df['Lighting [kW]'] = generate_realistic_lighting(df, building_type, cloud_cover, solar_radiation, building_efficiency, occupancy_internal)
    df['HVAC [kW]'] = generate_realistic_hvac(df, building_type, temperatures, solar_radiation, building_insulation, occupancy_internal)
    df['Special Equipment [kW]'] = generate_realistic_equipment(df, building_type, building_modernity, occupancy_internal)
    
    df['Use [kW]'] = (
        df['Special Equipment [kW]'] + 
        df['Lighting [kW]'] + 
        df['HVAC [kW]']
    ) * (1 + np.random.normal(0, 0.012, len(df)))
    
    df['Use [kW]'] = df['Use [kW]'].clip(lower=0)
    
    df = df.drop(columns=['IsSchoolVacation'], errors='ignore')
    
    return df

# Generate all building data
print("=" * 80)
print("GÉNÉRATION DES DONNÉES ÉNERGÉTIQUES RÉALISTES AVEC PATTERNS UNIQUES")
print("=" * 80)

total_buildings = 0
all_buildings_data = []

for building_type, count in building_counts.items():
    print(f"\n📊 Génération de {count} {building_type}(s):")
    
    for i in range(1, count + 1):
        df = generate_building_data(building_type, total_buildings + i)
        
        if count == 1:
            building_name = f"{building_type}"
        else:
            building_name = f"{building_type}{i}"
        
        df['Building'] = building_name
        all_buildings_data.append(df)
        
        daily_avg = df['Use [kW]'].mean() * 24
        monthly_stats = df.groupby('Month')['Use [kW]'].mean() * 24
        
        print(f"  ✓ {building_name:25s} | Daily Avg: {daily_avg:7.1f} kWh/day")
        print(f"    Jan: {monthly_stats[1]:6.1f} | Feb: {monthly_stats[2]:6.1f} | Jun: {monthly_stats[6]:6.1f} | Sep: {monthly_stats[9]:6.1f} | Dec: {monthly_stats[12]:6.1f}")
        
    total_buildings += count

print("\n📦 Création du fichier global...")
combined_df = pd.concat(all_buildings_data, ignore_index=True)

cols = combined_df.columns.tolist()
cols.remove('Building')
cols.insert(1, 'Building')
combined_df = combined_df[cols]

output_dir = '../data'
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, 'energy_consumption.csv')
combined_df.to_csv(output_path, index=False)
print(f"  ✓ {output_path} | Total rows: {len(combined_df):,}")

print("\n" + "=" * 80)
print(f"✅ SUCCÈS! Dataset avec PATTERNS UNIQUES pour chaque bâtiment")
print(f"📦 Fichier: {output_path}")
print("=" * 80)

print("\n🎯 AMÉLIORATIONS RÉALISTES:")
print("  ✓ Chaque maison a son propre pattern (vacances différentes)")
print("  ✓ Certaines familles voyagent en été, d'autres en hiver")
print("  ✓ Certaines personnes en télétravail (plus de consommation en journée)")
print("  ✓ Activités weekend différentes par famille")
print("  ✓ Plus de minimum artificiel en février/septembre")
print("  ✓ Patterns saisonniers décalés entre bâtiments")
print("  ✓ Amplitudes de variation uniques par bâtiment")
print("=" * 80)