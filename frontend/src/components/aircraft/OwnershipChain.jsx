import React from 'react';
import { User, MapPin, Calendar, ArrowDown } from 'lucide-react';
import Badge from '../common/Badge';
import { formatDate } from '../../utils/formatters';

/**
 * Ownership chain display for an aircraft.
 *
 * Props:
 * - records: Array<{ owner_name, owner_type, city, state, effective_date, is_current }>
 */
export default function OwnershipChain({ records = [] }) {
  if (!records.length) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No ownership records available.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {records.map((record, idx) => (
        <div key={idx}>
          <div
            className={`rounded-lg border p-4 ${
              record.is_current
                ? 'bg-blue-500/5 border-blue-500/30'
                : 'bg-zinc-900/50 border-zinc-800/50'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <User className="w-4 h-4 text-gray-400 shrink-0" />
                  <span className="text-sm font-medium text-gray-200 truncate">
                    {record.owner_name || 'Unknown Owner'}
                  </span>
                  {record.is_current && (
                    <Badge variant="success" dot>Current</Badge>
                  )}
                </div>

                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                  {record.owner_type && (
                    <span className="flex items-center gap-1">
                      <span className="text-gray-600">Type:</span>
                      <span className="text-gray-400">{record.owner_type}</span>
                    </span>
                  )}
                  {(record.city || record.state) && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-gray-600" />
                      <span className="text-gray-400">
                        {[record.city, record.state].filter(Boolean).join(', ')}
                      </span>
                    </span>
                  )}
                  {record.effective_date && (
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-gray-600" />
                      <span className="font-mono text-gray-400">
                        {formatDate(record.effective_date)}
                      </span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Arrow between cards */}
          {idx < records.length - 1 && (
            <div className="flex justify-center py-1">
              <ArrowDown className="w-4 h-4 text-gray-600" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
