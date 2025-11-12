-- =============================================================================
-- BATTERY SYSTEM TABLES - SILVER LAYER
-- =============================================================================
-- Système de tracking pour 2 batteries:
--   • Main Battery: 2,500 kWh (stockage principal)
--   • Backup Battery: 700 kWh (backup critique)
-- =============================================================================

\c silver;

-- =============================================================================
-- TABLE 1: PREDICTED SOLAR PRODUCTION (NEXT 7 DAYS)
-- =============================================================================
-- Production solaire prédite basée sur weather_forecast_hourly

DROP TABLE IF EXISTS predicted_solar_production CASCADE;

CREATE TABLE predicted_solar_production (
    -- Unique ID (format: YYYYMMDDHH)
    id                          VARCHAR(50)    PRIMARY KEY,
    
    -- Timestamp
    forecast_timestamp          TIMESTAMP      NOT NULL UNIQUE,
    
    -- Données météo sources (depuis weather_forecast_hourly)
    temperature_c               NUMERIC(5,2),
    humidity_pct                NUMERIC(5,2),
    cloud_cover_pct             NUMERIC(5,2),
    solar_radiation_w_m2        NUMERIC(8,2),
    wind_speed_kmh              NUMERIC(6,2),
    
    -- Production calculée (via pvlib)
    ghi_w_m2                    NUMERIC(8,2),   -- Global Horizontal Irradiance
    dni_w_m2                    NUMERIC(8,2),   -- Direct Normal Irradiance
    dhi_w_m2                    NUMERIC(8,2),   -- Diffuse Horizontal Irradiance
    cell_temperature_c          NUMERIC(5,2),   -- Température cellules PV
    
    -- Production système PV (1,364 panneaux × 550W = 750 kWc)
    dc_power_kw                 NUMERIC(10,4),  -- Puissance DC avant onduleur
    ac_power_kw                 NUMERIC(10,4),  -- Puissance AC après onduleur
    predicted_production_kwh    NUMERIC(10,4),  -- Énergie produite cette heure
    
    -- Métadonnées
    created_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_solar_prod_timestamp ON predicted_solar_production(forecast_timestamp);
CREATE INDEX idx_solar_prod_date ON predicted_solar_production(DATE(forecast_timestamp));

COMMENT ON TABLE predicted_solar_production IS 'Production solaire prédite (7 jours) calculée via pvlib depuis weather_forecast_hourly';


-- =============================================================================
-- TABLE 2: HISTORICAL SOLAR PRODUCTION (RÉEL PASSÉ)
-- =============================================================================
-- Production solaire réelle historique

DROP TABLE IF EXISTS historical_solar_production CASCADE;

CREATE TABLE historical_solar_production (
    -- Unique ID (format: YYYYMMDDHH)
    id                          VARCHAR(50)    PRIMARY KEY,
    
    -- Timestamp
    production_timestamp        TIMESTAMP      NOT NULL UNIQUE,
    
    -- Données météo réelles
    temperature_c               NUMERIC(5,2),
    humidity_pct                NUMERIC(5,2),
    cloud_cover_pct             NUMERIC(5,2),
    solar_radiation_w_m2        NUMERIC(8,2),
    
    -- Production réelle
    ghi_w_m2                    NUMERIC(8,2),
    dni_w_m2                    NUMERIC(8,2),
    dhi_w_m2                    NUMERIC(8,2),
    cell_temperature_c          NUMERIC(5,2),
    
    dc_power_kw                 NUMERIC(10,4),
    ac_power_kw                 NUMERIC(10,4),
    actual_production_kwh       NUMERIC(10,4),  -- Énergie réelle produite
    
    -- Métadonnées
    created_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_hist_solar_timestamp ON historical_solar_production(production_timestamp);
CREATE INDEX idx_hist_solar_date ON historical_solar_production(DATE(production_timestamp));

COMMENT ON TABLE historical_solar_production IS 'Production solaire historique réelle (passé)';


-- =============================================================================
-- TABLE 3: PREDICTED BATTERY STATE (NEXT 7 DAYS)
-- =============================================================================
-- État prédit des batteries pour les 7 prochains jours

DROP TABLE IF EXISTS predicted_battery_state CASCADE;

CREATE TABLE predicted_battery_state (
    -- Unique ID (format: YYYYMMDDHH_BatteryType)
    -- Example: 2024120108_main, 2024120108_backup
    id                          VARCHAR(50)    PRIMARY KEY,
    
    -- Timestamp et type
    forecast_timestamp          TIMESTAMP      NOT NULL,
    battery_type                VARCHAR(20)    NOT NULL CHECK (battery_type IN ('main', 'backup')),
    
    -- Capacité batterie (constante par type)
    battery_capacity_kwh        NUMERIC(10,2)  NOT NULL, -- 2500 pour main, 700 pour backup
    
    -- Flux énergétiques prévus (cette heure)
    predicted_solar_production_kwh   NUMERIC(10,4),  -- Production solaire prévue
    predicted_consumption_kwh        NUMERIC(10,4),  -- Consommation prévue (sum all buildings)
    predicted_net_energy_kwh         NUMERIC(10,4),  -- Net = production - consommation
    
    -- État batterie (simulation heure par heure)
    predicted_soc_start_pct     NUMERIC(5,2),   -- State of Charge début heure (%)
    predicted_soc_end_pct       NUMERIC(5,2),   -- State of Charge fin heure (%)
    predicted_energy_stored_kwh NUMERIC(10,2),  -- Énergie stockée fin heure (kWh)
    
    -- Flux batterie
    predicted_battery_charge_kwh    NUMERIC(10,4),  -- Énergie entrante batterie
    predicted_battery_discharge_kwh NUMERIC(10,4),  -- Énergie sortante batterie
    
    -- Interaction avec le réseau
    predicted_grid_import_kwh   NUMERIC(10,4),  -- Import réseau (si batterie vide)
    predicted_grid_export_kwh   NUMERIC(10,4),  -- Export réseau (si batterie pleine + surplus)
    
    -- Métadonnées
    created_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte unique
    CONSTRAINT uk_pred_battery_time_type UNIQUE (forecast_timestamp, battery_type)
);

-- Indexes
CREATE INDEX idx_pred_batt_timestamp ON predicted_battery_state(forecast_timestamp);
CREATE INDEX idx_pred_batt_type ON predicted_battery_state(battery_type);
CREATE INDEX idx_pred_batt_time_type ON predicted_battery_state(forecast_timestamp, battery_type);

COMMENT ON TABLE predicted_battery_state IS 'État prédit des batteries (7 jours) - Main (2500 kWh) et Backup (700 kWh)';


-- =============================================================================
-- TABLE 4: HISTORICAL BATTERY STATE (RÉEL PASSÉ)
-- =============================================================================
-- État historique réel des batteries

DROP TABLE IF EXISTS historical_battery_state CASCADE;

CREATE TABLE historical_battery_state (
    -- Unique ID (format: YYYYMMDDHH_BatteryType)
    id                          VARCHAR(50)    PRIMARY KEY,
    
    -- Timestamp et type
    timestamp                   TIMESTAMP      NOT NULL,
    battery_type                VARCHAR(20)    NOT NULL CHECK (battery_type IN ('main', 'backup')),
    
    -- Capacité batterie
    battery_capacity_kwh        NUMERIC(10,2)  NOT NULL,
    
    -- Flux énergétiques réels (cette heure)
    actual_solar_production_kwh NUMERIC(10,4),  -- Production solaire réelle
    actual_consumption_kwh      NUMERIC(10,4),  -- Consommation réelle (sum all buildings)
    actual_net_energy_kwh       NUMERIC(10,4),  -- Net = production - consommation
    
    -- État batterie réel
    actual_soc_start_pct        NUMERIC(5,2),   -- SOC début heure (%)
    actual_soc_end_pct          NUMERIC(5,2),   -- SOC fin heure (%)
    actual_energy_stored_kwh    NUMERIC(10,2),  -- Énergie stockée fin heure (kWh)
    
    -- Flux batterie réels
    actual_battery_charge_kwh   NUMERIC(10,4),  -- Charge batterie
    actual_battery_discharge_kwh NUMERIC(10,4), -- Décharge batterie
    
    -- Interaction réseau réelle
    actual_grid_import_kwh      NUMERIC(10,4),  -- Import réseau
    actual_grid_export_kwh      NUMERIC(10,4),  -- Export réseau
    
    -- Cycles batterie (compteur cumulatif)
    battery_cycles_count        NUMERIC(10,4),  -- Nombre de cycles depuis installation
    
    -- Métadonnées
    created_at                  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte unique
    CONSTRAINT uk_hist_battery_time_type UNIQUE (timestamp, battery_type)
);

-- Indexes
CREATE INDEX idx_hist_batt_timestamp ON historical_battery_state(timestamp);
CREATE INDEX idx_hist_batt_type ON historical_battery_state(battery_type);
CREATE INDEX idx_hist_batt_time_type ON historical_battery_state(timestamp, battery_type);

COMMENT ON TABLE historical_battery_state IS 'État historique réel des batteries - Main (2500 kWh) et Backup (700 kWh)';


-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Fonction pour générer ID timestamp
CREATE OR REPLACE FUNCTION generate_timestamp_id(
    p_timestamp TIMESTAMP
) RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Fonction pour générer ID avec type batterie
CREATE OR REPLACE FUNCTION generate_battery_id(
    p_timestamp TIMESTAMP,
    p_battery_type VARCHAR(20)
) RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN TO_CHAR(p_timestamp, 'YYYYMMDDHH24') || '_' || p_battery_type;
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- =============================================================================
-- VIEWS UTILES
-- =============================================================================

-- Vue: Production vs Consommation prédite (7 jours)
CREATE OR REPLACE VIEW v_predicted_energy_balance AS
SELECT 
    psp.forecast_timestamp,
    psp.predicted_production_kwh as solar_production_kwh,
    SUM(pec.predicted_use_kw) as total_consumption_kwh,
    psp.predicted_production_kwh - SUM(pec.predicted_use_kw) as net_balance_kwh,
    psp.temperature_c,
    psp.cloud_cover_pct
FROM predicted_solar_production psp
LEFT JOIN predicted_energy_consumption pec 
    ON psp.forecast_timestamp = pec.time_ts
GROUP BY psp.forecast_timestamp, psp.predicted_production_kwh, 
         psp.temperature_c, psp.cloud_cover_pct
ORDER BY psp.forecast_timestamp;

COMMENT ON VIEW v_predicted_energy_balance IS 'Balance énergétique prédite: Production solaire vs Consommation totale (7 jours)';


-- Vue: État batteries prédit avec métriques
CREATE OR REPLACE VIEW v_predicted_battery_summary AS
SELECT 
    forecast_timestamp,
    battery_type,
    battery_capacity_kwh,
    predicted_soc_end_pct as soc_pct,
    predicted_energy_stored_kwh,
    predicted_battery_charge_kwh,
    predicted_battery_discharge_kwh,
    predicted_grid_import_kwh,
    predicted_grid_export_kwh,
    CASE 
        WHEN predicted_soc_end_pct < 20 THEN 'CRITICAL'
        WHEN predicted_soc_end_pct < 50 THEN 'LOW'
        WHEN predicted_soc_end_pct > 90 THEN 'FULL'
        ELSE 'NORMAL'
    END as battery_status
FROM predicted_battery_state
ORDER BY forecast_timestamp, battery_type;

COMMENT ON VIEW v_predicted_battery_summary IS 'Résumé état batteries prédit avec alertes';


-- =============================================================================
-- END OF BATTERY SYSTEM SCHEMA
-- =============================================================================