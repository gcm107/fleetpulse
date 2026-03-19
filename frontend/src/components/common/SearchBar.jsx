import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Building2, PlaneTakeoff, Building, Loader2 } from 'lucide-react';
import { searchAll } from '../../api/client';

const CATEGORY_ICONS = {
  airports: Building2,
  aircraft: PlaneTakeoff,
  operators: Building,
};

const CATEGORY_LABELS = {
  airports: 'Airports',
  aircraft: 'Aircraft',
  operators: 'Operators',
};

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceRef = useRef(null);
  const navigate = useNavigate();

  const doSearch = useCallback(async (q) => {
    if (!q || q.length < 2) {
      setResults(null);
      setIsOpen(false);
      return;
    }
    setLoading(true);
    try {
      const res = await searchAll(q);
      setResults(res.data);
      setIsOpen(true);
    } catch (err) {
      console.error('Search failed:', err);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleChange = (e) => {
    const val = e.target.value;
    setQuery(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(val), 300);
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
    if (e.key === 'Enter' && query.length >= 2) {
      setIsOpen(false);
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleResultClick = (category, item) => {
    setIsOpen(false);
    setQuery('');
    if (category === 'airports') {
      const code = item.icao_code || item.iata_code || item.ident;
      navigate(`/airports/${code}`);
    } else if (category === 'aircraft') {
      navigate(`/aircraft/${item.n_number || item.id}`);
    } else if (category === 'operators') {
      navigate(`/operators/${item.cert_number || item.id}`);
    }
  };

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target) &&
        !inputRef.current?.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Cleanup debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const hasResults = results && Object.values(results).some(
    (arr) => Array.isArray(arr) && arr.length > 0
  );

  return (
    <div className="relative w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (hasResults) setIsOpen(true); }}
          placeholder="Search airports, aircraft, operators..."
          className="input-dark w-full pl-10 pr-10 py-2 text-sm"
        />
        {loading && (
          <Loader2 className="absolute right-8 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 animate-spin" />
        )}
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-1 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl overflow-hidden z-50 max-h-96 overflow-y-auto"
        >
          {hasResults ? (
            Object.entries(results).map(([category, items]) => {
              if (!Array.isArray(items) || items.length === 0) return null;
              const Icon = CATEGORY_ICONS[category] || Building2;
              return (
                <div key={category}>
                  <div className="px-3 py-2 bg-zinc-950/50 border-b border-zinc-800">
                    <span className="text-xxs font-semibold uppercase tracking-wider text-gray-500 flex items-center gap-2">
                      <Icon className="w-3 h-3" />
                      {CATEGORY_LABELS[category] || category}
                    </span>
                  </div>
                  {items.slice(0, 5).map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleResultClick(category, item)}
                      className="w-full px-3 py-2.5 text-left hover:bg-zinc-800/50 flex items-center gap-3 border-b border-zinc-800/50 transition-colors"
                    >
                      <Icon className="w-4 h-4 text-gray-500 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-sm text-gray-200 truncate">
                          {item.name || item.n_number || item.cert_number || 'Unknown'}
                        </div>
                        {item.icao_code && (
                          <span className="text-xs font-mono text-blue-400">
                            {item.icao_code}
                            {item.iata_code ? ` / ${item.iata_code}` : ''}
                          </span>
                        )}
                        {item.municipality && (
                          <span className="text-xs text-gray-500 ml-2">
                            {item.municipality}, {item.iso_region}
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              );
            })
          ) : (
            <div className="px-4 py-6 text-center text-sm text-gray-500">
              No results found for "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}
