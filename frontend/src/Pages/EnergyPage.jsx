// EnergyPage.jsx - Complete redesigned version
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
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800 text-lg font-semibold">Chargement des données de consommation...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 p-8">
      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-emerald-900">Consommation Énergétique</h1>
            <p className="text-emerald-600 mt-2 text-lg">Surveillance en temps réel de 17 bâtiments</p>
          </div>
          <div className="flex gap-3">
            <div className="relative">
              <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-emerald-500" />
              <input
                type="text"
                placeholder="Rechercher un bâtiment..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-3 rounded-xl bg-white border-2 border-emerald-100 focus:outline-none focus:border-emerald-400 transition-all w-64"
              />
            </div>
            <button
              onClick={() => setViewMode(viewMode === 'cards' ? 'table' : 'cards')}
              className="px-6 py-3 bg-white rounded-xl text-emerald-700 font-medium hover:shadow-lg transition-all border-2 border-emerald-100"
            >
              {viewMode === 'cards' ? 'Vue Tableau' : 'Vue Cartes'}
            </button>
          </div>
        </div>

        {/* Global KPIs */}
        <div className="grid grid-cols-4 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-blue-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Zap className="w-7 h-7 text-blue-600" />
              </div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            </div>
            <p className="text-sm text-gray-600 mb-2 font-medium">Consommation Totale</p>
            <p className="text-3xl font-bold text-gray-900">{getTotalConsumption().toFixed(1)} <span className="text-xl text-gray-600">kWh</span></p>
            <p className="text-xs text-emerald-600 mt-2 font-medium">Aujourd'hui</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-red-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-7 h-7 text-red-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-2 font-medium">Demande de Pointe</p>
            <p className="text-3xl font-bold text-gray-900">{getPeakDemand().toFixed(1)} <span className="text-xl text-gray-600">kW</span></p>
            <p className="text-xs text-gray-500 mt-2">Maximum enregistré</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-emerald-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-7 h-7 text-emerald-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-2 font-medium">Moyenne</p>
            <p className="text-3xl font-bold text-gray-900">{getAverageConsumption().toFixed(1)} <span className="text-xl text-gray-600">kW</span></p>
            <p className="text-xs text-gray-500 mt-2">Par heure</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-teal-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center">
                <Building2 className="w-7 h-7 text-teal-600" />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-2 font-medium">Bâtiments</p>
            <p className="text-3xl font-bold text-gray-900">{buildings.length}</p>
            <p className="text-xs text-green-600 mt-2 font-medium">✓ Tous surveillés</p>
          </div>
        </div>

        {/* Building Filter */}
        <div className="bg-white rounded-2xl p-5 shadow-lg border-2 border-emerald-100">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2 text-emerald-700 font-medium">
              <Filter className="w-5 h-5" />
              <span>Filtrer:</span>
            </div>
            <button
              onClick={() => setSelectedBuilding('all')}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                selectedBuilding === 'all'
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
              }`}
            >
              Tous les bâtiments
            </button>
            {['Hospital', 'School', 'Industry1', 'Industry2', 'Office1', 'Office2', 'Office3'].map(building => (
              <button
                key={building}
                onClick={() => setSelectedBuilding(building)}
                className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  selectedBuilding === building
                    ? 'bg-emerald-600 text-white shadow-md'
                    : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
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
                  className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all cursor-pointer border-2 border-gray-100 hover:border-emerald-300"
                >
                  {/* Header Section */}
                  <div className="flex items-start justify-between mb-5">
                    <div className="flex items-center gap-3">
                      <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                        building.includes('House') ? 'bg-blue-100' :
                        building.includes('Industry') ? 'bg-purple-100' :
                        building.includes('Office') ? 'bg-emerald-100' :
                        building === 'Hospital' ? 'bg-red-100' : 'bg-orange-100'
                      }`}>
                        <Building2 className={`w-7 h-7 ${
                          building.includes('House') ? 'text-blue-600' :
                          building.includes('Industry') ? 'text-purple-600' :
                          building.includes('Office') ? 'text-emerald-600' :
                          building === 'Hospital' ? 'text-red-600' : 'text-orange-600'
                        }`} />
                      </div>
                      <div>
                        <h3 className="font-bold text-gray-900 text-lg">{building}</h3>
                        <p className="text-xs text-gray-500 font-medium mt-0.5">
                          {building.includes('House') ? 'Résidentiel' :
                           building.includes('Industry') ? 'Industriel' :
                           building.includes('Office') ? 'Bureau' :
                           building === 'Hospital' ? 'Santé' : 'Éducation'}
                        </p>
                      </div>
                    </div>
                    {data.trend !== 0 && (
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-sm font-semibold ${
                        data.trend > 0 ? 'text-red-600 bg-red-50' : 'text-green-600 bg-green-50'
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

                  {/* Main Metric */}
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 mb-2 font-medium">Consommation Actuelle</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {data.current.toFixed(2)} <span className="text-xl text-gray-600">kW</span>
                    </p>
                  </div>

                  {/* Divider */}
                  <div className="h-px bg-gray-200 mb-4"></div>

                  {/* Secondary Metrics */}
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Aujourd'hui</p>
                      <p className="font-bold text-gray-900">{data.today.toFixed(1)} <span className="text-xs text-gray-600">kWh</span></p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">En Total</p>
                      <p className="font-bold text-gray-900">+ ${(data.today * 0.15).toFixed(0)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Statut</p>
                      <span className={`inline-block px-2 py-1 rounded-md text-xs font-bold ${
                        isHigh ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {isHigh ? 'Élevé' : 'Normal'}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 font-medium">Efficacité</span>
                      <span className="font-bold text-gray-900">
                        {Math.min((data.current / getPeakDemand()) * 100, 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isHigh ? 'bg-gradient-to-r from-red-500 to-orange-500' : 'bg-gradient-to-r from-emerald-500 to-teal-500'
                        }`}
                        style={{ width: `${Math.min((data.current / getPeakDemand()) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Table View */
          <div className="bg-white rounded-2xl overflow-hidden shadow-lg border-2 border-gray-100">
            <table className="w-full">
              <thead className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-bold">Bâtiment</th>
                  <th className="px-6 py-4 text-left text-sm font-bold">Type</th>
                  <th className="px-6 py-4 text-right text-sm font-bold">Actuelle (kW)</th>
                  <th className="px-6 py-4 text-right text-sm font-bold">Aujourd'hui (kWh)</th>
                  <th className="px-6 py-4 text-right text-sm font-bold">Tendance</th>
                  <th className="px-6 py-4 text-center text-sm font-bold">Statut</th>
                </tr>
              </thead>
              <tbody>
                {displayBuildings.map((building, idx) => {
                  const data = getBuildingData(building);
                  const isHigh = data.current > getAverageConsumption();
                  
                  return (
                    <tr key={building} className={`border-b border-gray-100 hover:bg-emerald-50/50 transition-colors ${idx % 2 === 0 ? 'bg-gray-50/30' : 'bg-white'}`}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            building.includes('House') ? 'bg-blue-100' :
                            building.includes('Industry') ? 'bg-purple-100' :
                            building.includes('Office') ? 'bg-emerald-100' :
                            building === 'Hospital' ? 'bg-red-100' : 'bg-orange-100'
                          }`}>
                            <Building2 className={`w-5 h-5 ${
                              building.includes('House') ? 'text-blue-600' :
                              building.includes('Industry') ? 'text-purple-600' :
                              building.includes('Office') ? 'text-emerald-600' :
                              building === 'Hospital' ? 'text-red-600' : 'text-orange-600'
                            }`} />
                          </div>
                          <span className="font-bold text-gray-900">{building}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-700 text-sm font-medium">
                        {building.includes('House') ? 'Résidentiel' :
                         building.includes('Industry') ? 'Industriel' :
                         building.includes('Office') ? 'Bureau' :
                         building === 'Hospital' ? 'Santé' : 'Éducation'}
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-gray-900 text-lg">
                        {data.current.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-gray-900">
                        {data.today.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className={`flex items-center justify-end gap-1 px-2 py-1 rounded-lg inline-flex font-bold ${
                          data.trend > 0 ? 'text-red-600 bg-red-50' : 'text-green-600 bg-green-50'
                        }`}>
                          {data.trend > 0 ? (
                            <ArrowUpRight className="w-4 h-4" />
                          ) : (
                            <ArrowDownRight className="w-4 h-4" />
                          )}
                          <span>{Math.abs(data.trend).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`px-4 py-1.5 rounded-full text-xs font-bold ${
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
    </div>
  );
};

export default EnergyPage;