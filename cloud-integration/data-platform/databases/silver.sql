-- =============================================================================
-- SILVER LAYER – CLEAN SCHEMA (ENERGY + WEATHER + SOLAR + BATTERY)
-- Aligned with:
--   - src/pipeline/load/*.py
--   - src/pipeline/generator/*.py
--   - initialization_pipeline + daily_prediction_pipeline DAGs
-- =============================================================================

-- Connect to silver DB (for psql usage)
\c silver;

-- =============================================================================
-- HELPER FUNCTIONS FOR IDS
-- =============================================================================

CREATE OR REPLACE FUNCTION generate_energy_id(p_timestamp TIMESTAMP, p_building VARCHAR(50))
RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24') || '_' || p_building;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION generate_battery_id(p_timestamp TIMESTAMP, p_type VARCHAR(20))
RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24') || '_' || p_type;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- 1. ENERGY CONSUMPTION – ARCHIVE (historique complet)
-- =============================================================================

DROP TABLE IF EXISTS energy_consumption_hourly_archive CASCADE;

CREATE TABLE energy_consumption_hourly_archive (
    id                     VARCHAR(50) PRIMARY KEY,
    time_ts                TIMESTAMP NOT NULL,
    building               VARCHAR(50) NOT NULL,
    
    -- Flags saisonniers
    winter_flag            SMALLINT NOT NULL,
    spring_flag            SMALLINT NOT NULL,
    summer_flag            SMALLINT NOT NULL,
    fall_flag              SMALLINT NOT NULL,

    -- Météo réelle / features météo
    outdoor_temp_c         NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),

    -- Features temporelles
    hour_of_day            SMALLINT NOT NULL,
    day_of_week            SMALLINT NOT NULL,
    month_num              SMALLINT NOT NULL,
    day_of_year            SMALLINT NOT NULL,
    is_weekend             SMALLINT NOT NULL,
    is_holiday             SMALLINT NOT NULL,
    is_peak_hour           SMALLINT NOT NULL,

    -- Consommation détaillée
    lighting_kw            NUMERIC(10,4),
    hvac_kw                NUMERIC(10,4),
    special_equipment_kw   NUMERIC(10,4),
    use_kw                 NUMERIC(10,4),

    CONSTRAINT uk_archive_time_building UNIQUE (time_ts, building)
);

CREATE INDEX idx_archive_time     ON energy_consumption_hourly_archive(time_ts);
CREATE INDEX idx_archive_building ON energy_consumption_hourly_archive(building);

-- =============================================================================
-- 2. ENERGY CONSUMPTION – LIVE (dernières heures)
-- =============================================================================

DROP TABLE IF EXISTS energy_consumption_hourly_live CASCADE;

CREATE TABLE energy_consumption_hourly_live (
    id                     VARCHAR(50) PRIMARY KEY,
    time_ts                TIMESTAMP NOT NULL,
    building               VARCHAR(50) NOT NULL,
    
    winter_flag            SMALLINT NOT NULL,
    spring_flag            SMALLINT NOT NULL,
    summer_flag            SMALLINT NOT NULL,
    fall_flag              SMALLINT NOT NULL,

    outdoor_temp_c         NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),

    hour_of_day            SMALLINT NOT NULL,
    day_of_week            SMALLINT NOT NULL,
    month_num              SMALLINT NOT NULL,
    day_of_year            SMALLINT NOT NULL,
    is_weekend             SMALLINT NOT NULL,
    is_holiday             SMALLINT NOT NULL,
    is_peak_hour           SMALLINT NOT NULL,

    lighting_kw            NUMERIC(10,4),
    hvac_kw                NUMERIC(10,4),
    special_equipment_kw   NUMERIC(10,4),
    use_kw                 NUMERIC(10,4),

    CONSTRAINT uk_live_time_building UNIQUE (time_ts, building)
);

CREATE INDEX idx_live_time     ON energy_consumption_hourly_live(time_ts);
CREATE INDEX idx_live_building ON energy_consumption_hourly_live(building);

-- =============================================================================
-- 3. PREDICTED ENERGY CONSUMPTION (ML) – HOURLY
--    → used by load_predicted_energy_consumption_to_db
-- =============================================================================

DROP TABLE IF EXISTS predicted_energy_consumption_hourly CASCADE;

-- Same structure as live (id, time_ts, building, flags, features, use_kw)
CREATE TABLE predicted_energy_consumption_hourly (
    id                     VARCHAR(50) PRIMARY KEY,
    time_ts                TIMESTAMP NOT NULL,
    building               VARCHAR(50) NOT NULL,
    
    winter_flag            SMALLINT NOT NULL,
    spring_flag            SMALLINT NOT NULL,
    summer_flag            SMALLINT NOT NULL,
    fall_flag              SMALLINT NOT NULL,

    outdoor_temp_c         NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),

    hour_of_day            SMALLINT NOT NULL,
    day_of_week            SMALLINT NOT NULL,
    month_num              SMALLINT NOT NULL,
    day_of_year            SMALLINT NOT NULL,
    is_weekend             SMALLINT NOT NULL,
    is_holiday             SMALLINT NOT NULL,
    is_peak_hour           SMALLINT NOT NULL,

    lighting_kw            NUMERIC(10,4),
    hvac_kw                NUMERIC(10,4),
    special_equipment_kw   NUMERIC(10,4),
    use_kw                 NUMERIC(10,4),

    CONSTRAINT uk_pred_energy_time_building UNIQUE (time_ts, building)
);

CREATE INDEX idx_pred_energy_time     ON predicted_energy_consumption_hourly(time_ts);
CREATE INDEX idx_pred_energy_building ON predicted_energy_consumption_hourly(building);

-- =============================================================================
-- 4. WEATHER – ARCHIVE (historique météo horaire)
-- =============================================================================

DROP TABLE IF EXISTS weather_archive_hourly CASCADE;

CREATE TABLE weather_archive_hourly (
    forecast_timestamp              TIMESTAMP PRIMARY KEY,
    forecast_date                   DATE NOT NULL,
    forecast_time                   TIME NOT NULL,
    
    temperature_c                   NUMERIC(5,2),
    humidity_pct                    NUMERIC(5,2),
    precipitation_mm                NUMERIC(6,2),
    precipitation_probability_pct   NUMERIC(5,2),
    weather_conditions              VARCHAR(100),
    wind_speed_kmh                  NUMERIC(6,2),
    wind_direction_deg              NUMERIC(5,2),
    pressure_hpa                    NUMERIC(7,2),
    cloud_cover_pct                 NUMERIC(5,2),
    solar_radiation_w_m2            NUMERIC(8,2),
    
    created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weather_archive_date ON weather_archive_hourly(forecast_date);

-- =============================================================================
-- 5. WEATHER – FORECAST (prévisions 7j, utilisées puis archivées)
-- =============================================================================

DROP TABLE IF EXISTS weather_forecast_hourly CASCADE;

CREATE TABLE weather_forecast_hourly (
    forecast_timestamp              TIMESTAMP PRIMARY KEY,
    forecast_date                   DATE NOT NULL,
    forecast_time                   TIME NOT NULL,
    
    temperature_c                   NUMERIC(5,2),
    humidity_pct                    NUMERIC(5,2),
    precipitation_mm                NUMERIC(6,2),
    precipitation_probability_pct   NUMERIC(5,2),
    weather_conditions              VARCHAR(100),
    wind_speed_kmh                  NUMERIC(6,2),
    wind_direction_deg              NUMERIC(5,2),
    pressure_hpa                    NUMERIC(7,2),
    cloud_cover_pct                 NUMERIC(5,2),
    solar_radiation_w_m2            NUMERIC(8,2)
);

CREATE INDEX idx_weather_forecast_date  ON weather_forecast_hourly(forecast_date);
CREATE INDEX idx_weather_forecast_range ON weather_forecast_hourly(forecast_timestamp);

-- =============================================================================
-- 6. SOLAR PRODUCTION – ARCHIVE (réelle, historique)
-- =============================================================================

DROP TABLE IF EXISTS solar_production_archive CASCADE;

CREATE TABLE solar_production_archive (
    id                     VARCHAR(50) PRIMARY KEY,
    timestamp              TIMESTAMP NOT NULL UNIQUE,
    
    temperature_c          NUMERIC(5,2),
    humidity_pct           NUMERIC(5,2),
    cloud_cover_pct        NUMERIC(5,2),
    solar_radiation_w_m2   NUMERIC(8,2),
    
    ghi_w_m2               NUMERIC(8,2),
    dni_w_m2               NUMERIC(8,2),
    dhi_w_m2               NUMERIC(8,2),
    cell_temperature_c     NUMERIC(5,2),
    
    dc_power_kw            NUMERIC(10,4),
    ac_power_kw            NUMERIC(10,4),
    real_production_kwh    NUMERIC(10,4),
    
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_solar_archive_ts ON solar_production_archive(timestamp);

-- =============================================================================
-- 7. PREDICTED SOLAR PRODUCTION (7 jours futurs)
--    → used by load_predicted_solar_production
-- =============================================================================

DROP TABLE IF EXISTS predicted_solar_production CASCADE;

CREATE TABLE predicted_solar_production (
    timestamp                TIMESTAMPTZ PRIMARY KEY,
    temperature_c            DOUBLE PRECISION,
    humidity_pct             DOUBLE PRECISION,
    cloud_cover_pct          DOUBLE PRECISION,
    solar_radiation_w_m2     DOUBLE PRECISION,
    ghi_w_m2                 DOUBLE PRECISION,
    dni_w_m2                 DOUBLE PRECISION,
    dhi_w_m2                 DOUBLE PRECISION,
    cell_temperature_c       DOUBLE PRECISION,
    dc_power_kw              DOUBLE PRECISION,
    ac_power_kw              DOUBLE PRECISION,
    predicted_production_kwh DOUBLE PRECISION
);

-- =======================================================
-- BATTERY TABLES (CLEAN VERSION)
-- =======================================================

DROP TABLE IF EXISTS battery_state_real CASCADE;
DROP TABLE IF EXISTS battery_state_predicted CASCADE;

-- REAL BATTERY STATE (historical / J-1)
CREATE TABLE battery_state_real (
    id                          VARCHAR(50) UNIQUE,
    timestamp                   TIMESTAMP NOT NULL,
    battery_type                VARCHAR(20) NOT NULL CHECK (battery_type IN ('main','backup')),
    battery_capacity_kwh        NUMERIC(10,2) NOT NULL,
    solar_production_kwh        NUMERIC(10,4),
    consumption_kwh             NUMERIC(10,4),
    net_energy_kwh              NUMERIC(10,4),
    soc_start_pct               NUMERIC(5,2),
    soc_end_pct                 NUMERIC(5,2),
    energy_stored_kwh           NUMERIC(10,2),
    battery_charge_kwh          NUMERIC(10,4),
    battery_discharge_kwh       NUMERIC(10,4),
    grid_import_kwh             NUMERIC(10,4),
    grid_export_kwh             NUMERIC(10,4),
    is_predicted                BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (timestamp, battery_type)
);

CREATE INDEX idx_battery_real_ts   ON battery_state_real(timestamp);
CREATE INDEX idx_battery_real_type ON battery_state_real(battery_type);

-- PREDICTED BATTERY STATE (7 days forecast)
CREATE TABLE battery_state_predicted (
    id                          VARCHAR(50) UNIQUE,
    timestamp                   TIMESTAMP NOT NULL,
    battery_type                VARCHAR(20) NOT NULL CHECK (battery_type IN ('main','backup')),
    battery_capacity_kwh        NUMERIC(10,2) NOT NULL,
    solar_production_kwh        NUMERIC(10,4),
    consumption_kwh             NUMERIC(10,4),
    net_energy_kwh              NUMERIC(10,4),
    soc_start_pct               NUMERIC(5,2),
    soc_end_pct                 NUMERIC(5,2),
    energy_stored_kwh           NUMERIC(10,2),
    battery_charge_kwh          NUMERIC(10,4),
    battery_discharge_kwh       NUMERIC(10,4),
    grid_import_kwh             NUMERIC(10,4),
    grid_export_kwh             NUMERIC(10,4),
    is_predicted                BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (timestamp, battery_type)
);

CREATE INDEX idx_battery_pred_ts   ON battery_state_predicted(timestamp);
CREATE INDEX idx_battery_pred_type ON battery_state_predicted(battery_type);


-- =============================================================================
-- 10. PIPELINE METADATA (flags techniques pour DAGs)
--     → used by initialization_pipeline.mark_initialization_complete
-- =============================================================================

DROP TABLE IF EXISTS pipeline_metadata CASCADE;

CREATE TABLE pipeline_metadata (
    key        VARCHAR(100) PRIMARY KEY,
    value      TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- FIN DU SCHÉMA SILVER
-- =============================================================================
