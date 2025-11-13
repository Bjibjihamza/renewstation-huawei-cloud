import { useState, useEffect } from 'react';
import { MapPin, Calendar, Zap } from 'lucide-react';
import BatteryStateSection from './BatteryStateSection';
import Card from './Card';
import CardHeader from './CardHeader';
import WeatherMetric from './WeatherMetric';

const colors = {
  huaweiRed: '#FC0D1B',
};

const Overview = () => {
  const [currentData, setCurrentData] = useState<any>(null);
  const [batteryStates, setBatteryStates] = useState<any>({ main: null, backup: null });
  const [predictedBatteryStates, setPredictedBatteryStates] = useState<any>({ main: null, backup: null });
  const [loading, setLoading] = useState(true);

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

  const mockBatteryStates = {
    main: {
      battery_type: 'main',
      battery_capacity_kwh: 2500,
      soc_start_pct: 82.0,
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

  const mockPredictedBatteryStates = {
    main: {
      battery_type: 'main',
      battery_capacity_kwh: 2500,
      soc_start_pct: 87.3,
      soc_end_pct: 92.8,
      energy_stored_kwh: 2320.0,
      battery_charge_kwh: 137.5,
      battery_discharge_kwh: 0,
      solar_production_kwh: 380.2,
      consumption_kwh: 242.7,
      net_energy_kwh: 137.5,
      grid_import_kwh: 0,
      grid_export_kwh: 0,
      is_predicted: true,
      timestamp: new Date(Date.now() + 3600000).toISOString()
    },
    backup: {
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
      is_predicted: true,
      timestamp: new Date(Date.now() + 3600000).toISOString()
    }
  };

  useEffect(() => {
    setTimeout(() => {
      setCurrentData(mockCurrentData);
      setBatteryStates(mockBatteryStates);
      setPredictedBatteryStates(mockPredictedBatteryStates);
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader icon={MapPin} title="Localisation & Météo" />
          <div className="mt-4">
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-2xl font-bold text-gray-800">{currentData.location.city}</p>
                <p className="text-sm text-gray-500 mt-1">Maroc</p>
                <div className="mt-3 space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Latitude:</span>
                    <span className="font-semibold text-gray-700">{currentData.location.lat}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Longitude:</span>
                    <span className="font-semibold text-gray-700">{currentData.location.lon}</span>
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <WeatherMetric
                  label="Température"
                  value={`${currentData.weather.temperature_c}°C`}
                />
                <WeatherMetric
                  label="Humidité"
                  value={`${currentData.weather.humidity_pct}%`}
                />
                <WeatherMetric
                  label="Couverture Nuageuse"
                  value={`${currentData.weather.cloud_cover_pct}%`}
                />
                <WeatherMetric
                  label="Radiation Solaire"
                  value={`${currentData.weather.solar_radiation_w_m2} W/m²`}
                />
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader icon={Zap} title="Installation Solaire" />
          <div className="mt-4 space-y-4">
            <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
              <span className="text-gray-600">Capacité Totale</span>
              <span className="text-3xl font-bold" style={{ color: colors.huaweiRed }}>
                {currentData.solar.capacity} kWc
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Panneaux Solaires</span>
                <span className="text-lg font-semibold text-gray-800">
                  {currentData.solar.panels}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Puissance/Panneau</span>
                <span className="text-lg font-semibold text-gray-800">
                  {currentData.solar.panelPower}W
                </span>
              </div>
            </div>
            <div className="p-4 border-2 rounded-lg" style={{ borderColor: colors.huaweiRed, backgroundColor: '#FFF5F5' }}>
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-medium">Production Actuelle</span>
                <span className="text-2xl font-bold" style={{ color: colors.huaweiRed }}>
                  {currentData.solar.currentProduction} kW
                </span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <BatteryStateSection
        realBatteries={batteryStates}
        predictedBatteries={predictedBatteryStates}
      />
    </div>
  );
};

export default Overview;
