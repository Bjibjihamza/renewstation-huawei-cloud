// api/src/controllers/solar.controller.js
// Controllers for all energy / weather / solar / battery endpoints

const db = require('../config/database');

// Helper function for pagination
const getPaginationParams = (req) => {
  const page = parseInt(req.query.page, 10) || 1;
  const limit = parseInt(req.query.limit, 10) || 100;
  const offset = (page - 1) * limit;
  return { page, limit, offset };
};

// Small helper to build a standard paginated response
const buildPaginatedResponse = (total, rows, page, limit) => ({
  count: total,
  results: rows,
  page,
  totalPages: Math.ceil(total / limit),
});

// ============================================================================
// 1. ENERGY CONSUMPTION – ARCHIVE (historique complet)
//    TABLE: energy_consumption_hourly_archive
// ============================================================================

exports.getEnergyConsumptionArchive = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM energy_consumption_hourly_archive'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM energy_consumption_hourly_archive
       ORDER BY time_ts DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching energy consumption (archive):', error);
    res.status(500).json({ error: 'Failed to fetch energy consumption archive' });
  }
};

exports.getEnergyConsumptionArchiveById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query(
      'SELECT * FROM energy_consumption_hourly_archive WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Archive record not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching energy consumption archive by ID:', error);
    res.status(500).json({ error: 'Failed to fetch archive energy record' });
  }
};

// ============================================================================
// 2. ENERGY CONSUMPTION – LIVE (dernières heures)
//    TABLE: energy_consumption_hourly_live
// ============================================================================

exports.getEnergyConsumptionLive = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM energy_consumption_hourly_live'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM energy_consumption_hourly_live
       ORDER BY time_ts DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching energy consumption (live):', error);
    res.status(500).json({ error: 'Failed to fetch live energy consumption' });
  }
};

exports.getEnergyConsumptionLiveById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query(
      'SELECT * FROM energy_consumption_hourly_live WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Live record not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching live energy consumption by ID:', error);
    res.status(500).json({ error: 'Failed to fetch live energy record' });
  }
};

// ============================================================================
// 3. WEATHER – FORECAST (7 jours futurs)
//    TABLE: weather_forecast_hourly
// ============================================================================

exports.getWeatherForecastHourly = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM weather_forecast_hourly'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM weather_forecast_hourly
       ORDER BY forecast_timestamp DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching weather forecast:', error);
    res.status(500).json({ error: 'Failed to fetch weather forecast data' });
  }
};

exports.getWeatherForecastByTimestamp = async (req, res) => {
  try {
    const { timestamp } = req.params;

    const result = await db.query(
      'SELECT * FROM weather_forecast_hourly WHERE forecast_timestamp = $1',
      [timestamp]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Forecast not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching weather forecast by timestamp:', error);
    res.status(500).json({ error: 'Failed to fetch weather forecast' });
  }
};

// ============================================================================
// 4. WEATHER – ARCHIVE (historique)
//    TABLE: weather_archive_hourly
// ============================================================================

exports.getWeatherArchiveHourly = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM weather_archive_hourly'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM weather_archive_hourly
       ORDER BY forecast_timestamp DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching weather archive:', error);
    res.status(500).json({ error: 'Failed to fetch weather archive data' });
  }
};

exports.getWeatherArchiveByTimestamp = async (req, res) => {
  try {
    const { timestamp } = req.params;

    const result = await db.query(
      'SELECT * FROM weather_archive_hourly WHERE forecast_timestamp = $1',
      [timestamp]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Weather archive record not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching weather archive by timestamp:', error);
    res.status(500).json({ error: 'Failed to fetch weather archive record' });
  }
};

// ============================================================================
// 5. PREDICTED ENERGY CONSUMPTION (ML, HOURLY)
//    TABLE: predicted_energy_consumption_hourly
// ============================================================================

exports.getPredictedEnergyConsumption = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM predicted_energy_consumption_hourly'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM predicted_energy_consumption_hourly
       ORDER BY time_ts DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching predicted energy:', error);
    res.status(500).json({ error: 'Failed to fetch predicted energy data' });
  }
};

exports.getPredictedEnergyById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query(
      'SELECT * FROM predicted_energy_consumption_hourly WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Predicted energy record not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching predicted energy by ID:', error);
    res.status(500).json({ error: 'Failed to fetch predicted energy record' });
  }
};

// ============================================================================
// 6. SOLAR PRODUCTION – ARCHIVE (réelle)
//    TABLE: solar_production_archive
// ============================================================================

exports.getSolarProductionArchive = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM solar_production_archive'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM solar_production_archive
       ORDER BY timestamp DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching solar archive:', error);
    res.status(500).json({ error: 'Failed to fetch solar archive data' });
  }
};

exports.getSolarProductionArchiveById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query(
      'SELECT * FROM solar_production_archive WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Solar archive record not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching solar archive by ID:', error);
    res.status(500).json({ error: 'Failed to fetch solar archive record' });
  }
};

// ============================================================================
// 7. PREDICTED SOLAR PRODUCTION (7 jours futurs)
//    TABLE: predicted_solar_production
//    NOTE: no "id" column, primary key = timestamp
// ============================================================================

// PREDICTED SOLAR PRODUCTION
exports.getPredictedSolarProduction = async (req, res) => {
  try {
    const { limit, offset } = getPaginationParams(req);
    
    const countResult = await db.query('SELECT COUNT(*) FROM predicted_solar_production');
    const total = parseInt(countResult.rows[0].count, 10);
    
    const result = await db.query(
      `SELECT * FROM predicted_solar_production 
       ORDER BY timestamp DESC 
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );
    
    res.json({
      count: total,
      results: result.rows,
      page: Math.floor(offset / limit) + 1,
      totalPages: Math.ceil(total / limit)
    });
  } catch (error) {
    console.error('Error fetching solar production:', error);
    res.status(500).json({ error: 'Failed to fetch solar production data' });
  }
};


exports.getPredictedSolarByTimestamp = async (req, res) => {
  try {
    const { timestamp } = req.params;

    const result = await db.query(
      'SELECT * FROM predicted_solar_production WHERE timestamp = $1',
      [timestamp]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Predicted solar record not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching predicted solar by timestamp:', error);
    res.status(500).json({ error: 'Failed to fetch predicted solar record' });
  }
};

// ============================================================================
// 8. BATTERY STATE – REAL (J-1, historique)
//    TABLE: battery_state_real
// ============================================================================

exports.getBatteryStateReal = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM battery_state_real'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM battery_state_real
       ORDER BY timestamp DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching real battery state:', error);
    res.status(500).json({ error: 'Failed to fetch real battery state data' });
  }
};

exports.getBatteryStateRealById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query(
      'SELECT * FROM battery_state_real WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Real battery state not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching real battery state by ID:', error);
    res.status(500).json({ error: 'Failed to fetch real battery state' });
  }
};

// ============================================================================
// 9. BATTERY STATE – PREDICTED (7 jours futurs)
//    TABLE: battery_state_predicted
// ============================================================================

exports.getBatteryStatePredicted = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);

    const countResult = await db.query(
      'SELECT COUNT(*) FROM battery_state_predicted'
    );
    const total = parseInt(countResult.rows[0].count, 10);

    const result = await db.query(
      `SELECT *
       FROM battery_state_predicted
       ORDER BY timestamp DESC
       LIMIT $1 OFFSET $2`,
      [limit, offset]
    );

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching predicted battery state:', error);
    res.status(500).json({ error: 'Failed to fetch predicted battery state data' });
  }
};

exports.getBatteryStatePredictedById = async (req, res) => {
  try {
    const { id } = req.params;

    const result = await db.query(
      'SELECT * FROM battery_state_predicted WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Predicted battery state not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    console.error('Error fetching predicted battery state by ID:', error);
    res.status(500).json({ error: 'Failed to fetch predicted battery state' });
  }
};

// OPTIONAL: unified view /battery-state?source=real|predicted|all for frontend
exports.getBatteryStateUnified = async (req, res) => {
  try {
    const { limit, offset, page } = getPaginationParams(req);
    const source = (req.query.source || 'all').toLowerCase();

    let baseQuery;
    if (source === 'real') {
      baseQuery = 'battery_state_real';
    } else if (source === 'predicted') {
      baseQuery = 'battery_state_predicted';
    } else {
      baseQuery = null; // union of both
    }

    let countResult;
    let result;

    if (baseQuery) {
      countResult = await db.query(`SELECT COUNT(*) FROM ${baseQuery}`);
      result = await db.query(
        `SELECT *
         FROM ${baseQuery}
         ORDER BY timestamp DESC
         LIMIT $1 OFFSET $2`,
        [limit, offset]
      );
    } else {
      // UNION ALL both tables
      countResult = await db.query(`
        SELECT
          (SELECT COUNT(*) FROM battery_state_real) +
          (SELECT COUNT(*) FROM battery_state_predicted) AS total
      `);

      result = await db.query(
        `
        SELECT * FROM (
          SELECT *, 'real'      AS source FROM battery_state_real
          UNION ALL
          SELECT *, 'predicted' AS source FROM battery_state_predicted
        ) t
        ORDER BY timestamp DESC
        LIMIT $1 OFFSET $2
        `,
        [limit, offset]
      );
    }

    const total = parseInt(countResult.rows[0].total || countResult.rows[0].count, 10);

    res.json(buildPaginatedResponse(total, result.rows, page, limit));
  } catch (error) {
    console.error('Error fetching unified battery state:', error);
    res.status(500).json({ error: 'Failed to fetch unified battery state' });
  }
};

// ============================================================================
// 10. SUMMARY ENDPOINT
// ============================================================================

exports.getSummary = async (req, res) => {
  try {
    const [
      energyArchiveCount,
      energyLiveCount,
      weatherForecastCount,
      weatherArchiveCount,
      predictedEnergyCount,
      solarArchiveCount,
      predictedSolarCount,
      batteryRealCount,
      batteryPredCount,
    ] = await Promise.all([
      db.query('SELECT COUNT(*) FROM energy_consumption_hourly_archive'),
      db.query('SELECT COUNT(*) FROM energy_consumption_hourly_live'),
      db.query('SELECT COUNT(*) FROM weather_forecast_hourly'),
      db.query('SELECT COUNT(*) FROM weather_archive_hourly'),
      db.query('SELECT COUNT(*) FROM predicted_energy_consumption_hourly'),
      db.query('SELECT COUNT(*) FROM solar_production_archive'),
      db.query('SELECT COUNT(*) FROM predicted_solar_production'),
      db.query('SELECT COUNT(*) FROM battery_state_real'),
      db.query('SELECT COUNT(*) FROM battery_state_predicted'),
    ]);

    res.json({
      tables: {
        energy_consumption_hourly_archive: parseInt(energyArchiveCount.rows[0].count, 10),
        energy_consumption_hourly_live: parseInt(energyLiveCount.rows[0].count, 10),
        weather_forecast_hourly: parseInt(weatherForecastCount.rows[0].count, 10),
        weather_archive_hourly: parseInt(weatherArchiveCount.rows[0].count, 10),
        predicted_energy_consumption_hourly: parseInt(predictedEnergyCount.rows[0].count, 10),
        solar_production_archive: parseInt(solarArchiveCount.rows[0].count, 10),
        predicted_solar_production: parseInt(predictedSolarCount.rows[0].count, 10),
        battery_state_real: parseInt(batteryRealCount.rows[0].count, 10),
        battery_state_predicted: parseInt(batteryPredCount.rows[0].count, 10),
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error fetching summary:', error);
    res.status(500).json({ error: 'Failed to fetch summary' });
  }
};
