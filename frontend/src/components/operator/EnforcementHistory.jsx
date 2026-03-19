import React from 'react';
import { Gavel, Scale } from 'lucide-react';
import Badge from '../common/Badge';
import { formatDate } from '../../utils/formatters';

function actionTypeBadgeVariant(type) {
  const t = (type || '').toLowerCase();
  if (t.includes('revocation') || t.includes('emergency')) return 'danger';
  if (t.includes('suspension') || t.includes('cease')) return 'warning';
  if (t.includes('civil penalty') || t.includes('fine')) return 'warning';
  if (t.includes('warning') || t.includes('letter')) return 'info';
  if (t.includes('consent') || t.includes('settlement')) return 'neutral';
  if (t.includes('certificate action')) return 'danger';
  return 'neutral';
}

function formatCurrency(amount) {
  if (amount == null || amount === '') return '--';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return amount;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Enforcement actions history table.
 *
 * Props:
 * - actions: array of enforcement action records
 */
export default function EnforcementHistory({ actions = [] }) {
  if (!actions.length) {
    return (
      <div className="text-center py-10">
        <Scale className="w-10 h-10 text-gray-600 mx-auto mb-3" />
        <p className="text-sm text-gray-400 font-medium mb-1">No enforcement actions on record</p>
        <p className="text-xs text-gray-500 max-w-md mx-auto">
          No FAA enforcement actions were found for this entity.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <Gavel className="w-3.5 h-3.5 text-orange-400" />
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          {actions.length} {actions.length === 1 ? 'Action' : 'Actions'}
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-700">
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Date
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Type
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Respondent
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Description
              </th>
              <th className="px-3 py-2.5 text-right text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Penalty
              </th>
              <th className="px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500">
                Disposition
              </th>
            </tr>
          </thead>
          <tbody>
            {actions.map((action, idx) => (
              <tr
                key={action.case_number || action.id || idx}
                className={`data-row border-b border-zinc-800/50
                  ${idx % 2 === 0 ? 'bg-zinc-900/30' : 'bg-zinc-950/30'}`}
              >
                <td className="px-3 py-2.5 font-mono text-gray-200 text-xs whitespace-nowrap">
                  {formatDate(action.action_date || action.date)}
                </td>
                <td className="px-3 py-2.5">
                  <Badge variant={actionTypeBadgeVariant(action.action_type || action.type)}>
                    {action.action_type || action.type || '--'}
                  </Badge>
                </td>
                <td className="px-3 py-2.5 text-gray-300 text-xs">
                  {action.respondent || action.respondent_name || '--'}
                </td>
                <td className="px-3 py-2.5 text-gray-300 text-xs max-w-xs">
                  <span className="line-clamp-2">
                    {action.description || action.violation || '--'}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right font-mono text-orange-400 text-xs whitespace-nowrap">
                  {formatCurrency(action.penalty_amount || action.penalty)}
                </td>
                <td className="px-3 py-2.5 text-gray-300 text-xs">
                  {action.disposition || action.status || '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
