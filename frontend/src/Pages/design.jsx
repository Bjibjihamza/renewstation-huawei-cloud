import React, { useState, useEffect } from 'react';
import {
  Zap,
  Battery,
  TrendingUp,
  Sun,
  Wind,
  Droplets,
  Activity,
  ArrowUp,
  ArrowDown,
  Calendar,
  AlertCircle,
  ChevronDown,
  BarChart3,
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const SolarDashboard = () => {
  // --- API data state ---
  const [batteryData, setBatteryData] = useState([]);
  const [solarProduction, setSolarProduction] = useState([]);
  const [energyConsumption, setEnergyConsumption] = useState([]);
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- Global battery selection (header) ---
  const [selectedBattery, setSelectedBattery] = useState('main');
  const [batteryDropdownOpen, setBatteryDropdownOpen] = useState(false);

  // --- Derived KPIs ---
  const [currentPower, setCurrentPower] = useState(0);
  const [todayProduction, setTodayProduction] = useState(0);
  const [todayConsumption, setTodayConsumption] = useState(0);

  // --- Chart period ---
  const [viewPeriod, setViewPeriod] = useState('day');

  const batteryOptions = [
    { value: 'main', label: 'Batterie Principale', capacity: '3000 kWh' },
    { value: 'backup', label: 'Batterie Backup', capacity: '1000 kWh' },
  ];

  const selectedOption =
    batteryOptions.find((opt) => opt.value === selectedBattery) || batteryOptions[0];

  // ------------------------
  // Helpers
  // ------------------------
  const safeParseFloat = (value, fallback = 0) => {
    const num = parseFloat(value);
    return Number.isNaN(num) ? fallback : num;
  };

  // ------------------------
  // Fetch data
  // ------------------------
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [batteryRes, solarRes, energyRes, weatherRes] = await Promise.all([
        fetch(`${API_BASE_URL}/battery-state?limit=600`),
        fetch(`${API_BASE_URL}/predicted-solar-production?limit=300`),
        fetch(`${API_BASE_URL}/energy-consumption-hourly?limit=200`),
        fetch(`${API_BASE_URL}/weather-forecast-hourly?limit=10`),
      ]);

      if (!batteryRes.ok || !solarRes.ok || !energyRes.ok || !weatherRes.ok) {
        throw new Error('Erreur lors de la récupération des données');
      }

      const batteryJson = await batteryRes.json();
      const solarJson = await solarRes.json();
      const energyJson = await energyRes.json();
      const weatherJson = await weatherRes.json();

      setBatteryData(batteryJson.results || []);
      const solarList = (solarJson.results || []).reverse();
      setSolarProduction(solarList);
      setEnergyConsumption(energyJson.results || []);
      setWeatherData(weatherJson.results?.[0] || null);

      calculateGlobalMetrics(solarJson.results || [], energyJson.results || []);
      setLoading(false);
    } catch (err) {
      console.error('Erreur API:', err);
      setError(err.message || 'Erreur inconnue');
      setLoading(false);
    }
  };

  // ------------------------
  // KPIs globaux
  // ------------------------
  const calculateGlobalMetrics = (solar, energy) => {
    if (!solar || solar.length === 0) {
      setCurrentPower(0);
      setTodayProduction(0);
      const todayReal = new Date().toISOString().split('T')[0];
      const todayEnergy = energy
        .filter((e) => (e.time_ts || '').startsWith(todayReal))
        .reduce((sum, e) => sum + safeParseFloat(e.use_kw, 0), 0);
      setTodayConsumption(todayEnergy);
      return;
    }

    const bestSolar = solar.reduce(
      (acc, s) => {
        const vKw = safeParseFloat(
          s.ac_power_kw ?? s.predicted_production_kwh,
          -Infinity
        );
        if (vKw > acc.valueKw) {
          return { row: s, valueKw: vKw };
        }
        return acc;
      },
      { row: solar[0], valueKw: safeParseFloat(solar[0].ac_power_kw ?? solar[0].predicted_production_kwh, 0) }
    );

    const bestKw = Math.max(bestSolar.valueKw, 0);
    setCurrentPower(bestKw * 1000);

    const sortedSolar = [...solar].sort((a, b) => {
      const ta = new Date(a.timestamp || a.forecast_timestamp);
      const tb = new Date(b.timestamp || b.forecast_timestamp);
      return ta - tb;
    });

    const firstTs = sortedSolar[0].timestamp || sortedSolar[0].forecast_timestamp;
    const forecastStartDay = firstTs.slice(0, 10);
    const todaySolar = solar
      .filter((s) =>
        (s.timestamp || s.forecast_timestamp || '').startsWith(forecastStartDay)
      )
      .reduce(
        (sum, s) => sum + safeParseFloat(s.predicted_production_kwh, 0),
        0
      );
    setTodayProduction(todaySolar);

    const todayReal = new Date().toISOString().split('T')[0];
    const todayEnergy = energy
      .filter((e) => (e.time_ts || '').startsWith(todayReal))
      .reduce((sum, e) => sum + safeParseFloat(e.use_kw, 0), 0);
    setTodayConsumption(todayEnergy);
  };

  // ------------------------
  // Battery helpers
  // ------------------------
  const getBatterySeries = () => {
    const filtered = batteryData
      .filter((b) => b.battery_type === selectedBattery)
      .map((b) => ({
        ...b,
        ts: new Date(b.timestamp),
        soc: safeParseFloat(b.soc_end_pct ?? b.soc_start_pct, 0),
        energy: safeParseFloat(b.energy_stored_kwh, 0),
        isPredicted: !!b.is_predicted,
      }))
      .sort((a, b) => a.ts - b.ts);
    return filtered;
  };

  const getCurrentBattery = () => {
    const series = getBatterySeries();
    if (series.length === 0) return {};
    return series[series.length - 1];
  };

  const getBatteryHistory = () => {
    const filtered = batteryData
      .filter((b) => b.battery_type === selectedBattery)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    return filtered.slice(-48);
  };

  // ------------------------
  // Chart data (SOC)
  // ------------------------
  const getChartData = () => {
    const series = getBatterySeries();
    if (series.length === 0) {
      return Array.from({ length: 24 }, (_, i) => ({
        label: `${i}h`,
        value: 0,
        isPredicted: false,
        highlight: false,
      }));
    }

    if (viewPeriod === 'hour') {
      const last24 = series.slice(-24);
      return last24.map((point) => {
        const hour = point.ts.getHours();
        return {
          label: `${hour}h`,
          value: Math.max(Math.min(point.soc, 100), 0),
          isPredicted: point.isPredicted,
          highlight: false,
        };
      });
    }

    if (viewPeriod === 'day') {
      const byDate = {};
      series.forEach((p) => {
        const key = p.ts.toISOString().split('T')[0];
        if (!byDate[key]) {
          byDate[key] = { sum: 0, count: 0, isPredicted: p.isPredicted };
        }
        byDate[key].sum += p.soc;
        byDate[key].count += 1;
        byDate[key].isPredicted = byDate[key].isPredicted || p.isPredicted;
      });
      const dates = Object.keys(byDate).sort();
      const last14 = dates.slice(-14);
      return last14.map((d) => {
        const obj = byDate[d];
        const avg = obj.count ? obj.sum / obj.count : 0;
        const dt = new Date(d);
        return {
          label: `${dt.getDate()}/${dt.getMonth() + 1}`,
          value: Math.max(Math.min(avg, 100), 0),
          isPredicted: obj.isPredicted,
          highlight: false,
        };
      });
    }

    // Week view
    const byWeek = {};
    series.forEach((p) => {
      const d = new Date(p.ts.getTime());
      const dayNum = (d.getDay() + 6) % 7 + 1;
      d.setDate(d.getDate() + 4 - dayNum);
      const year = d.getFullYear();
      const week = Math.ceil(((d - new Date(year, 0, 1)) / 86400000 + 1) / 7);
      const key = `${year}-W${String(week).padStart(2, '0')}`;
      if (!byWeek[key]) {
        byWeek[key] = { sum: 0, count: 0, isPredicted: p.isPredicted };
      }
      byWeek[key].sum += p.soc;
      byWeek[key].count += 1;
      byWeek[key].isPredicted = byWeek[key].isPredicted || p.isPredicted;
    });
    const weeks = Object.keys(byWeek).sort();
    const last8 = weeks.slice(-8);
    return last8.map((wKey) => {
      const obj = byWeek[wKey];
      const avg = obj.count ? obj.sum / obj.count : 0;
      return {
        label: wKey.replace('-W', ' S'),
        value: Math.max(Math.min(avg, 100), 0),
        isPredicted: obj.isPredicted,
        highlight: false,
      };
    });
  };

  // ------------------------
  // Loading / error UI
  // ------------------------
  if (loading && batteryData.length === 0) {
    return (
      <div className="min-h-screen bg-[#E9FAFD] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-[#4E6243] mx-auto mb-4"></div>
          <p className="text-[#18291E] font-medium">Chargement des données...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#E9FAFD] flex items-center justify-center p-8">
        <div className="bg-white rounded-2xl p-8 max-w-md shadow-xl border border-[#BEB6C6]/20">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-[#18291E] mb-2 text-center">Erreur de connexion</h2>
          <p className="text-[#4E6243] text-center mb-4">{error}</p>
          <button
            onClick={fetchAllData}
            className="w-full bg-[#4E6243] text-white px-6 py-3 rounded-xl font-medium hover:bg-[#18291E] transition-colors"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  // ------------------------
  // Derived values for UI
  // ------------------------
  const currentBattery = getCurrentBattery();
  const batteryHistory = getBatteryHistory();
  const chartData = getChartData();
  const batteryCapacity = safeParseFloat(
    currentBattery.battery_capacity_kwh,
    selectedBattery === 'main' ? 3000 : 1000
  );
  const batteryLevel = safeParseFloat(currentBattery.soc, 0);
  const batteryStored = safeParseFloat(currentBattery.energy, 0);

  const savings = todayProduction * 0.15;

  return (
    <div className="min-h-screen bg-[#E9FAFD] p-6">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between mb-8 gap-4">
          <div className="flex items-center gap-4 flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-shrink-0">
              <div className="w-10 h-10 bg-[#4E6243] rounded-xl flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl font-bold text-[#18291E] truncate">RenewStation</h1>
                <p className="text-xs text-[#4E6243]">Solar Energy Management</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="flex items-center gap-2 text-sm text-[#4E6243] bg-white px-4 py-2 rounded-lg border border-[#BEB6C6]/20">
              <Calendar className="w-4 h-4" />
              {new Date().toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
              })}
            </div>
            <div className="relative">
              <button
                onClick={() => setBatteryDropdownOpen((v) => !v)}
                className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg text-sm font-medium text-[#18291E] hover:bg-[#F5F5F5] transition-all border border-[#BEB6C6]/20"
              >
                <Battery className="w-4 h-4 text-[#4E6243]" />
                <span className="truncate max-w-[150px]">{selectedOption.label}</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {batteryDropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl z-20 overflow-hidden border border-[#BEB6C6]/20">
                  {batteryOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => {
                        setSelectedBattery(option.value);
                        setBatteryDropdownOpen(false);
                      }}
                      className={`w-full px-4 py-3 text-left hover:bg-[#E9FAFD] transition-colors ${
                        selectedBattery === option.value ? 'bg-[#E9FAFD]' : ''
                      }`}
                    >
                      <div className="font-medium text-[#18291E] text-sm">{option.label}</div>
                      <div className="text-xs text-[#4E6243]">{option.capacity}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={fetchAllData}
              className="p-2 hover:bg-white rounded-lg transition-colors border border-transparent hover:border-[#BEB6C6]/20"
              title="Rafraîchir"
            >
              <Activity className="w-5 h-5 text-[#4E6243]" />
            </button>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column */}
          <div className="col-span-3 space-y-6">
            {/* Current Power */}
            <div className="bg-[#4E6243] rounded-2xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
                  <Zap className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-white/90">
                  Production Actuelle
                </span>
              </div>
              <div className="mb-2">
                <span className="text-4xl font-bold text-white">
                  {currentPower > 1000
                    ? `${(currentPower / 1000).toFixed(1)}`
                    : `${Math.round(currentPower)}`}
                </span>
                <span className="text-xl text-white/70 ml-1">
                  {currentPower > 1000 ? 'kW' : 'W'}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm text-white/70">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>Système actif</span>
              </div>
            </div>

            {/* Battery Card */}
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-[#BEB6C6]/20">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Battery className="w-5 h-5 text-[#4E6243]" />
                  <span className="text-sm font-semibold text-[#18291E]">
                    Niveau de Charge
                  </span>
                </div>
              </div>
              <div className="mb-4">
                <span className="text-5xl font-bold text-[#18291E]">
                  {batteryLevel.toFixed(0)}
                </span>
                <span className="text-2xl text-[#4E6243] ml-1">%</span>
              </div>
              <div className="h-2 bg-[#E9FAFD] rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-[#4E6243] rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(0, Math.min(batteryLevel, 100))}%` }}
                ></div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[#BEB6C6]/20">
                <div>
                  <p className="text-xs text-[#4E6243] mb-1">Capacité</p>
                  <p className="font-semibold text-[#18291E] text-sm">
                    {batteryCapacity.toFixed(0)} kWh
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[#4E6243] mb-1">Stocké</p>
                  <p className="font-semibold text-[#18291E] text-sm">
                    {batteryStored.toFixed(0)} kWh
                  </p>
                </div>
              </div>
              {currentBattery.ts && (
                <div className="mt-4 pt-4 border-t border-[#BEB6C6]/20">
                  <p className="text-xs text-[#4E6243]">
                    Mise à jour:{' '}
                    {currentBattery.ts.toLocaleString('fr-FR', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                    {currentBattery.isPredicted && ' (prévu)'}
                  </p>
                </div>
              )}
            </div>

            {/* Weather Card */}
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-[#BEB6C6]/20">
              <div className="flex items-center gap-2 mb-4">
                <Sun className="w-5 h-5 text-[#4E6243]" />
                <span className="text-sm font-semibold text-[#18291E]">Conditions Météo</span>
              </div>
              {weatherData ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2">
                    <span className="text-sm text-[#4E6243]">Température</span>
                    <span className="font-semibold text-[#18291E]">
                      {safeParseFloat(weatherData.temperature_c, 0).toFixed(1)}°C
                    </span>
                  </div>
                  <div className="h-px bg-[#BEB6C6]/20"></div>
                  <div className="flex justify-between items-center py-2">
                    <div className="flex items-center gap-2">
                      <Droplets className="w-4 h-4 text-[#4E6243]" />
                      <span className="text-sm text-[#4E6243]">Humidité</span>
                    </div>
                    <span className="font-semibold text-[#18291E]">
                      {safeParseFloat(weatherData.humidity_pct, 0).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-px bg-[#BEB6C6]/20"></div>
                  <div className="flex justify-between items-center py-2">
                    <div className="flex items-center gap-2">
                      <Wind className="w-4 h-4 text-[#4E6243]" />
                      <span className="text-sm text-[#4E6243]">Couverture</span>
                    </div>
                    <span className="font-semibold text-[#18291E]">
                      {safeParseFloat(weatherData.cloud_cover_pct, 0).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-[#4E6243]">Données indisponibles</p>
              )}
            </div>
          </div>

          {/* Center Column – Battery Chart */}
          <div className="col-span-6">
            <div className="bg-white rounded-2xl p-8 shadow-lg h-full border border-[#BEB6C6]/20">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-[#18291E] mb-1">Historique de Charge</h2>
                  <p className="text-xs text-[#4E6243]">
                    Données réelles et prévisions sur 7 jours
                  </p>
                </div>
                <div className="flex gap-2">
                  {[
                    { label: 'Heure', value: 'hour' },
                    { label: 'Jour', value: 'day' },
                    { label: 'Semaine', value: 'week' },
                  ].map((period) => (
                    <button
                      key={period.value}
                      onClick={() => setViewPeriod(period.value)}
                      className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                        viewPeriod === period.value
                          ? 'bg-[#4E6243] text-white'
                          : 'bg-[#E9FAFD] text-[#4E6243] hover:bg-[#BEB6C6]/20'
                      }`}
                    >
                      {period.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Chart */}
              <div className="flex">
                {/* Y-axis */}
                <div className="flex flex-col justify-between text-xs text-[#4E6243] pr-4 h-80 w-8 flex-shrink-0">
                  <span>100%</span>
                  <span>75%</span>
                  <span>50%</span>
                  <span>25%</span>
                  <span>0%</span>
                </div>
                {/* Bars */}
                <div className="flex-1 flex items-end justify-between gap-1 min-w-0">
                  {chartData.map((data, idx) => (
                    <div
                      key={`${data.label}-${idx}`}
                      className="flex flex-col items-center gap-2 flex-1 min-w-0"
                    >
                      <div className="relative w-full h-80 flex flex-col justify-end">
                        <div
                          className={`w-full transition-all duration-300 rounded-t ${
                            data.isPredicted
                              ? 'bg-[#BEB6C6]/40 hover:bg-[#BEB6C6]/60'
                              : 'bg-[#4E6243] hover:bg-[#18291E]'
                          }`}
                          style={{
                            height: `${Math.max(data.value, 2)}%`,
                          }}
                          title={`${data.value.toFixed(1)}% ${
                            data.isPredicted ? '(prévu)' : '(réel)'
                          }`}
                        ></div>
                      </div>
                      <span className="text-xs text-[#4E6243] text-center truncate w-full">
                        {data.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Legend */}
              <div className="mt-6 flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-[#4E6243] rounded"></div>
                  <span className="text-[#4E6243]">Données réelles</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-[#BEB6C6]/50 rounded"></div>
                  <span className="text-[#4E6243]">Prévisions</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="col-span-3 space-y-6">
            {/* Today's Summary */}
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-[#BEB6C6]/20">
              <div className="flex items-center gap-2 mb-6">
                <BarChart3 className="w-5 h-5 text-[#4E6243]" />
                <span className="text-sm font-semibold text-[#18291E]">
                  Aujourd&apos;hui
                </span>
              </div>
              <div className="space-y-5">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-[#4E6243]">Production</span>
                    <ArrowUp className="w-4 h-4 text-green-600" />
                  </div>
                  <p className="text-3xl font-bold text-[#18291E]">
                    {todayProduction.toFixed(1)}
                  </p>
                  <p className="text-xs text-[#4E6243]">kWh</p>
                </div>
                <div className="h-px bg-[#BEB6C6]/20"></div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-[#4E6243]">Consommation</span>
                    <ArrowDown className="w-4 h-4 text-blue-600" />
                  </div>
                  <p className="text-3xl font-bold text-[#18291E]">
                    {todayConsumption.toFixed(1)}
                  </p>
                  <p className="text-xs text-[#4E6243]">kWh</p>
                </div>
              </div>
            </div>

            {/* Savings */}
            <div className="bg-[#BEB6C6] rounded-2xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-white/30 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-[#18291E]" />
                </div>
                <span className="text-sm font-medium text-[#18291E]">Économies</span>
              </div>
              <div className="mb-2">
                <span className="text-4xl font-bold text-[#18291E]">
                  ${savings.toFixed(0)}
                </span>
              </div>
              <p className="text-sm text-[#18291E]/80 mb-4">
                Estimé à 0.15$/kWh d&apos;énergie solaire produite
              </p>
              <div className="flex items-center justify-between pt-4 border-t border-white/20">
                <span className="text-xs text-[#18291E]/70">Objectif mensuel</span>
                <span className="text-xs font-medium text-[#18291E]">$500</span>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-[#BEB6C6]/20">
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-semibold text-[#18291E]">
                    Statut du Système
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-[#4E6243]">Panneaux solaires</span>
                  <span className="font-semibold text-[#18291E] text-sm">1364 actifs</span>
                </div>
                <div className="h-px bg-[#BEB6C6]/20"></div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-[#4E6243]">Capacité totale</span>
                  <span className="font-semibold text-[#18291E] text-sm">750 kW</span>
                </div>
                <div className="h-px bg-[#BEB6C6]/20"></div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-[#4E6243]">Points de données</span>
                  <span className="font-semibold text-green-600 text-sm">
                    {batteryHistory.length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SolarDashboard;