import React, { useState } from 'react';
import { Download, Calendar, TrendingUp, CloudSun, Database } from 'lucide-react';

const mockArchiveData = {
  weather: Array.from({ length: 720 }, (_, i) => ({
    time: new Date(Date.now() - (720 - i) * 3600000).toISOString(),
    temp: 20 + Math.sin(i / 24) * 6,
    solar: Math.max(0, 450 + Math.sin(i / 12) * 350),
    humidity: 55 + Math.random() * 20,
    wind: 8 + Math.random() * 10
  })),
  consumption: Array.from({ length: 720 }, (_, i) => ({
    time: new Date(Date.now() - (720 - i) * 3600000).toISOString(),
    total: 32 + Math.sin(i / 12) * 10,
    solar: Math.max(0, 20 + Math.sin(i / 12) * 18),
    hospital: 8 + Math.random() * 2,
    industry: 15 + Math.random() * 3,
    offices: 5 + Math.random() * 2
  }))
};

const Archives = () => {
  const [activeTab, setActiveTab] = useState('weather');
  const [dateRange, setDateRange] = useState('30days');

  const tabs = [
    { id: 'weather', name: 'Weather Archives', icon: CloudSun },
    { id: 'consumption', name: 'Consumption Archives', icon: TrendingUp }
  ];

  const dateRanges = [
    { id: '7days', name: '7 Days' },
    { id: '30days', name: '30 Days' },
    { id: '90days', name: '90 Days' },
    { id: '1year', name: '1 Year' }
  ];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Archives</h1>
          <p className="text-gray-600">Historical data and analytics</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg hover:from-orange-600 hover:to-orange-700 font-medium">
          <Download className="w-5 h-5" />
          Export CSV
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 mb-6 border-b border-gray-200">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-orange-600 text-orange-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <tab.icon className="w-5 h-5" />
            {tab.name}
          </button>
        ))}
      </div>

      {/* Date Range Selector */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-700">
            <Calendar className="w-5 h-5" />
            <span className="font-medium">Time Range:</span>
          </div>
          <div className="flex gap-2">
            {dateRanges.map(range => (
              <button
                key={range.id}
                onClick={() => setDateRange(range.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  dateRange === range.id
                    ? 'bg-orange-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {range.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'weather' && <WeatherArchives data={mockArchiveData.weather} />}
      {activeTab === 'consumption' && <ConsumptionArchives data={mockArchiveData.consumption} />}
    </div>
  );
};

const WeatherArchives = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <SummaryCard
          label="Avg Temperature"
          value="22.3°C"
          change="+1.2°C"
          positive={true}
        />
        <SummaryCard
          label="Avg Solar Radiation"
          value="485 W/m²"
          change="+15%"
          positive={true}
        />
        <SummaryCard
          label="Avg Humidity"
          value="62%"
          change="-3%"
          positive={false}
        />
        <SummaryCard
          label="Avg Wind Speed"
          value="11.5 km/h"
          change="+2.1 km/h"
          positive={true}
        />
      </div>

      {/* Temperature Chart */}
      <Card title="Temperature History" icon={CloudSun}>
        <div className="h-64 flex items-end justify-between gap-px">
          {data.slice(0, 720).map((d, i) => {
            const temp = d.temp;
            const normalized = ((temp - 10) / 20) * 100;
            return (
              <div
                key={i}
                className="flex-1 bg-gradient-to-t from-orange-400 to-yellow-300 rounded-t"
                style={{ height: `${Math.max(5, normalized)}%` }}
                title={`${new Date(d.time).toLocaleDateString()}: ${temp.toFixed(1)}°C`}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-4">
          <span>30 days ago</span>
          <span>Today</span>
        </div>
      </Card>

      {/* Solar Radiation Chart */}
      <Card title="Solar Radiation History" icon={CloudSun}>
        <div className="h-64 flex items-end justify-between gap-px">
          {data.slice(0, 720).map((d, i) => {
            const solar = d.solar;
            const normalized = (solar / 800) * 100;
            return (
              <div
                key={i}
                className="flex-1 bg-gradient-to-t from-yellow-500 to-yellow-200 rounded-t"
                style={{ height: `${Math.max(5, normalized)}%` }}
                title={`${new Date(d.time).toLocaleDateString()}: ${solar.toFixed(0)} W/m²`}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-4">
          <span>30 days ago</span>
          <span>Today</span>
        </div>
      </Card>

      {/* Combined View */}
      <Card title="Temperature vs Solar Radiation" icon={Database}>
        <div className="h-64 flex items-end justify-between gap-px">
          {data.slice(0, 240).map((d, i) => (
            <div key={i} className="flex-1 flex flex-col gap-px">
              <div
                className="bg-orange-400 rounded-t"
                style={{ height: `${((d.temp - 10) / 20) * 50}%` }}
                title={`Temp: ${d.temp.toFixed(1)}°C`}
              />
              <div
                className="bg-yellow-400 rounded-b"
                style={{ height: `${(d.solar / 800) * 50}%` }}
                title={`Solar: ${d.solar.toFixed(0)} W/m²`}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-400 rounded" />
            <span>Temperature</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-400 rounded" />
            <span>Solar Radiation</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

const ConsumptionArchives = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <SummaryCard
          label="Total Consumption"
          value="23,456 kWh"
          change="-5.2%"
          positive={true}
        />
        <SummaryCard
          label="Solar Production"
          value="18,234 kWh"
          change="+12.3%"
          positive={true}
        />
        <SummaryCard
          label="Grid Usage"
          value="5,222 kWh"
          change="-18%"
          positive={true}
        />
        <SummaryCard
          label="Cost Savings"
          value="$2,340"
          change="+$320"
          positive={true}
        />
      </div>

      {/* Total Consumption Chart */}
      <Card title="Total Consumption History" icon={TrendingUp}>
        <div className="h-64 flex items-end justify-between gap-px">
          {data.slice(0, 720).map((d, i) => {
            const total = d.total;
            const normalized = (total / 50) * 100;
            return (
              <div
                key={i}
                className="flex-1 bg-gradient-to-t from-red-500 to-red-300 rounded-t"
                style={{ height: `${Math.max(5, normalized)}%` }}
                title={`${new Date(d.time).toLocaleDateString()}: ${total.toFixed(1)} kW`}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-4">
          <span>30 days ago</span>
          <span>Today</span>
        </div>
      </Card>

      {/* Production vs Consumption */}
      <Card title="Solar Production vs Consumption" icon={Database}>
        <div className="h-64 flex items-end justify-between gap-px">
          {data.slice(0, 720).map((d, i) => (
            <div key={i} className="flex-1 flex flex-col-reverse gap-px">
              <div
                className="bg-green-400"
                style={{ height: `${(d.solar / 50) * 100}%` }}
                title={`Production: ${d.solar.toFixed(1)} kW`}
              />
              <div
                className="bg-red-400"
                style={{ height: `${(d.total / 50) * 100}%` }}
                title={`Consumption: ${d.total.toFixed(1)} kW`}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-6 mt-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-400 rounded" />
            <span>Solar Production</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-400 rounded" />
            <span>Total Consumption</span>
          </div>
        </div>
      </Card>

      {/* Breakdown by Building */}
      <Card title="Consumption by Building Type" icon={TrendingUp}>
        <div className="h-64 flex items-end justify-between gap-1">
          {data.slice(0, 168).map((d, i) => (
            <div key={i} className="flex-1 flex flex-col-reverse">
              <div
                className="bg-blue-400"
                style={{ height: `${(d.hospital / 30) * 100}%` }}
                title={`Hospital: ${d.hospital.toFixed(1)} kW`}
              />
              <div
                className="bg-orange-400"
                style={{ height: `${(d.industry / 30) * 100}%` }}
                title={`Industry: ${d.industry.toFixed(1)} kW`}
              />
              <div
                className="bg-green-400"
                style={{ height: `${(d.offices / 30) * 100}%` }}
                title={`Offices: ${d.offices.toFixed(1)} kW`}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-6 mt-4 text-sm flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-400 rounded" />
            <span>Hospital</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-400 rounded" />
            <span>Industry</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-400 rounded" />
            <span>Offices</span>
          </div>
        </div>
      </Card>
    </div>
  );
};

const Card = ({ title, icon: Icon, children }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
      {Icon && (
        <div className="p-2 bg-orange-100 rounded-lg">
          <Icon className="w-5 h-5 text-orange-600" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
    </div>
    {children}
  </div>
);

const SummaryCard = ({ label, value, change, positive }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <p className="text-sm text-gray-500 mb-2">{label}</p>
    <p className="text-2xl font-bold text-gray-800 mb-2">{value}</p>
    <p className={`text-sm font-medium ${positive ? 'text-green-600' : 'text-red-600'}`}>
      {change} vs last period
    </p>
  </div>
);

export default Archives;