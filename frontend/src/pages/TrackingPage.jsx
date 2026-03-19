import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Map, Radar, PlaneTakeoff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { lookupLiveAircraft } from '../api/client';
import FlightMap from '../components/tracking/FlightMap';
import TrackingControls from '../components/tracking/TrackingControls';
import Badge from '../components/common/Badge';

const REFRESH_INTERVAL_MS = 30000;

export default function TrackingPage() {
  const [positions, setPositions] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [lookupResults, setLookupResults] = useState({});
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [loading, setLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const intervalRef = useRef(null);

  const fetchAllWatchlist = useCallback(async () => {
    if (watchlist.length === 0) {
      setPositions([]);
      return;
    }
    setLoading(true);
    try {
      const results = await Promise.allSettled(
        watchlist.map((n) => lookupLiveAircraft(n))
      );

      const newPositions = [];
      const newResults = {};

      results.forEach((result, i) => {
        const nNum = watchlist[i];
        if (result.status === 'fulfilled') {
          const data = result.value.data;
          newResults[nNum] = data;
          if (data.position && data.position.latitude && data.position.longitude) {
            newPositions.push({
              ...data.position,
              n_number: data.n_number,
              manufacturer: data.manufacturer,
              model: data.model,
            });
          }
        } else {
          newResults[nNum] = {
            status: 'error',
            message: result.reason?.response?.data?.detail || 'Lookup failed',
          };
        }
      });

      setPositions(newPositions);
      setLookupResults(newResults);
      setConnectionStatus('connected');
    } catch (err) {
      console.error('[Tracking] Fetch failed', err);
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  }, [watchlist]);

  useEffect(() => {
    if (watchlist.length > 0) {
      fetchAllWatchlist();
    }
  }, [watchlist.length]);

  useEffect(() => {
    if (autoRefresh && watchlist.length > 0) {
      intervalRef.current = setInterval(fetchAllWatchlist, REFRESH_INTERVAL_MS);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh, fetchAllWatchlist]);

  function handleAddAircraft(nNumber) {
    const cleaned = nNumber.trim().toUpperCase().replace(/^N/, '');
    if (!cleaned || watchlist.includes(cleaned)) return;
    setWatchlist((prev) => [...prev, cleaned]);
  }

  function handleRemoveAircraft(nNumber) {
    setWatchlist((prev) => prev.filter((n) => n !== nNumber));
    setLookupResults((prev) => {
      const next = { ...prev };
      delete next[nNumber];
      return next;
    });
    setPositions((prev) => prev.filter((p) => p.n_number !== nNumber));
  }

  return (
    <div className="space-y-4 max-w-full">
      <div>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-zinc-800/50">
            <Radar className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Flight Tracking</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Real-time aircraft position tracking via OpenSky ADS-B
            </p>
          </div>
        </div>
      </div>

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
                  {watchlist.length > 0 ? 'No Aircraft Currently Airborne' : 'No Aircraft in View'}
                </h3>
                <p className="text-sm text-gray-500 max-w-sm mx-auto mb-4">
                  {watchlist.length > 0
                    ? 'The tracked aircraft are not currently broadcasting ADS-B positions. They may be on the ground or outside coverage.'
                    : 'Enter an N-number in the panel to look up a live aircraft position from the OpenSky Network.'}
                </p>
                {watchlist.length === 0 && (
                  <div className="text-xs text-gray-600 space-y-1">
                    <p>1. Enter an N-number (e.g. N144AL)</p>
                    <p>2. FleetPulse queries OpenSky ADS-B network in real-time</p>
                    <p>3. If airborne, the aircraft appears on the map</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Side panel */}
        <div className="w-full lg:w-80 xl:w-96 shrink-0 space-y-4">
          <TrackingControls
            watchlist={watchlist}
            onAddAircraft={handleAddAircraft}
            onRemoveAircraft={handleRemoveAircraft}
            autoRefresh={autoRefresh}
            onToggleAutoRefresh={() => setAutoRefresh((v) => !v)}
            refreshInterval={30}
            connectionStatus={connectionStatus}
            positionCount={positions.length}
            onManualRefresh={fetchAllWatchlist}
            loading={loading}
          />

          {/* Live results */}
          {Object.keys(lookupResults).length > 0 && (
            <div className="card">
              <div className="card-header flex items-center gap-2">
                <PlaneTakeoff className="w-3.5 h-3.5" />
                Lookup Results
              </div>
              <div className="space-y-2">
                {Object.entries(lookupResults).map(([nNum, data]) => (
                  <div
                    key={nNum}
                    className={`rounded-lg p-3 border ${
                      data.status === 'airborne'
                        ? 'border-green-500/30 bg-green-500/5'
                        : data.status === 'on_ground'
                        ? 'border-blue-500/20 bg-blue-500/5'
                        : data.status === 'error'
                        ? 'border-red-500/20 bg-red-500/5'
                        : 'border-zinc-700/30 bg-zinc-800/30'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono text-sm font-semibold text-gray-200">
                        N{nNum}
                      </span>
                      <Badge
                        variant={
                          data.status === 'airborne' ? 'success' :
                          data.status === 'on_ground' ? 'info' :
                          data.status === 'error' ? 'danger' : 'neutral'
                        }
                      >
                        {data.status === 'airborne' ? 'AIRBORNE' :
                         data.status === 'on_ground' ? 'ON GROUND' :
                         data.status === 'not_found' ? 'NO SIGNAL' :
                         data.status === 'error' ? 'ERROR' : data.status}
                      </Badge>
                    </div>
                    {data.manufacturer && (
                      <p className="text-xs text-gray-500">
                        {data.manufacturer} {data.model}
                      </p>
                    )}
                    {data.position && (
                      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                        <div>
                          <span className="text-gray-500">Alt: </span>
                          <span className="font-mono text-gray-300">
                            {data.position.altitude_ft?.toLocaleString() || '--'} ft
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Spd: </span>
                          <span className="font-mono text-gray-300">
                            {data.position.ground_speed_kts || '--'} kts
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Hdg: </span>
                          <span className="font-mono text-gray-300">
                            {data.position.track_deg != null ? Math.round(data.position.track_deg) + '\u00B0' : '--'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">V/S: </span>
                          <span className="font-mono text-gray-300">
                            {data.position.vertical_rate_fpm || '--'} fpm
                          </span>
                        </div>
                      </div>
                    )}
                    {data.message && !data.position && (
                      <p className="text-xs text-gray-500 mt-1">{data.message}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
