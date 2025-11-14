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
} from 'lucide-react';

const API_BASE_URL = '/api/solar';

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
  const [viewPeriod, setViewPeriod] = useState('day'); // 'hour' | 'day' | 'week'

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
      const solarList = (solarJson.results || []).reverse();
      setSolarProduction(solarList);

      const energyJson = await energyRes.json();
      const weatherJson = await weatherRes.json();

      // debug global
      console.log('🔥 Solar API sample:', solarJson.results?.[0]);
      console.log('🔥 Solar full response:', solarJson);

      setBatteryData(batteryJson.results || []);
      setSolarProduction(solarJson.results || []);
      setEnergyConsumption(energyJson.results || []);
      setWeatherData(weatherJson.results?.[0] || null);

      // pour pouvoir jouer dans la console
      window._solar = solarJson.results || [];

      calculateGlobalMetrics(solarJson.results || [], energyJson.results || []);

      setLoading(false);
    } catch (err) {
      console.error('Erreur API:', err);
      setError(err.message || 'Erreur inconnue');
      setLoading(false);
    }
  };

  // ------------------------
  // KPIs globaux (production / conso)
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

    // ---------- 1) Puissance "actuelle" = meilleure puissance prévue ----------
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
      {
        row: solar[0],
        valueKw: safeParseFloat(
          solar[0].ac_power_kw ?? solar[0].predicted_production_kwh,
          0
        ),
      }
    );

    const bestKw = Math.max(bestSolar.valueKw, 0);
    setCurrentPower(bestKw * 1000); // kW -> W

    // ---------- 2) "Aujourd'hui" = 1er jour de prévision ----------
    const sortedSolar = [...solar].sort((a, b) => {
      const ta = new Date(a.timestamp || a.forecast_timestamp);
      const tb = new Date(b.timestamp || b.forecast_timestamp);
      return ta - tb;
    });

    const firstTs = sortedSolar[0].timestamp || sortedSolar[0].forecast_timestamp;
    const forecastStartDay = firstTs.slice(0, 10); // 'YYYY-MM-DD'

    const todaySolar = solar
      .filter((s) =>
        (s.timestamp || s.forecast_timestamp || '').startsWith(forecastStartDay)
      )
      .reduce(
        (sum, s) => sum + safeParseFloat(s.predicted_production_kwh, 0),
        0
      );

    console.log(
      '🌞 Jour prévision "Aujourd’hui" =',
      forecastStartDay,
      '→',
      todaySolar,
      'kWh'
    );

    setTodayProduction(todaySolar);

    // ---------- 3) Consommation "Aujourd'hui" = date système réelle ----------
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
    return filtered.slice(-48); // 48 derniers points
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

    // viewPeriod === 'week'
    const byWeek = {};
    series.forEach((p) => {
      const d = new Date(p.ts.getTime());
      const dayNum = (d.getDay() + 6) % 7 + 1; // 1..7
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
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800 font-medium">Chargement des données...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center p-8">
        <div className="bg-white/60 backdrop-blur-sm rounded-3xl p-8 max-w-md shadow-lg">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-800 mb-2 text-center">
            Erreur de connexion
          </h2>
          <p className="text-red-600 text-center mb-4">{error}</p>
          <button
            onClick={fetchAllData}
            className="w-full bg-emerald-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-emerald-700 transition-colors"
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

  // ---- extra derived metrics for bottom full-width section ----
  const batterySeries = getBatterySeries();
  const realPoints = batterySeries.filter((p) => !p.isPredicted);
  const predictedPoints = batterySeries.filter((p) => p.isPredicted);

  const avgPredictedSoc =
    predictedPoints.length > 0
      ? predictedPoints.reduce((sum, p) => sum + (p.soc || 0), 0) /
        predictedPoints.length
      : 0;

  const next24hPredicted = predictedPoints.slice(0, 24);
  const minNext24hSoc =
    next24hPredicted.length > 0
      ? Math.min(...next24hPredicted.map((p) => p.soc || 0))
      : null;
  const maxNext24hSoc =
    next24hPredicted.length > 0
      ? Math.max(...next24hPredicted.map((p) => p.soc || 0))
      : null;

  const now = new Date();
  const last24hConsumptionPoints = energyConsumption.filter((e) => {
    if (!e.time_ts) return false;
    const ts = new Date(e.time_ts);
    return now - ts <= 24 * 60 * 60 * 1000 && now >= ts;
  });
  const totalLast24hUseKw = last24hConsumptionPoints.reduce(
    (sum, e) => sum + safeParseFloat(e.use_kw, 0),
    0
  );
  const avgLast24hUseKw =
    last24hConsumptionPoints.length > 0
      ? totalLast24hUseKw / last24hConsumptionPoints.length
      : 0;
  const estimatedAutonomyHours =
    avgLast24hUseKw > 0 ? batteryStored / avgLast24hUseKw : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 bg-white/60 backdrop-blur-sm px-6 py-3 rounded-full shadow-sm">
              <Sun className="w-6 h-6 text-emerald-600" />
              <span className="text-xl font-bold text-emerald-800">
                RenewStation
              </span>
            </div>
            <div className="text-sm text-emerald-700 bg-white/40 backdrop-blur-sm px-4 py-2 rounded-full">
              <Calendar className="w-4 h-4 inline mr-2" />
              {new Date().toLocaleDateString('fr-FR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Global battery selector */}
            <div className="relative">
              <button
                onClick={() => setBatteryDropdownOpen((v) => !v)}
                className="flex items-center gap-2 bg-white/80 px-4 py-2.5 rounded-full text-sm font-medium text-emerald-800 hover:bg-white transition-all shadow-sm"
              >
                <Battery className="w-4 h-4 text-green-600" />
                <span>{selectedOption.label}</span>
                <ChevronDown className="w-3 h-3" />
              </button>

              {batteryDropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg z-20 overflow-hidden">
                  {batteryOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => {
                        setSelectedBattery(option.value);
                        setBatteryDropdownOpen(false);
                      }}
                      className={`w-full px-4 py-3 text-left hover:bg-emerald-50 transition-colors ${
                        selectedBattery === option.value ? 'bg-emerald-50' : ''
                      }`}
                    >
                      <div className="font-medium text-emerald-900 text-sm">
                        {option.label}
                      </div>
                      <div className="text-xs text-emerald-600">
                        {option.capacity}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button className="bg-white/40 backdrop-blur-sm px-5 py-2.5 rounded-full text-sm font-medium text-emerald-800 hover:bg-white/60 transition-all">
              Casablanca, Morocco
            </button>
            <button
              onClick={fetchAllData}
              className="p-3 hover:bg-white/40 rounded-full transition-colors"
              title="Rafraîchir"
            >
              <Activity className="w-5 h-5 text-emerald-700" />
            </button>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column */}
          <div className="col-span-3 space-y-6">
            {/* Current Power */}
            <div className="bg-gradient-to-br from-emerald-400/30 to-teal-400/30 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-5 h-5 text-emerald-700" />
                <span className="text-sm font-medium text-emerald-800">
                  Production Solaire Actuelle
                </span>
              </div>
              <div className="mb-2">
                <span className="text-5xl font-bold text-emerald-900">
                  {currentPower > 1000
                    ? `${(currentPower / 1000).toFixed(1)}kW`
                    : `${Math.round(currentPower)}W`}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-emerald-700">Système actif</span>
                <span className="bg-white/60 px-3 py-1 rounded-full text-emerald-800 font-medium">
                  {solarProduction.length} points
                </span>
              </div>
            </div>

            {/* Battery Card */}
            <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Battery className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-emerald-800">
                    {selectedOption.label}
                  </span>
                </div>
                <span className="text-xs text-emerald-600">
                  {selectedOption.capacity}
                </span>
              </div>

              <div className="mb-4">
                <span className="text-4xl font-bold text-emerald-900">
                  {batteryLevel.toFixed(1)}%
                </span>
              </div>
              <div className="h-3 bg-emerald-100 rounded-full overflow-hidden mb-3">
                <div
                  className="h-full bg-gradient-to-r from-emerald-400 to-green-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.max(0, Math.min(batteryLevel, 100))}%` }}
                ></div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-emerald-600">Capacité</p>
                  <p className="font-semibold text-emerald-900">
                    {batteryCapacity.toFixed(0)} kWh
                  </p>
                </div>
                <div>
                  <p className="text-emerald-600">Stocké</p>
                  <p className="font-semibold text-emerald-900">
                    {batteryStored.toFixed(0)} kWh
                  </p>
                </div>
              </div>

              {currentBattery.ts && (
                <div className="mt-3 pt-3 border-t border-emerald-200">
                  <p className="text-xs text-emerald-600">
                    Dernière mise à jour:{' '}
                    {currentBattery.ts.toLocaleString('fr-FR', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                    {currentBattery.isPredicted ? ' (prévision)' : ' (réel)'}
                  </p>
                </div>
              )}
            </div>

            {/* Weather Card */}
            <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Sun className="w-5 h-5 text-yellow-600" />
                <span className="text-sm font-medium text-emerald-800">
                  Météo
                </span>
              </div>
              {weatherData ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-emerald-700">Température</span>
                    <span className="font-semibold text-emerald-900">
                      {safeParseFloat(weatherData.temperature_c, 0).toFixed(1)}°C
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <Droplets className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-emerald-700">Humidité</span>
                    </div>
                    <span className="font-semibold text-emerald-900">
                      {safeParseFloat(weatherData.humidity_pct, 0).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <Wind className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-emerald-700">Couverture</span>
                    </div>
                    <span className="font-semibold text-emerald-900">
                      {safeParseFloat(weatherData.cloud_cover_pct, 0).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-emerald-600">
                  Données météo indisponibles
                </p>
              )}
            </div>
          </div>

          {/* Center Column – Battery Level Chart */}
          <div className="col-span-6">
            <div className="bg-gradient-to-br from-emerald-200/40 to-teal-200/40 backdrop-blur-sm rounded-3xl p-8 shadow-lg h-full">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-emerald-900">
                    Niveau de Batterie
                  </h2>
                  <p className="text-xs text-emerald-700 mt-1">
                    Jusqu&apos;à aujourd&apos;hui : valeurs réelles • Ensuite :
                    prévisions 7 jours
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
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                        viewPeriod === period.value
                          ? 'bg-white/80 text-emerald-800 shadow-sm'
                          : 'bg-white/30 text-emerald-700 hover:bg-white/50'
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
                <div className="flex flex-col justify-between text-xs text-emerald-700 pr-4 h-80">
                  <span>100%</span>
                  <span>75%</span>
                  <span>50%</span>
                  <span>25%</span>
                  <span>0%</span>
                </div>

                {/* Bars */}
                <div className="flex-1 flex items-end justify-between gap-1">
                  {chartData.map((data, idx) => (
                    <div
                      key={`${data.label}-${idx}`}
                      className="flex flex-col items-center gap-2 flex-1"
                    >
                      <div className="relative w-full h-80 flex flex-col justify-end">
                        <div
                          className={`w-full transition-all duration-300 ${
                            data.isPredicted
                              ? 'bg-emerald-300/60 hover:bg-emerald-300/80'
                              : 'bg-gradient-to-t from-emerald-400 to-emerald-500 shadow-sm'
                          }`}
                          style={{
                            height: `${Math.max(data.value, 2)}%`,
                            borderRadius: '4px 4px 0 0',
                          }}
                          title={`${data.value.toFixed(1)}% ${
                            data.isPredicted ? '(prévu)' : '(réel)'
                          }`}
                        >
                          {!data.isPredicted &&
                            idx === chartData.length - 1 && (
                              <Zap className="w-4 h-4 text-yellow-400 absolute -top-2 left-1/2 -translate-x-1/2 -translate-y-full animate-pulse" />
                            )}
                        </div>
                      </div>

                      {chartData.length <= 24 || idx % 2 === 0 ? (
                        <span className="text-xs text-emerald-600">
                          {data.label}
                        </span>
                      ) : (
                        <span className="text-xs text-emerald-400">.</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Legend */}
              <div className="mt-6 flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gradient-to-t from-emerald-400 to-emerald-500 rounded"></div>
                  <span className="text-emerald-700">Niveau réel</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-emerald-300/70 rounded"></div>
                  <span className="text-emerald-700">Prévision</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column – Additional Stats */}
          <div className="col-span-3 space-y-6">
            {/* Today's Summary */}
            <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-5 h-5 text-emerald-600" />
                <span className="text-sm font-medium text-emerald-800">
                  Aujourd&apos;hui
                </span>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-emerald-700">Production</span>
                    <ArrowUp className="w-4 h-4 text-green-600" />
                  </div>
                  <p className="text-2xl font-bold text-emerald-900">
                    {todayProduction.toFixed(1)} kWh
                  </p>
                </div>
                <div className="h-px bg-emerald-200"></div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-emerald-700">Consommation</span>
                    <ArrowDown className="w-4 h-4 text-blue-600" />
                  </div>
                  <p className="text-2xl font-bold text-emerald-900">
                    {todayConsumption.toFixed(1)} kWh
                  </p>
                </div>
              </div>
            </div>

            {/* Savings */}
            <div className="bg-gradient-to-br from-yellow-200/40 to-amber-200/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-amber-700" />
                <span className="text-sm font-medium text-amber-800">
                  Économies
                </span>
              </div>
              <div className="mb-3">
                <span className="text-4xl font-bold text-amber-900">
                  ${((todayProduction - todayConsumption) * 0.15).toFixed(0)}
                </span>
              </div>
              <p className="text-sm text-amber-700">Aujourd&apos;hui</p>
              <div className="mt-4 flex items-center gap-2 text-sm text-amber-700">
                <ArrowUp className="w-4 h-4 text-green-600" />
                <span>Production active</span>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white/40 backdrop-blur-sm rounded-3xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-emerald-800">
                  Système Opérationnel
                </span>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-emerald-700">Panneaux</span>
                  <span className="font-semibold text-emerald-900">
                    1364 actifs
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-emerald-700">Capacité totale</span>
                  <span className="font-semibold text-emerald-900">750 kW</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-emerald-700">Données batterie</span>
                  <span className="font-semibold text-green-600">
                    {batteryHistory.length} points
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom full-width battery summary */}
        <div className="mt-8">
          <div className="bg-white/70 backdrop-blur-sm rounded-3xl p-6 shadow-lg flex flex-col gap-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Battery className="w-6 h-6 text-emerald-700" />
                <div>
                  <h3 className="text-lg font-semibold text-emerald-900">
                    Synthèse Batterie – {selectedOption.label}
                  </h3>
                  <p className="text-xs text-emerald-700">
                    Vue globale de l&apos;état actuel, des prévisions et de
                    l&apos;autonomie estimée.
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 w-full">
              {/* Carte 1 : Niveau actuel */}
              <div className="bg-emerald-50/70 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-emerald-700">
                    Niveau actuel
                  </span>
                  <Battery className="w-4 h-4 text-emerald-600" />
                </div>
                <p className="text-2xl font-bold text-emerald-900 mb-1">
                  {batteryLevel.toFixed(1)}%
                </p>
                <p className="text-xs text-emerald-700">
                  {batteryStored.toFixed(0)} /{' '}
                  {batteryCapacity.toFixed(0)} kWh stockés
                </p>
              </div>

              {/* Carte 2 : SOC moyen prédit */}
              <div className="bg-emerald-50/70 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-emerald-700">
                    SOC moyen (prévisions)
                  </span>
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                </div>
                <p className="text-2xl font-bold text-emerald-900 mb-1">
                  {predictedPoints.length > 0
                    ? `${avgPredictedSoc.toFixed(1)}%`
                    : '--'}
                </p>
                <p className="text-xs text-emerald-700">
                  Basé sur {predictedPoints.length} points futurs
                </p>
              </div>

              {/* Carte 3 : Variation prochaine 24h */}
              <div className="bg-emerald-50/70 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-emerald-700">
                    Prochaine fenêtre 24h
                  </span>
                  <Calendar className="w-4 h-4 text-emerald-600" />
                </div>
                <p className="text-2xl font-bold text-emerald-900 mb-1">
                  {minNext24hSoc !== null && maxNext24hSoc !== null
                    ? `${minNext24hSoc.toFixed(1)}–${maxNext24hSoc.toFixed(
                        1
                      )}%`
                    : '--'}
                </p>
                <p className="text-xs text-emerald-700">
                  Min / max SOC prévu sur les 24 prochaines heures
                </p>
              </div>

              {/* Carte 4 : Autonomie estimée */}
              <div className="bg-emerald-50/70 rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-emerald-700">
                    Autonomie estimée
                  </span>
                  <Zap className="w-4 h-4 text-emerald-600" />
                </div>
                <p className="text-2xl font-bold text-emerald-900 mb-1">
                  {estimatedAutonomyHours
                    ? `${estimatedAutonomyHours.toFixed(1)} h`
                    : '--'}
                </p>
                <p className="text-xs text-emerald-700">
                  Calculée à partir de la consommation moyenne des 24
                  dernières heures
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SolarDashboard;
