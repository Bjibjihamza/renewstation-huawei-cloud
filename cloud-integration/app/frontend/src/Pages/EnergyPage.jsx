// EnergyPage.jsx - Redesigned buildings section
import React, { useState, useEffect, useMemo } from 'react';
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

const API_BASE_URL = '/api/solar';

const EnergyPage = () => {
  const [energyData, setEnergyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBuilding, setSelectedBuilding] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'

  const buildings = [
    'Hospital',
    'House1',
    'House2',
    'House3',
    'House4',
    'House5',
    'House6',
    'House7',
    'House8',
    'House9',
    'House10',
    'Industry1',
    'Industry2',
    'Office1',
    'Office2',
    'Office3',
    'School',
  ];

  const safeNumber = (val, fallback = 0) => {
    const n = parseFloat(val);
    return Number.isNaN(n) ? fallback : n;
  };

  const fetchEnergyData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/energy-consumption-hourly?limit=1000`
      );
      const json = await response.json();
      setEnergyData(json.results || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching energy data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnergyData();
    const interval = setInterval(fetchEnergyData, 60000);
    return () => clearInterval(interval);
  }, []);

  // --------- Métriques dérivées ---------
  const {
    buildingStats,
    totalTodayKwh,
    peakDemandKw,
    avgDemandKw,
    overallCurrentKw,
  } = useMemo(() => {
    if (!energyData.length) {
      return {
        buildingStats: {},
        totalTodayKwh: 0,
        peakDemandKw: 0,
        avgDemandKw: 0,
        overallCurrentKw: 0,
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
          name: bName,
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

      if (kw > stats.maxKw) {
        stats.maxKw = kw;
      }

      if (kw > globalPeak) globalPeak = kw;
      sumAllKw += kw;
      countAllKw += 1;
    });

    const buildingStats = {};
    Object.values(perBuilding).forEach((stats) => {
      const { todayKwh, yesterdayKwh } = stats;
      const trend =
        yesterdayKwh > 0
          ? ((todayKwh - yesterdayKwh) / yesterdayKwh) * 100
          : 0;

      buildingStats[stats.name] = {
        ...stats,
        trend,
      };
    });

    const overallCurrentKw = Object.values(buildingStats).reduce(
      (sum, s) => sum + s.currentKw,
      0
    );
    const totalTodayKwh = Object.values(buildingStats).reduce(
      (sum, s) => sum + s.todayKwh,
      0
    );
    const avgDemandKw = countAllKw ? sumAllKw / countAllKw : 0;

    return {
      buildingStats,
      totalTodayKwh,
      peakDemandKw: globalPeak,
      avgDemandKw,
      overallCurrentKw,
    };
  }, [energyData]);

  const getBuildingStats = (name) =>
    buildingStats[name] || {
      name,
      currentKw: 0,
      todayKwh: 0,
      yesterdayKwh: 0,
      trend: 0,
      maxKw: 0,
      latestTs: null,
    };

  const filteredBuildings = buildings.filter((b) =>
    b.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const displayBuildings =
    selectedBuilding === 'all' ? filteredBuildings : [selectedBuilding];

  const topConsumers = useMemo(() => {
    const allStats = Object.values(buildingStats);
    return allStats
      .slice()
      .sort((a, b) => b.todayKwh - a.todayKwh)
      .slice(0, 3);
  }, [buildingStats]);

  const mostEfficient = useMemo(() => {
    const allStats = Object.values(buildingStats).filter(
      (s) => peakDemandKw > 0
    );
    if (!allStats.length) return null;
    return allStats
      .slice()
      .sort(
        (a, b) =>
          (a.currentKw / Math.max(a.maxKw, 1)) -
          (b.currentKw / Math.max(b.maxKw, 1))
      )[0];
  }, [buildingStats, peakDemandKw]);

  // ---------- Loading ----------
  if (loading && !energyData.length) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-emerald-800 text-lg font-semibold">
            Chargement des données de consommation...
          </p>
        </div>
      </div>
    );
  }

  // ---------- UI ----------
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 p-8">
      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* HEADER */}
        <div className="flex items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="flex items-center gap-2 bg-white/70 rounded-full px-4 py-2 shadow-sm">
                <Zap className="w-5 h-5 text-emerald-600" />
                <span className="text-sm font-semibold text-emerald-800">
                  Vue Consommation
                </span>
              </div>
              <div className="hidden md:flex items-center gap-2 bg-white/60 rounded-full px-3 py-1 text-xs text-emerald-700 shadow-sm">
                <Activity className="w-3 h-3" />
                <span>Mis à jour en continu</span>
              </div>
            </div>
            <h1 className="text-4xl font-bold text-emerald-900">
              Consommation Énergétique
            </h1>
            <p className="text-emerald-700 mt-2 text-base">
              Surveillance temps réel de 17 bâtiments — consommation
              agrégée, tendances et efficacité instantanée.
            </p>
            <div className="mt-3 inline-flex items-center gap-2 text-xs text-emerald-700 bg-white/60 px-3 py-1 rounded-full shadow-sm">
              <Calendar className="w-3 h-3" />
              <span>
                {new Date().toLocaleDateString('fr-FR', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </span>
            </div>
          </div>

          <div className="flex flex-col items-end gap-3">
            <div className="flex gap-3 items-center">
              <div className="relative">
                <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-emerald-500" />
                <input
                  type="text"
                  placeholder="Rechercher un bâtiment..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-3 rounded-xl bg-white border-2 border-emerald-100 focus:outline-none focus:border-emerald-400 transition-all w-64 shadow-sm"
                />
              </div>
              <button
                onClick={fetchEnergyData}
                className="p-3 rounded-xl bg-white border-2 border-emerald-100 hover:border-emerald-400 hover:shadow-md text-emerald-700 transition-all"
                title="Rafraîchir les données"
              >
                <Activity className="w-5 h-5" />
              </button>
            </div>
            <div className="inline-flex items-center rounded-full bg-white/70 border-2 border-emerald-100 shadow-sm">
              <button
                onClick={() => setViewMode('cards')}
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all ${
                  viewMode === 'cards'
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-emerald-700'
                }`}
              >
                Vue Cartes
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all ${
                  viewMode === 'table'
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-emerald-700'
                }`}
              >
                Vue Tableau
              </button>
            </div>
          </div>
        </div>

        {/* KPI GLOBAUX */}
        <div className="grid grid-cols-4 gap-6">
          {/* Total today */}
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-blue-100 relative overflow-hidden">
            <div className="absolute -right-8 -top-8 w-24 h-24 bg-blue-50 rounded-full" />
            <div className="relative">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Zap className="w-7 h-7 text-blue-600" />
                </div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              </div>
              <p className="text-xs text-gray-600 mb-1 font-semibold uppercase tracking-wide">
                Consommation totale aujourd&apos;hui
              </p>
              <p className="text-3xl font-bold text-gray-900">
                {totalTodayKwh.toFixed(1)}{' '}
                <span className="text-xl text-gray-600">kWh</span>
              </p>
              <p className="text-xs text-emerald-600 mt-2 font-medium">
                Somme sur l&apos;ensemble des 17 bâtiments
              </p>
            </div>
          </div>

          {/* Instant total demand */}
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-red-100 relative overflow-hidden">
            <div className="absolute -left-10 -bottom-10 w-24 h-24 bg-red-50 rounded-full" />
            <div className="relative">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                  <TrendingUp className="w-7 h-7 text-red-600" />
                </div>
              </div>
              <p className="text-xs text-gray-600 mb-1 font-semibold uppercase tracking-wide">
                Demande instantanée
              </p>
              <p className="text-3xl font-bold text-gray-900">
                {overallCurrentKw.toFixed(1)}{' '}
                <span className="text-xl text-gray-600">kW</span>
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Somme des puissances actuelles de tous les bâtiments
              </p>
            </div>
          </div>

          {/* Peak / avg */}
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-emerald-100">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-7 h-7 text-emerald-600" />
              </div>
              <CloudSun className="w-7 h-7 text-emerald-400 opacity-80" />
            </div>
            <p className="text-xs text-gray-600 mb-1 font-semibold uppercase tracking-wide">
              Demande de pointe & moyenne
            </p>
            <p className="text-sm text-gray-600">
              Pointe&nbsp;:
              <span className="font-bold text-gray-900">
                {' '}
                {peakDemandKw.toFixed(1)} kW
              </span>
            </p>
            <p className="text-sm text-gray-600">
              Moyenne&nbsp;:
              <span className="font-bold text-gray-900">
                {' '}
                {avgDemandKw.toFixed(1)} kW
              </span>
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Calculées sur l&apos;échantillon en mémoire
            </p>
          </div>

          {/* Buildings */}
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-teal-100">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-teal-100 rounded-xl flex items-center justify-center">
                <Building2 className="w-7 h-7 text-teal-600" />
              </div>
              <Battery className="w-7 h-7 text-teal-500" />
            </div>
            <p className="text-xs text-gray-600 mb-1 font-semibold uppercase tracking-wide">
              Couverture
            </p>
            <p className="text-3xl font-bold text-gray-900">
              {buildings.length}
            </p>
            <p className="text-xs text-green-600 mt-1 font-semibold">
              ✓ Tous surveillés en continu
            </p>
            {mostEfficient && (
              <p className="text-xs text-gray-500 mt-3">
                Bâtiment le plus « stable » :
                <span className="font-semibold text-emerald-700">
                  {' '}
                  {mostEfficient.name}
                </span>
              </p>
            )}
          </div>
        </div>

        {/* FILTER + INSIGHTS */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8 bg-white rounded-2xl p-5 shadow-lg border border-emerald-100">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2 text-emerald-700 font-medium">
                <Filter className="w-5 h-5" />
                <span>Filtrer par type de bâtiment :</span>
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
              {[
                'Hospital',
                'School',
                'Industry1',
                'Industry2',
                'Office1',
                'Office2',
                'Office3',
              ].map((building) => (
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

          <div className="col-span-4 bg-white rounded-2xl p-5 shadow-lg border border-amber-100">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-amber-600" />
              <span className="text-sm font-semibold text-amber-900">
                Observations automatiques
              </span>
            </div>
            {topConsumers.length ? (
              <div className="space-y-2 text-sm">
                <p className="text-gray-700">
                  • Plus gros consommateur aujourd&apos;hui&nbsp;:
                  <span className="font-semibold text-gray-900">
                    {' '}
                    {topConsumers[0].name}
                  </span>{' '}
                  ({topConsumers[0].todayKwh.toFixed(1)} kWh).
                </p>
                {topConsumers[1] && (
                  <p className="text-gray-700">
                    • Top 3 bâtiments les plus énergivores :
                    <span className="font-semibold text-gray-900">
                      {' '}
                      {topConsumers
                        .map(
                          (b) =>
                            `${b.name} (${b.todayKwh.toFixed(1)} kWh)`
                        )
                        .join(', ')}
                    </span>
                    .
                  </p>
                )}
                {mostEfficient && (
                  <p className="text-gray-700">
                    • Bâtiment le plus « stable » :
                    <span className="font-semibold text-gray-900">
                      {' '}
                      {mostEfficient.name}
                    </span>
                    .
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Pas encore assez de données pour calculer des observations.
              </p>
            )}
          </div>
        </div>

        {/* === SECTION BÂTIMENTS (NOUVEAU DESIGN) === */}
        {viewMode === 'cards' ? (
          <div className="grid grid-cols-3 gap-6">
            {displayBuildings.map((building) => {
              const stats = getBuildingStats(building);
              const isHigh = stats.currentKw > avgDemandKw;

              const efficiencyPercent =
                peakDemandKw > 0
                  ? Math.min((stats.currentKw / peakDemandKw) * 100, 100)
                  : 0;

              // pour le badge en haut à droite : % vs moyenne
              const relativeToAvg =
                avgDemandKw > 0
                  ? (stats.currentKw / avgDemandKw) * 100
                  : 0;

              const category = building.includes('House')
                ? 'Résidentiel'
                : building.includes('Industry')
                ? 'Industriel'
                : building.includes('Office')
                ? 'Bureau'
                : building === 'Hospital'
                ? 'Santé'
                : 'Éducation';

              const bgColor = building.includes('House')
                ? 'bg-blue-100'
                : building.includes('Industry')
                ? 'bg-purple-100'
                : building.includes('Office')
                ? 'bg-emerald-100'
                : building === 'Hospital'
                ? 'bg-red-100'
                : 'bg-orange-100';

              const iconColor = building.includes('House')
                ? 'text-blue-600'
                : building.includes('Industry')
                ? 'text-purple-600'
                : building.includes('Office')
                ? 'text-emerald-600'
                : building === 'Hospital'
                ? 'text-red-600'
                : 'text-orange-600';

              return (
                <div
                  key={building}
                  className="relative bg-white rounded-2xl p-6 shadow-[0_12px_30px_rgba(15,118,110,0.09)] border border-emerald-50 hover:border-emerald-300 hover:shadow-[0_16px_40px_rgba(16,185,129,0.20)] transition-all duration-300"
                >
                  {/* Badge en haut à droite */}
                  <div className="absolute right-5 top-5 flex items-center gap-1 bg-emerald-50 text-emerald-700 text-[11px] font-semibold px-3 py-1 rounded-full">
                    {relativeToAvg >= 100 ? (
                      <ArrowUpRight className="w-3 h-3" />
                    ) : (
                      <ArrowDownRight className="w-3 h-3" />
                    )}
                    <span>{relativeToAvg.toFixed(1)}%</span>
                  </div>

                  {/* Header */}
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center ${bgColor}`}
                    >
                      <Building2 className={`w-6 h-6 ${iconColor}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-lg">
                        {building}
                      </h3>
                      <p className="text-xs text-gray-500 font-medium mt-0.5">
                        {category}
                      </p>
                    </div>
                  </div>

                  {/* Consommation actuelle */}
                  <div className="mb-3">
                    <p className="text-[11px] text-gray-500 font-semibold tracking-wide">
                      CONSOMMATION ACTUELLE
                    </p>
                    <div className="flex items-baseline gap-1 mt-1">
                      <p className="text-3xl font-bold text-gray-900">
                        {stats.currentKw.toFixed(2)}
                      </p>
                      <span className="text-sm text-gray-500 font-medium">
                        kW
                      </span>
                    </div>
                    {stats.latestTs && (
                      <p className="text-[11px] text-gray-400 mt-1">
                        Dernière mesure :{' '}
                        {stats.latestTs.toLocaleTimeString('fr-FR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    )}
                  </div>

                  <div className="h-px bg-gray-100 my-3" />

                  {/* Ligne des 3 petites métriques */}
                  <div className="grid grid-cols-3 gap-3 text-xs mb-3">
                    <div>
                      <p className="text-gray-500 mb-1">Aujourd&apos;hui</p>
                      <p className="font-semibold text-gray-900">
                        {stats.todayKwh.toFixed(1)}{' '}
                        <span className="text-[11px] text-gray-500">
                          kWh
                        </span>
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500 mb-1">Coût estimé</p>
                      <p className="font-semibold text-gray-900">
                        ${ (stats.todayKwh * 0.15).toFixed(0)}
                      </p>
                    </div>
                    <div className="flex flex-col items-start">
                      <p className="text-gray-500 mb-1">Statut</p>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-[11px] font-bold ${
                          isHigh
                            ? 'bg-red-100 text-red-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {isHigh ? 'Élevé' : 'Normal'}
                      </span>
                    </div>
                  </div>

                  {/* Barre niveau par rapport à la pointe */}
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="text-gray-500 font-medium">
                        Niveau par rapport à la pointe
                      </span>
                      <span className="text-gray-900 font-semibold">
                        {efficiencyPercent.toFixed(0)}%
                      </span>
                    </div>
                    <div className="relative h-2.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="absolute left-1 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.25)]"
                        style={{
                          transform: `translateX(${Math.max(
                            0,
                            efficiencyPercent - 4
                          )}%) translateY(-50%)`,
                          transition: 'transform 0.4s ease',
                        }}
                      ></div>
                      <div
                        className={`h-full rounded-full transition-all ${
                          isHigh
                            ? 'bg-gradient-to-r from-red-400 to-orange-400'
                            : 'bg-gradient-to-r from-emerald-400 to-teal-400'
                        }`}
                        style={{
                          width: `${Math.max(efficiencyPercent, 4)}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* TABLE VIEW (inchangé) */
          <div className="bg-white rounded-2xl overflow-hidden shadow-lg border border-gray-100">
            <table className="w-full">
              <thead className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-bold">
                    Bâtiment
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-bold">
                    Type
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-bold">
                    Actuelle (kW)
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-bold">
                    Aujourd&apos;hui (kWh)
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-bold">
                    Tendance
                  </th>
                  <th className="px-6 py-4 text-center text-sm font-bold">
                    Statut
                  </th>
                </tr>
              </thead>
              <tbody>
                {displayBuildings.map((building, idx) => {
                  const stats = getBuildingStats(building);
                  const isHigh = stats.currentKw > avgDemandKw;
                  const category = building.includes('House')
                    ? 'Résidentiel'
                    : building.includes('Industry')
                    ? 'Industriel'
                    : building.includes('Office')
                    ? 'Bureau'
                    : building === 'Hospital'
                    ? 'Santé'
                    : 'Éducation';

                  const bgColor = building.includes('House')
                    ? 'bg-blue-100'
                    : building.includes('Industry')
                    ? 'bg-purple-100'
                    : building.includes('Office')
                    ? 'bg-emerald-100'
                    : building === 'Hospital'
                    ? 'bg-red-100'
                    : 'bg-orange-100';

                  const iconColor = building.includes('House')
                    ? 'text-blue-600'
                    : building.includes('Industry')
                    ? 'text-purple-600'
                    : building.includes('Office')
                    ? 'text-emerald-600'
                    : building === 'Hospital'
                    ? 'text-red-600'
                    : 'text-orange-600';

                  return (
                    <tr
                      key={building}
                      className={`border-b border-gray-100 hover:bg-emerald-50/50 transition-colors ${
                        idx % 2 === 0 ? 'bg-gray-50/30' : 'bg-white'
                      }`}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-10 h-10 rounded-lg flex items-center justify-center ${bgColor}`}
                          >
                            <Building2
                              className={`w-5 h-5 ${iconColor}`}
                            />
                          </div>
                          <span className="font-bold text-gray-900">
                            {building}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-700 text-sm font-medium">
                        {category}
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-gray-900 text-lg">
                        {stats.currentKw.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-gray-900">
                        {stats.todayKwh.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div
                          className={`flex items-center justify-end gap-1 px-2 py-1 rounded-lg inline-flex font-bold ${
                            stats.trend > 0
                              ? 'text-red-600 bg-red-50'
                              : 'text-green-600 bg-green-50'
                          }`}
                        >
                          {stats.trend > 0 ? (
                            <ArrowUpRight className="w-4 h-4" />
                          ) : (
                            <ArrowDownRight className="w-4 h-4" />
                          )}
                          <span>{Math.abs(stats.trend).toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span
                          className={`px-4 py-1.5 rounded-full text-xs font-bold ${
                            isHigh
                              ? 'bg-red-100 text-red-700'
                              : 'bg-green-100 text-green-700'
                          }`}
                        >
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
