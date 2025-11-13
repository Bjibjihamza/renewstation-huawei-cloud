// WeatherPage.jsx (Version Fixée & Améliorée)
import React, { useState, useEffect } from 'react';
import {
  CloudSun,
  ThermometerSun,
  Droplets,
  Wind,
  CloudRain,
  AlertCircle,
  RefreshCw,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar,
  Filter,
  Search,
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const WeatherPage = () => {
  const [forecastData, setForecastData] = useState([]);
  const [archiveData, setArchiveData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('forecast'); // 'forecast' or 'archive'
  const [searchTerm, setSearchTerm] = useState(''); // Filter by date/hour
  const [viewMode, setViewMode] = useState('charts'); // 'charts' or 'table'

  useEffect(() => {
    fetchWeatherData();
    const interval = setInterval(fetchWeatherData, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, [selectedPeriod]);

  const fetchWeatherData = async () => {
    try {
      setLoading(true);
      setError(null);

      const endpoint = selectedPeriod === 'forecast' 
        ? `${API_BASE_URL}/weather-forecast-hourly?limit=168` // 7 days
        : `${API_BASE_URL}/weather-archive-hourly?limit=168`; // Last 7 days

      const response = await fetch(endpoint);
      if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

      const json = await response.json();
      const data = json.results || [];

      console.log(`[DEBUG] ${selectedPeriod} data loaded:`, data.slice(0, 3)); // Log sample for debug

      if (selectedPeriod === 'forecast') {
        setForecastData(data);
      } else {
        setArchiveData(data);
      }

      setLoading(false);
    } catch (err) {
      console.error('Erreur API météo:', err);
      setError(err.message || 'Erreur inconnue');
      setLoading(false);
    }
  };

  const filterData = (data) => {
    if (!searchTerm) return data;
    const term = searchTerm.toLowerCase();
    return data.filter((item) => {
      const ts = item.forecast_timestamp || item.timestamp || '';
      const dateStr = new Date(ts).toLocaleDateString('fr-FR');
      const timeStr = new Date(ts).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      return dateStr.includes(term) || timeStr.includes(term) || ts.includes(term);
    });
  };

  const currentData = filterData(selectedPeriod === 'forecast' ? forecastData : archiveData);

  const calculateMetrics = (data) => {
    if (!data.length) return { avgTemp: 0, maxTemp: 0, avgHumidity: 0, totalPrecip: 0, maxRadiation: 0, avgWind: 0 };

    const temps = data.map(d => parseFloat(d.temperature_c || 0)).filter(t => !isNaN(t));
    const humidities = data.map(d => parseFloat(d.humidity_pct || 0)).filter(h => !isNaN(h));
    const precipitations = data.map(d => parseFloat(d.precipitation_mm || 0)).filter(p => !isNaN(p));
    const radiations = data.map(d => parseFloat(d.solar_radiation_w_m2 || 0)).filter(r => !isNaN(r));
    const winds = data.map(d => parseFloat(d.wind_speed_kmh || 0)).filter(w => !isNaN(w));

    return {
      avgTemp: temps.length ? (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1) : 0,
      maxTemp: temps.length ? Math.max(...temps).toFixed(1) : 0,
      avgHumidity: humidities.length ? (humidities.reduce((a, b) => a + b, 0) / humidities.length).toFixed(0) : 0,
      totalPrecip: precipitations.reduce((a, b) => a + b, 0).toFixed(1),
      maxRadiation: radiations.length ? Math.max(...radiations).toFixed(0) : 0,
      avgWind: winds.length ? (winds.reduce((a, b) => a + b, 0) / winds.length).toFixed(0) : 0,
    };
  };

  const getChartData = (data) => {
    const sorted = [...data].sort((a, b) => new Date(a.forecast_timestamp || a.timestamp) - new Date(b.forecast_timestamp || b.timestamp));
    return sorted.slice(-24).map((item, idx) => { // Last 24 hours
      const ts = new Date(item.forecast_timestamp || item.timestamp);
      const hour = ts.getHours();
      return {
        label: `${hour}h`,
        temp: parseFloat(item.temperature_c || 0),
        humidity: parseFloat(item.humidity_pct || 0),
        clouds: parseFloat(item.cloud_cover_pct || 0),
        radiation: parseFloat(item.solar_radiation_w_m2 || 0),
        precip: parseFloat(item.precipitation_mm || 0),
        wind: parseFloat(item.wind_speed_kmh || 0),
        index: idx,
      };
    });
  };

  const metrics = calculateMetrics(currentData);
  const chartData = getChartData(currentData);
  const periodLabel = selectedPeriod === 'forecast' ? 'Prévisions (7 jours)' : 'Historique Récent';

  if (loading && currentData.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800 font-medium">Chargement des données météo...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
        <div className="bg-white/70 backdrop-blur-lg rounded-3xl p-8 max-w-md shadow-lg text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-red-800 mb-2">Erreur de Connexion</h3>
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={fetchWeatherData}
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
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold text-emerald-900 flex items-center gap-3">
              <CloudSun className="w-8 h-8 text-sky-500" />
              Météo & Prévisions
            </h1>
            <p className="text-emerald-600">{periodLabel} • Casablanca, Maroc • {currentData.length} points</p>
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedPeriod('forecast')}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm ${
                  selectedPeriod === 'forecast'
                    ? 'bg-sky-500 text-white'
                    : 'bg-white/60 text-emerald-700 hover:bg-white'
                }`}
              >
                Prévisions
              </button>
              <button
                onClick={() => setSelectedPeriod('archive')}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm ${
                  selectedPeriod === 'archive'
                    ? 'bg-sky-500 text-white'
                    : 'bg-white/60 text-emerald-700 hover:bg-white'
                }`}
              >
                Historique
              </button>
            </div>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-emerald-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Filtrer par date/heure..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 rounded-xl bg-white/60 border border-emerald-200 focus:outline-none focus:ring-2 focus:ring-sky-400 text-sm w-64"
              />
            </div>
            <button
              onClick={fetchWeatherData}
              className="p-2.5 bg-white/60 rounded-xl hover:bg-white shadow-sm transition-all text-emerald-700"
              title="Rafraîchir les données"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* KPIs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-gradient-to-br from-sky-400/20 to-blue-400/20 backdrop-blur-sm rounded-2xl p-5 text-center">
            <ThermometerSun className="w-6 h-6 text-sky-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1">Temp. Moyenne</p>
            <p className="text-2xl font-bold text-emerald-900">{metrics.avgTemp}°C</p>
            <p className="text-xs text-sky-600">Max: {metrics.maxTemp}°C</p>
          </div>
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-5 text-center">
            <Droplets className="w-6 h-6 text-blue-500 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1">Humidité Moy.</p>
            <p className="text-2xl font-bold text-emerald-900">{metrics.avgHumidity}%</p>
          </div>
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-5 text-center">
            <CloudRain className="w-6 h-6 text-indigo-500 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1">Précip. Total</p>
            <p className="text-2xl font-bold text-emerald-900">{metrics.totalPrecip} mm</p>
          </div>
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-5 text-center">
            <Wind className="w-6 h-6 text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1">Vent Moyen</p>
            <p className="text-2xl font-bold text-emerald-900">{metrics.avgWind} km/h</p>
          </div>
          <div className="bg-gradient-to-br from-yellow-400/20 to-orange-400/20 backdrop-blur-sm rounded-2xl p-5 text-center">
            <CloudSun className="w-6 h-6 text-yellow-600 mx-auto mb-2" />
            <p className="text-sm text-emerald-700 mb-1">Rayonnement Max</p>
            <p className="text-2xl font-bold text-emerald-900">{metrics.maxRadiation} W/m²</p>
          </div>
        </div>

        {/* Charts Section – Responsive Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Temp Chart */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
            <h3 className="text-lg font-bold text-emerald-900 mb-4 flex items-center gap-2">
              <ThermometerSun className="w-5 h-5 text-sky-500" />
              Température (Dernières 24h)
            </h3>
            <div className="relative h-64 flex flex-col justify-end bg-gradient-to-b from-transparent to-emerald-100/50 rounded-lg p-2">
              {chartData.map((data) => (
                <div key={data.index} className="flex items-end justify-between h-1/6 border-b border-emerald-200 last:border-b-0">
                  <div className="flex-1 relative bg-transparent">
                    <div
                      className="absolute bottom-0 left-0 bg-gradient-to-t from-sky-400 to-blue-500 rounded-t-md hover:opacity-80 transition-opacity cursor-pointer"
                      style={{
                        height: `${Math.max(((data.temp + 10) / 50) * 100, 5)}%`, // Normalize -10°C to 40°C -> 0-100%
                        width: '100%',
                      }}
                      title={`${data.label}: ${data.temp.toFixed(1)}°C`}
                    />
                  </div>
                  <span className="text-xs text-emerald-700 w-8 text-right ml-1">{data.temp.toFixed(0)}</span>
                </div>
              ))}
              <div className="absolute bottom-0 left-0 right-0 h-4 flex items-center justify-between px-2 text-xs text-emerald-600">
                {chartData.filter((_, i) => i % 4 === 0).map((data) => (
                  <span key={data.index}>{data.label}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Humidity & Clouds */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
            <h3 className="text-lg font-bold text-emerald-900 mb-4 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-500" />
              Humidité & Nuages
            </h3>
            <div className="space-y-2 h-64 overflow-y-auto">
              {chartData.map((data) => (
                <div key={data.index} className="flex items-center justify-between h-4">
                  <span className="text-xs text-emerald-700 w-8">{data.label}</span>
                  <div className="flex-1 flex gap-1">
                    {/* Humidity Bar */}
                    <div className="flex-1 bg-blue-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${data.humidity}%` }}
                        title={`Humidité: ${data.humidity}%`}
                      />
                    </div>
                    <span className="text-xs text-blue-600 w-6 text-center">{data.humidity}</span>
                    {/* Clouds Bar */}
                    <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-gray-500 rounded-full transition-all"
                        style={{ width: `${data.clouds}%` }}
                        title={`Nuages: ${data.clouds}%`}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-6 text-center">{data.clouds}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Radiation & Precip */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
            <h3 className="text-lg font-bold text-emerald-900 mb-4 flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-yellow-500" />
              Rayonnement & Précipitations
            </h3>
            <div className="space-y-2 h-64 overflow-y-auto">
              {chartData.map((data) => (
                <div key={data.index} className="flex items-center justify-between h-4">
                  <span className="text-xs text-emerald-700 w-8">{data.label}</span>
                  <div className="flex-1 flex gap-1">
                    {/* Radiation Bar (normalized 0-1000 -> 0-100%) */}
                    <div className="flex-1 bg-yellow-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-yellow-500 rounded-full transition-all"
                        style={{ width: `${Math.min(data.radiation / 10, 100)}%` }} // /10 for scale
                        title={`Rayonnement: ${data.radiation.toFixed(0)} W/m²`}
                      />
                    </div>
                    <span className="text-xs text-yellow-600 w-8 text-center">{data.radiation.toFixed(0)}</span>
                    {/* Precip Bar (0-10mm -> 0-100%) */}
                    <div className="flex-1 bg-indigo-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-indigo-500 rounded-full transition-all"
                        style={{ width: `${Math.min(data.precip * 10, 100)}%` }} // *10 for scale
                        title={`Précip: ${data.precip.toFixed(1)} mm`}
                      />
                    </div>
                    <span className="text-xs text-indigo-600 w-6 text-center">{data.precip.toFixed(1)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Hourly Forecast Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          {chartData.slice(-8).reverse().map((data, idx) => { // Reverse for chronological
            const conditions = data.clouds > 70 ? '🌧️ Pluvieux' : data.clouds > 30 ? '⛅ Partiel' : '☀️ Soleil';
            const isPrecip = data.precip > 0;
            return (
              <div key={idx} className="bg-white/60 backdrop-blur-sm rounded-xl p-3 text-center shadow-sm hover:shadow-md transition-shadow border border-emerald-100/50">
                <p className="text-xs text-emerald-600 mb-1 font-medium">{data.label}</p>
                <div className={`text-xl mb-2 ${isPrecip ? 'text-blue-600' : 'text-yellow-600'}`}>
                  {conditions}
                </div>
                <p className="text-lg font-bold text-emerald-900">{data.temp.toFixed(1)}°</p>
                <div className="grid grid-cols-2 gap-1 text-xs text-emerald-700 mt-2">
                  <div>💧 {data.humidity}%</div>
                  <div>☀️ {data.radiation.toFixed(0)}W</div>
                </div>
                {data.precip > 0 && <p className="text-xs text-blue-600 mt-1">🌧️ {data.precip}mm</p>}
              </div>
            );
          })}
        </div>

        {/* Detailed View Toggle */}
        <div className="bg-white/40 backdrop-blur-sm rounded-2xl overflow-hidden">
          <div className="flex justify-between items-center p-4 bg-emerald-50">
            <h3 className="text-lg font-bold text-emerald-900">Détails Complets ({currentData.length} entrées)</h3>
            <button
              onClick={() => setViewMode(viewMode === 'table' ? 'cards' : 'table')}
              className="px-4 py-2 bg-white rounded-xl text-emerald-700 hover:bg-emerald-100 transition-all text-sm font-medium"
            >
              {viewMode === 'table' ? 'Vue Cartes' : 'Vue Tableau'}
            </button>
          </div>

          {viewMode === 'table' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-emerald-100 text-emerald-700">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold">Heure</th>
                    <th className="py-3 px-4 text-left font-semibold">Temp (°C)</th>
                    <th className="py-3 px-4 text-left font-semibold">Hum. (%)</th>
                    <th className="py-3 px-4 text-left font-semibold">Nuages (%)</th>
                    <th className="py-3 px-4 text-left font-semibold">Vent (km/h)</th>
                    <th className="py-3 px-4 text-left font-semibold">Rayonn. (W/m²)</th>
                    <th className="py-3 px-4 text-left font-semibold">Précip. (mm)</th>
                    <th className="py-3 px-4 text-left font-semibold">Pression (hPa)</th>
                  </tr>
                </thead>
                <tbody>
                  {currentData.slice(-12).map((row, idx) => ( // Last 12 for table
                    <tr key={idx} className="border-b border-emerald-100 hover:bg-emerald-50 transition-colors">
                      <td className="py-3 px-4 font-medium text-emerald-900">
                        {new Date(row.forecast_timestamp || row.timestamp).toLocaleString('fr-FR', {
                          hour: '2-digit',
                          minute: '2-digit',
                          day: '2-digit' , month: 'short',
                        })}
                      </td>
                      <td className="py-3 px-4">{parseFloat(row.temperature_c || 0).toFixed(1)}</td>
                      <td className="py-3 px-4">{parseFloat(row.humidity_pct || 0).toFixed(0)}</td>
                      <td className="py-3 px-4">{parseFloat(row.cloud_cover_pct || 0).toFixed(0)}</td>
                      <td className="py-3 px-4">{parseFloat(row.wind_speed_kmh || 0).toFixed(0)}</td>
                      <td className="py-3 px-4 font-semibold text-yellow-600">{parseFloat(row.solar_radiation_w_m2 || 0).toFixed(0)}</td>
                      <td className="py-3 px-4 text-blue-600">{parseFloat(row.precipitation_mm || 0).toFixed(1)}</td>
                      <td className="py-3 px-4">{parseFloat(row.pressure_hpa || 0).toFixed(0)}</td>
                    </tr>
                  ))}
                  {currentData.length === 0 && (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-emerald-500">
                        Aucune donnée disponible pour ce filtre. Essayez sans recherche.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4">
              {currentData.slice(-8).map((row, idx) => {
                const ts = new Date(row.forecast_timestamp || row.timestamp);
                const conditions = parseFloat(row.cloud_cover_pct || 0) > 70 ? '🌧️' : parseFloat(row.cloud_cover_pct || 0) > 30 ? '⛅' : '☀️';
                return (
                  <div key={idx} className="bg-white/70 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow border border-sky-100">
                    <p className="text-xs text-emerald-600 mb-1">{ts.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</p>
                    <div className="text-2xl mb-2">{conditions}</div>
                    <p className="text-lg font-bold text-emerald-900">{parseFloat(row.temperature_c || 0).toFixed(1)}°C</p>
                    <div className="space-y-1 text-xs text-emerald-700 mt-2">
                      <div className="flex justify-between">
                        <span>💧 Hum.</span><span>{parseFloat(row.humidity_pct || 0).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>☁️ Nuages</span><span>{parseFloat(row.cloud_cover_pct || 0).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>🌤️ Rad.</span><span>{parseFloat(row.solar_radiation_w_m2 || 0).toFixed(0)}W</span>
                      </div>
                      <div className="flex justify-between">
                        <span>🌧️ Précip.</span><span>{parseFloat(row.precipitation_mm || 0).toFixed(1)}mm</span>
                      </div>
                      <div className="flex justify-between">
                        <span>💨 Vent</span><span>{parseFloat(row.wind_speed_kmh || 0).toFixed(0)}km/h</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WeatherPage;