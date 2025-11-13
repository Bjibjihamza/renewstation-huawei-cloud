import React, { useState } from 'react';
import { User, Bell, Shield, Palette, Database, HelpCircle, Save } from 'lucide-react';

const SettingsPage = () => {
  const [activeSection, setActiveSection] = useState('profile');
  const [settings, setSettings] = useState({
    name: 'Kris Hancock',
    email: 'kris.hancock@example.com',
    phone: '+1 (555) 123-4567',
    company: 'Solar Gate',
    notifications: {
      email: true,
      push: true,
      sms: false,
      alerts: true
    },
    theme: 'light',
    language: 'en'
  });

  const sections = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'security', name: 'Security', icon: Shield },
    { id: 'appearance', name: 'Appearance', icon: Palette },
    { id: 'data', name: 'Data Management', icon: Database },
    { id: 'help', name: 'Help & Support', icon: HelpCircle }
  ];

  const handleSave = () => {
    alert('Settings saved successfully!');
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Settings</h1>
        <p className="text-gray-600">Manage your account and application preferences</p>
      </div>

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-64 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <nav className="space-y-1">
            {sections.map(section => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  activeSection === section.id
                    ? 'bg-orange-100 text-orange-600 font-semibold'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <section.icon className="w-5 h-5" />
                <span className="text-sm">{section.name}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeSection === 'profile' && <ProfileSection settings={settings} setSettings={setSettings} />}
          {activeSection === 'notifications' && <NotificationsSection settings={settings} setSettings={setSettings} />}
          {activeSection === 'security' && <SecuritySection />}
          {activeSection === 'appearance' && <AppearanceSection settings={settings} setSettings={setSettings} />}
          {activeSection === 'data' && <DataSection />}
          {activeSection === 'help' && <HelpSection />}

          {/* Save Button */}
          <div className="mt-6">
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg hover:from-orange-600 hover:to-orange-700 font-medium"
            >
              <Save className="w-5 h-5" />
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProfileSection = ({ settings, setSettings }) => (
  <div className="space-y-6">
    <Card title="Personal Information">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
          <input
            type="text"
            value={settings.name}
            onChange={(e) => setSettings({ ...settings, name: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
          <input
            type="email"
            value={settings.email}
            onChange={(e) => setSettings({ ...settings, email: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
          <input
            type="tel"
            value={settings.phone}
            onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company</label>
          <input
            type="text"
            value={settings.company}
            onChange={(e) => setSettings({ ...settings, company: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
      </div>
    </Card>

    <Card title="Profile Picture">
      <div className="flex items-center gap-6">
        <div className="w-24 h-24 bg-orange-100 rounded-full flex items-center justify-center">
          <span className="text-orange-600 text-3xl font-bold">KH</span>
        </div>
        <div>
          <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 mb-2">
            Upload New Picture
          </button>
          <p className="text-sm text-gray-500">Recommended: Square image, at least 400x400px</p>
        </div>
      </div>
    </Card>
  </div>
);

const NotificationsSection = ({ settings, setSettings }) => (
  <div className="space-y-6">
    <Card title="Notification Preferences">
      <div className="space-y-4">
        <ToggleItem
          label="Email Notifications"
          description="Receive updates and alerts via email"
          checked={settings.notifications.email}
          onChange={(checked) => setSettings({
            ...settings,
            notifications: { ...settings.notifications, email: checked }
          })}
        />
        <ToggleItem
          label="Push Notifications"
          description="Get real-time notifications in your browser"
          checked={settings.notifications.push}
          onChange={(checked) => setSettings({
            ...settings,
            notifications: { ...settings.notifications, push: checked }
          })}
        />
        <ToggleItem
          label="SMS Notifications"
          description="Receive important alerts via text message"
          checked={settings.notifications.sms}
          onChange={(checked) => setSettings({
            ...settings,
            notifications: { ...settings.notifications, sms: checked }
          })}
        />
        <ToggleItem
          label="System Alerts"
          description="Get notified about system issues and maintenance"
          checked={settings.notifications.alerts}
          onChange={(checked) => setSettings({
            ...settings,
            notifications: { ...settings.notifications, alerts: checked }
          })}
        />
      </div>
    </Card>
  </div>
);

const SecuritySection = () => (
  <div className="space-y-6">
    <Card title="Password">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
          <input
            type="password"
            placeholder="Enter current password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
          <input
            type="password"
            placeholder="Enter new password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
          <input
            type="password"
            placeholder="Confirm new password"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
          />
        </div>
        <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
          Update Password
        </button>
      </div>
    </Card>

    <Card title="Two-Factor Authentication">
      <p className="text-gray-600 mb-4">Add an extra layer of security to your account</p>
      <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
        Enable 2FA
      </button>
    </Card>
  </div>
);

const AppearanceSection = ({ settings, setSettings }) => (
  <div className="space-y-6">
    <Card title="Theme">
      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={() => setSettings({ ...settings, theme: 'light' })}
          className={`p-4 border-2 rounded-lg ${
            settings.theme === 'light' ? 'border-orange-600 bg-orange-50' : 'border-gray-200'
          }`}
        >
          <div className="w-full h-32 bg-white rounded border border-gray-200 mb-3"></div>
          <p className="font-medium text-center">Light</p>
        </button>
        <button
          onClick={() => setSettings({ ...settings, theme: 'dark' })}
          className={`p-4 border-2 rounded-lg ${
            settings.theme === 'dark' ? 'border-orange-600 bg-orange-50' : 'border-gray-200'
          }`}
        >
          <div className="w-full h-32 bg-gray-800 rounded border border-gray-700 mb-3"></div>
          <p className="font-medium text-center">Dark</p>
        </button>
      </div>
    </Card>

    <Card title="Language">
      <select
        value={settings.language}
        onChange={(e) => setSettings({ ...settings, language: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
      >
        <option value="en">English</option>
        <option value="fr">Français</option>
        <option value="es">Español</option>
        <option value="de">Deutsch</option>
      </select>
    </Card>
  </div>
);

const DataSection = () => (
  <div className="space-y-6">
    <Card title="Export Data">
      <p className="text-gray-600 mb-4">Download all your data in CSV format</p>
      <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
        Export All Data
      </button>
    </Card>

    <Card title="Delete Account">
      <p className="text-gray-600 mb-4">Permanently delete your account and all associated data</p>
      <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
        Delete Account
      </button>
    </Card>
  </div>
);

const HelpSection = () => (
  <div className="space-y-6">
    <Card title="Documentation">
      <p className="text-gray-600 mb-4">Access user guides and documentation</p>
      <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
        View Documentation
      </button>
    </Card>

    <Card title="Contact Support">
      <p className="text-gray-600 mb-4">Get help from our support team</p>
      <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
        Contact Support
      </button>
    </Card>

    <Card title="System Information">
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Version:</span>
          <span className="font-semibold">2.4.1</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Last Updated:</span>
          <span className="font-semibold">November 12, 2025</span>
        </div>
      </div>
    </Card>
  </div>
);

const Card = ({ title, children }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
    {children}
  </div>
);

const ToggleItem = ({ label, description, checked, onChange }) => (
  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
    <div>
      <p className="font-medium text-gray-800">{label}</p>
      <p className="text-sm text-gray-500">{description}</p>
    </div>
    <button
      onClick={() => onChange(!checked)}
      className={`relative w-12 h-6 rounded-full transition-colors ${
        checked ? 'bg-orange-600' : 'bg-gray-300'
      }`}
    >
      <div
        className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
          checked ? 'transform translate-x-6' : ''
        }`}
      />
    </button>
  </div>
);

export default SettingsPage;