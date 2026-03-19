import React, { useState } from 'react';
import { CheckCircle, ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react';
import Badge from '../common/Badge';
import { formatDate } from '../../utils/formatters';

function injuryVariant(severity) {
  const s = (severity || '').toLowerCase();
  if (s.includes('fatal') || s === 'fatl') return 'danger';
  if (s.includes('serious') || s === 'sers') return 'warning';
  if (s.includes('minor') || s === 'minr') return 'info';
  if (s.includes('none') || s === 'nont') return 'success';
  return 'neutral';
}

function injuryColor(severity) {
  const s = (severity || '').toLowerCase();
  if (s.includes('fatal') || s === 'fatl') return 'text-red-400';
  if (s.includes('serious') || s === 'sers') return 'text-orange-400';
  if (s.includes('minor') || s === 'minr') return 'text-yellow-400';
  if (s.includes('none') || s === 'nont') return 'text-green-400';
  return 'text-gray-400';
}

function AccidentRow({ accident, index }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        onClick={() => setExpanded(!expanded)}
        className={`data-row border-b border-zinc-800/50 cursor-pointer
          ${index % 2 === 0 ? 'bg-zinc-900/30' : 'bg-zinc-950/30'}`}
      >
        <td className="px-3 py-2.5 w-6">
          {accident.probable_cause ? (
            expanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
            )
          ) : (
            <span className="w-3.5 h-3.5" />
          )}
        </td>
        <td className="px-3 py-2.5 font-mono text-gray-200 text-xs whitespace-nowrap">
          {formatDate(accident.event_date || accident.date)}
        </td>
        <td className="px-3 py-2.5 font-mono text-blue-400 text-xs whitespace-nowrap">
          {accident.ntsb_number || accident.ntsb_id || '--'}
        </td>
        <td className="px-3 py-2.5 text-gray-300 text-xs">
          {accident.event_type || accident.type || '--'}
        </td>
        <td className="px-3 py-2.5 text-gray-300 text-xs">
          {[accident.city, accident.state].filter(Boolean).join(', ') ||
            accident.location || '--'}
        </td>
        <td className="px-3 py-2.5 text-gray-300 text-xs whitespace-nowrap">
          {[accident.aircraft_make, accident.aircraft_model].filter(Boolean).join(' ') ||
            accident.aircraft || '--'}
        </td>
        <td className="px-3 py-2.5">
          <span className={`text-xs font-semibold ${injuryColor(accident.highest_injury || accident.injury_severity)}`}>
            {accident.highest_injury || accident.injury_severity || '--'}
          </span>
        </td>
        <td className="px-3 py-2.5 text-gray-300 text-xs">
          {accident.aircraft_damage || accident.damage || '--'}
        </td>
      </tr>
      {expanded && accident.probable_cause && (
        <tr className={index % 2 === 0 ? 'bg-zinc-900/30' : 'bg-zinc-950/30'}>
          <td colSpan={8} className="px-3 py-3">
            <div className="ml-6 p-3 rounded border border-zinc-700 bg-zinc-900/50">
              <p className="text-xxs font-semibold uppercase tracking-wider text-gray-500 mb-1">
                Probable Cause
              </p>
              <p className="text-xs text-gray-300 leading-relaxed">
                {accident.probable_cause}
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

/**
 * NTSB accident list component.
 *
 * Props:
 * - accidents: array of accident records
 */
export default function AccidentList({ accidents = [] }) {
  if (!accidents.length) {
    return (
      <div className="text-center py-10">
        <CheckCircle className="w-10 h-10 text-green-500/60 mx-auto mb-3" />
        <p className="text-sm text-green-400 font-medium mb-1">No accidents on record</p>
        <p className="text-xs text-gray-500 max-w-md mx-auto">
          No NTSB accident or incident reports were found associated with this entity.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          {accidents.length} {accidents.length === 1 ? 'Record' : 'Records'}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-700">
              <th className="px-3 py-2.5 w-6" />
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Date
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                NTSB #
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Type
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Location
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Aircraft
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Injury
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Damage
              </th>
            </tr>
          </thead>
          <tbody>
            {accidents.map((accident, idx) => (
              <AccidentRow
                key={accident.ntsb_number || accident.ntsb_id || idx}
                accident={accident}
                index={idx}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
