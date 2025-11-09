# Building Energy Consumption Dataset Documentation

## 📋 Overview

This dataset contains **highly realistic synthetic building energy consumption data** for 21 buildings across 5 different types over a full calendar year (2023). The data simulates hourly energy usage patterns with realistic weather conditions, occupancy patterns, and building-specific characteristics.

---

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Buildings** | 21 |
| **Time Period** | January 1, 2023 - December 31, 2023 |
| **Temporal Resolution** | Hourly (8,760 hours/year) |
| **Total Rows** | 184,380 (21 buildings × 8,760 hours) |
| **Total Columns** | 22 |
| **File Format** | CSV |

---

## 🏢 Building Distribution

| Building Type | Count | Description |
|---------------|-------|-------------|
| **Hospital** | 1 | 24/7 medical facility with high equipment usage |
| **House** | 10 | Residential homes with daily living patterns |
| **Industry** | 5 | Industrial facilities with shift-based operations |
| **Office** | 4 | Commercial office buildings with business hours |
| **School** | 1 | Educational facility with weekday schedules |

---

## 📁 Files Generated

### Individual Files (21 files)
- `Hospital_data.csv`
- `House1_data.csv` through `House10_data.csv`
- `Industry1_data.csv` through `Industry5_data.csv`
- `Office1_data.csv` through `Office4_data.csv`
- `School_data.csv`

### Combined File
- **`All_Buildings_Combined.csv`** - Single file containing all building data with a `Building` identifier column

---

## 📋 Column Descriptions

### Temporal Features

| Column | Type | Range/Values | Description |
|--------|------|--------------|-------------|
| `Time` | datetime | 2023-01-01 to 2023-12-31 | Timestamp of the observation (hourly) |
| `Building` | string | Building names | Identifier for each building (e.g., "Hospital", "House1", "Industry3") |
| `Hour` | integer | 0-23 | Hour of the day (24-hour format) |
| `DayOfWeek` | integer | 0-6 | Day of week (0=Monday, 6=Sunday) |
| `Month` | integer | 1-12 | Month of the year |
| `DayOfYear` | integer | 1-365 | Day number in the year |
| `IsWeekend` | binary | 0 or 1 | 1 if Saturday or Sunday, 0 otherwise |
| `IsHoliday` | binary | 0 or 1 | 1 if major holiday period, 0 otherwise |
| `IsPeakHour` | binary | 0 or 1 | 1 if peak electricity hours (7-9am, 5-8pm), 0 otherwise |

### Seasonal Indicators (One-Hot Encoded)

| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `Winter` | binary | 0 or 1 | 1 if winter season (Jan-Mar), 0 otherwise |
| `Spring` | binary | 0 or 1 | 1 if spring season (Apr-Jun), 0 otherwise |
| `Summer` | binary | 0 or 1 | 1 if summer season (Jul-Sep), 0 otherwise |
| `Fall` | binary | 0 or 1 | 1 if fall season (Oct-Dec), 0 otherwise |

### Weather Features

| Column | Type | Range | Unit | Description |
|--------|------|-------|------|-------------|
| `Outdoor Temp (°C)` | float | -15 to 45 | Celsius | Outdoor air temperature with seasonal patterns and day/night cycles |
| `Humidity (%)` | float | 30-100 | Percent | Relative humidity (inversely correlated with temperature) |
| `Cloud Cover (%)` | float | 0-100 | Percent | Sky cloud coverage (affects solar radiation and lighting needs) |
| `Solar Radiation (W/m²)` | float | 0-1000 | Watts/m² | Solar energy intensity (affects HVAC cooling load and solar generation) |

### Energy Consumption Features

| Column | Type | Range | Unit | Description |
|--------|------|-------|------|-------------|
| `Occupancy` | integer | Varies by type | People | Number of occupants in the building at the given hour |
| `Lighting [kW]` | float | Varies by type | Kilowatts | Electricity consumption for lighting (affected by natural light and occupancy) |
| `HVAC [kW]` | float | Varies by type | Kilowatts | Heating, Ventilation, and Air Conditioning consumption |
| `Special Equipment [kW]` | float | Varies by type | Kilowatts | Building-specific equipment (medical, industrial machinery, appliances) |
| `Solar Generation [kW]` | float | 0+ | Kilowatts | Solar panel generation (Schools, Offices, Industries only) |
| `Use [kW]` | float | 0+ | Kilowatts | **TARGET VARIABLE** - Total net energy consumption |

---

## 🎯 Target Variable

**`Use [kW]`** - Total building energy consumption

**Calculation:**
```
Use [kW] = Special Equipment [kW] + Lighting [kW] + HVAC [kW] - Solar Generation [kW]
```

- Includes 1.5% measurement noise for realism
- Clipped to minimum of 0 (no negative consumption)
- Primary variable for predictive modeling

---

## 🏗️ Building Type Characteristics

### 🏥 Hospital
- **Occupancy Range:** 200-400 people
- **Operation:** 24/7 with shift changes at 7am, 3pm, 11pm
- **Equipment:** High (200-500 kW) - Medical equipment, life support systems
- **HVAC:** High (30-60 kW) - Continuous climate control required
- **Special Features:** Minimal occupancy variation, critical equipment always on

### 🏠 House (10 buildings)
- **Occupancy Range:** 1-4 people
- **Operation:** Peak mornings (6-9am) and evenings (6-11pm), low during work hours
- **Equipment:** Low (0.5-2 kW) - Appliances, electronics
- **HVAC:** Low (1-3 kW) - Residential heating/cooling
- **Special Features:** Natural daily living patterns, weekend variation

### 🏭 Industry (5 buildings)
- **Occupancy Range:** 20-200 people
- **Operation:** Three shifts (day/evening/night), reduced weekend operations
- **Equipment:** Medium-High (20-50 kW) - Industrial machinery
- **HVAC:** Medium (5-10 kW) - Factory floor climate control
- **Special Features:** Shift-based patterns, continuous but variable production

### 🏢 Office (4 buildings)
- **Occupancy Range:** 10-100 people
- **Operation:** Business hours (8am-6pm) weekdays, minimal weekends
- **Equipment:** Medium (10-20 kW) - Computers, office equipment
- **HVAC:** Low-Medium (2-5 kW) - Office comfort
- **Special Features:** Friday early departure, setback during nights/weekends

### 🏫 School
- **Occupancy Range:** 50-500 students/staff
- **Operation:** School hours (7am-4pm) weekdays only, closed holidays
- **Equipment:** Medium (10-30 kW) - Educational technology, cafeteria
- **HVAC:** Low-Medium (2-5 kW) - Classroom comfort
- **Special Features:** After-school activities (4-6pm), extended holiday closures

---

## 🌡️ Realistic Weather Modeling

### Temperature Patterns
- **Seasonal Variation:** Sinusoidal pattern with peak in summer (~35°C) and trough in winter (~0°C)
- **Daily Cycles:** ±8°C variation between day and night
- **Regional Variation:** Each building has location offset (-3°C to +3°C)
- **Extreme Events:** 0.1% chance of heatwaves or cold snaps (±10°C)
- **Autocorrelation:** Weather changes gradually with 92% persistence

### Humidity Patterns
- **Temperature Correlation:** Inversely related (hot = dry, cool = humid)
- **Seasonal Component:** Higher humidity in spring/early summer
- **Autocorrelation:** 90% persistence for realistic weather systems
- **Range:** 30-100% relative humidity

### Cloud Cover
- **Humidity Driven:** More clouds with higher humidity
- **Temperature Effect:** Clearer skies at temperature extremes
- **Autocorrelation:** 85% persistence (weather fronts move slowly)
- **Range:** 0-100% coverage

### Solar Radiation
- **Seasonal Pattern:** Higher in summer, lower in winter
- **Daily Pattern:** Zero at night, peak at noon (sine curve)
- **Cloud Effect:** Reduced by cloud cover (up to 67% reduction)
- **Range:** 0-1000 W/m²

---

## 🔋 Energy Consumption Modeling

### Occupancy Patterns
- **Smooth Transitions:** 70% previous + 30% target (no teleporting!)
- **Building-Specific Schedules:** Realistic daily routines per building type
- **Random Variation:** ±5% noise around target occupancy
- **Holiday Effects:** Reduced occupancy during holiday periods

### Lighting Consumption
- **Natural Light Dependency:** Reduced consumption with higher solar radiation
- **Cloud Effect:** Increased artificial lighting on cloudy days
- **Occupancy Scaling:** Proportional to number of occupants
- **Smart Controls:** Motion sensors reduce lighting at low occupancy (offices/schools)
- **Efficiency Variation:** Buildings have different lighting efficiency (0.8-1.2×)

### HVAC Consumption
- **Thermal Inertia:** Indoor temperature changes gradually (90% persistence)
- **Solar Gain:** Solar radiation increases indoor temperature
- **Occupancy Heat:** People generate heat load
- **Temperature Differential:** Load proportional to |indoor - comfort temp|
- **Setback Mode:** 70% reduction during low occupancy
- **Insulation Quality:** Building-specific efficiency (0.8-1.2×)
- **Peak Hour Load:** 10% increase during peak hours

### Equipment Consumption
- **Base Load:** 40% always-on equipment (servers, refrigeration)
- **Variable Load:** 60% scales with occupancy
- **Building-Specific Patterns:** 
  - Hospitals: Higher during day (medical procedures)
  - Industry: Active during shift hours
  - Others: Proportional to occupancy
- **Modernity Factor:** Newer buildings have more but efficient equipment (0.9-1.1×)

### Solar Generation
- **Coverage:** Schools, Offices, and Industries have rooftop solar
- **Capacity:** School (50 kW), Office (30 kW), Industry (100 kW)
- **Efficiency:** 20% panel efficiency
- **Cloud Effect:** Reduced generation on cloudy days
- **Net Metering:** Subtracted from total consumption

---

## 📈 Data Quality Features

### Realism Enhancements
1. **Building Variations:** Each building has unique characteristics:
   - Size factor (0.7-1.3×)
   - Efficiency rating (0.8-1.2×)
   - Insulation quality (0.8-1.2×)
   - Equipment modernity (0.9-1.1×)

2. **Physical Constraints:**
   - Thermal inertia (temperature doesn't change instantly)
   - Weather autocorrelation (smooth transitions)
   - Occupancy smoothing (gradual changes)

3. **Measurement Noise:** 1.5% random noise on final consumption

4. **No Negative Values:** All consumption values clipped to ≥ 0

---


## 📊 Sample Statistics by Building Type

| Building Type | Avg Use (kW) | Max Use (kW) | Min Use (kW) | Std Dev (kW) |
|--------------|--------------|--------------|--------------|--------------|
| Hospital | ~450 | ~600 | ~300 | ~60 |
| House | ~2.5 | ~5 | ~0.5 | ~1.2 |
| Industry | ~40 | ~80 | ~15 | ~15 |
| Office | ~15 | ~30 | ~2 | ~8 |
| School | ~20 | ~45 | ~1 | ~12 |

*Note: Actual values vary by individual building characteristics*

---
## 🔍 Data Validation

### Quality Checks Performed
✅ No missing values  
✅ No duplicate timestamps per building  
✅ All consumption values ≥ 0  
✅ Temporal features consistent with timestamps  
✅ Weather values within realistic ranges  
✅ Occupancy within building-specific limits  
✅ Smooth transitions (no unrealistic jumps)

---