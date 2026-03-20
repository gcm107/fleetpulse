import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Building2,
  PlaneTakeoff,
  Radar,
  MapPin,
  ArrowRight,
} from 'lucide-react';
import { getStats, searchAll } from '../api/client';

export default function Dashboard() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [stats, setStats] = useState(null);
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    getStats()
      .then((res) => setStats(res.data))
      .catch(() => {});
  }, []);

  function handleChange(e) {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!val.trim()) {
      setResults(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await searchAll(val.trim());
        setResults(res.data);
      } catch {
        setResults(null);
      } finally {
        setSearching(false);
      }
    }, 300);
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  }

  function handleResultClick(type, item) {
    setQuery('');
    setResults(null);
    if (type === 'airport') {
      navigate(`/airports/${item.icao_code || item.iata_code}`);
    } else if (type === 'aircraft') {
      navigate(`/aircraft/${item.n_number}`);
    }
  }

  const airports = results?.airports || [];
  const aircraft = results?.aircraft || [];
  const hasResults = airports.length > 0 || aircraft.length > 0;

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-80px)]">
      <div className="w-full max-w-2xl px-4 -mt-20">
        {/* Logo / Title */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-100 tracking-tight">
            FleetPulse
          </h1>
          <p className="text-sm text-gray-500 mt-2">
            Aviation Intelligence Platform
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSubmit} className="relative">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={handleChange}
            placeholder="Search aircraft, airports, tail numbers..."
            autoFocus
            className="w-full bg-zinc-900/80 border border-zinc-700/50 rounded-2xl pl-14 pr-5 py-4 text-base text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
          />
          {searching && (
            <div className="absolute right-5 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-gray-600 border-t-blue-400 rounded-full animate-spin" />
          )}

          {/* Live results dropdown */}
          {hasResults && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-zinc-700/50 rounded-xl shadow-2xl overflow-hidden z-50 max-h-96 overflow-y-auto">
              {airports.length > 0 && (
                <div>
                  <div className="px-4 py-2 bg-zinc-950/50 border-b border-zinc-800">
                    <span className="text-xxs font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
                      <Building2 className="w-3 h-3" />
                      Airports
                    </span>
                  </div>
                  {airports.slice(0, 5).map((item, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleResultClick('airport', item)}
                      className="w-full px-4 py-3 text-left hover:bg-zinc-800/50 flex items-center gap-3 border-b border-zinc-800/30 transition-colors"
                    >
                      <MapPin className="w-4 h-4 text-gray-500 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-gray-200 truncate">{item.name}</div>
                        <div className="text-xs text-gray-500">
                          <span className="font-mono text-blue-400">{item.icao_code}</span>
                          {item.iata_code && <span className="ml-1">/ {item.iata_code}</span>}
                          {item.city && <span className="ml-2">{item.city}, {item.state_province || item.country_code}</span>}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              {aircraft.length > 0 && (
                <div>
                  <div className="px-4 py-2 bg-zinc-950/50 border-b border-zinc-800">
                    <span className="text-xxs font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
                      <PlaneTakeoff className="w-3 h-3" />
                      Aircraft
                    </span>
                  </div>
                  {aircraft.slice(0, 5).map((item, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleResultClick('aircraft', item)}
                      className="w-full px-4 py-3 text-left hover:bg-zinc-800/50 flex items-center gap-3 border-b border-zinc-800/30 transition-colors"
                    >
                      <PlaneTakeoff className="w-4 h-4 text-gray-500 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm text-gray-200">
                          <span className="font-mono text-blue-400">N{item.n_number}</span>
                          <span className="text-gray-500 ml-2">
                            {[item.manufacturer, item.model].filter(Boolean).join(' ')}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500">
                          {item.registrant_name && <span>{item.registrant_name}</span>}
                          {item.year_mfr && <span className="ml-2">({item.year_mfr})</span>}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              <button
                type="submit"
                className="w-full px-4 py-2.5 text-xs text-blue-400 hover:bg-zinc-800/50 flex items-center justify-center gap-1 transition-colors"
              >
                View all results
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </form>

        {/* Example queries */}
        <div className="flex flex-wrap justify-center gap-2 mt-5">
          {['KJFK', 'N100A', 'Gulfstream', 'Cessna 172', 'EGLL', 'Boeing'].map((q) => (
            <button
              key={q}
              onClick={() => { setQuery(q); handleChange({ target: { value: q } }); }}
              className="px-3 py-1.5 rounded-full bg-zinc-800/50 border border-zinc-700/30 text-xs text-gray-500 hover:text-gray-300 hover:border-zinc-600 transition-colors font-mono"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Subtle stats */}
        {stats && (
          <div className="flex justify-center gap-8 mt-12 text-center">
            <div>
              <p className="text-lg font-mono font-semibold text-gray-400">
                {stats.airports ? Number(stats.airports).toLocaleString() : '--'}
              </p>
              <p className="text-xxs uppercase tracking-wider text-gray-600 mt-0.5">Airports</p>
            </div>
            <div className="w-px bg-zinc-800" />
            <div>
              <p className="text-lg font-mono font-semibold text-gray-400">
                {stats.aircraft ? Number(stats.aircraft).toLocaleString() : '--'}
              </p>
              <p className="text-xxs uppercase tracking-wider text-gray-600 mt-0.5">Aircraft</p>
            </div>
            <div className="w-px bg-zinc-800" />
            <div>
              <p className="text-lg font-mono font-semibold text-gray-400">6</p>
              <p className="text-xxs uppercase tracking-wider text-gray-600 mt-0.5">Data Sources</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
