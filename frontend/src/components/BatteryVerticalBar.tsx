import { Battery } from 'lucide-react';

interface BatteryState {
  battery_type: string;
  battery_capacity_kwh: number;
  soc_start_pct: number;
  soc_end_pct: number;
  energy_stored_kwh: number;
  is_predicted: boolean;
}

interface BatteryVerticalBarProps {
  battery: BatteryState;
  label: string;
  isPrimary: boolean;
}

const BatteryVerticalBar = ({ battery, label, isPrimary }: BatteryVerticalBarProps) => {
  const colors = {
    primary: {
      bg: '#FC0D1B',
      light: '#FFF5F5',
      border: '#FC0D1B'
    },
    secondary: {
      bg: '#6B7280',
      light: '#F9FAFB',
      border: '#E5E7EB'
    }
  };

  const theme = isPrimary ? colors.primary : colors.secondary;
  const socChange = battery.soc_end_pct - battery.soc_start_pct;
  const isCharging = socChange > 0;
  const isDischarging = socChange < 0;

  return (
    <div className="flex flex-col items-center">
      <div className="mb-3 text-center">
        <div className="flex items-center justify-center gap-2 mb-1">
          <Battery
            className="w-5 h-5"
            style={{ color: theme.bg }}
          />
          <h4 className="font-semibold text-sm text-gray-700">{label}</h4>
        </div>
        <p className="text-xs text-gray-500">{battery.battery_capacity_kwh} kWh</p>
      </div>

      <div
        className="relative w-24 h-64 rounded-2xl border-4 flex flex-col justify-end overflow-hidden"
        style={{
          borderColor: theme.border,
          backgroundColor: '#F3F4F6'
        }}
      >
        <div
          className="w-full transition-all duration-700 ease-out relative"
          style={{
            height: `${battery.soc_end_pct}%`,
            backgroundColor: theme.bg,
            boxShadow: `0 -4px 12px ${theme.bg}40`
          }}
        >
          <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white to-transparent opacity-20"></div>
        </div>

        <div
          className="absolute top-0 left-0 right-0 flex flex-col items-center justify-center"
          style={{ height: '100%' }}
        >
          <div className="text-center">
            <p
              className="text-2xl font-bold mb-1"
              style={{
                color: battery.soc_end_pct > 50 ? 'white' : theme.bg,
                textShadow: battery.soc_end_pct > 50 ? '0 1px 3px rgba(0,0,0,0.3)' : 'none'
              }}
            >
              {battery.soc_end_pct.toFixed(1)}%
            </p>

            {socChange !== 0 && (
              <div className="flex items-center justify-center gap-1">
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    isCharging
                      ? 'bg-green-100 text-green-700'
                      : 'bg-orange-100 text-orange-700'
                  }`}
                >
                  {isCharging ? '↑' : '↓'} {Math.abs(socChange).toFixed(1)}%
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="absolute top-0 left-0 right-0 h-px bg-gray-300" style={{ top: '0%' }}></div>
        <div className="absolute left-0 right-0 h-px bg-gray-300" style={{ top: '25%' }}></div>
        <div className="absolute left-0 right-0 h-px bg-gray-300" style={{ top: '50%' }}></div>
        <div className="absolute left-0 right-0 h-px bg-gray-300" style={{ top: '75%' }}></div>
      </div>

      <div className="mt-3 text-center">
        <p className="text-xs text-gray-600 font-medium">
          {battery.energy_stored_kwh.toFixed(1)} kWh
        </p>
        <p className="text-xs text-gray-400">Stockés</p>
      </div>
    </div>
  );
};

export default BatteryVerticalBar;
