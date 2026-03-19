import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlaneTakeoff, Search, ArrowRight } from 'lucide-react';
import { searchAll } from '../api/client';
import DataTable from '../components/common/DataTable';
import Badge from '../components/common/Badge';

export default function AircraftBrowse() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const res = await searchAll(query.trim());
      setResults(res.data.aircraft || []);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }

  const columns = [
    {
      key: 'n_number',
      label: 'N-Number',
      render: (val) => <span className="font-mono text-blue-400">N{val}</span>,
    },
    { key: 'manufacturer', label: 'Manufacturer' },
    { key: 'model', label: 'Model' },
    { key: 'year_mfr', label: 'Year', render: (val) => val || '--' },
    { key: 'registrant_name', label: 'Registrant', render: (val) => val || '--' },
    {
      key: 'registration_status',
      label: 'Status',
      render: (val) => (
        <Badge variant={val === 'Valid' ? 'success' : 'neutral'}>{val || '--'}</Badge>
      ),
    },
  ];

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-zinc-800/50">
          <PlaneTakeoff className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Aircraft Registry</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Search {'>'}310,000 FAA-registered aircraft by N-number, manufacturer, model, or registrant
          </p>
        </div>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by N-number, manufacturer, model, or registrant name..."
            className="w-full bg-zinc-900/50 border border-zinc-700/30 rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          Search
        </button>
      </form>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block w-5 h-5 border-2 border-gray-600 border-t-blue-400 rounded-full animate-spin" />
        </div>
      ) : searched && results.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No aircraft found matching "{query}"</p>
        </div>
      ) : results.length > 0 ? (
        <div className="card">
          <div className="card-header">
            {results.length} result{results.length !== 1 ? 's' : ''}
          </div>
          <DataTable
            columns={columns}
            data={results}
            onRowClick={(row) => navigate(`/aircraft/${row.n_number}`)}
          />
        </div>
      ) : (
        <div className="card text-center py-16">
          <PlaneTakeoff className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
          <p className="text-gray-400 mb-1">Search the FAA Aircraft Registry</p>
          <p className="text-xs text-gray-600">
            Try searching for "Gulfstream", "N100A", "Cessna 172", or a registrant name
          </p>
        </div>
      )}
    </div>
  );
}
