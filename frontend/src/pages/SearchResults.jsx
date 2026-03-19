import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Building2,
  PlaneTakeoff,
  Building,
  Search,
  ArrowLeft,
  ArrowRight,
} from 'lucide-react';
import { searchAll } from '../api/client';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Badge from '../components/common/Badge';
import { AIRPORT_TYPES } from '../utils/constants';

const CATEGORY_CONFIG = {
  airports: {
    icon: Building2,
    label: 'Airports',
    linkPrefix: '/airports',
    getLink: (item) => `/airports/${item.icao_code || item.iata_code || item.ident}`,
    getTitle: (item) => item.name,
    getSubtitle: (item) => {
      const codes = [item.icao_code, item.iata_code, item.local_code].filter(Boolean).join(' / ');
      const location = [item.municipality, item.iso_region].filter(Boolean).join(', ');
      return `${codes}${location ? ' -- ' + location : ''}`;
    },
    getBadge: (item) => AIRPORT_TYPES[item.type] || item.type,
  },
  aircraft: {
    icon: PlaneTakeoff,
    label: 'Aircraft',
    getLink: (item) => `/aircraft/${item.n_number || item.id}`,
    getTitle: (item) => item.n_number || item.registration || 'Unknown',
    getSubtitle: (item) => [item.manufacturer, item.model].filter(Boolean).join(' '),
    getBadge: (item) => item.type_aircraft || null,
  },
  operators: {
    icon: Building,
    label: 'Operators',
    getLink: (item) => `/operators/${item.cert_number || item.id}`,
    getTitle: (item) => item.name || item.dba_name || 'Unknown',
    getSubtitle: (item) => [item.city, item.state].filter(Boolean).join(', '),
    getBadge: (item) => item.cert_type || null,
  },
};

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!query || query.length < 2) {
      setResults(null);
      return;
    }

    async function doSearch() {
      setLoading(true);
      setError(null);
      try {
        const res = await searchAll(query);
        setResults(res.data);
      } catch (err) {
        setError('Search failed. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    doSearch();
  }, [query]);

  const totalResults = results
    ? Object.values(results).reduce(
        (sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0),
        0
      )
    : 0;

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/" className="text-gray-400 hover:text-gray-200">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-100">Search Results</h1>
          {query && (
            <p className="text-sm text-gray-500 mt-0.5">
              {loading
                ? 'Searching...'
                : `${totalResults} result${totalResults !== 1 ? 's' : ''} for "${query}"`}
            </p>
          )}
        </div>
      </div>

      {loading && <LoadingSpinner message={`Searching for "${query}"...`} />}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* No query */}
      {!query && !loading && (
        <div className="card text-center py-12">
          <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-300 mb-2">Enter a Search Query</h2>
          <p className="text-sm text-gray-500">
            Search for airports by ICAO/IATA code, name, or city.
            Search for aircraft by N-number or operators by name.
          </p>
        </div>
      )}

      {/* No results */}
      {!loading && query && results && totalResults === 0 && (
        <div className="card text-center py-12">
          <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-300 mb-2">No Results Found</h2>
          <p className="text-sm text-gray-500">
            No matches found for "{query}". Try a different search term.
          </p>
        </div>
      )}

      {/* Results by category */}
      {!loading &&
        results &&
        Object.entries(results).map(([category, items]) => {
          if (!Array.isArray(items) || items.length === 0) return null;
          const config = CATEGORY_CONFIG[category];
          if (!config) return null;
          const Icon = config.icon;

          return (
            <div key={category} className="card">
              <div className="card-header flex items-center gap-2">
                <Icon className="w-3.5 h-3.5" />
                {config.label}
                <span className="text-gray-600 font-normal">({items.length})</span>
              </div>
              <div className="divide-y divide-zinc-800/50">
                {items.map((item, idx) => {
                  const badge = config.getBadge(item);
                  return (
                    <Link
                      key={idx}
                      to={config.getLink(item)}
                      className="flex items-center justify-between py-3 px-1 hover:bg-zinc-800/30 rounded transition-colors group"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-gray-200 group-hover:text-blue-400 transition-colors">
                          {config.getTitle(item)}
                        </p>
                        <p className="text-xs text-gray-500 font-mono truncate mt-0.5">
                          {config.getSubtitle(item)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 shrink-0 ml-4">
                        {badge && <Badge variant="neutral">{badge}</Badge>}
                        <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors" />
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
    </div>
  );
}
