import React from 'react';
import { Circle } from 'lucide-react';
import Badge from '../common/Badge';
import { formatDate } from '../../utils/formatters';

/**
 * Registration history timeline for an aircraft.
 *
 * Props:
 * - events: Array<{ date, event_type, n_number, registrant_name, description }>
 */
export default function AircraftTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        No registration history available.
      </div>
    );
  }

  const eventVariant = (type) => {
    const t = (type || '').toLowerCase();
    if (t.includes('new') || t.includes('initial') || t.includes('register')) return 'success';
    if (t.includes('transfer') || t.includes('change')) return 'warning';
    if (t.includes('cancel') || t.includes('revoke') || t.includes('deregister')) return 'danger';
    if (t.includes('renew') || t.includes('update')) return 'info';
    return 'neutral';
  };

  return (
    <div className="relative pl-6">
      {/* Vertical timeline line */}
      <div className="absolute left-[9px] top-2 bottom-2 w-0.5 bg-blue-500/30" />

      <div className="space-y-6">
        {events.map((event, idx) => (
          <div key={idx} className="relative flex gap-4">
            {/* Timeline dot */}
            <div className="absolute -left-6 top-1 z-10">
              <Circle className="w-[18px] h-[18px] text-blue-400 fill-zinc-950 stroke-blue-400" strokeWidth={2.5} />
            </div>

            {/* Event content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="text-xs font-mono text-gray-400">
                  {formatDate(event.date)}
                </span>
                {event.event_type && (
                  <Badge variant={eventVariant(event.event_type)}>
                    {event.event_type}
                  </Badge>
                )}
              </div>
              {event.n_number && (
                <p className="text-sm font-mono text-blue-400">
                  N{event.n_number}
                </p>
              )}
              {event.registrant_name && (
                <p className="text-sm text-gray-300 mt-0.5">
                  {event.registrant_name}
                </p>
              )}
              {event.description && (
                <p className="text-xs text-gray-500 mt-1">
                  {event.description}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
