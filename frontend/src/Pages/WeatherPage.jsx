// WeatherPage.jsx
import React, { useState, useEffect } from 'react';
import {
  Sun,
  CloudSun,
  Wind,
  Droplets,
  Calendar,
  Activity,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Table,
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const WeatherPage = () => {
  const [forecastData, setForecastData] = useState([]);
  const [archiveData, setArchiveData] = useState([]);
  const [mode, setMode] = useState('forecast'); // 'forecast' | 'history'
  const [selectedDay, setSelectedDay] = useState(null);
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'
  const [loading, setLoading] = useState(true);

  // ------------ generic helpers (robust to field names) ------------
  const safeNumber = (v, fallback = 0) => {
    const n = parseFloat(v);
    return Number.isNaN(n) ? fallback : n;
  };

  // choose the first existing field from candidates, otherwise try first numeric field
  const pickField = (row, candidates, fallback = 0) => {
    if (!row) return fallback;
    for (const key of candidates) {
      if (row[key] !== undefined && row[key] !== null) {
        return safeNumber(row[key], fallback);
      }
    }
    // last resort: first numeric-ish value
    for (const [k, v] of Object.entries(row)) {
      const n = parseFloat(v);
      if (!Number.isNaN(n)) return n;
    }
    return fallback;
  };

  // timestamp getter – tries several common keys
  const getTimestamp = (row) =>
    row?.forecast_timestamp ||
    row?.timestamp ||
    row?.time_ts ||
    row?.time ||
    row?.datetime ||
    null;

  const getHour = (row) => {
    const ts = getTimestamp(row);
    if (!ts) return 0;
    return new Date(ts).getHours();
  };

  const formatTemp = (v) => `${safeNumber(v).toFixed(1)}°C`;
  const formatPercent = (v) => `${safeNumber(v).toFixed(0)}%`;
  const formatMm = (v) => `${safeNumber(v).toFixed(1)} mm`;
  const formatWind = (v) => `${safeNumber(v).toFixed(1)} km/h`;

  const groupByDay = (rows) => {
    const out = {};
    rows.forEach((row) => {
      const ts = getTimestamp(row);
      if (!ts) return;
      const key = ts.slice(0, 10); // YYYY-MM-DD
      if (!out[key]) out[key] = [];
      out[key].push(row);
    });
    return out;
  };

  const formatDayLabel = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
    });
  };

  // --------------------- Fetch data ---------------------
  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setLoading(true);
        const [fRes, aRes] = await Promise.all([
          fetch(`${API_BASE_URL}/weather-forecast-hourly?limit=2000`),
          fetch(`${API_BASE_URL}/weather-archive-hourly?limit=2000`),
        ]);

        const fJson = await fRes.json();
        const aJson = await aRes.json();

        const fRows = fJson.results || [];
        const aRows = aJson.results || [];

        console.log('🌤 Forecast sample:', fRows[0]);
        console.log('📈 Archive sample:', aRows[0]);

        setForecastData(fRows);
        setArchiveData(aRows);
      } catch (e) {
        console.error('Weather API error:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchWeather();
  }, []);

  // When data or mode changes, choose a valid selected day
  useEffect(() => {
    const active = mode === 'forecast' ? forecastData : archiveData;
    if (!active.length) {
      setSelectedDay(null);
      return;
    }
    const firstTs = getTimestamp(active[0]);
    if (!firstTs) {
      setSelectedDay(null);
      return;
    }
    const firstKey = firstTs.slice(0, 10);
    setSelectedDay(firstKey);
  }, [mode, forecastData, archiveData]);

  // --------------------- Derived data ---------------------
  const activeRows = mode === 'forecast' ? forecastData : archiveData;
  const grouped = groupByDay(activeRows);
  const dayKeys = Object.keys(grouped).sort();

  const currentSelectedKey =
    selectedDay && grouped[selectedDay]
      ? selectedDay
      : dayKeys.length
      ? dayKeys[0]
      : null;

  const selectedRows = currentSelectedKey ? grouped[currentSelectedKey] || [] : [];

  const average = (rows, getter) => {
    if (!rows.length) return 0;
    const sum = rows.reduce((acc, r) => acc + getter(r), 0);
    return sum / rows.length;
  };

  const sumField = (rows, getter) =>
    rows.reduce((acc, r) => acc + getter(r), 0);

  // mapping to your likely API fields
  const getTemp = (r) =>
    pickField(r, [
      'temperature_2m',
      'temp_mean_c',
      'temp_c',
      'temperature',
      'temperature_c',
    ]);
  const getHum = (r) =>
    pickField(r, [
      'relative_humidity_2m',
      'humidity_pct',
      'humidity',
      'hum',
    ]);
  const getPrec = (r) =>
    pickField(r, [
      'precipitation',
      'precip_mm',
      'precipitation_mm',
      'rain_mm',
    ]);
  const getWind = (r) =>
    pickField(r, [
      'wind_speed_10m',
      'wind_speed',
      'wind_speed_kmh',
      'wind_kmh',
    ]);
  const getRad = (r) =>
    pickField(r, [
      'shortwave_radiation',
      'solar_radiation',
      'solar_radiation_wm2',
      'radiation_wm2',
    ]);

  const avgTemp = average(activeRows, getTemp);
  const avgHum = average(activeRows, getHum);
  const totalPrec = sumField(activeRows, getPrec);
  const avgWind = average(activeRows, getWind);

  // day summaries
  const daySummaries = dayKeys.map((key) => {
    const rows = grouped[key];
    return {
      key,
      label: formatDayLabel(key),
      avgTemp: average(rows, getTemp),
      avgHum: average(rows, getHum),
      totalPrec: sumField(rows, getPrec),
      points: rows.length,
    };
  });

  // mini-charts
  const sortedSelected = [...selectedRows].sort(
    (a, b) => getHour(a) - getHour(b)
  );

  const tempValues = sortedSelected.map(getTemp);
  const humValues = sortedSelected.map(getHum);
  const radValues = sortedSelected.map(getRad);

  const miniChart = (values, rows, colorClass) => {
    if (!rows.length || !values.length) {
      return (
        <div className="flex items-center justify-center h-32 text-xs text-emerald-500/70">
          Pas de données pour ce jour.
        </div>
      );
    }

    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    return (
      <div className="flex items-end gap-1 h-32">
        {rows.map((r, idx) => {
          const h = getHour(r);
          const val = values[idx];
          const pct = ((val - min) / range) * 100;
          return (
            <div key={idx} className="flex flex-col items-center flex-1">
              <div className="w-full bg-emerald-50 rounded-full h-24 overflow-hidden flex items-end">
                <div
                  className={`w-full ${colorClass} rounded-full transition-all`}
                  style={{ height: `${Math.max(4, pct)}%` }}
                />
              </div>
              {idx % 3 === 0 && (
                <span className="mt-1 text-[10px] text-emerald-700">
                  {h}h
                </span>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  // hourly details for selected day
  const hourlyDetails = sortedSelected.map((r, idx) => {
    const hour = getHour(r);
    return {
      id: idx,
      hourLabel: `${hour.toString().padStart(2, '0')}:00`,
      temp: formatTemp(getTemp(r)),
      hum: formatPercent(getHum(r)),
      prec: `${safeNumber(getPrec(r)).toFixed(1)} mm`,
      rad: `${safeNumber(getRad(r)).toFixed(0)} W/m²`,
    };
  });

  const displayedHourlyCards =
    viewMode === 'cards' ? hourlyDetails.slice(0, 8) : hourlyDetails;

  // ---------------- loading state ----------------
  if (loading && !activeRows.length) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-emerald-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4" />
          <p className="text-emerald-800 font-medium">
            Chargement des données météo...
          </p>
        </div>
      </div>
    );
  }

  // ---------------- UI ----------------
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-emerald-50 to-teal-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sun className="w-7 h-7 text-emerald-600" />
              <h1 className="text-3xl font-bold text-emerald-900">
                Météo &amp; Prévisions
              </h1>
            </div>
            <p className="text-sm text-emerald-700">
              Prévisions 7 jours · Casablanca, Maroc ·{' '}
              <span className="font-semibold">{activeRows.length} points</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/70 rounded-full px-4 py-2 shadow-sm">
              <Calendar className="w-4 h-4 text-emerald-600" />
              <span className="text-sm text-emerald-800">
                {new Date().toLocaleDateString('fr-FR', {
                  weekday: 'long',
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric',
                })}
              </span>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="p-2 rounded-full bg-white/70 hover:bg-white shadow-sm transition-colors"
            >
              <Activity className="w-4 h-4 text-emerald-700" />
            </button>
          </div>
        </div>

        {/* Tabs + KPIs */}
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-3 flex gap-3">
            <button
              onClick={() => setMode('forecast')}
              className={`flex-1 rounded-2xl px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 shadow-sm transition-all ${
                mode === 'forecast'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white/80 text-emerald-700 hover:bg-white'
              }`}
            >
              <CloudSun className="w-4 h-4" />
              Prévisions
            </button>
            <button
              onClick={() => setMode('history')}
              className={`flex-1 rounded-2xl px-4 py-3 text-sm font-semibold flex items-center justify-center gap-2 shadow-sm transition-all ${
                mode === 'history'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white/80 text-emerald-700 hover:bg-white'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Historique
            </button>
          </div>

          {/* Global metrics */}
          <div className="col-span-9 grid grid-cols-4 gap-4">
            <div className="bg-white/80 rounded-2xl p-4 shadow-sm">
              <p className="text-xs text-emerald-600 font-semibold mb-1">
                Temp. Moyenne (24h)
              </p>
              <p className="text-2xl font-bold text-emerald-900">
                {formatTemp(avgTemp)}
              </p>
            </div>
            <div className="bg-white/80 rounded-2xl p-4 shadow-sm">
              <p className="text-xs text-emerald-600 font-semibold mb-1">
                Humidité Moyenne
              </p>
              <p className="text-2xl font-bold text-emerald-900">
                {formatPercent(avgHum)}
              </p>
            </div>
            <div className="bg-white/80 rounded-2xl p-4 shadow-sm">
              <p className="text-xs text-emerald-600 font-semibold mb-1">
                Précipitation Totale
              </p>
              <p className="text-2xl font-bold text-emerald-900">
                {formatMm(totalPrec)}
              </p>
            </div>
            <div className="bg-white/80 rounded-2xl p-4 shadow-sm">
              <p className="text-xs text-emerald-600 font-semibold mb-1">
                Vent Moyen
              </p>
              <p className="text-2xl font-bold text-emerald-900">
                {formatWind(avgWind)}
              </p>
            </div>
          </div>
        </div>

        {/* Day selector */}
        <div className="bg-white/70 rounded-2xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-semibold text-emerald-800">
              {mode === 'forecast' ? 'Prévisions 7 jours' : 'Historique récent'}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  if (!currentSelectedKey || !dayKeys.length) return;
                  const idx = dayKeys.indexOf(currentSelectedKey);
                  if (idx > 0) setSelectedDay(dayKeys[idx - 1]);
                }}
                className="p-1 rounded-full hover:bg-emerald-50 text-emerald-700"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  if (!currentSelectedKey || !dayKeys.length) return;
                  const idx = dayKeys.indexOf(currentSelectedKey);
                  if (idx < dayKeys.length - 1) setSelectedDay(dayKeys[idx + 1]);
                }}
                className="p-1 rounded-full hover:bg-emerald-50 text-emerald-700"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex gap-3 overflow-x-auto pb-1">
            {daySummaries.map((d) => {
              const active = d.key === currentSelectedKey;
              return (
                <button
                  key={d.key}
                  onClick={() => setSelectedDay(d.key)}
                  className={`min-w-[170px] rounded-xl border text-left px-4 py-3 flex-shrink-0 transition-all ${
                    active
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-md'
                      : 'bg-white border-emerald-100 hover:border-emerald-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold flex items-center gap-1">
                      <Sun className="w-3 h-3" />
                      {d.label}
                    </span>
                    <span className="text-[11px] opacity-80">
                      {d.points} pts
                    </span>
                  </div>
                  <p className="text-sm font-semibold">
                    {formatTemp(d.avgTemp)} moyenne
                  </p>
                  <div className="mt-1 text-[11px] opacity-90 space-x-2">
                    <span>💧 {formatPercent(d.avgHum)}</span>
                    <span>🌧 {d.totalPrec.toFixed(1)} mm</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Mini charts */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white/80 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-emerald-700">
                Température (jour sélectionné)
              </span>
              <span className="text-[11px] text-emerald-500">24 heures</span>
            </div>
            {miniChart(tempValues, sortedSelected, 'bg-emerald-400')}
          </div>

          <div className="bg-white/80 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-emerald-700">
                Humidité &amp; Pluie
              </span>
              <span className="text-[11px] text-emerald-500">24 heures</span>
            </div>
            {miniChart(humValues, sortedSelected, 'bg-sky-400')}
          </div>

          <div className="bg-white/80 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-emerald-700">
                Rayonnement Solaire
              </span>
              <span className="text-[11px] text-emerald-500">24 heures</span>
            </div>
            {miniChart(radValues, sortedSelected, 'bg-amber-400')}
          </div>
        </div>

        {/* Details */}
        <div className="bg-white/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-emerald-800">
              Détails pour{' '}
              {currentSelectedKey ? formatDayLabel(currentSelectedKey) : '—'}
            </p>
            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={() => setViewMode('cards')}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full border transition-all ${
                  viewMode === 'cards'
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-white text-emerald-700 border-emerald-200 hover:border-emerald-400'
                }`}
              >
                <BarChart3 className="w-3 h-3" />
                Vue cartes
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full border transition-all ${
                  viewMode === 'table'
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-white text-emerald-700 border-emerald-200 hover:border-emerald-400'
                }`}
              >
                <Table className="w-3 h-3" />
                Vue tableau
              </button>
            </div>
          </div>

          {viewMode === 'cards' ? (
            <div className="grid grid-cols-4 gap-3">
              {displayedHourlyCards.map((h) => (
                <div
                  key={h.id}
                  className="border border-emerald-100 rounded-xl px-3 py-3 bg-white hover:border-emerald-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-emerald-800">
                      {h.hourLabel}
                    </span>
                    <Sun className="w-3 h-3 text-amber-400" />
                  </div>
                  <p className="text-sm font-bold text-emerald-900 mb-2">
                    {h.temp}
                  </p>
                  <div className="space-y-1 text-[11px] text-emerald-700">
                    <div>💧 Humidité : {h.hum}</div>
                    <div>🌧 Pluie : {h.prec}</div>
                    <div>☀ Rad. : {h.rad}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-emerald-50 text-emerald-800">
                    <th className="text-left px-4 py-2">Heure</th>
                    <th className="text-left px-4 py-2">Température</th>
                    <th className="text-left px-4 py-2">Humidité</th>
                    <th className="text-left px-4 py-2">Pluie</th>
                    <th className="text-left px-4 py-2">Rayonnement</th>
                  </tr>
                </thead>
                <tbody>
                  {hourlyDetails.map((h, idx) => (
                    <tr
                      key={h.id}
                      className={`border-top border-emerald-50 ${
                        idx % 2 === 0 ? 'bg-white' : 'bg-emerald-50/40'
                      }`}
                    >
                      <td className="px-4 py-2 font-semibold text-emerald-900">
                        {h.hourLabel}
                      </td>
                      <td className="px-4 py-2">{h.temp}</td>
                      <td className="px-4 py-2">{h.hum}</td>
                      <td className="px-4 py-2">{h.prec}</td>
                      <td className="px-4 py-2">{h.rad}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WeatherPage;
