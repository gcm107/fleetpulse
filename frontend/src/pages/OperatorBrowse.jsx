import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building, Search } from 'lucide-react';
import { searchOperators } from '../api/client';
import DataTable from '../components/common/DataTable';
import Badge from '../components/common/Badge';

export default function OperatorBrowse() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    // Load all operators on mount
    async function loadAll() {
      setLoading(true);
      try {
        const res = await searchOperators('', '');
        setResults(res.data || []);
      } catch (err) {
        console.error('Failed to load operators:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAll();
  }, []);

  async function handleSearch(e) {
    e.preventDefault();
    setLoading(true);
    setSearched(true);
    try {
      const res = await searchOperators(query.trim(), stateFilter.trim());
      setResults(res.data || []);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  }

  const statusVariant = (s) => {
    if (s === 'active') return 'success';
    if (s === 'suspended') return 'warning';
    if (s === 'revoked') return 'danger';
    return 'neutral';
  };

  const columns = [
    { key: 'holder_name', label: 'Operator Name' },
    {
      key: 'certificate_number',
      label: 'Certificate',
      render: (val) => <span className="font-mono text-blue-400">{val}</span>,
    },
    {
      key: 'certificate_type',
      label: 'Type',
      render: (val) => <Badge variant="info">{val?.replace('part_', 'Part ') || '--'}</Badge>,
    },
    { key: 'city', label: 'City', render: (val) => val || '--' },
    { key: 'state', label: 'State', render: (val) => val || '--' },
    {
      key: 'certificate_status',
      label: 'Status',
      render: (val) => <Badge variant={statusVariant(val)}>{val || '--'}</Badge>,
    },
  ];

  return (
    <div className="max-w-6xl space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-zinc-800/50">
          <Building className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Operators</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Part 91/135/121 certificate holders and air carriers
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
            placeholder="Search by name, DBA, or certificate number..."
            className="w-full bg-zinc-900/50 border border-zinc-700/30 rounded-lg pl-10 pr-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50"
          />
        </div>
        <input
          type="text"
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          placeholder="State"
          className="w-20 bg-zinc-900/50 border border-zinc-700/30 rounded-lg px-3 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 font-mono text-center"
          maxLength={2}
        />
        <button
          type="submit"
          disabled={loading}
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
      ) : results.length === 0 && searched ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No operators found</p>
        </div>
      ) : results.length > 0 ? (
        <div className="card">
          <div className="card-header">
            {results.length} operator{results.length !== 1 ? 's' : ''}
          </div>
          <DataTable
            columns={columns}
            data={results}
            onRowClick={(row) => navigate(`/operators/${row.certificate_number}`)}
          />
        </div>
      ) : null}
    </div>
  );
}
