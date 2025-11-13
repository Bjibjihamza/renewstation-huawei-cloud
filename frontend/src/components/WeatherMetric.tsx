interface WeatherMetricProps {
  label: string;
  value: string;
}

const WeatherMetric = ({ label, value }: WeatherMetricProps) => (
  <div className="flex justify-between items-center">
    <span className="text-sm text-gray-600">{label}</span>
    <span className="font-semibold text-gray-800">{value}</span>
  </div>
);

export default WeatherMetric;
