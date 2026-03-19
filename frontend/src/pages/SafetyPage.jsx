import React, { useState, useCallback } from 'react';
import {
  Shield,
  Search,
  X,
  BarChart3,
  Info,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { searchOperators, getSafetyComparison } from '../api/client';
import ComparisonView from '../components/safety/ComparisonView';
import AccidentList from '../components/safety/AccidentList';
import { SCORE_THRESHOLDS } from '../utils/constants';

const MAX_OPERATORS = 4;

// Placeholder recent accidents for display
const PLACEHOLDER_ACCIDENTS = [
  {
    ntsb_number: 'ERA25FA001',
    event_date: '2025-12-15',
    event_type: 'Accident',
    city: 'Fort Lauderdale',
    state: 'FL',
    aircraft_make: 'Cessna',
    aircraft_model: '172S',
    highest_injury: 'None',
    aircraft_damage: 'Substantial',
    probable_cause: 'The pilot\'s failure to maintain adequate airspeed during the approach, which resulted in an aerodynamic stall.',
  },
  {
    ntsb_number: 'CEN25IA002',
    event_date: '2025-11-28',
    event_type: 'Incident',
    city: 'Dallas',
    state: 'TX',
    aircraft_make: 'Boeing',
    aircraft_model: '737-800',
    highest_injury: 'None',
    aircraft_damage: 'Minor',
    probable_cause: null,
  },
  {
    ntsb_number: 'WPR25FA003',
    event_date: '2025-11-10',
    event_type: 'Accident',
    city: 'Van Nuys',
    state: 'CA',
    aircraft_make: 'Piper',
    aircraft_model: 'PA-28-181',
    highest_injury: 'Serious',
    aircraft_damage: 'Destroyed',
    probable_cause: 'The pilot\'s decision to continue VFR flight into instrument meteorological conditions.',
  },
];

function OperatorChip({ name, onRemove }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/15 text-blue-400 border border-blue-500/30 text-xs font-semibold">
      {name}
      <button
        onClick={onRemove}
        className="hover:text-blue-200 transition-colors"
        aria-label={`Remove ${name}`}
      >
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}

export default function SafetyPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedOperators, setSelectedOperators] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);

  const handleSearch = useCallback(async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    setSearching(true);
    try {
      const res = await searchOperators(query);
      const ops = Array.isArray(res.data) ? res.data : res.data?.operators || res.data?.results || [];
      setSearchResults(ops.slice(0, 10));
      setShowDropdown(true);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const addOperator = (operator) => {
    const id = operator.cert_number || operator.id;
    const name = operator.name || operator.dba_name || `Operator ${id}`;
    if (selectedOperators.length >= MAX_OPERATORS) return;
    if (selectedOperators.some((o) => o.id === id)) return;
    setSelectedOperators((prev) => [...prev, { id, name }]);
    setSearchQuery('');
    setSearchResults([]);
    setShowDropdown(false);
  };

  const removeOperator = (id) => {
    setSelectedOperators((prev) => prev.filter((o) => o.id !== id));
    if (comparisonData) {
      setComparisonData(null);
    }
  };

  const handleCompare = async () => {
    if (selectedOperators.length < 1) return;
    setComparing(true);
    setCompareError(null);
    try {
      const ids = selectedOperators.map((o) => o.id);
      const res = await getSafetyComparison(ids);
      const data = res.data;

      // Map response to ComparisonView format
      const operators = Array.isArray(data)
        ? data.map((d) => ({
            name: d.entity_name || d.name || 'Unknown',
            score: d,
          }))
        : data?.operators || data?.comparisons || [];

      // Fallback: if API returns nothing usable, use selected names with null scores
      if (!operators.length) {
        setComparisonData(
          selectedOperators.map((o) => ({ name: o.name, score: null }))
        );
      } else {
        setComparisonData(operators);
      }
    } catch (err) {
      setCompareError(
        err.response?.data?.detail || 'Failed to load comparison data. The safety comparison API may not be available yet.'
      );
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Safety Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">
          Compare operator safety scores, review accident histories, and analyze enforcement actions.
        </p>
      </div>

      {/* Operator comparison section */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <BarChart3 className="w-3.5 h-3.5" />
          Operator Safety Comparison
        </div>

        <div className="space-y-4">
          {/* Search input */}
          <div className="relative">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                  onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                  placeholder="Search operators by name..."
                  disabled={selectedOperators.length >= MAX_OPERATORS}
                  className="w-full pl-10 pr-4 py-2.5 bg-zinc-800/50 border border-zinc-700 rounded-lg
                    text-sm text-gray-200 placeholder-gray-600
                    focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/25
                    disabled:opacity-50 disabled:cursor-not-allowed"
                />
                {searching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 animate-spin" />
                )}
              </div>
              <button
                onClick={handleCompare}
                disabled={selectedOperators.length < 1 || comparing}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500
                  text-white text-sm font-semibold rounded-lg transition-colors
                  disabled:cursor-not-allowed flex items-center gap-2"
              >
                {comparing && <Loader2 className="w-4 h-4 animate-spin" />}
                Compare
              </button>
            </div>

            {/* Search dropdown */}
            {showDropdown && searchResults.length > 0 && (
              <div className="absolute z-20 top-full mt-1 w-full bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
                {searchResults.map((op) => {
                  const id = op.cert_number || op.id;
                  const isSelected = selectedOperators.some((o) => o.id === id);
                  return (
                    <button
                      key={id}
                      onClick={() => addOperator(op)}
                      disabled={isSelected}
                      className={`w-full text-left px-4 py-2.5 text-sm flex items-center justify-between
                        border-b border-zinc-800/50 last:border-b-0 transition-colors
                        ${isSelected
                          ? 'text-gray-600 cursor-not-allowed'
                          : 'text-gray-300 hover:bg-zinc-800/50 hover:text-gray-100 cursor-pointer'}`}
                    >
                      <span>{op.name || op.dba_name || 'Unknown'}</span>
                      <span className="text-xxs font-mono text-gray-600">
                        {id}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Selected operators chips */}
          {selectedOperators.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedOperators.map((op) => (
                <OperatorChip
                  key={op.id}
                  name={op.name}
                  onRemove={() => removeOperator(op.id)}
                />
              ))}
              <span className="text-xxs text-gray-600 self-center ml-1">
                {selectedOperators.length}/{MAX_OPERATORS} operators
              </span>
            </div>
          )}

          {/* Error message */}
          {compareError && (
            <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
              <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
              <p className="text-xs text-red-400">{compareError}</p>
            </div>
          )}

          {/* Comparison results */}
          {comparisonData && (
            <div className="pt-2">
              <ComparisonView operators={comparisonData} />
            </div>
          )}
        </div>
      </div>

      {/* Recent NTSB Accidents */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5" />
          Recent NTSB Reports
          <span className="text-gray-600 font-normal text-xs">(sample data)</span>
        </div>
        <AccidentList accidents={PLACEHOLDER_ACCIDENTS} />
      </div>

      {/* Scoring Methodology */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Info className="w-3.5 h-3.5" />
          Scoring Methodology
        </div>
        <div className="space-y-4">
          <p className="text-sm text-gray-400 leading-relaxed">
            FleetPulse safety scores aggregate multiple data sources into a
            composite 0-100 rating. Each operator and aircraft is evaluated
            across several weighted components including accident history,
            service difficulty reports (SDRs), FAA enforcement actions, fleet
            age, certificate tenure, and airworthiness directive (AD) compliance.
          </p>
          <p className="text-sm text-gray-400 leading-relaxed">
            Scores are recalculated periodically as new data becomes available
            from the NTSB, FAA, and other federal sources. The methodology
            version is displayed on each scorecard for transparency.
          </p>

          {/* Score interpretation guide */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
              Score Interpretation Guide
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-700">
                    <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                      Range
                    </th>
                    <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                      Rating
                    </th>
                    <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                      Interpretation
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { range: '90 - 100', label: 'Excellent', color: '#22c55e', desc: 'Outstanding safety record with minimal risk indicators across all categories.' },
                    { range: '75 - 89', label: 'Good', color: '#84cc16', desc: 'Strong safety profile with minor areas for monitoring.' },
                    { range: '60 - 74', label: 'Average', color: '#f97316', desc: 'Acceptable safety record with some areas requiring attention.' },
                    { range: '40 - 59', label: 'Below Average', color: '#f97316', desc: 'Elevated risk indicators present. Multiple areas need improvement.' },
                    { range: '20 - 39', label: 'Poor', color: '#ef4444', desc: 'Significant safety concerns identified. Heightened oversight recommended.' },
                    { range: '0 - 19', label: 'Critical', color: '#dc2626', desc: 'Severe safety deficiencies detected. Immediate review warranted.' },
                  ].map((row) => (
                    <tr
                      key={row.range}
                      className="border-b border-zinc-800/50"
                    >
                      <td className="px-3 py-2.5 font-mono text-gray-200 text-xs whitespace-nowrap">
                        {row.range}
                      </td>
                      <td className="px-3 py-2.5">
                        <span
                          className="text-xs font-bold uppercase tracking-wider"
                          style={{ color: row.color }}
                        >
                          {row.label}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-gray-400 text-xs">
                        {row.desc}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Component descriptions */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
              Score Components
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { name: 'Accident History', desc: 'NTSB accident and incident records weighted by severity and recency.' },
                { name: 'Service Difficulty Reports', desc: 'FAA SDR filings indicating mechanical issues and maintenance concerns.' },
                { name: 'Enforcement Actions', desc: 'FAA enforcement actions including violations, civil penalties, and certificate actions.' },
                { name: 'Fleet Age', desc: 'Average age of operated aircraft weighted by type and maintenance status.' },
                { name: 'Certificate Tenure', desc: 'Length of operating certificate history and regulatory continuity.' },
                { name: 'AD Compliance', desc: 'Airworthiness directive compliance rate and timeliness of implementation.' },
              ].map((comp) => (
                <div
                  key={comp.name}
                  className="p-3 rounded border border-zinc-800/50 bg-zinc-900/20"
                >
                  <p className="text-xs font-semibold text-gray-300 mb-1">{comp.name}</p>
                  <p className="text-xxs text-gray-500 leading-relaxed">{comp.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
