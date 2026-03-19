import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, User, Hash } from 'lucide-react';
import Badge from '../common/Badge';

const MATCH_TYPE_LABELS = {
  tail_number: 'Tail Number',
  owner_name: 'Owner Name',
  serial_number: 'Serial Number',
  registrant_name: 'Registrant Name',
  operator_name: 'Operator Name',
};

function ConfidenceBar({ confidence }) {
  const pct = Math.min(Math.max(confidence || 0, 0), 100);
  const color =
    pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-orange-500' : 'bg-yellow-500';
  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xxs mb-1">
        <span className="text-gray-500 uppercase tracking-wider font-semibold">
          Match Confidence
        </span>
        <span className="font-mono text-gray-200">{pct}%</span>
      </div>
      <div className="w-full bg-zinc-900/50 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function MatchCard({ match }) {
  return (
    <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span className="text-sm font-semibold text-red-300">
            {match.sdn_name || match.entity_name || 'SDN Entity'}
          </span>
        </div>
        <Badge variant="danger">
          {MATCH_TYPE_LABELS[match.match_type] || match.match_type || 'Match'}
        </Badge>
      </div>

      {match.sdn_type && (
        <div className="text-xs text-gray-400">
          <span className="text-gray-500">Entity Type: </span>
          {match.sdn_type}
        </div>
      )}

      {match.program && (
        <div className="text-xs text-gray-400">
          <span className="text-gray-500">Program: </span>
          <span className="font-mono">{match.program}</span>
        </div>
      )}

      {match.remarks && (
        <div className="text-xs text-gray-400 border-l-2 border-red-500/30 pl-2">
          {match.remarks}
        </div>
      )}

      <ConfidenceBar confidence={match.confidence || match.score} />
    </div>
  );
}

export default function SanctionsCheck({ result }) {
  if (!result) {
    return (
      <div className="text-center py-8">
        <ShieldCheck className="w-10 h-10 text-gray-600 mx-auto mb-3" />
        <p className="text-sm text-gray-500">
          Enter an N-number above to run a sanctions screening check.
        </p>
      </div>
    );
  }

  const hasMatch = result.has_match || (result.matches && result.matches.length > 0);
  const matches = result.matches || [];

  if (!hasMatch) {
    return (
      <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-6 text-center">
        <ShieldCheck className="w-12 h-12 text-green-400 mx-auto mb-3" />
        <Badge variant="success">CLEAR</Badge>
        <p className="text-sm text-gray-300 mt-3">
          No sanctions matches found. This aircraft and its registrant are not on
          the OFAC Specially Designated Nationals (SDN) list.
        </p>
        {result.checked_at && (
          <p className="text-xxs text-gray-500 mt-2 font-mono">
            Last checked: {result.checked_at}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 flex items-center gap-3">
        <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-red-300">
            Sanctions Match Detected
          </p>
          <p className="text-xs text-red-400/80">
            {matches.length} potential match{matches.length !== 1 ? 'es' : ''} found
            against OFAC SDN list. Review details below.
          </p>
        </div>
      </div>

      {matches.map((match, i) => (
        <MatchCard key={i} match={match} />
      ))}

      {result.checked_at && (
        <p className="text-xxs text-gray-500 font-mono text-right">
          Screened: {result.checked_at}
        </p>
      )}
    </div>
  );
}
