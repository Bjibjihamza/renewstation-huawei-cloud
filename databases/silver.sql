-- =============================================================================
-- SILVER LAYER – CLEANED / MODELED TABLES (WITH ID SUPPORT)
-- =============================================================================
-- This database represents the SILVER layer of our data warehouse.
--
-- UPDATED: Added unique ID column (YYYYMMDDHH format) for ML predictions
-- =============================================================================

-- ✅ Create the SILVER database (if not exists)
CREATE DATABASE silver;

-- ✅ Switch to SILVER database context
\c silver;

-- =============================================================================
-- TABLE 1: ENERGY CONSUMPTION – HOURLY FACT TABLE (SILVER) - WITH ID
-- =============================================================================

DROP TABLE IF EXISTS energy_consumption_hourly CASCADE;

CREATE TABLE energy_consumption_hourly (
    -- Unique ID for ML predictions (format: YYYYMMDDHH_BuildingName)
    -- Example: 2024010108_Hospital, 2024010108_House1
    id                     VARCHAR(50)    PRIMARY KEY,
    
    -- Time & building identification
    time_ts                TIMESTAMP      NOT NULL,
    building               VARCHAR(50)    NOT NULL,

    -- Season flags (one-hot encoding)
    winter_flag            SMALLINT       NOT NULL,
    spring_flag            SMALLINT       NOT NULL,
    summer_flag            SMALLINT       NOT NULL,
    fall_flag              SMALLINT       NOT NULL,

    -- Weather-related features (REAL DATA from weather_forecast_hourly)
    outdoor_temp_c         NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),

    -- Temporal features
    hour_of_day            SMALLINT       NOT NULL,
    day_of_week            SMALLINT       NOT NULL,
    month_num              SMALLINT       NOT NULL,
    day_of_year            SMALLINT       NOT NULL,
    is_weekend             SMALLINT       NOT NULL,
    is_holiday             SMALLINT       NOT NULL,
    is_peak_hour           SMALLINT       NOT NULL,

    -- Energy consumption components
    lighting_kw            NUMERIC(10,4),
    hvac_kw                NUMERIC(10,4),
    special_equipment_kw   NUMERIC(10,4),
    use_kw                 NUMERIC(10,4),

    -- Unique constraint on timestamp and building (business key)
    CONSTRAINT uk_energy_time_building UNIQUE (time_ts, building)
);

-- Indexes for performance
CREATE INDEX idx_energy_time ON energy_consumption_hourly(time_ts);
CREATE INDEX idx_energy_building ON energy_consumption_hourly(building);
CREATE INDEX idx_energy_time_building ON energy_consumption_hourly(time_ts, building);
CREATE INDEX idx_energy_temporal ON energy_consumption_hourly(month_num, day_of_week, hour_of_day);

-- =============================================================================
-- HELPER FUNCTION: Generate ID from timestamp and building
-- =============================================================================

CREATE OR REPLACE FUNCTION generate_energy_id(
    p_timestamp TIMESTAMP,
    p_building VARCHAR(50)
) RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24') || '_' || p_building;
END;
$$ LANGUAGE plpgsql IMMUTABLE;



-- =============================================================================
-- TABLE 3: WEATHER FORECAST – HOURLY (CASABLANCA, 3-DAY HORIZON)
-- =============================================================================

DROP TABLE IF EXISTS weather_forecast_hourly CASCADE;

CREATE TABLE weather_forecast_hourly (
    -- Clé primaire: timestamp unique pour chaque prévision
    forecast_timestamp TIMESTAMP PRIMARY KEY,
    
    -- Date et heure séparées (pour faciliter les requêtes)
    forecast_date DATE NOT NULL,
    forecast_time TIME NOT NULL,
    
    -- Données météorologiques
    temperature_c NUMERIC(5,2),
    humidity_pct NUMERIC(5,2),
    precipitation_mm NUMERIC(6,2),
    precipitation_probability_pct NUMERIC(5,2),
    weather_conditions VARCHAR(100),
    wind_speed_kmh NUMERIC(6,2),
    wind_direction_deg NUMERIC(5,2),
    pressure_hpa NUMERIC(7,2),
    cloud_cover_pct NUMERIC(5,2),
    solar_radiation_w_m2 NUMERIC(8,2),

    -- Métadonnées de suivi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour accélérer les requêtes
CREATE INDEX idx_weather_forecast_date ON weather_forecast_hourly(forecast_date);
CREATE INDEX idx_weather_forecast_timestamp ON weather_forecast_hourly(forecast_timestamp);
CREATE INDEX idx_weather_conditions ON weather_forecast_hourly(weather_conditions);







-- =============================================================================
-- TABLE: PREDICTED ENERGY CONSUMPTION (FOR ML OUTPUT)
-- =============================================================================

DROP TABLE IF EXISTS predicted_energy_consumption CASCADE;

CREATE TABLE predicted_energy_consumption (
    -- Unique ID (format: YYYYMMDDHH_BuildingName)
    -- Example: 2024010108_Hospital, 2024123123_House1
    id                     VARCHAR(50)    PRIMARY KEY,
    
    -- Time & building identification
    time_ts                TIMESTAMP      NOT NULL,
    building               VARCHAR(50)    NOT NULL,

    -- Season flags (one-hot encoding)
    winter_flag            SMALLINT       NOT NULL,
    spring_flag            SMALLINT       NOT NULL,
    summer_flag            SMALLINT       NOT NULL,
    fall_flag              SMALLINT       NOT NULL,

    -- Weather-related features (from forecast)
    outdoor_temp_c         NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),

    -- Temporal features
    hour_of_day            SMALLINT       NOT NULL,
    day_of_week            SMALLINT       NOT NULL,
    month_num              SMALLINT       NOT NULL,
    day_of_year            SMALLINT       NOT NULL,
    is_weekend             SMALLINT       NOT NULL,
    is_holiday             SMALLINT       NOT NULL,
    is_peak_hour           SMALLINT       NOT NULL,

    -- ML Prediction (to be filled by model - NULL until predicted)
    predicted_use_kw       NUMERIC(10,4)   NULL,
    
    -- Confidence Interval (NULL until predicted)
    predicted_use_kw_min   NUMERIC(10,4)   NULL,  -- Lower bound
    predicted_use_kw_max   NUMERIC(10,4)   NULL,  -- Upper bound

    -- Metadata
    created_at             TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint on timestamp and building
    CONSTRAINT uk_predicted_time_building UNIQUE (time_ts, building)
);

-- Indexes for performance
CREATE INDEX idx_predicted_time ON predicted_energy_consumption(time_ts);
CREATE INDEX idx_predicted_building ON predicted_energy_consumption(building);
CREATE INDEX idx_predicted_time_building ON predicted_energy_consumption(time_ts, building);

-- =============================================================================
-- END OF SILVER LAYER DEFINITION
-- =============================================================================