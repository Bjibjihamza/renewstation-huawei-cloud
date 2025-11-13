// api/src/server.js
// Main Express server entry point

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true
}));
app.use(express.json());
app.use(morgan('dev'));

// Health check endpoint
// =========================================
// HEALTH CHECK – obligatoire pour Docker
// =========================================
// Health check endpoint
// =========================================
// HEALTH CHECK – obligatoire pour Docker
// =========================================
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'OK',
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// Import routes
const solarRoutes = require('./routes/solar.routes');

// API routes
app.use('/api/solar', solarRoutes);

// Root endpoint
// Root endpoint
app.get('/', (req, res) => {
  res.json({
    message: 'RenewStation API',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      solarBase: '/api/solar',

      energyArchive: '/api/solar/energy-consumption-archive',
      energyLive: '/api/solar/energy-consumption-live',

      weatherForecast: '/api/solar/weather-forecast-hourly',
      weatherArchive: '/api/solar/weather-archive-hourly',

      predictedEnergy: '/api/solar/predicted-energy-consumption',

      solarArchive: '/api/solar/solar-production-archive',
      predictedSolar: '/api/solar/predicted-solar-production',

      batteryReal: '/api/solar/battery-state-real',
      batteryPredicted: '/api/solar/battery-state-predicted',
      batteryUnified: '/api/solar/battery-state',

      summary: '/api/solar/summary',
    },
  });
});


// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 RenewStation API running on http://0.0.0.0:${PORT}`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🗄️  Database: ${process.env.DB_NAME}@${process.env.DB_HOST}:${process.env.DB_PORT}`);
});