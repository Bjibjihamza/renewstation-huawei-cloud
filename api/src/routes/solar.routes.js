// api/src/routes/solar.routes.js
// Routes for all energy / weather / solar / battery endpoints

const express = require('express');
const router = express.Router();
const solarController = require('../controllers/solar.controller');

// ---------------------------------------------------------------------------
// ENERGY – ARCHIVE & LIVE
// ---------------------------------------------------------------------------

// Archive
router.get('/energy-consumption-archive', solarController.getEnergyConsumptionArchive);
router.get('/energy-consumption-archive/:id', solarController.getEnergyConsumptionArchiveById);

// Live
router.get('/energy-consumption-live', solarController.getEnergyConsumptionLive);
router.get('/energy-consumption-live/:id', solarController.getEnergyConsumptionLiveById);

// (If you want backward compatibility, you can alias old route here)
// e.g. /energy-consumption-hourly → archive by default
router.get(
  '/energy-consumption-hourly',
  solarController.getEnergyConsumptionArchive
);

// ---------------------------------------------------------------------------
// WEATHER – FORECAST & ARCHIVE
// ---------------------------------------------------------------------------

// Forecast 7d
router.get('/weather-forecast-hourly', solarController.getWeatherForecastHourly);
router.get(
  '/weather-forecast-hourly/:timestamp',
  solarController.getWeatherForecastByTimestamp
);

// Archive
router.get('/weather-archive-hourly', solarController.getWeatherArchiveHourly);
router.get(
  '/weather-archive-hourly/:timestamp',
  solarController.getWeatherArchiveByTimestamp
);

// ---------------------------------------------------------------------------
// PREDICTED ENERGY CONSUMPTION (ML)
// ---------------------------------------------------------------------------

router.get(
  '/predicted-energy-consumption',
  solarController.getPredictedEnergyConsumption
);
router.get(
  '/predicted-energy-consumption/:id',
  solarController.getPredictedEnergyById
);

// ---------------------------------------------------------------------------
// SOLAR PRODUCTION – ARCHIVE & PREDICTED
// ---------------------------------------------------------------------------

// Real / archive
router.get(
  '/solar-production-archive',
  solarController.getSolarProductionArchive
);
router.get(
  '/solar-production-archive/:id',
  solarController.getSolarProductionArchiveById
);

// Predicted 7d
router.get(
  '/predicted-solar-production',
  solarController.getPredictedSolarProduction
);
router.get(
  '/predicted-solar-production/:timestamp',
  solarController.getPredictedSolarByTimestamp
);

// ---------------------------------------------------------------------------
// BATTERY STATE – REAL & PREDICTED
// ---------------------------------------------------------------------------

// Real historical
router.get('/battery-state-real', solarController.getBatteryStateReal);
router.get('/battery-state-real/:id', solarController.getBatteryStateRealById);

// Predicted 7d
router.get(
  '/battery-state-predicted',
  solarController.getBatteryStatePredicted
);
router.get(
  '/battery-state-predicted/:id',
  solarController.getBatteryStatePredictedById
);

// Unified (for dashboard if you want one endpoint)
router.get('/battery-state', solarController.getBatteryStateUnified);

// ---------------------------------------------------------------------------
// SUMMARY
// ---------------------------------------------------------------------------

router.get('/summary', solarController.getSummary);

module.exports = router;
