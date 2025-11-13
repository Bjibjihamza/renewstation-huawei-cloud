// WeatherPage.jsx
import React, { useEffect, useState } from 'react';
import { CloudSun, ArrowLeft, ArrowRight, AlertCircle } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const WeatherPage = () => {
  const [rows, setRows] = useState([]);
  const [pageInfo, setPageInfo] = useState({ page: 1, totalPages: 1, count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const limit = 40;

  const fetchPage = async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(
        `${API_BASE_URL}/weather-forecast-hourly?page=${page}&limit=${limit}`
      );
      if (!res.ok) throw new Error('Erreur API');
      const json = await res.json();
      setRows(json.results || []);
      setPageInfo({
        page: json.page || page,
        totalPages: json.totalPages || 1,
        count: json.count || 0,
      });
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Erreur inconnue');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPage(1);
  }, []);

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-emerald-900 flex items-center gap-2">
              <CloudSun className="w-5 h-5 text-sky-500" />
              Météo – Prévisions Horaires
            </h2>
            <p className="text-sm text-emerald-700">
              Table <code>weather_forecast_hourly</code>
            </p>
          </div>
          <p className="text-xs text-emerald-600 bg-white/60 px-3 py-1 rounded-full">
            {pageInfo.count} points • page {pageInfo.page}/{pageInfo.totalPages}
          </p>
        </div>

        <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-sm p-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 mb-3">
              <AlertCircle className="w-4 h-4" /> {error}
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b border-emerald-100 text-emerald-500">
                  <th className="py-2 px-2 text-left">Horodatage</th>
                  <th className="py-2 px-2 text-right">Temp °C</th>
                  <th className="py-2 px-2 text-right">Humidité</th>
                  <th className="py-2 px-2 text-right">Nuages</th>
                  <th className="py-2 px-2 text-right">Rayonnement W/m²</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-emerald-500">
                      Chargement...
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-emerald-500">
                      Aucune donnée
                    </td>
                  </tr>
                ) : (
                  rows.map((row) => (
                    <tr
                      key={row.forecast_timestamp}
                      className="border-b border-emerald-50"
                    >
                      <td className="py-1.5 px-2 text-emerald-900">
                        {row.forecast_timestamp
                          ? new Date(
                              row.forecast_timestamp
                            ).toLocaleString('fr-FR', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-900">
                        {Number(row.temperature_c || 0).toFixed(1)}
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-800">
                        {Number(row.humidity_pct || 0).toFixed(0)}%
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-800">
                        {Number(row.cloud_cover_pct || 0).toFixed(0)}%
                      </td>
                      <td className="py-1.5 px-2 text-right text-emerald-800">
                        {Number(row.solar_radiation_w_m2 || 0).toFixed(0)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4 text-xs text-emerald-700">
            <span>
              Page {pageInfo.page} sur {pageInfo.totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={pageInfo.page <= 1}
                onClick={() => fetchPage(pageInfo.page - 1)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-full border border-emerald-200 text-emerald-700 hover:bg-emerald-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ArrowLeft className="w-3 h-3" />
                Précédent
              </button>
              <button
                disabled={pageInfo.page >= pageInfo.totalPages}
                onClick={() => fetchPage(pageInfo.page + 1)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-full border border-emerald-200 text-emerald-700 hover:bg-emerald-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Suivant
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherPage;
