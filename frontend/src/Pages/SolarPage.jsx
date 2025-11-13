// SolarPage.jsx (standalone, no tabs)
import React, { useState, useEffect } from 'react';
import {
  Sun,
  Zap,
  TrendingUp,
  TrendingDown,
  Building2,
  Battery,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  CloudSun,
  BarChart3,
  Activity,
  Filter,
  Search,
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const SolarPage = () => {
  const [solarData, setSolarData] = useState([]);
  const [weatherData, setWeatherData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('today'); // today, week, month
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchSolarData();
    const interval = setInterval(fetchSolarData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchSolarData = async () => {
    try {
      setLoading(true);
      const [solarRes, weatherRes] = await Promise.all([
        fetch(`${API_BASE_URL}/predicted-solar-production?limit=500`),
        fetch(`${API_BASE_URL}/weather-forecast-hourly?limit=100`)
      ]);

      const solarJson = await solarRes.json();
      const weatherJson = await weatherRes.json();

      setSolarData(solarJson.results || []);
      setWeatherData(weatherJson.results || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching solar data:', error);
      setLoading(false);
    }
  };

  const calculateMetrics = () => {
    if (!solarData.length) return { current: 0, today: 0, week: 0, efficiency: 0 };

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
    const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

    const todayData = solarData.filter(d => d.timestamp >= todayStart);
    const weekData = solarData.filter(d => d.timestamp >= weekStart);

    const current = solarData[0]?.ac_power_kw || solarData[0]?.predicted_production_kwh || 0;
    const today = todayData.reduce((sum, d) => sum + parseFloat(d.predicted_production_kwh || 0), 0);
    const week = weekData.reduce((sum, d) => sum + parseFloat(d.predicted_production_kwh || 0), 0);
    const efficiency = todayData.length > 0 
      ? (today / (todayData.length * 0.75)) * 100 // 750kW capacity / 1000
      : 0;

    return { current, today, week, efficiency: Math.min(efficiency, 100) };
  };

  const getChartData = () => {
    const now = new Date();
    const filtered = solarData.filter(d => {
      const ts = new Date(d.timestamp);
      if (selectedPeriod === 'today') {
        return ts.toDateString() === now.toDateString();
      } else if (selectedPeriod === 'week') {
        return ts >= new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      }
      return ts >= new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    });

    return filtered.slice(0, 24).map(d => ({
      label: new Date(d.timestamp).getHours() + 'h',
      value: parseFloat(d.predicted_production_kwh || 0),
      temp: parseFloat(d.temperature_c || 0),
      radiation: parseFloat(d.solar_radiation_w_m2 || 0)
    }));
  };

  const getCurrentWeather = () => {
    if (!weatherData.length) return null;
    return weatherData[0];
  };

  const metrics = calculateMetrics();
  const chartData = getChartData();
  const weather = getCurrentWeather();

  if (loading && !solarData.length) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800">Chargement des données solaires...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-emerald-900">Production Solaire</h1>
          <p className="text-emerald-600 mt-1">Système photovoltaïque 750 kW - 1364 panneaux</p>
        </div>
        <div className="flex gap-3">
          {['today', 'week', 'month'].map(period => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedPeriod === period
                  ? 'bg-emerald-600 text-white shadow-lg'
                  : 'bg-white/60 text-emerald-700 hover:bg-white'
              }`}
            >
              {period === 'today' ? "Aujourd'hui" : period === 'week' ? 'Semaine' : 'Mois'}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-yellow-400/20 to-orange-400/20 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center justify-between mb-3">
            <Sun className="w-8 h-8 text-yellow-600" />
            <div className="flex items-center gap-1 text-green-600 text-sm">
              <TrendingUp className="w-4 h-4" />
              <span>+12%</span>
            </div>
          </div>
          <p className="text-sm text-emerald-700 mb-1">Production Actuelle</p>
          <p className="text-3xl font-bold text-emerald-900">{metrics.current.toFixed(1)} kW</p>
        </div>

        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center justify-between mb-3">
            <Zap className="w-8 h-8 text-emerald-600" />
            <Calendar className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-sm text-emerald-700 mb-1">Production Aujourd'hui</p>
          <p className="text-3xl font-bold text-emerald-900">{metrics.today.toFixed(1)} kWh</p>
        </div>

        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center justify-between mb-3">
            <BarChart3 className="w-8 h-8 text-blue-600" />
            <div className="flex items-center gap-1 text-blue-600 text-sm">
              <TrendingUp className="w-4 h-4" />
              <span>+8%</span>
            </div>
          </div>
          <p className="text-sm text-emerald-700 mb-1">Cette Semaine</p>
          <p className="text-3xl font-bold text-emerald-900">{metrics.week.toFixed(0)} kWh</p>
        </div>

        <div className="bg-gradient-to-br from-emerald-400/20 to-teal-400/20 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center justify-between mb-3">
            <Activity className="w-8 h-8 text-emerald-600" />
            <div className={`w-2 h-2 rounded-full ${metrics.efficiency > 70 ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`}></div>
          </div>
          <p className="text-sm text-emerald-700 mb-1">Efficacité</p>
          <p className="text-3xl font-bold text-emerald-900">{metrics.efficiency.toFixed(0)}%</p>
        </div>
      </div>

      {/* Main Chart & Weather */}
      <div className="grid grid-cols-3 gap-6">
        {/* Production Chart */}
        <div className="col-span-2 bg-white/40 backdrop-blur-sm rounded-2xl p-6">
          <h3 className="text-lg font-bold text-emerald-900 mb-6">Production Horaire</h3>
          <div className="flex items-end justify-between gap-2 h-64">
            {chartData.map((data, idx) => (
              <div key={idx} className="flex flex-col items-center gap-2 flex-1">
                <div className="relative w-full h-full flex flex-col justify-end">
                  <div
                    className="w-full bg-gradient-to-t from-yellow-400 to-orange-400 rounded-t-lg transition-all hover:opacity-80 cursor-pointer"
                    style={{ height: `${(data.value / Math.max(...chartData.map(d => d.value))) * 100}%` }}
                    title={`${data.value.toFixed(2)} kWh\nTemp: ${data.temp.toFixed(1)}°C\nRadiation: ${data.radiation.toFixed(0)} W/m²`}
                  ></div>
                </div>
                <span className="text-xs text-emerald-600">{data.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Weather & Conditions */}
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-blue-400/20 to-cyan-400/20 backdrop-blur-sm rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <CloudSun className="w-6 h-6 text-blue-600" />
              <h3 className="text-lg font-bold text-emerald-900">Conditions Météo</h3>
            </div>
            {weather ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-emerald-700">Température</span>
                  <span className="font-bold text-emerald-900">{parseFloat(weather.temperature_c || 0).toFixed(1)}°C</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-emerald-700">Humidité</span>
                  <span className="font-bold text-emerald-900">{parseFloat(weather.humidity_pct || 0).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-emerald-700">Couverture</span>
                  <span className="font-bold text-emerald-900">{parseFloat(weather.cloud_cover_pct || 0).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-emerald-700">Radiation</span>
                  <span className="font-bold text-emerald-900">{parseFloat(weather.solar_radiation_w_m2 || 0).toFixed(0)} W/m²</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-emerald-600">Données non disponibles</p>
            )}
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
            <h3 className="text-lg font-bold text-emerald-900 mb-4">État du Système</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-emerald-700">Panneaux actifs</span>
                <span className="font-semibold text-green-600">1364 / 1364</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-700">Capacité totale</span>
                <span className="font-semibold text-emerald-900">750 kW</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-700">Onduleurs</span>
                <span className="font-semibold text-green-600">Tous OK</span>
              </div>
              <div className="flex justify-between">
                <span className="text-emerald-700">Données en temps réel</span>
                <span className="font-semibold text-green-600">✓ Actif</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Predictions */}
      <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
        <h3 className="text-lg font-bold text-emerald-900 mb-4">Prévisions Production (Prochaines 24h)</h3>
        <div className="grid grid-cols-8 gap-3">
          {solarData.slice(0, 8).map((data, idx) => {
            const ts = new Date(data.timestamp);
            const production = parseFloat(data.predicted_production_kwh || 0);
            return (
              <div key={idx} className="bg-white/60 rounded-xl p-4 text-center">
                <p className="text-xs text-emerald-600 mb-2">
                  {ts.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </p>
                <p className="text-lg font-bold text-emerald-900">{production.toFixed(1)}</p>
                <p className="text-xs text-emerald-600">kWh</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SolarPage;