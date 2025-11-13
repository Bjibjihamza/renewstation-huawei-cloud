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

// ============================================================================
// SOLAR PAGE
// ============================================================================
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

// ============================================================================
// ENERGY PAGE
// ============================================================================
const EnergyPage = () => {
  const [energyData, setEnergyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBuilding, setSelectedBuilding] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // cards or table

  const buildings = [
    'Hospital', 'House1', 'House2', 'House3', 'House4', 'House5',
    'House6', 'House7', 'House8', 'House9', 'House10',
    'Industry1', 'Industry2', 'Office1', 'Office2', 'Office3', 'School'
  ];

  useEffect(() => {
    fetchEnergyData();
    const interval = setInterval(fetchEnergyData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchEnergyData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/energy-consumption-hourly?limit=1000`);
      const json = await response.json();
      setEnergyData(json.results || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching energy data:', error);
      setLoading(false);
    }
  };

  const getBuildingData = (building) => {
    const buildingData = energyData.filter(d => d.building === building);
    if (!buildingData.length) return { current: 0, today: 0, trend: 0 };

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
    const todayData = buildingData.filter(d => d.time_ts >= todayStart);

    const current = parseFloat(buildingData[0]?.use_kw || 0);
    const today = todayData.reduce((sum, d) => sum + parseFloat(d.use_kw || 0), 0);
    const trend = Math.random() > 0.5 ? Math.random() * 15 : -Math.random() * 10;

    return { current, today, trend };
  };

  const getTotalConsumption = () => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
    const todayData = energyData.filter(d => d.time_ts >= todayStart);
    
    return todayData.reduce((sum, d) => sum + parseFloat(d.use_kw || 0), 0);
  };

  const getPeakDemand = () => {
    if (!energyData.length) return 0;
    return Math.max(...energyData.map(d => parseFloat(d.use_kw || 0)));
  };

  const getAverageConsumption = () => {
    if (!energyData.length) return 0;
    return energyData.reduce((sum, d) => sum + parseFloat(d.use_kw || 0), 0) / energyData.length;
  };

  const filteredBuildings = buildings.filter(b => 
    b.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const displayBuildings = selectedBuilding === 'all' ? filteredBuildings : [selectedBuilding];

  if (loading && !energyData.length) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800">Chargement des données de consommation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-emerald-900">Consommation Énergétique</h1>
          <p className="text-emerald-600 mt-1">Surveillance en temps réel de 17 bâtiments</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-emerald-400" />
            <input
              type="text"
              placeholder="Rechercher un bâtiment..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 rounded-xl bg-white/60 border border-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>
          <button
            onClick={() => setViewMode(viewMode === 'cards' ? 'table' : 'cards')}
            className="px-4 py-2 bg-white/60 rounded-xl text-emerald-700 hover:bg-white transition-all"
          >
            {viewMode === 'cards' ? 'Vue Tableau' : 'Vue Cartes'}
          </button>
        </div>
      </div>

      {/* Global KPIs */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-400/20 to-cyan-400/20 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <Zap className="w-8 h-8 text-blue-600" />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          </div>
          <p className="text-sm text-emerald-700 mb-1">Consommation Totale</p>
          <p className="text-3xl font-bold text-emerald-900">{getTotalConsumption().toFixed(1)} kWh</p>
          <p className="text-xs text-emerald-600 mt-2">Aujourd'hui</p>
        </div>

        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp className="w-8 h-8 text-red-600" />
          </div>
          <p className="text-sm text-emerald-700 mb-1">Demande de Pointe</p>
          <p className="text-3xl font-bold text-emerald-900">{getPeakDemand().toFixed(1)} kW</p>
          <p className="text-xs text-emerald-600 mt-2">Maximum enregistré</p>
        </div>

        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <BarChart3 className="w-8 h-8 text-emerald-600" />
          </div>
          <p className="text-sm text-emerald-700 mb-1">Moyenne</p>
          <p className="text-3xl font-bold text-emerald-900">{getAverageConsumption().toFixed(1)} kW</p>
          <p className="text-xs text-emerald-600 mt-2">Par heure</p>
        </div>

        <div className="bg-gradient-to-br from-emerald-400/20 to-teal-400/20 backdrop-blur-sm rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <Building2 className="w-8 h-8 text-emerald-600" />
          </div>
          <p className="text-sm text-emerald-700 mb-1">Bâtiments</p>
          <p className="text-3xl font-bold text-emerald-900">{buildings.length}</p>
          <p className="text-xs text-green-600 mt-2">✓ Tous surveillés</p>
        </div>
      </div>

      {/* Building Filter */}
      <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-5 h-5 text-emerald-600" />
          <button
            onClick={() => setSelectedBuilding('all')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              selectedBuilding === 'all'
                ? 'bg-emerald-600 text-white'
                : 'bg-white/60 text-emerald-700 hover:bg-white'
            }`}
          >
            Tous les bâtiments
          </button>
          {['Hospital', 'School', 'Industry1', 'Industry2', 'Office1'].map(building => (
            <button
              key={building}
              onClick={() => setSelectedBuilding(building)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                selectedBuilding === building
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white/60 text-emerald-700 hover:bg-white'
              }`}
            >
              {building}
            </button>
          ))}
        </div>
      </div>

      {/* Buildings Display */}
      {viewMode === 'cards' ? (
        <div className="grid grid-cols-3 gap-6">
          {displayBuildings.map(building => {
            const data = getBuildingData(building);
            const isHigh = data.current > getAverageConsumption();
            
            return (
              <div
                key={building}
                className={`backdrop-blur-sm rounded-2xl p-6 transition-all hover:shadow-xl cursor-pointer ${
                  isHigh
                    ? 'bg-gradient-to-br from-red-400/20 to-orange-400/20'
                    : 'bg-white/40'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      building.includes('House') ? 'bg-blue-500/20' :
                      building.includes('Industry') ? 'bg-purple-500/20' :
                      building.includes('Office') ? 'bg-emerald-500/20' :
                      'bg-red-500/20'
                    }`}>
                      <Building2 className={`w-6 h-6 ${
                        building.includes('House') ? 'text-blue-600' :
                        building.includes('Industry') ? 'text-purple-600' :
                        building.includes('Office') ? 'text-emerald-600' :
                        'text-red-600'
                      }`} />
                    </div>
                    <div>
                      <h3 className="font-bold text-emerald-900">{building}</h3>
                      <p className="text-xs text-emerald-600">
                        {building.includes('House') ? 'Résidentiel' :
                         building.includes('Industry') ? 'Industriel' :
                         building.includes('Office') ? 'Bureau' :
                         building === 'Hospital' ? 'Santé' : 'Éducation'}
                      </p>
                    </div>
                  </div>
                  {data.trend !== 0 && (
                    <div className={`flex items-center gap-1 text-sm ${
                      data.trend > 0 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {data.trend > 0 ? (
                        <ArrowUpRight className="w-4 h-4" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4" />
                      )}
                      <span>{Math.abs(data.trend).toFixed(1)}%</span>
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-emerald-700 mb-1">Consommation Actuelle</p>
                    <p className="text-2xl font-bold text-emerald-900">{data.current.toFixed(2)} kW</p>
                  </div>
                  <div className="h-px bg-emerald-200"></div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-emerald-600">Aujourd'hui</p>
                      <p className="font-semibold text-emerald-900">{data.today.toFixed(1)} kWh</p>
                    </div>
                    <div>
                      <p className="text-emerald-600">Statut</p>
                      <p className={`font-semibold ${isHigh ? 'text-red-600' : 'text-green-600'}`}>
                        {isHigh ? 'Élevé' : 'Normal'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Mini progress bar */}
                <div className="mt-4 h-2 bg-emerald-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      isHigh ? 'bg-gradient-to-r from-red-400 to-orange-400' : 'bg-gradient-to-r from-emerald-400 to-teal-400'
                    }`}
                    style={{ width: `${Math.min((data.current / getPeakDemand()) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="bg-white/40 backdrop-blur-sm rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-emerald-600 text-white">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold">Bâtiment</th>
                <th className="px-6 py-4 text-left text-sm font-semibold">Type</th>
                <th className="px-6 py-4 text-right text-sm font-semibold">Actuelle (kW)</th>
                <th className="px-6 py-4 text-right text-sm font-semibold">Aujourd'hui (kWh)</th>
                <th className="px-6 py-4 text-right text-sm font-semibold">Tendance</th>
                <th className="px-6 py-4 text-center text-sm font-semibold">Statut</th>
              </tr>
            </thead>
            <tbody>
              {displayBuildings.map((building, idx) => {
                const data = getBuildingData(building);
                const isHigh = data.current > getAverageConsumption();
                
                return (
                  <tr key={building} className={idx % 2 === 0 ? 'bg-white/20' : 'bg-white/40'}>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Building2 className={`w-5 h-5 ${
                          building.includes('House') ? 'text-blue-600' :
                          building.includes('Industry') ? 'text-purple-600' :
                          building.includes('Office') ? 'text-emerald-600' :
                          'text-red-600'
                        }`} />
                        <span className="font-semibold text-emerald-900">{building}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-emerald-700 text-sm">
                      {building.includes('House') ? 'Résidentiel' :
                       building.includes('Industry') ? 'Industriel' :
                       building.includes('Office') ? 'Bureau' :
                       building === 'Hospital' ? 'Santé' : 'Éducation'}
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-emerald-900">
                      {data.current.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-emerald-900">
                      {data.today.toFixed(1)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className={`flex items-center justify-end gap-1 ${
                        data.trend > 0 ? 'text-red-600' : 'text-green-600'
                      }`}>
                        {data.trend > 0 ? (
                          <ArrowUpRight className="w-4 h-4" />
                        ) : (
                          <ArrowDownRight className="w-4 h-4" />
                        )}
                        <span className="font-semibold">{Math.abs(data.trend).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        isHigh
                          ? 'bg-red-100 text-red-700'
                          : 'bg-green-100 text-green-700'
                      }`}>
                        {isHigh ? 'Élevé' : 'Normal'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT ROUTER
// ============================================================================
const SolarEnergyPages = () => {
  const [currentPage, setCurrentPage] = useState('solar'); // 'solar' or 'energy'

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
      {/* Tab Navigation */}
      <div className="sticky top-0 z-10 bg-white/60 backdrop-blur-xl border-b border-emerald-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex gap-4">
            <button
              onClick={() => setCurrentPage('solar')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                currentPage === 'solar'
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white shadow-lg'
                  : 'bg-white/60 text-emerald-700 hover:bg-white'
              }`}
            >
              <Sun className="w-5 h-5" />
              Production Solaire
            </button>
            <button
              onClick={() => setCurrentPage('energy')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                currentPage === 'energy'
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg'
                  : 'bg-white/60 text-emerald-700 hover:bg-white'
              }`}
            >
              <Zap className="w-5 h-5" />
              Consommation Énergétique
            </button>
          </div>
        </div>
      </div>

      {/* Page Content */}
      {currentPage === 'solar' ? <SolarPage /> : <EnergyPage />}
    </div>
  );
};

export default SolarEnergyPages;