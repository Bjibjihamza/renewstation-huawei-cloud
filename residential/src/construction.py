import pandas as pd
import numpy as np
import random

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Constants
hours_per_year = 8760
seasons = ['Winter', 'Spring', 'Summer', 'Fall']

# Define how many buildings of each type to generate
building_counts = {
    'Hospital': 1,
    'House': 10,
    'Industry': 5,
    'Office': 4,
    'School': 1
}

# Building-specific ranges with building size variation
occupancy_range = {
    'Hospital': (200, 400),
    'House': (1, 4),
    'Industry': (20, 200),
    'School': (50, 500),
    'Office': (10, 100)
}

special_equipment_range = {
    'Hospital': (200, 500),
    'House': (0.5, 2),
    'Industry': (20, 50),
    'School': (10, 30),
    'Office': (10, 20)
}

lighting_range = {
    'Hospital': (10, 20),
    'House': (0.3, 1.5),
    'Industry': (1, 5),
    'School': (0.5, 2),
    'Office': (0.5, 2)
}

hvac_range = {
    'Hospital': (30, 60),
    'House': (1, 3),
    'Industry': (5, 10),
    'School': (2, 5),
    'Office': (2, 5)
}

def generate_realistic_temperature(hours, location_offset=0):
    """Generate realistic seasonal temperature with regional variation"""
    temperatures = []
    weather_noise = 0
    
    for hour in range(hours):
        day_of_year = hour // 24
        hour_of_day = hour % 24
        
        # Seasonal pattern with location offset
        seasonal_temp = (17.5 + location_offset) + 25.5 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        # Daily cycle (warmer afternoon, cooler night)
        daily_variation = 8 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        
        # Weather patterns with autocorrelation and extreme events
        weather_noise = 0.92 * weather_noise + 0.08 * np.random.normal(0, 3)
        
        # Occasional extreme weather (heatwaves, cold snaps)
        if np.random.random() < 0.001:  # 0.1% chance
            weather_noise += np.random.choice([-10, 10])
        
        temp = seasonal_temp + daily_variation + weather_noise
        temperatures.append(np.clip(temp, -15, 45))
    
    return temperatures

def generate_realistic_humidity(hours, temperatures):
    """Generate humidity with weather patterns"""
    humidity = []
    humidity_noise = 0
    
    for i, temp in enumerate(temperatures):
        day_of_year = i // 24
        
        # Inverse relationship with temperature
        base_humidity = 75 - (temp - 10) * 1.2
        
        # Seasonal variation (summer more humid in some regions)
        seasonal_factor = 10 * np.sin(2 * np.pi * (day_of_year - 120) / 365)
        
        # Weather pattern autocorrelation
        humidity_noise = 0.9 * humidity_noise + 0.1 * np.random.normal(0, 8)
        
        hum = base_humidity + seasonal_factor + humidity_noise
        humidity.append(np.clip(hum, 30, 100))
    
    return humidity

def generate_realistic_cloud_cover(hours, humidity, temperatures):
    """Generate cloud cover with weather systems"""
    cloud_cover = []
    prev_clouds = 50
    
    for i, (hum, temp) in enumerate(zip(humidity, temperatures)):
        # Higher humidity and moderate temps = more clouds
        base_clouds = (hum - 30) * 1.0
        
        # Temperature effect (very hot or cold = clearer skies)
        temp_factor = -5 * ((temp - 20) / 20) ** 2
        
        # Autocorrelation with weather systems (fronts move slowly)
        clouds = 0.85 * prev_clouds + 0.15 * (base_clouds + temp_factor) + np.random.normal(0, 8)
        clouds = np.clip(clouds, 0, 100)
        
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
    
    # Extended holidays
    df['IsHoliday'] = (
        ((df['Time'].dt.month == 12) & (df['Time'].dt.day.between(24, 31))) |  # Christmas week
        ((df['Time'].dt.month == 1) & (df['Time'].dt.day == 1)) |               # New Year
        ((df['Time'].dt.month == 7) & (df['Time'].dt.day == 4)) |               # July 4th
        ((df['Time'].dt.month == 11) & (df['Time'].dt.day.between(22, 28))) |   # Thanksgiving week
        ((df['Time'].dt.month == 3) & (df['Time'].dt.day.between(15, 22))) |    # Spring break
        ((df['Time'].dt.month == 7) & (df['Time'].dt.day.between(1, 15)))       # Summer vacation
    ).astype(int)
    
    # Peak hours (electricity prices often higher)
    df['IsPeakHour'] = df['Hour'].isin([7, 8, 9, 17, 18, 19, 20]).astype(int)
    
    return df

def generate_realistic_occupancy(df, building_type, building_size_factor):
    """Generate realistic occupancy with gradual transitions"""
    occupancy = []
    base_min, base_max = occupancy_range[building_type]
    prev_occupancy = 0.5
    
    # Adjust for building size
    base_min = int(base_min * building_size_factor)
    base_max = int(base_max * building_size_factor)
    
    for idx, row in df.iterrows():
        hour = row['Hour']
        day_of_week = row['DayOfWeek']
        is_weekend = row['IsWeekend']
        is_holiday = row['IsHoliday']
        
        if building_type == 'House':
            # Houses: realistic daily routines
            if hour in [6, 7, 8]:  # Morning rush
                target_level = 0.9
            elif hour in [9, 10, 11, 12, 13, 14, 15, 16]:  # Work hours
                target_level = 0.2 if not is_weekend else 0.7
            elif hour in [17, 18, 19, 20, 21, 22]:  # Evening
                target_level = 0.95
            elif hour in [23, 0, 1, 2, 3, 4, 5]:  # Night
                target_level = 1.0
            else:
                target_level = 0.5
        
        elif building_type == 'Hospital':
            # Hospitals: 24/7 with shift changes
            if hour in [7, 15, 23]:  # Shift changes
                target_level = 0.95
            elif hour in range(0, 6):
                target_level = 0.65
            else:
                target_level = 0.85
        
        elif building_type == 'School':
            # Schools: realistic school schedule
            if is_weekend or is_holiday:
                target_level = 0.02
            elif hour in [7, 8]:  # Arrival
                target_level = 0.6
            elif hour in [9, 10, 11, 12, 13, 14]:  # Classes
                target_level = 0.95
            elif hour == 15:  # Dismissal
                target_level = 0.5
            elif hour in [16, 17]:  # After school activities
                target_level = 0.3
            else:
                target_level = 0.05
        
        elif building_type == 'Office':
            # Offices: realistic work patterns
            if is_weekend:
                target_level = 0.03
            elif is_holiday:
                target_level = 0.01
            elif day_of_week == 4:  # Friday - people leave early
                if hour < 16:
                    target_level = 0.85
                else:
                    target_level = 0.2
            elif hour in [6, 7]:  # Early arrivals
                target_level = 0.15
            elif hour in [8, 9]:  # Morning arrival
                target_level = 0.7
            elif hour in [10, 11, 14, 15, 16]:  # Core work hours
                target_level = 0.9
            elif hour in [12, 13]:  # Lunch (some leave)
                target_level = 0.6
            elif hour in [17, 18]:  # Evening departure
                target_level = 0.4
            else:
                target_level = 0.05
        
        elif building_type == 'Industry':
            # Industry: shift work
            if is_weekend:
                target_level = 0.4  # Weekend shifts
            elif hour in [6, 7, 14, 15, 22, 23]:  # Shift changes
                target_level = 0.95
            elif hour in [8, 9, 10, 11, 12, 13]:  # Day shift
                target_level = 0.9
            elif hour in [16, 17, 18, 19, 20, 21]:  # Evening shift
                target_level = 0.7
            else:  # Night shift
                target_level = 0.5
        else:
            target_level = 0.5
        
        # Smooth transitions (people don't teleport)
        occupancy_level = 0.7 * prev_occupancy + 0.3 * target_level
        prev_occupancy = occupancy_level
        
        # Add random variation
        occupancy_level += np.random.normal(0, 0.05)
        occupancy_level = np.clip(occupancy_level, 0, 1)
        
        occ = int(base_min + (base_max - base_min) * occupancy_level)
        occupancy.append(max(0, occ))
    
    return occupancy

def generate_solar_radiation(hours, cloud_cover):
    """Generate solar radiation (affects cooling load and solar panels)"""
    solar = []
    for hour in range(hours):
        hour_of_day = hour % 24
        day_of_year = hour // 24
        clouds = cloud_cover[hour]
        
        # Seasonal solar intensity
        seasonal_factor = 0.7 + 0.3 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
        
        # Daily solar pattern
        if 6 <= hour_of_day <= 18:
            daily_pattern = np.sin(np.pi * (hour_of_day - 6) / 12)
        else:
            daily_pattern = 0
        
        # Cloud effect (reduces solar radiation)
        cloud_factor = 1 - (clouds / 150)
        
        solar_radiation = 1000 * seasonal_factor * daily_pattern * cloud_factor
        solar.append(max(0, solar_radiation))
    
    return solar

def generate_realistic_lighting(df, building_type, cloud_cover, solar_radiation, building_efficiency):
    """Generate realistic lighting with smart controls and efficiency"""
    lighting = []
    base_min, base_max = lighting_range[building_type]
    
    # Adjust for building efficiency (newer buildings = more efficient)
    base_max = base_max * building_efficiency
    
    for idx, row in df.iterrows():
        hour = row['Hour']
        clouds = cloud_cover[idx]
        solar = solar_radiation[idx]
        occupancy = row['Occupancy']
        max_occupancy = occupancy_range[building_type][1]
        
        # Natural light availability
        natural_light = solar / 1000  # 0 to 1
        
        # Occupancy effect
        occupancy_factor = occupancy / max_occupancy if max_occupancy > 0 else 0
        
        # Lighting need (inverse of natural light)
        if occupancy_factor < 0.1:  # Very low occupancy
            lighting_need = 0.1 * occupancy_factor
        else:
            lighting_need = (1 - natural_light * 0.8) * occupancy_factor
        
        # Add smart lighting behavior (dimming, motion sensors)
        if building_type in ['Office', 'School'] and occupancy_factor < 0.3:
            lighting_need *= 0.5  # Smart sensors reduce lighting
        
        light = base_min + (base_max - base_min) * np.clip(lighting_need, 0, 1)
        lighting.append(max(0, light + np.random.normal(0, 0.03 * light)))
    
    return lighting

def generate_realistic_hvac(df, building_type, temperatures, solar_radiation, building_insulation):
    """Generate realistic HVAC with thermal inertia and building properties"""
    hvac = []
    base_min, base_max = hvac_range[building_type]
    comfort_temp = 21
    indoor_temp = comfort_temp
    
    for idx, row in df.iterrows():
        outdoor_temp = temperatures[idx]
        occupancy = row['Occupancy']
        max_occupancy = occupancy_range[building_type][1]
        hour = row['Hour']
        solar = solar_radiation[idx]
        
        # Thermal inertia (indoor temp changes slowly)
        indoor_temp = 0.9 * indoor_temp + 0.1 * outdoor_temp
        
        # Solar gain (increases indoor temp)
        solar_gain = solar / 50000  # Solar heating effect
        indoor_temp += solar_gain
        
        # Occupancy heat gain
        occupancy_factor = occupancy / max_occupancy if max_occupancy > 0 else 0
        internal_gain = occupancy_factor * 1.5  # People generate heat
        indoor_temp += internal_gain
        
        # Temperature difference from comfort
        temp_diff = abs(indoor_temp - comfort_temp)
        
        # HVAC operates based on difference and building efficiency
        hvac_need = (temp_diff / (20 * building_insulation)) * occupancy_factor
        
        # Setback during unoccupied hours
        if building_type not in ['Hospital']:
            if occupancy_factor < 0.1:
                hvac_need *= 0.3  # Setback mode
        
        # Time of day efficiency (peak vs off-peak)
        if row['IsPeakHour'] and occupancy_factor > 0.5:
            time_factor = 1.1  # Work harder during peak
        else:
            time_factor = 0.9
        
        hvac_load = base_min + (base_max - base_min) * np.clip(hvac_need * time_factor, 0, 1.5)
        hvac.append(max(0, hvac_load + np.random.normal(0, 0.08 * hvac_load)))
    
    return hvac

def generate_realistic_equipment(df, building_type, building_modernity):
    """Generate equipment usage with operational patterns"""
    equipment = []
    base_min, base_max = special_equipment_range[building_type]
    
    # Modern buildings have more equipment but more efficient
    base_max = base_max * building_modernity
    
    for idx, row in df.iterrows():
        occupancy = row['Occupancy']
        max_occupancy = occupancy_range[building_type][1]
        hour = row['Hour']
        is_peak = row['IsPeakHour']
        
        occupancy_factor = occupancy / max_occupancy if max_occupancy > 0 else 0
        
        # Base load (always on equipment)
        base_equipment = 0.4
        
        # Variable load
        if building_type == 'Hospital':
            # Medical equipment - varies by time
            if 6 <= hour <= 20:
                variable_load = 0.9
            else:
                variable_load = 0.6
        elif building_type == 'Industry':
            # Industrial machinery
            variable_load = 0.8 if occupancy_factor > 0.3 else 0.3
        else:
            # Office equipment, appliances
            variable_load = occupancy_factor
        
        equipment_factor = base_equipment + (variable_load * 0.6)
        
        equip = base_min + (base_max - base_min) * equipment_factor
        equipment.append(max(0, equip + np.random.normal(0, 0.04 * equip)))
    
    return equipment

def add_renewable_energy(df, building_type, solar_radiation):
    """Add rooftop solar generation (reduces net consumption)"""
    solar_generation = []
    
    # Not all buildings have solar
    has_solar = building_type in ['School', 'Office', 'Industry']
    solar_capacity = {'School': 50, 'Office': 30, 'Industry': 100}.get(building_type, 0)
    
    if has_solar:
        for solar in solar_radiation:
            # Solar panel efficiency ~20%
            generation = solar_capacity * (solar / 1000) * 0.20
            solar_generation.append(generation)
    else:
        solar_generation = [0] * len(df)
    
    return solar_generation

def generate_building_data(building_type, building_number):
    """Generate highly realistic dataset for one building"""
    
    np.random.seed(42 + building_number)
    random.seed(42 + building_number)
    
    # Building-specific characteristics
    location_offset = np.random.uniform(-3, 3)  # Regional climate variation
    building_size_factor = np.random.uniform(0.7, 1.3)  # Size variation
    building_efficiency = np.random.uniform(0.8, 1.2)  # Lighting efficiency
    building_insulation = np.random.uniform(0.8, 1.2)  # Insulation quality
    building_modernity = np.random.uniform(0.9, 1.1)  # Equipment modernity
    
    # Generate realistic weather
    temperatures = generate_realistic_temperature(hours_per_year, location_offset)
    humidity = generate_realistic_humidity(hours_per_year, temperatures)
    cloud_cover = generate_realistic_cloud_cover(hours_per_year, humidity, temperatures)
    solar_radiation = generate_solar_radiation(hours_per_year, cloud_cover)
    
    # Create base dataframe
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
    
    # Add temporal features
    df = add_temporal_features(df)
    
    # Generate realistic consumption
    df['Occupancy'] = generate_realistic_occupancy(df, building_type, building_size_factor)
    df['Lighting [kW]'] = generate_realistic_lighting(df, building_type, cloud_cover, solar_radiation, building_efficiency)
    df['HVAC [kW]'] = generate_realistic_hvac(df, building_type, temperatures, solar_radiation, building_insulation)
    df['Special Equipment [kW]'] = generate_realistic_equipment(df, building_type, building_modernity)
    df['Solar Generation [kW]'] = add_renewable_energy(df, building_type, solar_radiation)
    
    # Calculate net consumption
    df['Use [kW]'] = (
        df['Special Equipment [kW]'] + 
        df['Lighting [kW]'] + 
        df['HVAC [kW]'] -
        df['Solar Generation [kW]']
    ) * (1 + np.random.normal(0, 0.015, len(df)))  # 1.5% measurement noise
    
    df['Use [kW]'] = df['Use [kW]'].clip(lower=0)
    
    return df

# Generate all building files
print("=" * 70)
print("GENERATING HIGHLY REALISTIC BUILDING ENERGY DATASETS")
print("=" * 70)

total_buildings = 0
all_buildings_data = []  # Store all data for combined file

for building_type, count in building_counts.items():
    print(f"\n📊 Generating {count} {building_type}(s):")
    
    for i in range(1, count + 1):
        df = generate_building_data(building_type, total_buildings + i)
        
        # Add Building column to identify each building
        if count == 1:
            building_name = f"{building_type}"
        else:
            building_name = f"{building_type}{i}"
        
        df['Building'] = building_name
        
        # Save individual file
        filename = f"{building_name}_data.csv"
        df.to_csv(filename, index=False)
        
        # Add to combined dataset
        all_buildings_data.append(df)
        
        avg_use = df['Use [kW]'].mean()
        max_use = df['Use [kW]'].max()
        print(f"  ✓ {filename:25s} | Avg: {avg_use:6.2f} kW | Peak: {max_use:6.2f} kW")
        
    total_buildings += count

# Combine all buildings into one dataset
print("\n📦 Combining all buildings into one file...")
combined_df = pd.concat(all_buildings_data, ignore_index=True)

# Reorder columns to have Building as first column after Time
cols = combined_df.columns.tolist()
cols.remove('Building')
cols.insert(1, 'Building')
combined_df = combined_df[cols]

# Save combined file
combined_df.to_csv('All_Buildings_Combined.csv', index=False)
print(f"  ✓ All_Buildings_Combined.csv | Total rows: {len(combined_df):,}")

print("\n" + "=" * 70)
print(f"✅ SUCCESS! Generated {total_buildings} datasets")
print(f"📊 Individual files: {total_buildings} CSV files")
print(f"📦 Combined file: 1 CSV file with all data")
print("=" * 70)

print("\n🎯 ADVANCED REALISTIC FEATURES:")
print("  ✓ Regional climate variations (location offset)")
print("  ✓ Building size variations (0.7x to 1.3x)")
print("  ✓ Extreme weather events (heatwaves, cold snaps)")
print("  ✓ Thermal inertia (indoor temp changes gradually)")
print("  ✓ Solar radiation modeling")
print("  ✓ Solar gain heating effect")
print("  ✓ Occupancy heat generation")
print("  ✓ Building insulation quality variations")
print("  ✓ Smart lighting controls (motion sensors, dimming)")
print("  ✓ HVAC setback during low occupancy")
print("  ✓ Peak hour load management")
print("  ✓ Smooth occupancy transitions (no teleporting!)")
print("  ✓ Shift changes in hospitals & industries")
print("  ✓ Friday early departure in offices")
print("  ✓ School schedules with after-school activities")
print("  ✓ Renewable energy (solar panels on some buildings)")
print("  ✓ Equipment modernity variations")
print("  ✓ Extended holiday periods")
print("  ✓ Base loads + variable loads")
print("=" * 70)