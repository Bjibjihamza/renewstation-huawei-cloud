import React, { useState, useEffect } from 'react';
import {
  Sun,
  Zap,
  TrendingUp,
  Activity,
  Calendar,
  CloudSun,
  Droplets,
  Wind,
  AlertCircle,
  RefreshCw,
  Database
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const SolarProductionPage = () => {
  const [archiveData, setArchiveData] = useState([]);
  const [predictedData, setPredictedData] = useState([]);
  const [weatherData, setWeatherData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('unknown'); // 'real', 'predicted', or 'unknown'

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [archiveRes, predictedRes, weatherRes] = await Promise.all([
        fetch(`${API_BASE_URL}/solar-production-archive?limit=168`),
        fetch(`${API_BASE_URL}/predicted-solar-production?limit=168`),
        fetch(`${API_BASE_URL}/weather-archive-hourly?limit=24`)
      ]);

      const archive = archiveRes.ok ? (await archiveRes.json()).results || [] : [];
      const predicted = predictedRes.ok ? (await predictedRes.json()).results || [] : [];
      const weather = weatherRes.ok ? (await weatherRes.json()).results || [] : [];

      console.log('Solar Data:', { archive: archive.length, predicted: predicted.length, weather: weather.length });

      if (archive.length > 0) {
        setDataSource('real');
        setArchiveData(archive);
      } else if (predicted.length > 0) {
        setDataSource('predicted');
        setPredictedData(predicted);
      } else {
        setDataSource('unknown');
      }

      setWeatherData(weather);
      setLoading(false);
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const calculateMetrics = () => {
    const data = dataSource === 'real' ? archiveData : predictedData;
    if (!data.length) {
      return { currentPower: 0, todayProduction: 0, weekProduction: 0, efficiency: 0, peakPower: 0, avgRadiation: 0 };
    }

    const sorted = [...data].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    const latest = sorted[0];
    const currentPower = parseFloat(latest.ac_power_kw || 0);

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const todayData = sorted.filter(d => new Date(d.timestamp) >= todayStart);
    const todayProduction = todayData.reduce((sum, d) => {
      const val = dataSource === 'real' ? d.real_production_kwh : d.predicted_production_kwh;
      return sum + parseFloat(val || 0);
    }, 0);

    const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const weekData = sorted.filter(d => new Date(d.timestamp) >= weekStart);
    const weekProduction = weekData.reduce((sum, d) => {
      const val = dataSource === 'real' ? d.real_production_kwh : d.predicted_production_kwh;
      return sum + parseFloat(val || 0);
    }, 0);

    const peakPower = Math.max(...data.map(d => parseFloat(d.ac_power_kw || 0)));
    const radiation = data.map(d => parseFloat(d.solar_radiation_w_m2 || 0)).filter(r => r > 0);
    const avgRadiation = radiation.length ? radiation.reduce((a, b) => a + b, 0) / radiation.length : 0;

    const efficiency = currentPower > 0 ? (currentPower / 750 * 100) : 0;

    return {
      currentPower: currentPower.toFixed(1),
      todayProduction: todayProduction.toFixed(1),
      weekProduction: weekProduction.toFixed(0),
      efficiency: efficiency.toFixed(0),
      peakPower: peakPower.toFixed(1),
      avgRadiation: avgRadiation.toFixed(0)
    };
  };

  const getHourlyData = () => {
    const data = dataSource === 'real' ? archiveData : predictedData;
    return data
      .slice(0, 24)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      .map(d => ({
        time: new Date(d.timestamp).getHours() + 'h',
        power: parseFloat(d.ac_power_kw || 0).toFixed(1),
        production: (dataSource === 'real' ? d.real_production_kwh : d.predicted_production_kwh || 0).toFixed(2),
        radiation: parseFloat(d.solar_radiation_w_m2 || 0).toFixed(0),
        temp: parseFloat(d.temperature_c || 0).toFixed(1),
        clouds: parseFloat(d.cloud_cover_pct || 0).toFixed(0)
      }));
  };

  const getCurrentWeather = () => {
    if (!weatherData.length) return null;
    const latest = weatherData[0];
    return {
      temp: parseFloat(latest.temperature_c || 0).toFixed(1),
      humidity: parseFloat(latest.humidity_pct || 0).toFixed(0),
      clouds: parseFloat(latest.cloud_cover_pct || 0).toFixed(0),
      radiation: parseFloat(latest.solar_radiation_w_m2 || 0).toFixed(0)
    };
  };

  const metrics = calculateMetrics();
  const hourlyData = getHourlyData();
  const weather = getCurrentWeather();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800 font-medium">Chargement des données solaires...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center p-8">
        <div className="bg-white/60 backdrop-blur-sm rounded-3xl p-8 max-w-md shadow-lg text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-red-800 mb-2">Erreur de Connexion</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchAllData}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 text-white font-medium hover:bg-emerald-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-emerald-900 flex items-center gap-3">
              <Sun className="w-8 h-8 text-emerald-600" />
              Production Solaire
            </h1>
            <p className="text-emerald-700 mt-1">
              Système photovoltaïque 750 kW - 1364 panneaux
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchAllData}
              className="p-2.5 bg-white/60 backdrop-blur-sm rounded-xl hover:bg-white shadow-sm transition-all"
              title="Rafraîchir"
            >
              <RefreshCw className={`w-4 h-4 text-emerald-700 ${loading ? 'animate-spin' : ''}`} />
            </button>

            {dataSource === 'predicted' && (
              <div className="flex items-center gap-2 bg-yellow-100/80 backdrop-blur-sm border border-yellow-300 text-yellow-800 px-4 py-2 rounded-xl text-sm font-medium">
                <AlertCircle className="w-4 h-4" />
                Données prédites
              </div>
            )}
            {dataSource === 'real' && (
              <div className="flex items-center gap-2 bg-emerald-100/80 backdrop-blur-sm border border-emerald-300 text-emerald-800 px-4 py-2 rounded-xl text-sm font-medium">
                <Database className="w-4 h-4" />
                Données réelles
              </div>
            )}
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-emerald-400/30 to-teal-400/30 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
            <Sun className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1 text-center">Production Actuelle</p>
            <p className="text-4xl font-bold text-emerald-900 text-center">{metrics.currentPower}</p>
            <p className="text-sm text-emerald-600 text-center">kW</p>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
            <Zap className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1 text-center">Aujourd'hui</p>
            <p className="text-4xl font-bold text-emerald-900 text-center">{metrics.todayProduction}</p>
            <p className="text-sm text-emerald-600 text-center">kWh</p>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
            <Calendar className="w-8 h-8 text-teal-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1 text-center">Cette Semaine</p>
            <p className="text-4xl font-bold text-emerald-900 text-center">{metrics.weekProduction}</p>
            <p className="text-sm text-emerald-600 text-center">kWh</p>
          </div>

          <div className="bg-gradient-to-br from-green-400/30 to-emerald-400/30 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
            <Activity className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1 text-center">Efficacité</p>
            <p className="text-4xl font-bold text-emerald-900 text-center">{metrics.efficiency}%</p>
            <div className="w-full bg-emerald-100 rounded-full h-2 mt-3">
              <div
                className="bg-gradient-to-r from-emerald-400 to-green-500 h-2 rounded-full transition-all"
                style={{ width: `${metrics.efficiency}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Weather */}
        {weather && (
          <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
            <h3 className="text-lg font-bold text-emerald-900 mb-4 flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-teal-600" />
              Conditions Météo Actuelles
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-sm text-emerald-700">Température</p>
                <p className="text-2xl font-bold text-emerald-900">{weather.temp}°C</p>
              </div>
              <div className="text-center">
                <Droplets className="w-6 h-6 text-blue-600 mx-auto mb-1" />
                <p className="text-sm text-emerald-700">Humidité</p>
                <p className="text-2xl font-bold text-emerald-900">{weather.humidity}%</p>
              </div>
              <div className="text-center">
                <Wind className="w-6 h-6 text-gray-600 mx-auto mb-1" />
                <p className="text-sm text-emerald-700">Couverture</p>
                <p className="text-2xl font-bold text-emerald-900">{weather.clouds}%</p>
              </div>
              <div className="text-center">
                <Sun className="w-6 h-6 text-yellow-500 mx-auto mb-1" />
                <p className="text-sm text-emerald-700">Radiation</p>
                <p className="text-2xl font-bold text-emerald-900">{weather.radiation}</p>
                <p className="text-xs text-emerald-600">W/m²</p>
              </div>
            </div>
          </div>
        )}
{/* Hourly Chart - 8h to 21h only */}
<div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
  <h3 className="text-lg font-bold text-emerald-900 mb-4">Production Horaire</h3>
  
  <div className="overflow-x-auto">
    {/* This container centers the bars when they don't fill the width */}
    <div className="flex justify-center pb-4">
      <div className="flex gap-2">
        {hourlyData
          .filter(d => {
            const hour = parseInt(d.time);
            return hour >= 8 && hour <= 21;
          })
          .map((d, i) => {
            const filteredData = hourlyData.filter(x => {
              const h = parseInt(x.time);
              return h >= 8 && h <= 21;
            });
            const max = Math.max(...filteredData.map(x => parseFloat(x.power)));
            const height = max > 0 ? (parseFloat(d.power) / max) * 100 : 0;

            return (
              <div key={i} className="flex flex-col items-center gap-2 min-w-[60px]">
                <div className="relative h-40 w-full bg-orange-50/50 rounded-lg flex items-end justify-center">
                  <div
                    className="w-full bg-gradient-to-t from-orange-500 to-yellow-400 rounded-t-lg transition-all hover:from-orange-600 hover:to-yellow-500 cursor-pointer shadow-sm"
                    style={{ height: `${height}%` }}
                    title={`${d.time}: ${d.power} kW (${d.production} kWh)`}
                  >
                    <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-orange-900 text-white text-xs px-2 py-1 rounded opacity-0 hover:opacity-100 transition-opacity whitespace-nowrap">
                      {d.power} kW ({d.production} kWh)
                    </div>
                  </div>
                </div>
                <p className="text-xs font-medium text-orange-800">{d.time}</p>
                <p className="text-xs text-orange-600">{d.production} kWh</p>
              </div>
            );
          })}
      </div>
    </div>
  </div>
</div>

        {/* Prévisions (si prédites) */}
        {dataSource === 'predicted' && (
          <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
            <h3 className="text-lg font-bold text-emerald-900 mb-4">Prévisions (Prochaines 8h)</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
              {hourlyData.slice(0, 8).map((d, i) => (
                <div key={i} className="bg-white/60 backdrop-blur-sm rounded-xl p-3 text-center shadow-sm">
                  <p className="text-xs text-emerald-700 mb-1">{d.time}</p>
                  <p className="text-lg font-bold text-emerald-900">{d.power}</p>
                  <p className="text-xs text-emerald-600">kW</p>
                  <div className="mt-2 text-xs text-emerald-600 space-y-1">
                    <div>Radiation {d.radiation}W</div>
                    <div>Clouds {d.clouds}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Status */}
        <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
          <h3 className="text-lg font-bold text-emerald-900 mb-4">État du Système</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-emerald-700">Panneaux</span>
              <span className="font-bold text-emerald-900">1364 / 1364</span>
            </div>
            <div className="flex justify-between">
              <span className="text-emerald-700">Capacité</span>
              <span className="font-bold text-emerald-900">750 kW</span>
            </div>
            <div className="flex justify-between">
              <span className="text-emerald-700">Onduleurs</span>
              <span className="font-bold text-green-600">OK</span>
            </div>
            <div className="flex justify-between">
              <span className="text-emerald-700">Connexion</span>
              <span className="font-bold text-green-600">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SolarProductionPage;