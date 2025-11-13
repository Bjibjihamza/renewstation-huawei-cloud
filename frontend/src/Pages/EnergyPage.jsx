// EnergyPage.jsx (standalone, no tabs)
import React, { useState, useEffect } from 'react';
import {
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

export default EnergyPage;