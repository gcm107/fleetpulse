import { getScoreLevel } from './constants';

/**
 * Format decimal degrees to DMS notation.
 * @param {number} deg - Decimal degrees
 * @param {'lat'|'lon'} type - Coordinate type
 * @returns {string} e.g. "40 38'23"N"
 */
export function formatCoordinate(deg, type) {
  if (deg == null) return '--';
  const abs = Math.abs(deg);
  const d = Math.floor(abs);
  const minFloat = (abs - d) * 60;
  const m = Math.floor(minFloat);
  const s = Math.round((minFloat - m) * 60);

  let dir;
  if (type === 'lat') {
    dir = deg >= 0 ? 'N' : 'S';
  } else {
    dir = deg >= 0 ? 'E' : 'W';
  }

  return `${d}\u00B0${String(m).padStart(2, '0')}'${String(s).padStart(2, '0')}"${dir}`;
}

/**
 * Format elevation in feet.
 */
export function formatElevation(ft) {
  if (ft == null) return '--';
  return `${Number(ft).toLocaleString()} ft`;
}

/**
 * Get color for a score value.
 */
export function formatScore(score) {
  const level = getScoreLevel(score);
  return {
    color: level.color,
    label: level.label,
    value: score != null ? Math.round(score) : '--',
  };
}

/**
 * Format ISO date string to localized date.
 */
export function formatDate(dateStr) {
  if (!dateStr) return '--';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format ISO date to date + time.
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '--';
  try {
    const d = new Date(dateStr);
    return d.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format radio frequency in MHz.
 */
export function formatFrequency(mhz) {
  if (mhz == null) return '--';
  return Number(mhz).toFixed(3);
}

/**
 * Format runway length in feet.
 */
export function formatRunwayLength(ft) {
  if (ft == null) return '--';
  return `${Number(ft).toLocaleString()} ft`;
}

/**
 * Format a number with commas.
 */
export function formatNumber(n) {
  if (n == null) return '--';
  return Number(n).toLocaleString();
}

/**
 * Truncate text with ellipsis.
 */
export function truncate(str, maxLen = 50) {
  if (!str) return '';
  return str.length > maxLen ? str.slice(0, maxLen) + '...' : str;
}

/**
 * Calculate relative time (e.g. "3 hours ago").
 */
export function timeAgo(dateStr) {
  if (!dateStr) return '--';
  try {
    const now = new Date();
    const then = new Date(dateStr);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(dateStr);
  } catch {
    return dateStr;
  }
}
