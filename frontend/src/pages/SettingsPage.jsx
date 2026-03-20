import React, { useEffect, useState, useCallback } from 'react';
import {
  Settings,
  Key,
  Database,
  RefreshCw,
  Server,
  HardDrive,
} from 'lucide-react';
import { getStats, getEtlStatus } from '../api/client';
import Badge from '../components/common/Badge';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { formatDateTime } from '../utils/formatters';

const API_KEYS = [
  { key: 'opensky', label: 'OpenSky Network', description: 'ADS-B flight tracking data' },
  { key: 'faa_notam', label: 'FAA NOTAM', description: 'Notice to Air Missions API' },
];

function ApiKeyStatus({ label, description, configured }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-zinc-800/30 last:border-0">
      <div className="flex items-center gap-3">
        <Key className="w-4 h-4 text-gray-500" />
        <div>
          <p className="text-sm text-gray-200 font-medium">{label}</p>
          <p className="text-xs text-gray-500">{description}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {configured ? (
          <>
            <span className="w-2 h-2 rounded-full bg-green-400" />
            <span className="text-xs text-green-400 font-medium">Configured</span>
          </>
        ) : (
          <>
            <span className="w-2 h-2 rounded-full bg-red-400" />
            <span className="text-xs text-red-400 font-medium">Not Set</span>
          </>
        )}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [stats, setStats] = useState(null);
  const [etlStatus, setEtlStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openskyClientId, setOpenskyClientId] = useState(() => localStorage.getItem('opensky_client_id') || '');
  const [openskyClientSecret, setOpenskyClientSecret] = useState(() => localStorage.getItem('opensky_client_secret') || '');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, etlRes] = await Promise.allSettled([
        getStats(),
        getEtlStatus(),
      ]);
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (etlRes.status === 'fulfilled') setEtlStatus(etlRes.value.data);
    } catch (err) {
      console.error('[Settings] Fetch failed', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const apiKeyStatuses = stats?.api_keys || {};

  const etlColumns = [
    { key: 'source', label: 'Module', mono: true },
    {
      key: 'status',
      label: 'Status',
      render: (val) => (
        <Badge
          variant={
            val === 'success'
              ? 'success'
              : val === 'running'
              ? 'info'
              : val === 'failed'
              ? 'danger'
              : 'neutral'
          }
          dot
        >
          {val || 'unknown'}
        </Badge>
      ),
    },
    {
      key: 'started_at',
      label: 'Started',
      mono: true,
      render: (val) => formatDateTime(val),
    },
    {
      key: 'completed_at',
      label: 'Completed',
      mono: true,
      render: (val) => formatDateTime(val),
    },
    {
      key: 'records_processed',
      label: 'Records',
      align: 'right',
      mono: true,
      render: (val) => (val != null ? Number(val).toLocaleString() : '--'),
    },
  ];

  if (loading) return <LoadingSpinner message="Loading settings..." />;

  return (
    <div className="max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-zinc-800/50">
            <Settings className="w-5 h-5 text-gray-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              System configuration, data management, and API keys
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Keys */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Key className="w-3.5 h-3.5" />
            API Keys
          </div>
          <div>
            {API_KEYS.map((apiKey) => (
              <ApiKeyStatus
                key={apiKey.key}
                label={apiKey.label}
                description={apiKey.description}
                configured={
                  apiKey.key === 'opensky'
                    ? !!(openskyClientId && openskyClientSecret)
                    : (apiKeyStatuses[apiKey.key] || false)
                }
              />
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-3 leading-relaxed">
            These API keys are <span className="text-gray-400 font-medium">optional</span>. All core features (aircraft registry, airport data, safety scores, sanctions screening) work without them using pre-downloaded public data. Keys are only needed for enhanced real-time features:
          </p>
          <ul className="text-xs text-gray-600 mt-1.5 space-y-1 list-disc list-inside">
            <li><span className="text-gray-400">OpenSky</span> increases live tracking API limits from 100 to 4,000 calls/day</li>
            <li><span className="text-gray-400">FAA NOTAM</span> enables real-time Notices to Air Missions at airports</li>
          </ul>
          <div className="mt-4 pt-4 border-t border-zinc-800/30 space-y-3">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5 block">
                OpenSky Client ID
              </label>
              <input
                type="text"
                value={openskyClientId}
                onChange={(e) => {
                  setOpenskyClientId(e.target.value);
                  localStorage.setItem('opensky_client_id', e.target.value);
                }}
                placeholder="e.g. myusername-api-client"
                className="w-full bg-zinc-900/50 border border-zinc-700/30 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5 block">
                OpenSky Client Secret
              </label>
              <input
                type="password"
                value={openskyClientSecret}
                onChange={(e) => {
                  setOpenskyClientSecret(e.target.value);
                  localStorage.setItem('opensky_client_secret', e.target.value);
                }}
                placeholder="Your client secret"
                className="w-full bg-zinc-900/50 border border-zinc-700/30 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 font-mono"
              />
            </div>
            <p className="text-xxs text-gray-600">
              Get free credentials at <a href="https://opensky-network.org/index.php/login" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">opensky-network.org</a>. Stored in your browser only.
            </p>
          </div>
        </div>

        {/* System Info */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Server className="w-3.5 h-3.5" />
            System Information
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-zinc-800/30">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <HardDrive className="w-3.5 h-3.5" />
                Airports
              </div>
              <span className="text-sm font-mono text-gray-200">
                {stats?.airports != null
                  ? Number(stats.airports).toLocaleString()
                  : '--'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-zinc-800/30">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <HardDrive className="w-3.5 h-3.5" />
                Aircraft
              </div>
              <span className="text-sm font-mono text-gray-200">
                {stats?.aircraft != null
                  ? Number(stats.aircraft).toLocaleString()
                  : '--'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-zinc-800/30">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <HardDrive className="w-3.5 h-3.5" />
                Operators
              </div>
              <span className="text-sm font-mono text-gray-200">
                {stats?.operators != null
                  ? Number(stats.operators).toLocaleString()
                  : '--'}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-zinc-800/30">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <HardDrive className="w-3.5 h-3.5" />
                Data Sources
              </div>
              <span className="text-sm font-mono text-gray-200">
                {stats?.data_sources ?? '--'}
              </span>
            </div>
            {stats?.db_size && (
              <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <Database className="w-3.5 h-3.5" />
                  Database Size
                </div>
                <span className="text-sm font-mono text-gray-200">
                  {stats.db_size}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Data Info */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" />
          Data Sources
        </div>
        <p className="text-xs text-gray-500">
          FleetPulse ingests data from free, public aviation sources. Data is loaded automatically on server startup.
        </p>
        <div className="mt-3 space-y-2 text-xs">
          <div className="flex justify-between py-1.5 border-b border-zinc-800/30">
            <span className="text-gray-400">FAA Aircraft Registry</span>
            <span className="text-gray-500">310,000+ aircraft, updated daily</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-zinc-800/30">
            <span className="text-gray-400">OurAirports</span>
            <span className="text-gray-500">84,000+ airports worldwide</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-zinc-800/30">
            <span className="text-gray-400">NTSB</span>
            <span className="text-gray-500">Aviation accident database</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-zinc-800/30">
            <span className="text-gray-400">OFAC SDN</span>
            <span className="text-gray-500">US Treasury sanctions list</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-zinc-800/30">
            <span className="text-gray-400">OpenSky Network</span>
            <span className="text-gray-500">Real-time ADS-B flight tracking</span>
          </div>
          <div className="flex justify-between py-1.5">
            <span className="text-gray-400">NOAA Aviation Weather</span>
            <span className="text-gray-500">METAR/TAF observations</span>
          </div>
        </div>
      </div>
    </div>
  );
}
