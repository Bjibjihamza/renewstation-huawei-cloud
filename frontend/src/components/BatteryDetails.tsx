interface BatteryState {
  battery_type: string;
  battery_capacity_kwh: number;
  soc_end_pct: number;
  energy_stored_kwh: number;
  battery_charge_kwh: number;
  battery_discharge_kwh: number;
  solar_production_kwh: number;
  consumption_kwh: number;
  net_energy_kwh: number;
  grid_import_kwh: number;
  grid_export_kwh: number;
  is_predicted: boolean;
  timestamp: string;
}

interface BatteryDetailsProps {
  battery: BatteryState;
}

const BatteryDetails = ({ battery }: BatteryDetailsProps) => {
  return (
    <div className="mt-4 space-y-2">
      <div className="bg-white rounded-lg border border-gray-200 p-3">
        <h5 className="text-xs font-semibold text-gray-600 mb-2 uppercase">Flux Énergétiques</h5>

        <div className="space-y-1.5">
          <DetailRow
            label="☀️ Production"
            value={battery.solar_production_kwh}
            unit="kWh"
            color="text-yellow-600"
          />
          <DetailRow
            label="⚡ Consommation"
            value={battery.consumption_kwh}
            unit="kWh"
            color="text-blue-600"
          />
          <DetailRow
            label="🔋 Charge"
            value={battery.battery_charge_kwh}
            unit="kWh"
            color="text-green-600"
          />
          <DetailRow
            label="📤 Décharge"
            value={battery.battery_discharge_kwh}
            unit="kWh"
            color="text-orange-600"
          />
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-3">
        <h5 className="text-xs font-semibold text-gray-600 mb-2 uppercase">Réseau</h5>

        <div className="space-y-1.5">
          <DetailRow
            label="📥 Import"
            value={battery.grid_import_kwh}
            unit="kWh"
            color="text-red-600"
          />
          <DetailRow
            label="📤 Export"
            value={battery.grid_export_kwh}
            unit="kWh"
            color="text-purple-600"
          />
          <div className="pt-1.5 mt-1.5 border-t border-gray-200">
            <DetailRow
              label="∑ Net"
              value={battery.net_energy_kwh}
              unit="kWh"
              color={battery.net_energy_kwh >= 0 ? 'text-green-700 font-bold' : 'text-red-700 font-bold'}
            />
          </div>
        </div>
      </div>

      <div className="text-xs text-gray-400 text-center pt-1">
        {new Date(battery.timestamp).toLocaleTimeString('fr-FR')}
      </div>
    </div>
  );
};

const DetailRow = ({ label, value, unit, color }: { label: string; value: number; unit: string; color: string }) => (
  <div className="flex justify-between items-center text-xs">
    <span className="text-gray-600">{label}</span>
    <span className={`font-semibold ${color}`}>
      {value.toFixed(2)} {unit}
    </span>
  </div>
);

export default BatteryDetails;
