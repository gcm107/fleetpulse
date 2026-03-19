import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Map, Radar } from 'lucide-react';
import { getLiveTracking, addToWatchlist, removeFromWatchlist } from '../api/client';
import FlightMap from '../components/tracking/FlightMap';
import TrackingControls from '../components/tracking/TrackingControls';

const REFRESH_INTERVAL_MS = 30000;

export default function TrackingPage() {
  const [positions, setPositions] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const intervalRef = useRef(null);

  const fetchTracking = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getLiveTracking();
      const data = res.data;
      setPositions(data?.positions || data?.aircraft || (Array.isArray(data) ? data : []));
      setWatchlist(data?.watchlist || watchlist);
      setConnectionStatus('connected');
    } catch (err) {
      console.error('[Tracking] Fetch failed', err);
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTracking();
  }, [fetchTracking]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchTracking, REFRESH_INTERVAL_MS);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh, fetchTracking]);

  async function handleAddAircraft(nNumber) {
    try {
      await addToWatchlist(nNumber);
      setWatchlist((prev) => {
        if (prev.includes(nNumber)) return prev;
        return [...prev, nNumber];
      });
      fetchTracking();
    } catch (err) {
      console.error('[Tracking] Failed to add aircraft', err);
    }
  }

  async function handleRemoveAircraft(nNumber) {
    try {
      await removeFromWatchlist(nNumber);
      setWatchlist((prev) => prev.filter((n) => n !== nNumber));
    } catch (err) {
      console.error('[Tracking] Failed to remove aircraft', err);
    }
  }

  return (
    <div className="space-y-4 max-w-full">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-zinc-800/50">
            <Radar className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Flight Tracking</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Real-time aircraft position tracking via ADS-B data
            </p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col lg:flex-row gap-4">
        {/* Map area */}
        <div className="flex-1 min-h-[500px] lg:min-h-[600px]">
          {positions.length > 0 ? (
            <FlightMap positions={positions} />
          ) : (
            <div className="w-full h-full min-h-[500px] rounded-lg border border-zinc-800/50 bg-zinc-900/30 flex items-center justify-center">
              <div className="text-center px-6">
                <div className="flex justify-center mb-4">
                  <div className="p-4 rounded-xl bg-zinc-800/30">
                    <Map className="w-12 h-12 text-gray-600" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-gray-300 mb-2">
                  No Aircraft in View
                </h3>
                <p className="text-sm text-gray-500 max-w-sm mx-auto mb-4">
                  Add aircraft to your watchlist using the controls panel.
                  Tracked aircraft will appear on the map in real time.
                </p>
                <div className="text-xs text-gray-600 space-y-1">
                  <p>1. Enter an N-number in the Add Aircraft field</p>
                  <p>2. Enable auto-refresh for continuous updates</p>
                  <p>3. Aircraft positions update every 30 seconds</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Side panel */}
        <div className="w-full lg:w-72 xl:w-80 shrink-0">
          <TrackingControls
            watchlist={watchlist}
            onAddAircraft={handleAddAircraft}
            onRemoveAircraft={handleRemoveAircraft}
            autoRefresh={autoRefresh}
            onToggleAutoRefresh={() => setAutoRefresh((v) => !v)}
            refreshInterval={30}
            connectionStatus={connectionStatus}
            positionCount={positions.length}
            onManualRefresh={fetchTracking}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}
