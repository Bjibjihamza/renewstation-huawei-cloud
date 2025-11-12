-- =============================================================================
-- BATTERY SYSTEM TABLES - SILVER LAYER (SIMPLIFIED)
-- =============================================================================
-- Architecture simplifiée:
--   • Focus sur prédictions 7 jours
--   • État actuel réel des batteries (dernières 6h)
--   • 2 batteries: Main (2500 kWh) + Backup (700 kWh)
-- =============================================================================

\c silver;

-- =============================================================================
-- TABLE 1: PREDICTED SOLAR PRODUCTION (NEXT 7 DAYS ONLY)
-- =============================================================================

DROP TABLE IF EXISTS predicted_solar_production CASCADE;

CREATE TABLE predicted_solar_production (
    -- Unique ID (format: YYYYMMDDHH)
    id                          VARCHAR(50)    PRIMARY KEY,
    
    -- Timestamp
    forecast_timestamp          TIMESTAMP      NOT NULL UNIQUE,
    
    -- Données météo sources
    temperature_c               NUMERIC(5,2),
    humidity_pct                NUMERIC(5,2),
    cloud_cover_pct             NUMERIC(5,2),
    solar_radiation_w_m2        NUMERIC(8,2),
    wind_speed_kmh              NUMERIC(6,2),
    
    -- Production calculée (via pvlib)
    ghi_w_m2                    NUMERIC(8,2),
    dni_w_m2                    NUMERIC(8,2),
    dhi_w_m2                    NUMERIC(8,2),
    cell_temperature_c          NUMERIC(5,2),
    
    -- Production système PV (1,364 panneaux × 550W = 750 kWc)
    dc_power_kw                 NUMERIC(10,4),
    ac_power_kw                 NUMERIC(10,4),
    predicted_production_kwh    NUMERIC(10,4),
    
    -- Métadonnées
    created_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_solar_prod_timestamp ON predicted_solar_production(forecast_timestamp);
CREATE INDEX idx_solar_prod_date ON predicted_solar_production(DATE(forecast_timestamp));

COMMENT ON TABLE predicted_solar_production IS 'Production solaire prédite (7 jours futurs uniquement)';


-- =============================================================================
-- TABLE 2: BATTERY STATE (UNIFIED TABLE - REAL + PREDICTED)
-- =============================================================================
-- Table unique contenant:
--   • État ACTUEL réel des batteries (timestamp <= NOW)
--   • Prédictions futures (timestamp > NOW, jusqu'à +7 jours)
-- =============================================================================

DROP TABLE IF EXISTS battery_state CASCADE;

CREATE TABLE battery_state (
    -- Unique ID (format: YYYYMMDDHH_BatteryType)
    id                          VARCHAR(50)    PRIMARY KEY,
    
    -- Timestamp et type
    timestamp                   TIMESTAMP      NOT NULL,
    battery_type                VARCHAR(20)    NOT NULL CHECK (battery_type IN ('main', 'backup')),
    
    -- Indicateur: données réelles ou prédites
    is_predicted                BOOLEAN        NOT NULL DEFAULT TRUE,
    
    -- Capacité batterie (constante par type)
    battery_capacity_kwh        NUMERIC(10,2)  NOT NULL,
    
    -- Flux énergétiques (cette heure)
    solar_production_kwh        NUMERIC(10,4),  -- Production solaire
    consumption_kwh             NUMERIC(10,4),  -- Consommation totale (sum all buildings)
    net_energy_kwh              NUMERIC(10,4),  -- Net = production - consommation
    
    -- État batterie (début et fin de l'heure)
    soc_start_pct               NUMERIC(5,2),   -- State of Charge début (%)
    soc_end_pct                 NUMERIC(5,2),   -- State of Charge fin (%)
    energy_stored_kwh           NUMERIC(10,2),  -- Énergie stockée fin heure (kWh)
    
    -- Flux batterie
    battery_charge_kwh          NUMERIC(10,4),  -- Énergie entrante
    battery_discharge_kwh       NUMERIC(10,4),  -- Énergie sortante
    
    -- Interaction réseau
    grid_import_kwh             NUMERIC(10,4),  -- Import réseau (si batterie vide)
    grid_export_kwh             NUMERIC(10,4),  -- Export réseau (si batterie pleine)
    
    -- Métadonnées
    created_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte unique
    CONSTRAINT uk_battery_time_type UNIQUE (timestamp, battery_type)
);

-- Indexes
CREATE INDEX idx_battery_timestamp ON battery_state(timestamp);
CREATE INDEX idx_battery_type ON battery_state(battery_type);
CREATE INDEX idx_battery_is_predicted ON battery_state(is_predicted);
CREATE INDEX idx_battery_time_type ON battery_state(timestamp, battery_type);

COMMENT ON TABLE battery_state IS 'État batteries unifié: réel (6h passées) + prédit (7j futurs) - Main (2500) + Backup (700)';


-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION generate_timestamp_id(
    p_timestamp TIMESTAMP
) RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION generate_battery_id(
    p_timestamp TIMESTAMP,
    p_battery_type VARCHAR(20)
) RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24') || '_' || p_battery_type;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

