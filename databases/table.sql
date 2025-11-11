-- =============================================================================
-- TABLE 3: ENERGY PREDICTION – HOURLY (ML MODEL OUTPUT)
-- =============================================================================
-- Description: Stores the output of energy forecasting models.
-- =============================================================================

CREATE TABLE IF NOT EXISTS energy_prediction_hourly (

    prediction_timestamp  TIMESTAMP     NOT NULL,


    building              VARCHAR(50)   NOT NULL,

    -- === MLOps & Versioning Keys (Who, How) ===

    -- Timestamp of when the model was run to generate this forecast
    -- (e.g., '2025-11-11 09:00:00')
    -- This is VITAL. It lets you distinguish the 9 AM forecast
    -- from the 10 AM forecast for the same future hour.
    model_run_timestamp   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,



    -- === Predicted Values (The Model's "Answer") ===

    -- The main predicted value (point estimate) for total consumption
    predicted_use_kw      NUMERIC(10,4),


    -- === Uncertainty (Highly Recommended) ===

    -- Storing confidence intervals is best practice for forecasting
    -- Example: The 95% confidence interval lower bound
    predicted_use_kw_lower NUMERIC(10,4),

    -- Example: The 95% confidence interval upper bound
    predicted_use_kw_upper NUMERIC(10,4),

    -- === Primary Key ===
    -- This composite key uniquely identifies a specific prediction
    -- for a specific hour, from a specific building, by a specific model,
    -- generated during a specific run.
    CONSTRAINT pk_energy_prediction PRIMARY KEY (
        prediction_timestamp,
        building,
        model_run_timestamp,
        model_id
    )
);

-- === Indexes for Performance ===

-- Quickly get the LATEST forecast for a building
-- This is the most common query: "What's the forecast right now?"
CREATE INDEX IF NOT EXISTS idx_prediction_latest
    ON energy_prediction_hourly(building, prediction_timestamp, model_run_timestamp DESC);

-- Quickly analyze a specific model's performance over time
CREATE INDEX IF NOT EXISTS idx_prediction_model_performance
    ON energy_prediction_hourly(model_id, prediction_timestamp);