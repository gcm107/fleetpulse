import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  Search,
  AlertTriangle,
  ShieldCheck,
  Info,
  Clock,
  User,
} from 'lucide-react';
import { getSanctionsAlerts, checkSanctions } from '../api/client';
import SanctionsCheck from '../components/sanctions/SanctionsCheck';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { timeAgo } from '../utils/formatters';

function AlertCard({ alert }) {
  // Extract data from the first match in the nested API response
  const firstMatch = alert.matches?.[0] || {};
  const sdnEntry = firstMatch.sdn_entry || {};
  const confidence = Math.round((firstMatch.match_confidence || 0) * 100);
  const pct = Math.min(Math.max(confidence, 0), 100);
  const barColor =
    pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-orange-500' : 'bg-yellow-500';

  return (
    <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-300">
              N{alert.n_number || '--'}
            </p>
            {sdnEntry.program_list && (
              <p className="text-xs text-gray-500">
                {sdnEntry.program_list}
              </p>
            )}
          </div>
        </div>
        <Badge variant="danger" dot>
          {firstMatch.is_confirmed === null ? 'Unconfirmed' : firstMatch.is_confirmed ? 'Confirmed' : 'Dismissed'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">SDN Entity</span>
          <p className="text-gray-300 font-medium">
            {sdnEntry.primary_name || '--'}
          </p>
        </div>
        <div>
          <span className="text-gray-500">Matched On</span>
          <p className="text-gray-300 font-mono">
            {firstMatch.matched_value || firstMatch.sdn_value || '--'}
          </p>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between text-xxs mb-1">
          <span className="text-gray-500 uppercase tracking-wider font-semibold">
            Confidence
          </span>
          <span className="font-mono text-gray-200">{pct}%</span>
        </div>
        <div className="w-full bg-zinc-900/50 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {alert.match_count > 1 && (
        <p className="text-xxs text-orange-400">
          +{alert.match_count - 1} additional match{alert.match_count > 2 ? 'es' : ''}
        </p>
      )}
    </div>
  );
}

export default function SanctionsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [checkResult, setCheckResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState(null);
  const [checkedNNumber, setCheckedNNumber] = useState(null);

  useEffect(() => {
    async function fetchAlerts() {
      setLoadingAlerts(true);
      try {
        const res = await getSanctionsAlerts();
        const data = res.data;
        setAlerts(Array.isArray(data) ? data : data?.alerts || []);
      } catch (err) {
        console.error('[Sanctions] Failed to load alerts', err);
      } finally {
        setLoadingAlerts(false);
      }
    }
    fetchAlerts();
  }, []);

  async function handleCheck(e) {
    e.preventDefault();
    const cleaned = searchInput.trim().toUpperCase().replace(/^N/, '');
    if (!cleaned) return;

    setChecking(true);
    setCheckError(null);
    setCheckResult(null);
    setCheckedNNumber(cleaned);

    try {
      const res = await checkSanctions(cleaned);
      setCheckResult(res.data);
    } catch (err) {
      setCheckError(
        err.response?.data?.detail || 'Failed to run sanctions check'
      );
    } finally {
      setChecking(false);
    }
  }

  return (
    <div className="max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-zinc-800/50">
            <ShieldAlert className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">
              Sanctions Screening
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              OFAC SDN list monitoring and compliance screening
            </p>
          </div>
        </div>
      </div>

      {/* Info banner */}
      <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg px-4 py-3 flex items-start gap-3">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-400 leading-relaxed">
          <p className="font-medium text-gray-300 mb-1">
            What is OFAC Sanctions Screening?
          </p>
          <p>
            The Office of Foreign Assets Control (OFAC) maintains the Specially
            Designated Nationals (SDN) list -- a registry of individuals,
            companies, and entities subject to trade sanctions. This tool
            cross-references aircraft registration data (tail numbers, owner
            names, serial numbers) against the SDN list to identify potential
            compliance concerns. A match does not necessarily indicate a
            violation; results should be reviewed by compliance personnel.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Search and results */}
        <div className="lg:col-span-3 space-y-4">
          {/* Search form */}
          <div className="card">
            <div className="card-header flex items-center gap-2">
              <Search className="w-3.5 h-3.5" />
              Check Aircraft
            </div>
            <form onSubmit={handleCheck} className="flex gap-2">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Enter N-Number (e.g. N12345)"
                className="flex-1 bg-zinc-900/50 border border-zinc-700/30 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 font-mono"
              />
              <button
                type="submit"
                disabled={!searchInput.trim() || checking}
                className="px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <ShieldAlert className="w-4 h-4" />
                Screen
              </button>
            </form>
          </div>

          {/* Check results */}
          <div className="card">
            <div className="card-header flex items-center gap-2">
              {checkResult?.has_match || (checkResult?.matches?.length > 0) ? (
                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
              ) : (
                <ShieldCheck className="w-3.5 h-3.5" />
              )}
              Screening Results
              {checkedNNumber && (
                <span className="ml-2 font-mono text-blue-400 text-xxs">
                  N{checkedNNumber}
                </span>
              )}
            </div>
            {checking ? (
              <div className="py-8 text-center">
                <div className="inline-block w-5 h-5 border-2 border-gray-600 border-t-blue-400 rounded-full animate-spin mb-3" />
                <p className="text-sm text-gray-500">Running sanctions check...</p>
              </div>
            ) : checkError ? (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-300">
                {checkError}
              </div>
            ) : (
              <SanctionsCheck result={checkResult} />
            )}
          </div>
        </div>

        {/* Active alerts sidebar */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card">
            <div className="card-header flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              Active Alerts
              {alerts.length > 0 && (
                <span className="ml-auto bg-red-500/20 text-red-400 text-xxs font-mono px-1.5 py-0.5 rounded">
                  {alerts.length}
                </span>
              )}
            </div>
            {loadingAlerts ? (
              <div className="py-6 text-center">
                <div className="inline-block w-4 h-4 border-2 border-gray-600 border-t-blue-400 rounded-full animate-spin" />
              </div>
            ) : alerts.length > 0 ? (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {alerts.map((alert, i) => (
                  <AlertCard key={alert.id || i} alert={alert} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <ShieldCheck className="w-8 h-8 text-green-400/50 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No active alerts</p>
                <p className="text-xs text-gray-600 mt-1">
                  Sanctions alerts appear here when potential SDN matches are detected
                  during automated screening.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
