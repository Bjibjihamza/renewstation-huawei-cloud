import { Battery } from 'lucide-react';
import Card from './Card';
import CardHeader from './CardHeader';
import BatteryVerticalBar from './BatteryVerticalBar';
import BatteryDetails from './BatteryDetails';

interface BatteryState {
  battery_type: string;
  battery_capacity_kwh: number;
  soc_start_pct: number;
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

interface BatteryStateSectionProps {
  realBatteries: {
    main: BatteryState;
    backup: BatteryState;
  };
  predictedBatteries: {
    main: BatteryState;
    backup: BatteryState;
  };
}

const BatteryStateSection = ({ realBatteries, predictedBatteries }: BatteryStateSectionProps) => {
  return (
    <Card className="mb-6">
      <CardHeader icon={Battery} title="État des Batteries - Visualisation" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">État Actuel (Réel)</h3>
            <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-medium">
              TEMPS RÉEL
            </span>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <BatteryVerticalBar
                battery={realBatteries.main}
                label="Batterie Principale"
                isPrimary={true}
              />
              <BatteryDetails battery={realBatteries.main} />
            </div>

            <div>
              <BatteryVerticalBar
                battery={realBatteries.backup}
                label="Batterie de Secours"
                isPrimary={false}
              />
              <BatteryDetails battery={realBatteries.backup} />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">État Prédit (Prochaine Heure)</h3>
            <span className="text-xs bg-purple-100 text-purple-700 px-3 py-1 rounded-full font-medium">
              PRÉDICTION
            </span>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <BatteryVerticalBar
                battery={predictedBatteries.main}
                label="Batterie Principale"
                isPrimary={true}
              />
              <BatteryDetails battery={predictedBatteries.main} />
            </div>

            <div>
              <BatteryVerticalBar
                battery={predictedBatteries.backup}
                label="Batterie de Secours"
                isPrimary={false}
              />
              <BatteryDetails battery={predictedBatteries.backup} />
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default BatteryStateSection;
