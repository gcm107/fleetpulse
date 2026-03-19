import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlaneTakeoff, Search, ChevronDown, Filter } from 'lucide-react';
import { searchAll, getManufacturers, getModels, searchByType } from '../api/client';
import DataTable from '../components/common/DataTable';
import Badge from '../components/common/Badge';

export default function AircraftBrowse() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Type search state
  const [manufacturers, setManufacturers] = useState([]);
  const [models, setModelsState] = useState([]);
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [manufacturerFilter, setManufacturerFilter] = useState('');
  const [typeLoading, setTypeLoading] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(false);

  // Load manufacturers on mount
  useEffect(() => {
    async function fetchManufacturers() {
      try {
        const res = await getManufacturers();
        setManufacturers(res.data.manufacturers || []);
      } catch (err) {
        console.error('Failed to load manufacturers:', err);
      }
    }
    fetchManufacturers();
  }, []);

  // Load models when manufacturer changes
  useEffect(() => {
    if (!selectedManufacturer) {
      setModelsState([]);
      setSelectedModel('');
      return;
    }
    async function fetchModels() {
      setModelsLoading(true);
      setSelectedModel('');
      try {
        const res = await getModels(selectedManufacturer);
        setModelsState(res.data.models || []);
      } catch (err) {
        console.error('Failed to load models:', err);
      } finally {
        setModelsLoading(false);
      }
    }
    fetchModels();
  }, [selectedManufacturer]);

  // Filter manufacturers based on text input
  const filteredManufacturers = useMemo(() => {
    if (!manufacturerFilter.trim()) return manufacturers;
    const lower = manufacturerFilter.toLowerCase();
    return manufacturers.filter((m) => m.toLowerCase().includes(lower));
  }, [manufacturers, manufacturerFilter]);

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

  async function handleTypeSearch() {
    if (!selectedManufacturer) return;
    setTypeLoading(true);
    setSearched(true);
    try {
      const res = await searchByType(
        selectedManufacturer,
        selectedModel || undefined,
        50
      );
      setResults(res.data || []);
    } catch (err) {
      console.error('Type search failed:', err);
    } finally {
      setTypeLoading(false);
    }
  }

  const isLoading = loading || typeLoading;

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
          disabled={!query.trim() || isLoading}
          className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Search className="w-4 h-4" />
          Search
        </button>
      </form>

      {/* Browse by Aircraft Type */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Filter className="w-3.5 h-3.5" />
          Browse by Aircraft Type
        </div>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Manufacturer dropdown with filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Manufacturer
              </label>
              <input
                type="text"
                value={manufacturerFilter}
                onChange={(e) => setManufacturerFilter(e.target.value)}
                placeholder="Filter manufacturers..."
                className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50"
              />
              <select
                value={selectedManufacturer}
                onChange={(e) => {
                  setSelectedManufacturer(e.target.value);
                  setManufacturerFilter('');
                }}
                className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer"
                size={1}
              >
                <option value="">Select Manufacturer</option>
                {filteredManufacturers.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {/* Model dropdown */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Model
              </label>
              <div className="h-[38px]" /> {/* spacer to align with manufacturer filter input */}
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={!selectedManufacturer || modelsLoading}
                className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 appearance-none cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <option value="">
                  {modelsLoading
                    ? 'Loading models...'
                    : !selectedManufacturer
                    ? 'Select a manufacturer first'
                    : 'All Models'}
                </option>
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            type="button"
            onClick={handleTypeSearch}
            disabled={!selectedManufacturer || isLoading}
            className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-5 h-5 border-2 border-gray-600 border-t-blue-400 rounded-full animate-spin" />
        </div>
      ) : searched && results.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No aircraft found</p>
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
