// Dashboard.jsx
import React, { useState } from 'react';
import {
  Home,
  Battery as BatteryIcon,
  Zap,
  CloudSun,
  BarChart3,
  Menu,
} from 'lucide-react';

import Overview from './Overviews';
import Battery from './Battery';
import EnergyPage from './EnergyPage';
import SolarPage from './SolarPage';
import WeatherPage from './WeatherPage';

const Dashboard = () => {
  const [activePage, setActivePage] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigation = [
    { id: 'overview', name: 'Vue d’ensemble', icon: Home },
    { id: 'battery', name: 'Batteries', icon: BatteryIcon },
    { id: 'energy', name: 'Consommation', icon: BarChart3 },
    { id: 'solar', name: 'Production Solaire', icon: Zap },
    { id: 'weather', name: 'Météo', icon: CloudSun },
  ];

  return (
    <div className="flex h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-white/70 backdrop-blur-xl border-r border-emerald-100 transition-all duration-300 flex flex-col shadow-lg`}
      >
        <div className="p-4 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-md">
                <span className="text-white font-bold text-xl">☀</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-emerald-900">RenewStation</h1>
                <p className="text-[11px] text-emerald-500">
                  Campus Energy Control
                </p>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-emerald-50 rounded-xl transition-colors"
          >
            <Menu className="w-5 h-5 text-emerald-700" />
          </button>
        </div>

        <nav className="flex-1 px-3 space-y-1 mt-2">
          {navigation.map((item) => (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                activePage === item.id
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-md'
                  : 'text-emerald-800 hover:bg-emerald-50'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.name}</span>}
            </button>
          ))}
        </nav>

        {sidebarOpen && (
          <div className="p-4 border-t border-emerald-100">
            <div className="flex items-center gap-3 px-2 py-1.5">
              <div className="w-8 h-8 bg-emerald-500/80 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                GT
              </div>
              <div>
                <p className="text-xs font-semibold text-emerald-900">
                  RenewStation Admin
                </p>
                <p className="text-[11px] text-emerald-500">Superviseur</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main content area */}
      <div className="flex-1 overflow-auto">
        {activePage === 'overview' && <Overview />}
        {activePage === 'battery' && <Battery />}
        {activePage === 'energy' && <EnergyPage />}
        {activePage === 'solar' && <SolarPage />}
        {activePage === 'weather' && <WeatherPage />}
      </div>
    </div>
  );
};

export default Dashboard;
