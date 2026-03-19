import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import AirportBrowse from './pages/AirportBrowse';
import AirportPage from './pages/AirportPage';
import AircraftBrowse from './pages/AircraftBrowse';
import AircraftPage from './pages/AircraftPage';
import OperatorBrowse from './pages/OperatorBrowse';
import OperatorPage from './pages/OperatorPage';
import TrackingPage from './pages/TrackingPage';
import SafetyPage from './pages/SafetyPage';
import SanctionsPage from './pages/SanctionsPage';
import SettingsPage from './pages/SettingsPage';
import SearchResults from './pages/SearchResults';

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/airports" element={<AirportBrowse />} />
        <Route path="/airports/:code" element={<AirportPage />} />
        <Route path="/aircraft" element={<AircraftBrowse />} />
        <Route path="/aircraft/:nNumber" element={<AircraftPage />} />
        <Route path="/operators" element={<OperatorBrowse />} />
        <Route path="/operators/:certNumber" element={<OperatorPage />} />
        <Route path="/tracking" element={<TrackingPage />} />
        <Route path="/safety" element={<SafetyPage />} />
        <Route path="/sanctions" element={<SanctionsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/search" element={<SearchResults />} />
        <Route
          path="*"
          element={
            <div className="flex flex-col items-center justify-center py-20">
              <h1 className="text-4xl font-mono font-bold text-gray-600 mb-4">404</h1>
              <p className="text-sm text-gray-500">Page not found</p>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
