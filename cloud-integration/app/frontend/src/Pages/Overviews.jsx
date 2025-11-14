// src/Pages/Overviews.jsx
import React, { useEffect, useMemo, useState } from 'react';
import {
  Zap,
  SunMedium,
  BatteryCharging,
  CloudSun,
  Activity,
  Gauge,
  Building2,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight,
} from 'lucide-react';

const API_BASE_URL = '/api/solar';

const safeNumber = (val, fallback = 0) => {
  const n = parseFloat(val);
  return Number.isNaN(n) ? fallback : n;
};

const Overview = ({ onNavigate }) => {
  const [energyData, setEnergyData] = useState([]);
  const [solarData, setSolarData] = useState([]);
  const [batteryData, setBatteryData] = useState([]);
  const [weatherData, setWeatherData] = useState([]);
  const [loading, setLoading] = useState(true);

  // ---------- FETCH ----------
  const fetchAll = async () => {
    try {
      setLoading(true);
      const [energyRes, solarRes, batteryRes, weatherRes] = await Promise.all([
        fetch(`${API_BASE_URL}/energy-consumption-hourly?limit=1000`),
        fetch(`${API_BASE_URL}/predicted-solar-production?limit=300`),
        fetch(`${API_BASE_URL}/battery-state?limit=300`),
        fetch(`${API_BASE_URL}/weather-forecast-hourly?limit=24`),
      ]);

      const energyJson = energyRes.ok ? await energyRes.json() : { results: [] };
      const solarJson = solarRes.ok ? await solarRes.json() : { results: [] };
      const batteryJson = batteryRes.ok ? await batteryRes.json() : { results: [] };
      const weatherJson = weatherRes.ok ? await weatherRes.json() : { results: [] };

      setEnergyData(energyJson.results || []);
      setSolarData(solarJson.results || []);
      setBatteryData(batteryJson.results || []);
      setWeatherData(weatherJson.results || []);
    } catch (e) {
      console.error('Overview API error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 60000);
    return () => clearInterval(id);
  }, []);

  // ---------- ENERGY METRICS (reuse logic from EnergyPage) ----------
  const energyMetrics = useMemo(() => {
    if (!energyData.length) {
      return {
        overallCurrentKw: 0,
        totalTodayKwh: 0,
        peakDemandKw: 0,
        avgDemandKw: 0,
      };
    }

    const now = new Date();
    const todayKey = now.toISOString().slice(0, 10);
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const yesterdayKey = yesterday.toISOString().slice(0, 10);

    const perBuilding = {};
    let globalPeak = 0;
    let sumAllKw = 0;
    let countAllKw = 0;

    energyData.forEach((row) => {
      const bName = row.building;
      if (!bName) return;

      const kw = safeNumber(row.use_kw, 0);
      const ts = new Date(row.time_ts);
      const dateKey = row.time_ts?.slice(0, 10);

      if (!perBuilding[bName]) {
        perBuilding[bName] = {
          latestTs: null,
          currentKw: 0,
          todayKwh: 0,
          yesterdayKwh: 0,
          maxKw: 0,
        };
      }

      const stats = perBuilding[bName];

      if (!stats.latestTs || ts > stats.latestTs) {
        stats.latestTs = ts;
        stats.currentKw = kw;
      }

      if (dateKey === todayKey) {
        stats.todayKwh += kw;
      } else if (dateKey === yesterdayKey) {
        stats.yesterdayKwh += kw;
      }

      if (kw > stats.maxKw) stats.maxKw = kw;
      if (kw > globalPeak) globalPeak = kw;
      sumAllKw += kw;
      countAllKw += 1;
    });

    const overallCurrentKw = Object.values(perBuilding).reduce(
      (sum, s) => sum + s.currentKw,
      0
    );
    const totalTodayKwh = Object.values(perBuilding).reduce(
      (sum, s) => sum + s.todayKwh,
      0
    );
    const avgDemandKw = countAllKw ? sumAllKw / countAllKw : 0;

    return {
      overallCurrentKw,
      totalTodayKwh,
      peakDemandKw: globalPeak,
      avgDemandKw,
    };
  }, [energyData]);

  // ---------- SOLAR METRICS (simplified from SolarDashboard) ----------
  const solarMetrics = useMemo(() => {
    if (!solarData.length) {
      return {
        currentPowerKw: 0,
        todayProductionKwh: 0,
        weekProductionKwh: 0,
      };
    }

    const data = solarData;

    // current power = max predicted_ac_power / ac_power_kw
    const best = data.reduce(
      (acc, s) => {
        const val = safeNumber(
          s.ac_power_kw ?? s.predicted_production_kwh,
          -Infinity
        );
        if (val > acc.value) return { row: s, value: val };
        return acc;
      },
      {
        row: data[0],
        value: safeNumber(
          data[0].ac_power_kw ?? data[0].predicted_production_kwh,
          0
        ),
      }
    );
    const currentPowerKw = Math.max(best.value, 0);

    // sort by timestamp
    const tsKey = (row) =>
      row.timestamp || row.forecast_timestamp || row.time_ts || '';
    const sorted = [...data].sort(
      (a, b) => new Date(tsKey(a)) - new Date(tsKey(b))
    );

    const firstTs = tsKey(sorted[0]);
    const todayKey = firstTs.slice(0, 10);

    const now = new Date();
    const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    let todayProductionKwh = 0;
    let weekProductionKwh = 0;

    sorted.forEach((s) => {
      const ts = new Date(tsKey(s));
      const prod = safeNumber(
        s.real_production_kwh ?? s.predicted_production_kwh,
        0
      );

      if (tsKey(s).startsWith(todayKey)) {
        todayProductionKwh += prod;
      }
      if (ts >= weekStart && ts <= now) {
        weekProductionKwh += prod;
      }
    });

    return {
      currentPowerKw,
      todayProductionKwh,
      weekProductionKwh,
    };
  }, [solarData]);

  // ---------- BATTERY METRICS ----------
  const batteryMetrics = useMemo(() => {
    if (!batteryData.length) {
      return {
        socPct: 0,
        storedKwh: 0,
        capacityKwh: 0,
      };
    }

    const mainSeries = batteryData
      .filter((b) => b.battery_type === 'main' || !b.battery_type)
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    const last = mainSeries[mainSeries.length - 1] || batteryData[0];

    const socPct = safeNumber(last.soc_end_pct ?? last.soc_start_pct, 0);
    const storedKwh = safeNumber(last.energy_stored_kwh, 0);
    const capacityKwh = safeNumber(last.battery_capacity_kwh, 3000);

    return { socPct, storedKwh, capacityKwh };
  }, [batteryData]);

  // ---------- WEATHER METRICS ----------
  const weatherMetrics = useMemo(() => {
    if (!weatherData.length) {
      return {
        tempC: 0,
        humidityPct: 0,
        windKmh: 0,
        radiation: 0,
      };
    }
    const latest = weatherData[0];

    const tempC = safeNumber(
      latest.temperature_c ?? latest.temperature ?? latest.temp_c,
      0
    );
    const humidityPct = safeNumber(
      latest.humidity_pct ?? latest.humidity ?? latest.relative_humidity_2m,
      0
    );
    const windKmh = safeNumber(
      latest.wind_speed_kmh ?? latest.wind_speed_10m ?? latest.wind_speed,
      0
    );
    const radiation = safeNumber(
      latest.solar_radiation_w_m2 ??
        latest.shortwave_radiation ??
        latest.radiation_wm2,
      0
    );

    return { tempC, humidityPct, windKmh, radiation };
  }, [weatherData]);

  const handleNavigate = (pageId) => {
    if (typeof onNavigate === 'function') onNavigate(pageId);
  };

  // ---------- LOADING ----------
  if (loading && !energyData.length && !solarData.length) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4" />
          <p className="text-emerald-800 font-semibold">
            Chargement de la vue d&apos;ensemble...
          </p>
        </div>
      </div>
    );
  }

  const { overallCurrentKw, totalTodayKwh, peakDemandKw, avgDemandKw } =
    energyMetrics;
  const { currentPowerKw, todayProductionKwh, weekProductionKwh } = solarMetrics;
  const { socPct, storedKwh, capacityKwh } = batteryMetrics;
  const { tempC, humidityPct, windKmh, radiation } = weatherMetrics;

  const energyChange = 0; // si tu veux, tu peux le calculer vs hier plus tard
  const solarChange = 0;

  const alerts = [
    {
      type: 'Énergie',
      label: 'Campus',
      message: `Demande instantanée ~${overallCurrentKw.toFixed(
        1
      )} kW. Pointe observée ${peakDemandKw.toFixed(1)} kW.`,
      level: 'info',
    },
    {
      type: 'Solaire',
      label: 'PV 750 kW',
      message: `Production d&apos;aujourd&apos;hui ~${todayProductionKwh.toFixed(
        1
      )} kWh.`,
      level: 'info',
    },
    {
      type: 'Batterie',
      label: 'Batterie principale',
      message: `SOC ~${socPct.toFixed(
        1
      )}%, ${storedKwh.toFixed(0)} / ${capacityKwh.toFixed(
        0
      )} kWh stockés.`,
      level: socPct < 30 ? 'warning' : 'info',
    },
  ];

  return (
    <div className="h-full overflow-y-auto px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-emerald-950 flex items-center gap-2">
            Vue d’ensemble du campus
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-700">
              <Activity className="w-3.5 h-3.5" />
              Temps réel
            </span>
          </h1>
          <p className="mt-1 text-sm text-emerald-700">
            Synthèse des données&nbsp;: consommation, production PV, stockage et
            météo (données issues de vos APIs).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="px-3 py-1.5 rounded-full bg-white/80 border border-emerald-100 text-xs text-emerald-700">
            Aujourd&apos;hui ·{' '}
            {new Date().toLocaleDateString('fr-FR', {
              weekday: 'short',
              day: '2-digit',
              month: 'short',
            })}
          </span>
          <span className="px-3 py-1.5 rounded-full bg-emerald-600 text-xs font-semibold text-white shadow-sm">
            Casablanca · Campus
          </span>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {/* ENERGY */}
        <div className="relative overflow-hidden rounded-2xl border border-emerald-100 bg-white/90 shadow-sm">
          <div className="absolute -top-10 -right-10 h-24 w-24 rounded-full bg-emerald-100/70" />
          <div className="relative p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100">
                  <Zap className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-emerald-500">
                    Consommation actuelle
                  </p>
                  <p className="text-[11px] text-emerald-700">Campus complet</p>
                </div>
              </div>
              <button
                onClick={() => handleNavigate('energy')}
                className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-100"
              >
                Détails
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>

            <div className="flex items-end gap-2">
              <p className="text-3xl font-bold text-emerald-950">
                {overallCurrentKw.toFixed(1)}
                <span className="ml-1 text-sm font-semibold text-emerald-600">
                  kW
                </span>
              </p>
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                  energyChange >= 0
                    ? 'bg-red-50 text-red-600'
                    : 'bg-emerald-50 text-emerald-700'
                }`}
              >
                {energyChange >= 0 ? (
                  <ArrowUpRight className="h-3 w-3" />
                ) : (
                  <ArrowDownRight className="h-3 w-3" />
                )}
                {Math.abs(energyChange).toFixed(1)}% vs hier
              </span>
            </div>

            <div className="mt-1 h-2 w-full rounded-full bg-emerald-50">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500"
                style={{
                  width:
                    peakDemandKw > 0
                      ? `${Math.min(
                          (overallCurrentKw / peakDemandKw) * 100,
                          100
                        )}%`
                      : '0%',
                }}
              />
            </div>
            <p className="text-[11px] text-emerald-600">
              Total aujourd&apos;hui :{' '}
              <span className="font-semibold">
                {totalTodayKwh.toFixed(1)} kWh
              </span>
            </p>
          </div>
        </div>

        {/* SOLAR */}
        <div className="relative overflow-hidden rounded-2xl border border-sky-100 bg-white/90 shadow-sm">
          <div className="absolute -top-10 -right-16 h-24 w-32 rounded-full bg-sky-100/70" />
          <div className="relative p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-100">
                  <SunMedium className="h-5 w-5 text-sky-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-sky-500">
                    Production Solaire
                  </p>
                  <p className="text-[11px] text-sky-700">Instantanée</p>
                </div>
              </div>
              <button
                onClick={() => handleNavigate('solar')}
                className="flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-1 text-[11px] font-semibold text-sky-700 hover:bg-sky-100"
              >
                Courbes
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>

            <div className="flex items-end gap-2">
              <p className="text-3xl font-bold text-sky-950">
                {currentPowerKw.toFixed(1)}
                <span className="ml-1 text-sm font-semibold text-sky-600">
                  kW
                </span>
              </p>
              <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold bg-emerald-50 text-emerald-700">
                <ArrowUpRight className="h-3 w-3" />
                {solarChange.toFixed(1)}% vs prévision
              </span>
            </div>

            <p className="text-[11px] text-sky-700">
              Aujourd&apos;hui :{' '}
              <span className="font-semibold">
                {todayProductionKwh.toFixed(1)} kWh
              </span>{' '}
              · 7 jours :{' '}
              <span className="font-semibold">
                {weekProductionKwh.toFixed(0)} kWh
              </span>
            </p>
          </div>
        </div>

        {/* BATTERY */}
        <div className="relative overflow-hidden rounded-2xl border border-amber-100 bg-white/90 shadow-sm">
          <div className="absolute -top-10 -right-12 h-24 w-24 rounded-full bg-amber-100/70" />
          <div className="relative p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-100">
                  <BatteryCharging className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-amber-500">
                    Stockage Batterie
                  </p>
                  <p className="text-[11px] text-amber-700">
                    Batterie principale
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleNavigate('battery')}
                className="flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700 hover:bg-amber-100"
              >
                Bancs
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-end gap-1">
                <p className="text-3xl font-bold text-amber-950">
                  {socPct.toFixed(1)}
                  <span className="ml-0.5 text-sm font-semibold text-amber-600">
                    %
                  </span>
                </p>
              </div>
              <div className="flex flex-col gap-1 text-[11px] text-amber-700">
                <p>
                  Stocké :{' '}
                  <span className="font-semibold">
                    {storedKwh.toFixed(0)} / {capacityKwh.toFixed(0)} kWh
                  </span>
                </p>
                <p>Mode : <span className="font-semibold">Hybride</span></p>
              </div>
            </div>

            <div className="mt-1 h-2 w-full rounded-full bg-amber-50">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-500 to-lime-500"
                style={{ width: `${Math.max(0, Math.min(socPct, 100))}%` }}
              />
            </div>
          </div>
        </div>

        {/* WEATHER */}
        <div className="relative overflow-hidden rounded-2xl border border-cyan-100 bg-white/90 shadow-sm">
          <div className="absolute -top-16 -right-6 h-28 w-28 rounded-full bg-cyan-100/60" />
          <div className="relative p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-100">
                  <CloudSun className="h-5 w-5 text-cyan-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-cyan-500">
                    Conditions météo
                  </p>
                  <p className="text-[11px] text-cyan-700">
                    Impact PV & confort
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleNavigate('weather')}
                className="flex items-center gap-1 rounded-full bg-cyan-50 px-2.5 py-1 text-[11px] font-semibold text-cyan-700 hover:bg-cyan-100"
              >
                Prévisions
                <ChevronRight className="h-3 w-3" />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-cyan-950">
                  {tempC.toFixed(1)}
                  <span className="ml-0.5 text-sm font-semibold text-cyan-600">
                    °C
                  </span>
                </p>
                <p className="text-[11px] text-cyan-700">
                  Humidité : {humidityPct.toFixed(0)}%
                </p>
              </div>
              <div className="flex flex-col gap-1 text-[11px] text-cyan-700">
                <p>
                  Vent : <span className="font-semibold">{windKmh.toFixed(1)} km/h</span>
                </p>
                <p>
                  Radiation :{' '}
                  <span className="font-semibold">{radiation.toFixed(0)} W/m²</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Small extra: building mix + alerts, using simple placeholders but real metrics in text */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="col-span-2 rounded-2xl border border-emerald-100 bg-white/90 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-500">
                Profil de charge (vue globale)
              </p>
              <p className="text-xs text-emerald-700">
                Moyenne vs pointe sur les données chargées
              </p>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-emerald-700">
              <span>
                Pointe :{' '}
                <span className="font-semibold">{peakDemandKw.toFixed(1)} kW</span>
              </span>
              <span>
                Moyenne :{' '}
                <span className="font-semibold">{avgDemandKw.toFixed(1)} kW</span>
              </span>
            </div>
          </div>
          <div className="mt-2 h-24 rounded-xl bg-emerald-50/70 flex items-center justify-center text-xs text-emerald-600">
            (Tu peux brancher un vrai graph ici si tu veux, en réutilisant les
            courbes de EnergyPage.)
          </div>
        </div>

        <div className="rounded-2xl border border-amber-100 bg-white/90 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-500">
                Alertes / points de vigilance
              </p>
            </div>
            <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700">
              {alerts.length} éléments
            </span>
          </div>
          <div className="space-y-2">
            {alerts.map((a, i) => (
              <div
                key={i}
                className="flex items-start gap-2 rounded-xl border border-amber-50 bg-amber-50/70 px-3 py-2.5"
              >
                <div className="mt-0.5">
                  <Activity className="h-4 w-4 text-amber-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-semibold text-amber-900">
                    {a.type} · {a.label}
                  </p>
                  <p className="mt-1 text-[11px] text-amber-800">{a.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// quick action buttons kept same as before if you want to re-add them later
// (tu peux les remettre en bas si besoin)

export default Overview;
