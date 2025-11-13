// Overview.jsx
import React, { useEffect, useState } from 'react';
import {
  Activity,
  Zap,
  Battery,
  CloudSun,
  Server,
  AlertCircle,
  RefreshCw,
  BarChart3
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const Overview = () => {
  const [summary, setSummary] = useState(null);
  const [energySample, setEnergySample] = useState([]);
  const [batterySample, setBatterySample] = useState([]);
  const [weatherSample, setWeatherSample] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryRes, energyRes, batteryRes, weatherRes] = await Promise.all(
        [
          fetch(`${API_BASE_URL}/summary`),
          fetch(`${API_BASE_URL}/energy-consumption-hourly?limit=5`),
          fetch(`${API_BASE_URL}/battery-state?limit=5`),
          fetch(`${API_BASE_URL}/weather-forecast-hourly?limit=5`),
        ]
      );

      if (
        !summaryRes.ok ||
        !energyRes.ok ||
        !batteryRes.ok ||
        !weatherRes.ok
      ) {
        throw new Error('Erreur lors du chargement des données');
      }

      const summaryJson = await summaryRes.json();
      const energyJson = await energyRes.json();
      const batteryJson = await batteryRes.json();
      const weatherJson = await weatherRes.json();

      setSummary(summaryJson);
      setEnergySample(energyJson.results || []);
      setBatterySample(batteryJson.results || []);
      setWeatherSample(weatherJson.results || []);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Erreur inconnue');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading && !summary) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800 font-medium">Chargement...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white/70 backdrop-blur-lg rounded-3xl p-8 max-w-md shadow-lg text-center">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p className="font-semibold text-red-700 mb-2">
            Impossible de charger le tableau de bord
          </p>
          <p className="text-sm text-red-500 mb-4">{error}</p>
          <button
            onClick={fetchOverview}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700"
          >
            <RefreshCw className="w-4 h-4" />
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  const tables = summary?.tables || {};
  const lastUpdated = summary?.timestamp
    ? new Date(summary.timestamp)
    : null;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-emerald-900">
              Vue d’ensemble du Campus
            </h2>
            <p className="text-sm text-emerald-700 mt-1">
              Résumé des données énergie, solaire, météo et batteries
            </p>
          </div>
          {lastUpdated && (
            <p className="text-xs text-emerald-600 bg-white/70 px-3 py-1 rounded-full">
              Dernière mise à jour :{' '}
              {lastUpdated.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          )}
        </div>

        {/* KPI cards */}
        <div className="grid grid-cols-4 gap-5">
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-600" />
                <span className="text-sm font-semibold text-emerald-900">
                  Enregistrements énergie
                </span>
              </div>
            </div>
            <p className="text-3xl font-bold text-emerald-900">
              {tables.energy_consumption_hourly ?? '—'}
            </p>
            <p className="text-xs text-emerald-600">
              Données horaires de consommation (silver)
            </p>
          </div>

          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span className="text-sm font-semibold text-emerald-900">
                  Prédictions solaires
                </span>
              </div>
            </div>
            <p className="text-3xl font-bold text-emerald-900">
              {tables.predicted_solar_production ?? '—'}
            </p>
            <p className="text-xs text-emerald-600">
              7 jours de production solaire prévue
            </p>
          </div>

          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Battery className="w-5 h-5 text-green-600" />
                <span className="text-sm font-semibold text-emerald-900">
                  États de batteries
                </span>
              </div>
            </div>
            <p className="text-3xl font-bold text-emerald-900">
              {tables.battery_state ?? '—'}
            </p>
            <p className="text-xs text-emerald-600">
              Historique + prédictions « main & backup »
            </p>
          </div>

          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CloudSun className="w-5 h-5 text-sky-500" />
                <span className="text-sm font-semibold text-emerald-900">
                  Données météo
                </span>
              </div>
            </div>
            <p className="text-3xl font-bold text-emerald-900">
              {tables.weather_forecast_hourly ?? '—'}
            </p>
            <p className="text-xs text-emerald-600">
              Prévisions horaires utilisées par les modèles
            </p>
          </div>
        </div>

        {/* Data preview panels */}
        <div className="grid grid-cols-3 gap-6 mt-4">
          {/* Energy table */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-semibold text-emerald-900">
                  Dernières consommations (kW)
                </span>
              </div>
              <Server className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="text-emerald-500 border-b border-emerald-100">
                    <th className="py-2 pr-2 text-left">Heure</th>
                    <th className="py-2 px-2 text-right">Bâtiment</th>
                    <th className="py-2 px-2 text-right">Use kW</th>
                  </tr>
                </thead>
                <tbody>
                  {energySample.map((row) => (
                    <tr key={row.id} className="border-b border-emerald-50">
                      <td className="py-1.5 pr-2 text-emerald-900">
                        {row.time_ts
                          ? new Date(row.time_ts).toLocaleString('fr-FR', {
                              hour: '2-digit',
                              minute: '2-digit',
                              day: '2-digit',
                              month: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-700">
                        {row.building}
                      </td>
                      <td className="py-1.5 px-2 text-right font-semibold text-emerald-900">
                        {Number(row.use_kw || 0).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                  {energySample.length === 0 && (
                    <tr>
                      <td
                        colSpan={3}
                        className="py-3 text-center text-emerald-500"
                      >
                        Aucune donnée
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Battery table */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Battery className="w-4 h-4 text-emerald-600" />
                <span className="text-sm font-semibold text-emerald-900">
                  Derniers états de batterie
                </span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="text-emerald-500 border-b border-emerald-100">
                    <th className="py-2 pr-2 text-left">Heure</th>
                    <th className="py-2 px-2 text-right">Type</th>
                    <th className="py-2 px-2 text-right">SOC %</th>
                    <th className="py-2 pl-2 text-right">Énergie kWh</th>
                  </tr>
                </thead>
                <tbody>
                  {batterySample.map((row) => (
                    <tr key={`${row.timestamp}-${row.battery_type}`}>
                      <td className="py-1.5 pr-2 text-emerald-900">
                        {row.timestamp
                          ? new Date(row.timestamp).toLocaleString('fr-FR', {
                              hour: '2-digit',
                              minute: '2-digit',
                              day: '2-digit',
                              month: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-700">
                        {row.battery_type}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-900">
                        {Number(row.soc_end_pct || row.soc_start_pct || 0).toFixed(1)}
                      </td>
                      <td className="py-1.5 pl-2 text-right font-semibold text-emerald-900">
                        {Number(row.energy_stored_kwh || 0).toFixed(1)}
                      </td>
                    </tr>
                  ))}
                  {batterySample.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="py-3 text-center text-emerald-500"
                      >
                        Aucune donnée
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Weather table */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <CloudSun className="w-4 h-4 text-sky-500" />
                <span className="text-sm font-semibold text-emerald-900">
                  Prochaines heures météo
                </span>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="text-emerald-500 border-b border-emerald-100">
                    <th className="py-2 pr-2 text-left">Heure</th>
                    <th className="py-2 px-2 text-right">Temp °C</th>
                    <th className="py-2 px-2 text-right">Humidité</th>
                    <th className="py-2 pl-2 text-right">Nuages</th>
                  </tr>
                </thead>
                <tbody>
                  {weatherSample.map((row) => (
                    <tr key={row.forecast_timestamp}>
                      <td className="py-1.5 pr-2 text-emerald-900">
                        {row.forecast_timestamp
                          ? new Date(
                              row.forecast_timestamp
                            ).toLocaleString('fr-FR', {
                              hour: '2-digit',
                              day: '2-digit',
                              month: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-900">
                        {Number(row.temperature_c || 0).toFixed(1)}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-700">
                        {Number(row.humidity_pct || 0).toFixed(0)}%
                      </td>
                      <td className="py-1.5 pl-2 text-right text-emerald-700">
                        {Number(row.cloud_cover_pct || 0).toFixed(0)}%
                      </td>
                    </tr>
                  ))}
                  {weatherSample.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="py-3 text-center text-emerald-500"
                      >
                        Aucune donnée
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
