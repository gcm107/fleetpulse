import React, { useEffect, useState } from 'react';
import {
  Building2,
  PlaneTakeoff,
  Building,
  Database,
  RefreshCw,
  Clock,
  XCircle,
  ArrowRight,
  ShieldAlert,
  AlertTriangle,
  Radar,
  Activity,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { getStats, getEtlStatus, getSanctionsAlerts } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import DataTable from '../components/common/DataTable';
import { formatDateTime, timeAgo } from '../utils/formatters';

function StatCard({ icon: Icon, label, value, color = 'text-blue-400', subtext, linkTo }) {
  const content = (
    <div className="card flex items-start gap-4 hover:border-blue-500/20 transition-colors">
      <div className={`p-2.5 rounded-lg bg-zinc-800/50 ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xxs font-semibold uppercase tracking-wider text-gray-500 mb-1">
          {label}
        </p>
        <p className="stat-value">
          {value ?? '--'}
        </p>
        {subtext && (
          <p className="text-xs text-gray-500 mt-1">{subtext}</p>
        )}
      </div>
    </div>
  );

  if (linkTo) {
    return <Link to={linkTo}>{content}</Link>;
  }
  return content;
}

function FreshnessCard({ source, lastUpdated, recordCount, status }) {
  const variant = status === 'fresh' ? 'success' : status === 'stale' ? 'warning' : status === 'expired' ? 'danger' : 'neutral';
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-zinc-800/50 last:border-0">
      <div className="flex items-center gap-3">
        <Database className="w-4 h-4 text-gray-500" />
        <div>
          <p className="text-sm text-gray-200 font-medium">{source}</p>
          <p className="text-xs text-gray-500 font-mono">
            {recordCount != null ? `${Number(recordCount).toLocaleString()} records` : 'No data'}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500">{timeAgo(lastUpdated)}</span>
        <Badge variant={variant} dot>
          {status || 'unknown'}
        </Badge>
      </div>
    </div>
  );
}

function SanctionsAlertPreview({ alert }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-zinc-800/50 last:border-0">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
        <div>
          <span className="text-sm font-mono text-red-300">
            N{alert.n_number || alert.tail_number || '--'}
          </span>
          <span className="text-xs text-gray-500 ml-2">
            {alert.sdn_name || alert.entity_name || ''}
          </span>
        </div>
      </div>
      <Badge variant="danger" dot>
        {alert.status || 'alert'}
      </Badge>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [etlStatus, setEtlStatus] = useState(null);
  const [sanctionsAlerts, setSanctionsAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [statsRes, etlRes, alertsRes] = await Promise.allSettled([
          getStats(),
          getEtlStatus(),
          getSanctionsAlerts(),
        ]);
        if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
        if (etlRes.status === 'fulfilled') setEtlStatus(etlRes.value.data);
        if (alertsRes.status === 'fulfilled') {
          const aData = alertsRes.value.data;
          setSanctionsAlerts(Array.isArray(aData) ? aData : aData?.alerts || []);
        }
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) return <LoadingSpinner message="Loading dashboard..." />;

  const etlColumns = [
    { key: 'source', label: 'Source', mono: true },
    {
      key: 'status',
      label: 'Status',
      render: (val) => (
        <Badge variant={val === 'success' ? 'success' : val === 'running' ? 'info' : 'danger'} dot>
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
      render: (val) => val != null ? Number(val).toLocaleString() : '--',
    },
  ];

  const ntsb_count = stats?.ntsb_accidents || stats?.accidents || stats?.ntsb;

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">
          FleetPulse -- Aviation Intelligence Platform
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Monitor airports, aircraft, operators, and compliance in real time.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex items-center gap-2">
          <XCircle className="w-4 h-4 text-red-400" />
          <span className="text-sm text-red-200">{error}</span>
        </div>
      )}

      {/* Sanctions alert banner */}
      {sanctionsAlerts.length > 0 && (
        <Link to="/sanctions">
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex items-center gap-3 hover:bg-red-500/15 transition-colors cursor-pointer">
            <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-red-300">
                {sanctionsAlerts.length} Active Sanctions Alert{sanctionsAlerts.length !== 1 ? 's' : ''}
              </p>
              <p className="text-xs text-red-400/70">
                Potential OFAC SDN matches require review
              </p>
            </div>
            <ArrowRight className="w-4 h-4 text-red-400" />
          </div>
        </Link>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          icon={Building2}
          label="Airports"
          value={stats?.airports != null ? Number(stats.airports).toLocaleString() : '--'}
          color="text-blue-400"
          subtext="Total in database"
        />
        <StatCard
          icon={PlaneTakeoff}
          label="Aircraft"
          value={stats?.aircraft != null ? Number(stats.aircraft).toLocaleString() : '--'}
          color="text-green-400"
          subtext="FAA registrations"
        />
        {ntsb_count > 0 && (
          <StatCard
            icon={Activity}
            label="NTSB Accidents"
            value={Number(ntsb_count).toLocaleString()}
            color="text-blue-300"
            subtext="Accident records"
          />
        )}
        {sanctionsAlerts.length > 0 && (
          <StatCard
            icon={ShieldAlert}
            label="Sanctions Alerts"
            value={sanctionsAlerts.length}
            color="text-red-400"
            subtext="Requires review"
            linkTo="/sanctions"
          />
        )}
      </div>

      {/* Data freshness and ETL runs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data freshness */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" />
            Data Freshness
          </div>
          <div className="space-y-0">
            {stats?.sources ? (
              stats.sources.map((src, i) => (
                <FreshnessCard
                  key={i}
                  source={src.name}
                  lastUpdated={src.last_updated}
                  recordCount={src.record_count}
                  status={src.status}
                />
              ))
            ) : (
              <div className="text-sm text-gray-500 py-4 text-center">
                Connect to the backend API to view data source status.
              </div>
            )}
          </div>
        </div>

        {/* Sanctions alerts preview - only shown when there are active alerts */}
        {sanctionsAlerts.length > 0 && (
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                Sanctions Alerts
              </div>
              <Link
                to="/sanctions"
                className="text-xxs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
              >
                View All
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div>
              {sanctionsAlerts.slice(0, 5).map((alert, i) => (
                <SanctionsAlertPreview key={alert.id || i} alert={alert} />
              ))}
              {sanctionsAlerts.length > 5 && (
                <p className="text-xxs text-gray-500 text-center mt-2">
                  +{sanctionsAlerts.length - 5} more alerts
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Recent ETL runs */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" />
          Recent ETL Runs
        </div>
        {etlStatus?.recent_runs ? (
          <DataTable
            columns={etlColumns}
            data={etlStatus.recent_runs}
            emptyMessage="No ETL runs recorded"
          />
        ) : (
          <div className="text-sm text-gray-500 py-4 text-center">
            ETL status will appear here once the backend is running.
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-gradient-to-r from-zinc-900 to-zinc-900/50 border-blue-500/20">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-200 mb-1">
                Quick Search
              </h3>
              <p className="text-xs text-gray-500">
                Find airports or aircraft. Try "KJFK", "N476CA", or "Gulfstream".
              </p>
            </div>
            <Link
              to="/search?q="
              className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              Search
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        <Link to="/tracking" className="card bg-gradient-to-r from-zinc-900 to-zinc-900/50 border-blue-500/20 hover:border-blue-500/30 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-200 mb-1">
                Flight Tracking
              </h3>
              <p className="text-xs text-gray-500">
                Track aircraft in real time on the map.
              </p>
            </div>
            <Radar className="w-5 h-5 text-blue-400" />
          </div>
        </Link>

        <Link to="/settings" className="card bg-gradient-to-r from-zinc-900 to-zinc-900/50 border-blue-500/20 hover:border-blue-500/30 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-200 mb-1">
                Data Management
              </h3>
              <p className="text-xs text-gray-500">
                Trigger ETL jobs and manage data sources.
              </p>
            </div>
            <Database className="w-5 h-5 text-gray-400" />
          </div>
        </Link>
      </div>
    </div>
  );
}
