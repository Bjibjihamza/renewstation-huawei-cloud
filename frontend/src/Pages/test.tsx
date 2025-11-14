import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, CheckCircle, Database, Calendar } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000/api/solar';

const SolarDebugTool = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

  const endpoints = [
    { key: 'solarArchive', url: `${API_BASE_URL}/solar-production-archive?limit=24`, label: 'Solar Archive (Historical)' },
    { key: 'predictedSolar', url: `${API_BASE_URL}/predicted-solar-production?limit=24`, label: 'Predicted Solar' },
    { key: 'weatherForecast', url: `${API_BASE_URL}/weather-forecast-hourly?limit=24`, label: 'Weather Forecast' },
    { key: 'weatherArchive', url: `${API_BASE_URL}/weather-archive-hourly?limit=24`, label: 'Weather Archive' },
  ];

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    const newResults = {};

    for (const endpoint of endpoints) {
      try {
        console.log(`🔍 Fetching ${endpoint.label}:`, endpoint.url);
        const response = await fetch(endpoint.url);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const json = await response.json();
        const data = json.results || [];

        console.log(`✅ ${endpoint.label} - ${data.length} records:`, data.slice(0, 3));

        newResults[endpoint.key] = {
          count: data.length,
          data: data,
          sample: data.slice(0, 3),
          status: 'success'
        };
      } catch (err) {
        console.error(`❌ Error fetching ${endpoint.label}:`, err);
        newResults[endpoint.key] = {
          count: 0,
          data: [],
          error: err.message,
          status: 'error'
        };
      }
    }

    setResults(newResults);
    setLoading(false);
    
    // Analyze data
    analyzeProductionData(newResults);
  };

  const analyzeProductionData = (data) => {
    console.log('\n📊 === SOLAR PRODUCTION ANALYSIS ===\n');

    // Solar Archive Analysis
    if (data.solarArchive?.data?.length > 0) {
      console.log('🏭 SOLAR ARCHIVE (Historical Real Production):');
      const archive = data.solarArchive.data;
      
      const totalAC = archive.reduce((sum, row) => sum + (parseFloat(row.ac_power_kw) || 0), 0);
      const totalDC = archive.reduce((sum, row) => sum + (parseFloat(row.dc_power_kw) || 0), 0);
      const totalRealProduction = archive.reduce((sum, row) => sum + (parseFloat(row.real_production_kwh) || 0), 0);
      
      console.log(`  - Total AC Power: ${totalAC.toFixed(2)} kW`);
      console.log(`  - Total DC Power: ${totalDC.toFixed(2)} kW`);
      console.log(`  - Total Real Production: ${totalRealProduction.toFixed(2)} kWh`);
      console.log(`  - Records: ${archive.length}`);
      console.log('  - Sample:', archive[0]);
      
      // Check timestamps
      const timestamps = archive.map(r => new Date(r.timestamp));
      const latest = new Date(Math.max(...timestamps));
      const oldest = new Date(Math.min(...timestamps));
      console.log(`  - Time Range: ${oldest.toLocaleString('fr-FR')} → ${latest.toLocaleString('fr-FR')}`);
    }

    // Predicted Solar Analysis
    if (data.predictedSolar?.data?.length > 0) {
      console.log('\n🔮 PREDICTED SOLAR PRODUCTION:');
      const predicted = data.predictedSolar.data;
      
      const totalPredicted = predicted.reduce((sum, row) => sum + (parseFloat(row.predicted_production_kwh) || 0), 0);
      const totalAC = predicted.reduce((sum, row) => sum + (parseFloat(row.ac_power_kw) || 0), 0);
      
      console.log(`  - Total Predicted Production: ${totalPredicted.toFixed(2)} kWh`);
      console.log(`  - Total AC Power: ${totalAC.toFixed(2)} kW`);
      console.log(`  - Records: ${predicted.length}`);
      console.log('  - Sample:', predicted[0]);
      
      const timestamps = predicted.map(r => new Date(r.timestamp));
      const latest = new Date(Math.max(...timestamps));
      const oldest = new Date(Math.min(...timestamps));
      console.log(`  - Time Range: ${oldest.toLocaleString('fr-FR')} → ${latest.toLocaleString('fr-FR')}`);
    }

    console.log('\n=================================\n');
  };

  const formatValue = (value, decimals = 2) => {
    if (value === null || value === undefined) return 'N/A';
    const num = parseFloat(value);
    return isNaN(num) ? 'N/A' : num.toFixed(decimals);
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
                <Database className="w-8 h-8 text-emerald-600" />
                Solar Production Debug Tool
              </h1>
              <p className="text-slate-600 mt-2">Inspectez les données de production solaire</p>
            </div>
            <button
              onClick={fetchAllData}
              disabled={loading}
              className="px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50 transition-all font-medium flex items-center gap-2"
            >
              <Search className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Chargement...' : 'Rafraîchir'}
            </button>
          </div>
        </div>

        {/* Results Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {endpoints.map((endpoint) => {
            const result = results[endpoint.key];
            if (!result) return null;

            return (
              <div key={endpoint.key} className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className={`p-4 ${result.status === 'success' ? 'bg-emerald-50' : 'bg-red-50'}`}>
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-slate-900 flex items-center gap-2">
                      {result.status === 'success' ? (
                        <CheckCircle className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-600" />
                      )}
                      {endpoint.label}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.status === 'success' 
                        ? 'bg-emerald-100 text-emerald-700' 
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {result.count} records
                    </span>
                  </div>
                </div>

                <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
                  {result.error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm">
                      <strong>Erreur:</strong> {result.error}
                    </div>
                  )}

                  {result.sample?.map((record, idx) => (
                    <div key={idx} className="bg-slate-50 rounded-lg p-3 text-xs font-mono">
                      <div className="font-bold text-slate-700 mb-2 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        {record.timestamp || record.forecast_timestamp ? 
                          new Date(record.timestamp || record.forecast_timestamp).toLocaleString('fr-FR') : 
                          'No timestamp'
                        }
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2">
                        {/* Solar Archive specific fields */}
                        {record.ac_power_kw !== undefined && (
                          <>
                            <div className="text-slate-600">AC Power:</div>
                            <div className="text-slate-900 font-semibold">{formatValue(record.ac_power_kw)} kW</div>
                          </>
                        )}
                        {record.dc_power_kw !== undefined && (
                          <>
                            <div className="text-slate-600">DC Power:</div>
                            <div className="text-slate-900 font-semibold">{formatValue(record.dc_power_kw)} kW</div>
                          </>
                        )}
                        {record.real_production_kwh !== undefined && (
                          <>
                            <div className="text-slate-600">Real Production:</div>
                            <div className="text-emerald-600 font-bold">{formatValue(record.real_production_kwh)} kWh</div>
                          </>
                        )}
                        {record.predicted_production_kwh !== undefined && (
                          <>
                            <div className="text-slate-600">Predicted Production:</div>
                            <div className="text-blue-600 font-bold">{formatValue(record.predicted_production_kwh)} kWh</div>
                          </>
                        )}
                        
                        {/* Weather fields */}
                        {record.temperature_c !== undefined && (
                          <>
                            <div className="text-slate-600">Temperature:</div>
                            <div className="text-slate-900">{formatValue(record.temperature_c)}°C</div>
                          </>
                        )}
                        {record.solar_radiation_w_m2 !== undefined && (
                          <>
                            <div className="text-slate-600">Solar Radiation:</div>
                            <div className="text-yellow-600 font-semibold">{formatValue(record.solar_radiation_w_m2, 0)} W/m²</div>
                          </>
                        )}
                        {record.cloud_cover_pct !== undefined && (
                          <>
                            <div className="text-slate-600">Cloud Cover:</div>
                            <div className="text-slate-900">{formatValue(record.cloud_cover_pct, 0)}%</div>
                          </>
                        )}
                      </div>
                    </div>
                  ))}

                  {result.count === 0 && !result.error && (
                    <div className="text-center text-slate-500 py-8">
                      Aucune donnée disponible
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Console Instructions */}
        <div className="mt-6 bg-slate-900 text-slate-100 rounded-2xl p-6">
          <h3 className="font-bold text-lg mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-400" />
            Instructions de Debug
          </h3>
          <ol className="space-y-2 text-sm list-decimal list-inside">
            <li>Ouvrez la Console Développeur (F12)</li>
            <li>Regardez les logs commençant par 🔍, ✅, et 📊</li>
            <li>Vérifiez les valeurs dans "SOLAR PRODUCTION ANALYSIS"</li>
            <li>Comparez <code className="bg-slate-800 px-2 py-1 rounded">real_production_kwh</code> vs <code className="bg-slate-800 px-2 py-1 rounded">predicted_production_kwh</code></li>
            <li>Vérifiez si les timestamps sont corrects (aujourd'hui vs futur)</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default SolarDebugTool;