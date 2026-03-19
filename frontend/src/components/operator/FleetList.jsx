import React from 'react';
import DataTable from '../common/DataTable';
import Badge from '../common/Badge';

/**
 * Fleet table for an operator.
 *
 * Props:
 * - fleet: Array<{ n_number, manufacturer, model, year, role, active }>
 * - onAircraftClick: (row) => void
 */
export default function FleetList({ fleet = [], onAircraftClick }) {
  const columns = [
    {
      key: 'n_number',
      label: 'N-Number',
      mono: true,
      render: (val) => (
        <span className="text-blue-400 font-mono font-medium">
          {val ? `N${val}` : '--'}
        </span>
      ),
    },
    {
      key: 'manufacturer',
      label: 'Manufacturer',
    },
    {
      key: 'model',
      label: 'Model',
      mono: true,
    },
    {
      key: 'year',
      label: 'Year',
      mono: true,
      align: 'center',
    },
    {
      key: 'role',
      label: 'Role',
      render: (val) => val || '--',
    },
    {
      key: 'active',
      label: 'Status',
      align: 'center',
      render: (val) =>
        val === true || val === 'active' || val === 'Active' ? (
          <Badge variant="success" dot>Active</Badge>
        ) : val === false || val === 'inactive' || val === 'Inactive' ? (
          <Badge variant="neutral" dot>Inactive</Badge>
        ) : (
          <Badge variant="neutral">{val || '--'}</Badge>
        ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={fleet}
      onRowClick={onAircraftClick}
      emptyMessage="No fleet records available"
    />
  );
}
