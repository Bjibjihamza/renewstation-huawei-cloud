import React, { useState } from 'react';
import { Home, BarChart3, History, Settings, Menu } from 'lucide-react';
import Overview from './Overviews';
import Battery from './Battery'

const Dashboard = () => {
  const [activePage, setActivePage] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const navigation = [
    { id: 'overview', name: 'Overview', icon: Home },
    { id: 'battery', name: 'battery', icon: Home },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-gradient-to-br from-orange-400 via-orange-500 to-orange-600 text-white transition-all duration-300 flex flex-col`}>
        <div className="p-6 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <span className="text-orange-500 font-bold text-xl">S</span>
              </div>
              <div>
                <h1 className="text-xl font-bold">Solar Gate</h1>
                <p className="text-xs text-orange-100">Powered by Huawei</p>
              </div>
            </div>
          )}
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-orange-400 rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          {navigation.map(item => (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                activePage === item.id
                  ? 'bg-white text-orange-600 shadow-lg font-semibold'
                  : 'text-white hover:bg-orange-400'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="text-sm">{item.name}</span>}
            </button>
          ))}
        </nav>

        {sidebarOpen && (
          <div className="p-4 border-t border-orange-400">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 bg-orange-300 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold text-sm">KH</span>
              </div>
              <div>
                <p className="text-sm font-semibold">Kris Hancock</p>
                <p className="text-xs text-orange-100">Admin</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {activePage === 'overview' && <Overview />}
        {activePage === 'battery' && <Battery />}
      </div>
    </div>
  );
};

export default Dashboard;