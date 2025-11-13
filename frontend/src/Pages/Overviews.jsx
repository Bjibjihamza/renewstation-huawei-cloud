import React, { useState, useEffect } from 'react';
import { MapPin, Zap, Battery, Building2, TrendingUp, Sun, AlertCircle, Calendar, ArrowUp, ArrowDown } from 'lucide-react';

// Huawei Color Palette
const colors = {
  huaweiRed: '#FC0D1B',
  huaweiBlack: '#000000',
  huaweiWhite: '#FFFFFF',
  huaweiGray: '#F5F5F5'
};

const Overview = () => {
  const [currentData, setCurrentData] = useState(null);
  const [batteryStates, setBatteryStates] = useState({ 
    real: { main: null, backup: null },
    predicted: { main: [], backup: [] }
  });
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Mock data structure matching your PostgreSQL schema
  const mockCurrentData = {
    location: { city: "Casablanca", lat: 33.5731, lon: -7.5898 },
    solar: { 
      capacity: 750, 
      panels: 1364, 
      panelPower: 550,
      currentProduction: 342.5
    },
    weather: {
      temperature_c: 22,
      humidity_pct: 65,
      cloud_cover_pct: 30,
      solar_radiation_w_m2: 650
    },
    timestamp: new Date().toISOString()
  };

  // Mock REAL battery states (current, is_predicted = false)
  const mockRealBatteryStates = {
    main: {
      id: `${new Date().toISOString().slice(0,13).replace(/[-:T]/g, '')}_main`,
      battery_type: 'main',
      battery_capacity_kwh: 2500,
      soc_start_pct: 85.0,
      soc_end_pct: 87.3,
      energy_stored_kwh: 2182.5,
      battery_charge_kwh: 45.2,
      battery_discharge_kwh: 0,
      solar_production_kwh: 342.5,
      consumption_kwh: 297.3,
      net_energy_kwh: 45.2,
      grid_import_kwh: 0,
      grid_export_kwh: 0,
      is_predicted: false,
      timestamp: new Date().toISOString()
    },
    backup: {
      id: `${new Date().toISOString().slice(0,13).replace(/[-:T]/g, '')}_backup`,
      battery_type: 'backup',
      battery_capacity_kwh: 700,
      soc_start_pct: 100,
      soc_end_pct: 100,
      energy_stored_kwh: 700,
      battery_charge_kwh: 0,
      battery_discharge_kwh: 0,
      solar_production_kwh: 0,
      consumption_kwh: 0,
      net_energy_kwh: 0,
      grid_import_kwh: 0,
      grid_export_kwh: 0,
      is_predicted: false,
      timestamp: new Date().toISOString()
    }
  };

  // Mock PREDICTED battery states (next 24 hours, is_predicted = true)
  const mockPredictedBatteryStates = {
    main: Array.from({ length: 24 }, (_, i) => ({
      id: `${new Date(Date.now() + i * 3600000).toISOString().slice(0,13).replace(/[-:T]/g, '')}_main`,
      battery_type: 'main',
      battery_capacity_kwh: 2500,
      soc_end_pct: 87.3 - (i * 2) + Math.random() * 5,
      energy_stored_kwh: 2182.5 - (i * 50) + Math.random() * 100,
      solar_production_kwh: Math.max(0, 300 + Math.sin(i / 4) * 200),
      consumption_kwh: 280 + Math.random() * 40,
      net_energy_kwh: 20 - i * 2,
      battery_charge_kwh: Math.max(0, 30 - i * 2),
      battery_discharge_kwh: Math.max(0, i * 1.5 - 10),
      grid_import_kwh: i > 16 ? Math.random() * 10 : 0,
      grid_export_kwh: i < 8 ? Math.random() * 5 : 0,
      is_predicted: true,
      timestamp: new Date(Date.now() + i * 3600000).toISOString()
    })),
    backup: Array.from({ length: 24 }, (_, i) => ({
      id: `${new Date(Date.now() + i * 3600000).toISOString().slice(0,13).replace(/[-:T]/g, '')}_backup`,
      battery_type: 'backup',
      battery_capacity_kwh: 700,
      soc_end_pct: 100,
      energy_stored_kwh: 700,
      solar_production_kwh: 0,
      consumption_kwh: 0,
      net_energy_kwh: 0,
      battery_charge_kwh: 0,
      battery_discharge_kwh: 0,
      grid_import_kwh: 0,
      grid_export_kwh: 0,
      is_predicted: true,
      timestamp: new Date(Date.now() + i * 3600000).toISOString()
    }))
  };

  // Mock predicted energy consumption
  const mockPredictions = Array.from({ length: 168 }, (_, i) => ({
    id: `2025${String(new Date().getMonth() + 1).padStart(2, '0')}${String(new Date().getDate()).padStart(2, '0')}${String(i).padStart(2, '0')}_Hospital`,
    time_ts: new Date(Date.now() + i * 3600000).toISOString(),
    building: 'Total',
    predicted_use_kw: 28 + Math.sin(i / 6) * 12 + Math.random() * 4,
    predicted_use_kw_min: 25,
    predicted_use_kw_max: 31,
    outdoor_temp_c: 18 + Math.sin(i / 12) * 8,
    solar_radiation_w_m2: Math.max(0, 500 + Math.sin(i / 6) * 400)
  }));

  useEffect(() => {
    setTimeout(() => {
      setCurrentData(mockCurrentData);
      setBatteryStates({
        real: mockRealBatteryStates,
        predicted: mockPredictedBatteryStates
      });
      setPredictions(mockPredictions);
      setLoading(false);
    }, 500);
  }, []);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-gray-200 border-t-red-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading RenewStation data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">RenewStation Overview</h1>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            {new Date().toLocaleString('fr-FR', { 
              dateStyle: 'full', 
              timeStyle: 'short' 
            })}
          </span>
          <span className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            {currentData.location.city}
          </span>
        </div>
      </div>



      {/* Battery State - Main Battery Only */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        
        {/* REAL Battery State */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg" style={{ backgroundColor: '#FFF5F5' }}>
                <Battery className="w-5 h-5" style={{ color: colors.huaweiRed }} />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Batterie Principale</h3>
                <p className="text-xs text-gray-500">État Actuel (Temps Réel)</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold" style={{ color: colors.huaweiRed }}>
                {batteryStates.real.main.soc_end_pct.toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500">Last Peak: {batteryStates.real.main.soc_start_pct.toFixed(0)}%</p>
            </div>
          </div>

          {/* Vertical Bar Chart */}
          <div className="relative h-64 bg-gradient-to-b from-gray-100 to-gray-50 rounded-xl p-4 mb-4">
            <div className="absolute left-4 top-4 bottom-4 flex flex-col justify-between text-xs text-gray-400">
              <span>100%</span>
              <span>75%</span>
              <span>50%</span>
              <span>25%</span>
              <span>0%</span>
            </div>
            
            <div className="ml-12 h-full flex items-end gap-3">
              {/* Current State Bar */}
              <div className="flex-1 flex flex-col items-center gap-2">
                <div className="relative w-full h-full">
                  <div 
                    className="absolute bottom-0 w-full rounded-t-lg transition-all duration-500"
                    style={{ 
                      height: `${batteryStates.real.main.soc_end_pct}%`,
                      backgroundColor: colors.huaweiRed,
                      opacity: 0.9
                    }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-t-lg"></div>
                    {batteryStates.real.main.battery_charge_kwh > 0 && (
                      <div className="absolute top-2 left-1/2 transform -translate-x-1/2">
                        <Zap className="w-6 h-6 text-yellow-300 animate-pulse" />
                      </div>
                    )}
                  </div>
                  <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 text-white font-bold text-sm drop-shadow-lg">
                    {batteryStates.real.main.energy_stored_kwh.toFixed(0)} kWh
                  </div>
                </div>
                <span className="text-xs font-semibold text-gray-700">Actuel</span>
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Capacité</p>
              <p className="text-sm font-bold text-gray-800">{batteryStates.real.main.battery_capacity_kwh} kWh</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Charge</p>
              <p className="text-sm font-bold text-green-600">+{batteryStates.real.main.battery_charge_kwh.toFixed(1)} kWh</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Décharge</p>
              <p className="text-sm font-bold text-orange-600">-{batteryStates.real.main.battery_discharge_kwh.toFixed(1)} kWh</p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-600">Production</span>
              <span className="font-semibold text-gray-800">{batteryStates.real.main.solar_production_kwh.toFixed(1)} kWh</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-600">Consommation</span>
              <span className="font-semibold text-gray-800">{batteryStates.real.main.consumption_kwh.toFixed(1)} kWh</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-600">Import Réseau</span>
              <span className="font-semibold text-red-600">{batteryStates.real.main.grid_import_kwh.toFixed(2)} kWh</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-gray-600">Export Réseau</span>
              <span className="font-semibold text-purple-600">{batteryStates.real.main.grid_export_kwh.toFixed(2)} kWh</span>
            </div>
          </div>
        </Card>

        {/* PREDICTED Battery State */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Prédiction Batterie</h3>
                <p className="text-xs text-gray-500">Prochaines 24 heures</p>
              </div>
            </div>
            <button className="px-3 py-1 bg-gray-100 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-200">
              This Week ▼
            </button>
          </div>

          {/* Vertical Bar Chart - Predictions */}
          <div className="relative h-64 bg-gradient-to-b from-blue-50 to-blue-25 rounded-xl p-4 mb-4">
            <div className="absolute left-4 top-4 bottom-4 flex flex-col justify-between text-xs text-gray-400">
              <span>100%</span>
              <span>75%</span>
              <span>50%</span>
              <span>25%</span>
              <span>0%</span>
            </div>
            
            <div className="ml-12 h-full flex items-end gap-1">
              {batteryStates.predicted.main.slice(0, 7).map((battery, i) => {
                const hour = new Date(battery.timestamp).getHours();
                const isHighlight = i === 3; // Highlight middle bar (like Thu in example)
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2">
                    <div className="relative w-full h-full">
                      <div 
                        className={`absolute bottom-0 w-full rounded-t-lg transition-all duration-300 hover:opacity-100 ${isHighlight ? 'opacity-100' : 'opacity-70'}`}
                        style={{ 
                          height: `${battery.soc_end_pct}%`,
                          backgroundColor: isHighlight ? colors.huaweiRed : '#9CA3AF'
                        }}
                        title={`${hour}h: ${battery.soc_end_pct.toFixed(1)}%`}
                      >
                        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent rounded-t-lg"></div>
                        {isHighlight && battery.battery_charge_kwh > 0 && (
                          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                            <Zap className="w-5 h-5 text-yellow-300" />
                          </div>
                        )}
                        {isHighlight && (
                          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-bold whitespace-nowrap">
                            <div className="bg-white px-2 py-1 rounded shadow-lg text-gray-800">
                              {battery.soc_end_pct.toFixed(0)}%
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    <span className={`text-xs ${isHighlight ? 'font-bold text-gray-800' : 'text-gray-500'}`}>
                      {hour}h
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Prediction Stats */}
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-semibold text-gray-800">Optimisation IA Activée</span>
              <div className="ml-auto">
                <div className="w-10 h-5 bg-blue-600 rounded-full relative">
                  <div className="absolute right-0.5 top-0.5 w-4 h-4 bg-white rounded-full"></div>
                </div>
              </div>
            </div>
            <p className="text-xs text-gray-600">Utilisation optimisée de l'énergie avec IA</p>
          </div>

          {/* Average Stats */}
          <div className="grid grid-cols-3 gap-3">
            {(() => {
              const avgSoc = batteryStates.predicted.main.slice(0, 7).reduce((sum, p) => sum + p.soc_end_pct, 0) / 7;
              const avgCharge = batteryStates.predicted.main.slice(0, 7).reduce((sum, p) => sum + p.battery_charge_kwh, 0) / 7;
              const avgDischarge = batteryStates.predicted.main.slice(0, 7).reduce((sum, p) => sum + p.battery_discharge_kwh, 0) / 7;
              
              return (
                <>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 mb-1">SOC Moy.</p>
                    <p className="text-sm font-bold text-gray-800">{avgSoc.toFixed(1)}%</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 mb-1">Charge Moy.</p>
                    <p className="text-sm font-bold text-green-600">{avgCharge.toFixed(1)} kWh</p>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 mb-1">Décharge Moy.</p>
                    <p className="text-sm font-bold text-orange-600">{avgDischarge.toFixed(1)} kWh</p>
                  </div>
                </>
              );
            })()}
          </div>
        </Card>
      </div>



    </div>
  );
};

// Components
const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>{children}</div>
);

const CardHeader = ({ icon: Icon, title }) => (
  <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
    <div className="p-2 rounded-lg" style={{ backgroundColor: '#FFF5F5' }}>
      <Icon className="w-5 h-5" style={{ color: colors.huaweiRed }} />
    </div>
    <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
  </div>
);

const WeatherMetric = ({ label, value }) => (
  <div className="flex justify-between items-center">
    <span className="text-sm text-gray-600">{label}</span>
    <span className="font-semibold text-gray-800">{value}</span>
  </div>
);

const BatteryVerticalBar = ({ battery, label, isPrimary }) => (
  <div className="flex flex-col items-center gap-3 w-32">
    <div className="relative w-20 h-64 bg-gray-200 rounded-lg overflow-hidden border-2" 
         style={{ borderColor: isPrimary ? colors.huaweiRed : '#9CA3AF' }}>
      <div className="absolute bottom-0 w-full transition-all duration-500 rounded-t-lg"
           style={{ 
             height: `${battery.soc_end_pct}%`,
             backgroundColor: isPrimary ? colors.huaweiRed : '#6B7280'
           }}>
        <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white to-transparent opacity-20"></div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-white drop-shadow-lg">
          {battery.soc_end_pct.toFixed(0)}%
        </span>
      </div>
    </div>
    <div className="text-center">
      <p className="text-sm font-bold text-gray-800">{label}</p>
      <p className="text-xs text-gray-500">{battery.energy_stored_kwh.toFixed(0)} kWh</p>
    </div>
  </div>
);

const BatteryDetailsCard = ({ battery, title }) => (
  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
    <h5 className="font-bold text-gray-800 text-center mb-3">{title}</h5>
    <DetailRow label="Capacité" value={`${battery.battery_capacity_kwh} kWh`} />
    <DetailRow label="SOC Début" value={`${battery.soc_start_pct.toFixed(1)}%`} />
    <DetailRow label="SOC Fin" value={`${battery.soc_end_pct.toFixed(1)}%`} highlight />
    <DetailRow label="Énergie Stockée" value={`${battery.energy_stored_kwh.toFixed(1)} kWh`} />
    <DetailRow label="Charge" value={`${battery.battery_charge_kwh.toFixed(2)} kWh`} color="green" />
    <DetailRow label="Décharge" value={`${battery.battery_discharge_kwh.toFixed(2)} kWh`} color="orange" />
    <DetailRow label="Production" value={`${battery.solar_production_kwh.toFixed(1)} kWh`} />
    <DetailRow label="Consommation" value={`${battery.consumption_kwh.toFixed(1)} kWh`} />
    <DetailRow label="Net" value={`${battery.net_energy_kwh > 0 ? '+' : ''}${battery.net_energy_kwh.toFixed(1)} kWh`} 
               color={battery.net_energy_kwh > 0 ? 'green' : 'red'} />
  </div>
);

const PredictedDetailsCard = ({ predictions, title, batteryType }) => {
  const avgSoc = predictions.reduce((sum, p) => sum + p.soc_end_pct, 0) / predictions.length;
  const avgCharge = predictions.reduce((sum, p) => sum + p.battery_charge_kwh, 0) / predictions.length;
  const avgDischarge = predictions.reduce((sum, p) => sum + p.battery_discharge_kwh, 0) / predictions.length;
  const avgProduction = predictions.reduce((sum, p) => sum + p.solar_production_kwh, 0) / predictions.length;
  const avgConsumption = predictions.reduce((sum, p) => sum + p.consumption_kwh, 0) / predictions.length;
  
  return (
    <div className="bg-blue-50 rounded-lg p-4 space-y-2">
      <h5 className="font-bold text-gray-800 text-center mb-3">{title}</h5>
      <DetailRow label="SOC Moyen" value={`${avgSoc.toFixed(1)}%`} highlight />
      <DetailRow label="Charge Moy." value={`${avgCharge.toFixed(2)} kWh`} color="green" />
      <DetailRow label="Décharge Moy." value={`${avgDischarge.toFixed(2)} kWh`} color="orange" />
      <DetailRow label="Production Moy." value={`${avgProduction.toFixed(1)} kWh`} />
      <DetailRow label="Consommation Moy." value={`${avgConsumption.toFixed(1)} kWh`} />
    </div>
  );
};

const DetailRow = ({ label, value, highlight, color }) => {
  const colorMap = { green: 'text-green-600', orange: 'text-orange-600', red: 'text-red-600' };
  const textColor = color ? colorMap[color] : 'text-gray-800';
  
  return (
    <div className="flex justify-between items-center text-xs">
      <span className="text-gray-600">{label}</span>
      <span className={`font-semibold ${highlight ? 'text-base' : ''} ${textColor}`}>{value}</span>
    </div>
  );
};

const EnergyFlowCard = ({ label, value, unit, color, icon }) => {
  const colorMap = { yellow: '#FCD34D', blue: '#60A5FA', green: '#10B981', red: colors.huaweiRed, purple: '#A78BFA' };
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 text-center">
      <div className="text-3xl mb-2">{icon}</div>
      <p className="text-xs text-gray-500 mb-2">{label}</p>
      <p className="text-xl font-bold" style={{ color: colorMap[color] }}>{value.toFixed(1)}</p>
      <p className="text-xs text-gray-400">{unit}</p>
    </div>
  );
};

const MonthCard = ({ month, icon, production, bgColor }) => (
  <div className="rounded-lg p-4 text-center border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
       style={{ backgroundColor: bgColor }}>
    <div className="flex items-center justify-center gap-2 mb-3">
      <span className="text-sm font-semibold text-gray-800">{month}</span>
    </div>
    <div className="text-4xl mb-3">{icon}</div>
    <div className="text-sm font-bold" style={{ color: colors.huaweiRed }}>{production}</div>
  </div>
);

export default Overview;