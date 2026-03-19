import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

/**
 * Sortable, dark-themed data table.
 *
 * Props:
 * - columns: Array<{ key, label, sortable?, render?, align?, mono? }>
 * - data: Array<object>
 * - onRowClick?: (row) => void
 * - emptyMessage?: string
 */
export default function DataTable({
  columns = [],
  data = [],
  onRowClick,
  emptyMessage = 'No data available',
}) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const cmp = String(aVal).localeCompare(String(bVal));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir]);

  if (!data.length) {
    return (
      <div className="text-center py-8 text-gray-500 text-sm">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-zinc-700">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-3 py-2.5 text-left text-xxs font-semibold uppercase tracking-wider text-gray-500
                  ${col.sortable !== false ? 'cursor-pointer hover:text-gray-300 select-none' : ''}
                  ${col.align === 'right' ? 'text-right' : ''}
                  ${col.align === 'center' ? 'text-center' : ''}`}
                onClick={() => col.sortable !== false && handleSort(col.key)}
              >
                <span className="inline-flex items-center gap-1">
                  {col.label}
                  {col.sortable !== false && (
                    <span className="text-gray-600">
                      {sortKey === col.key ? (
                        sortDir === 'asc' ? (
                          <ChevronUp className="w-3 h-3" />
                        ) : (
                          <ChevronDown className="w-3 h-3" />
                        )
                      ) : (
                        <ChevronsUpDown className="w-3 h-3" />
                      )}
                    </span>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              onClick={() => onRowClick?.(row)}
              className={`data-row border-b border-zinc-800/50
                ${rowIdx % 2 === 0 ? 'bg-zinc-900/30' : 'bg-zinc-950/30'}
                ${onRowClick ? 'cursor-pointer' : ''}`}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`px-3 py-2.5
                    ${col.mono ? 'font-mono text-gray-200' : 'text-gray-300'}
                    ${col.align === 'right' ? 'text-right' : ''}
                    ${col.align === 'center' ? 'text-center' : ''}`}
                >
                  {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '--')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
