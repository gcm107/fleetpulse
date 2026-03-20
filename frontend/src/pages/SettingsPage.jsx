import React, { useEffect, useState, useCallback } from 'react';
import {
  Settings,
  Key,
  Database,
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Server,
  HardDrive,
  Loader2,
} from 'lucide-react';
import { getStats, getEtlStatus, triggerEtl } from '../api/client';
import Badge from '../components/common/Badge';
import DataTable from '../components/common/DataTable';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { formatDateTime, timeAgo } from '../utils/formatters';

const ETL_MODULES = [
  { key: 'airports', label: 'Airports', description: 'OurAirports global airport data' },
  { key: 'faa_registry', label: 'FAA Registry', description: 'FAA aircraft registration database' },
  { key: 'operators_sample', label: 'Operators', description: 'Part 121/135 certified operators' },
  { key: 'ntsb', label: 'NTSB Accidents', description: 'NTSB aviation accident reports' },
  { key: 'enforcement', label: 'Enforcement', description: 'FAA enforcement actions' },
  { key: 'safety_scores', label: 'Safety Scores', description: 'Computed safety score aggregation' },
  { key: 'ofac', label: 'OFAC SDN', description: 'OFAC Specially Designated Nationals list' },
];

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

function EtlModuleRow({ module, lastRun, onTrigger, triggering }) {
  const isRunning = triggering === module.key;
  const lastRunTime = lastRun?.completed_at || lastRun?.started_at;
  const status = lastRun?.status;

  return (
    <div className="flex items-center justify-between py-3 border-b border-zinc-800/30 last:border-0">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Database className="w-4 h-4 text-gray-500 shrink-0" />
        <div className="min-w-0">
          <p className="text-sm text-gray-200 font-medium">{module.label}</p>
          <p className="text-xs text-gray-500 truncate">{module.description}</p>
        </div>
      </div>
      <div className="flex items-center gap-4 shrink-0">
        <div className="text-right">
          {lastRunTime ? (
            <>
              <p className="text-xxs text-gray-500">{timeAgo(lastRunTime)}</p>
              {status && (
                <Badge
                  variant={
                    status === 'success'
                      ? 'success'
                      : status === 'running'
                      ? 'info'
                      : status === 'failed'
                      ? 'danger'
                      : 'neutral'
                  }
                  dot
                >
                  {status}
                </Badge>
              )}
            </>
          ) : (
            <span className="text-xxs text-gray-600">Never run</span>
          )}
        </div>
        <button
          onClick={() => onTrigger(module.key)}
          disabled={isRunning}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 text-xs font-medium transition-colors border border-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Play className="w-3.5 h-3.5" />
          )}
          {isRunning ? 'Running...' : 'Trigger'}
        </button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [stats, setStats] = useState(null);
  const [etlStatus, setEtlStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(null);
  const [triggerResult, setTriggerResult] = useState(null);
  const [adminKey, setAdminKey] = useState('');
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

  async function handleTrigger(moduleKey) {
    setTriggering(moduleKey);
    setTriggerResult(null);
    try {
      await triggerEtl(moduleKey, adminKey || undefined);
      setTriggerResult({ module: moduleKey, success: true });
      // Refresh status after a brief pause for the ETL to register
      setTimeout(fetchData, 2000);
    } catch (err) {
      setTriggerResult({
        module: moduleKey,
        success: false,
        error: err.response?.data?.detail || 'Trigger failed',
      });
    } finally {
      setTriggering(null);
    }
  }

  function getModuleLastRun(moduleKey) {
    if (!etlStatus?.recent_runs) return null;
    return etlStatus.recent_runs.find(
      (r) => r.source === moduleKey || r.module === moduleKey
    );
  }

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

      {/* Trigger result toast */}
      {triggerResult && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg border ${
            triggerResult.success
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-red-500/10 border-red-500/30'
          }`}
        >
          {triggerResult.success ? (
            <CheckCircle2 className="w-4 h-4 text-green-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span
            className={`text-sm ${
              triggerResult.success ? 'text-green-200' : 'text-red-200'
            }`}
          >
            {triggerResult.success
              ? `ETL job "${triggerResult.module}" triggered successfully`
              : `Failed to trigger "${triggerResult.module}": ${triggerResult.error}`}
          </span>
        </div>
      )}

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
                configured={apiKeyStatuses[apiKey.key] || false}
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
          <div className="mt-4 pt-4 border-t border-zinc-800/30">
            <label className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2 block">
              Admin API Key (for ETL triggers)
            </label>
            <input
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="Enter admin key (leave blank if not configured)"
              className="w-full bg-zinc-900/50 border border-zinc-700/30 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 font-mono"
            />
            <p className="text-xxs text-gray-600 mt-1">
              Set ADMIN_API_KEY in .env to require authentication for ETL triggers.
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

      {/* Data Management */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" />
          Data Management -- ETL Jobs
        </div>
        <p className="text-xs text-gray-500 mb-4">
          Trigger data ingestion jobs manually. Each module pulls data from its
          source, transforms it, and loads it into the database.
        </p>
        <div>
          {ETL_MODULES.map((mod) => (
            <EtlModuleRow
              key={mod.key}
              module={mod}
              lastRun={getModuleLastRun(mod.key)}
              onTrigger={handleTrigger}
              triggering={triggering}
            />
          ))}
        </div>
      </div>

      {/* Recent ETL Runs */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Clock className="w-3.5 h-3.5" />
          Recent ETL Runs
        </div>
        {etlStatus?.recent_runs && etlStatus.recent_runs.length > 0 ? (
          <DataTable
            columns={etlColumns}
            data={etlStatus.recent_runs}
            emptyMessage="No ETL runs recorded"
          />
        ) : (
          <div className="text-sm text-gray-500 text-center py-6">
            No ETL runs recorded. Trigger a job above to get started.
          </div>
        )}
      </div>
    </div>
  );
}
