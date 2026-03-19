import React from 'react';

const VARIANTS = {
  success: 'bg-green-500/15 text-green-400 border-green-500/30',
  warning: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  danger: 'bg-red-500/15 text-red-400 border-red-500/30',
  info: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  neutral: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
};

/**
 * Status badge component.
 *
 * Props:
 * - variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
 * - children: label text
 * - dot: boolean - show colored dot before text
 */
export default function Badge({ variant = 'neutral', children, dot = false }) {
  const classes = VARIANTS[variant] || VARIANTS.neutral;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xxs font-semibold uppercase tracking-wider border ${classes}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            variant === 'success' ? 'bg-green-400' :
            variant === 'warning' ? 'bg-orange-400' :
            variant === 'danger' ? 'bg-red-400' :
            variant === 'info' ? 'bg-blue-400' :
            'bg-gray-400'
          }`}
        />
      )}
      {children}
    </span>
  );
}
