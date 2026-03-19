import React, { useState } from 'react';
import {
  Eye,
  Plus,
  Trash2,
  RefreshCw,
  Wifi,
  WifiOff,
  PlaneTakeoff,
} from 'lucide-react';
import Badge from '../common/Badge';

export default function TrackingControls({
  watchlist = [],
  onAddAircraft,
  onRemoveAircraft,
  autoRefresh = false,
  onToggleAutoRefresh,
  refreshInterval = 30,
  connectionStatus = 'disconnected',
  positionCount = 0,
  onManualRefresh,
  loading = false,
}) {
  const [input, setInput] = useState('');

  function handleAdd(e) {
    e.preventDefault();
    const cleaned = input.trim().toUpperCase().replace(/^N/, '');
    if (cleaned && onAddAircraft) {
      onAddAircraft(cleaned);
      setInput('');
    }
  }

  return (
    <div className="w-full space-y-4">
      {/* Connection status */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <div className="card-header flex items-center gap-2 mb-0 pb-0 border-0">
            {connectionStatus === 'connected' ? (
              <Wifi className="w-3.5 h-3.5 text-green-400" />
            ) : (
              <WifiOff className="w-3.5 h-3.5 text-gray-500" />
            )}
            Connection
          </div>
          <Badge
            variant={connectionStatus === 'connected' ? 'success' : 'neutral'}
            dot
          >
            {connectionStatus}
          </Badge>
        </div>
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Tracked positions</span>
          <span className="font-mono text-gray-200">{positionCount}</span>
        </div>
      </div>

      {/* Auto-refresh */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <RefreshCw className={`w-3.5 h-3.5 ${autoRefresh ? 'text-blue-400' : ''}`} />
          Auto-Refresh
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            Every {refreshInterval}s
          </span>
          <button
            onClick={onToggleAutoRefresh}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
              autoRefresh ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                autoRefresh ? 'translate-x-4' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        {onManualRefresh && (
          <button
            onClick={onManualRefresh}
            disabled={loading}
            className="mt-3 w-full flex items-center justify-center gap-2 text-xs font-medium px-3 py-2 rounded-lg bg-zinc-800/50 hover:bg-zinc-700/50 text-gray-300 transition-colors border border-zinc-700/30 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Now
          </button>
        )}
      </div>

      {/* Add aircraft */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Plus className="w-3.5 h-3.5" />
          Add Aircraft
        </div>
        <form onSubmit={handleAdd} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="N-Number (e.g. N12345)"
            className="flex-1 bg-zinc-900/50 border border-zinc-700/30 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 font-mono"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Plus className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Watchlist */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Eye className="w-3.5 h-3.5" />
          Watchlist
          <span className="ml-auto text-xxs font-mono text-gray-500">
            {watchlist.length}
          </span>
        </div>
        {watchlist.length > 0 ? (
          <div className="space-y-1 max-h-[300px] overflow-y-auto">
            {watchlist.map((item) => {
              const nNum = typeof item === 'string' ? item : item.n_number || item;
              return (
                <div
                  key={nNum}
                  className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-zinc-800/30 group"
                >
                  <div className="flex items-center gap-2">
                    <PlaneTakeoff className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-sm font-mono text-gray-200">N{nNum}</span>
                  </div>
                  <button
                    onClick={() => onRemoveAircraft && onRemoveAircraft(nNum)}
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-gray-500 text-center py-3">
            No aircraft on watchlist. Add an N-number above to begin tracking.
          </p>
        )}
      </div>
    </div>
  );
}
