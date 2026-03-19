import {
  Plane,
  Building2,
  PlaneTakeoff,
  Building,
  Map,
  Shield,
  AlertTriangle,
  Settings,
} from 'lucide-react';

export const SCORE_COLORS = {
  excellent: '#22c55e',
  good: '#84cc16',
  average: '#f97316',
  belowAverage: '#f97316',
  poor: '#ef4444',
  critical: '#dc2626',
};

export const SCORE_THRESHOLDS = [
  { min: 90, label: 'Excellent', color: SCORE_COLORS.excellent },
  { min: 75, label: 'Good', color: SCORE_COLORS.good },
  { min: 60, label: 'Average', color: SCORE_COLORS.average },
  { min: 40, label: 'Below Average', color: SCORE_COLORS.belowAverage },
  { min: 20, label: 'Poor', color: SCORE_COLORS.poor },
  { min: 0, label: 'Critical', color: SCORE_COLORS.critical },
];

export const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: Plane },
  { path: '/airports', label: 'Airports', icon: Building2 },
  { path: '/aircraft', label: 'Aircraft', icon: PlaneTakeoff },
  { path: '/tracking', label: 'Tracking', icon: Map },
  { path: '/safety', label: 'Safety', icon: Shield },
  { path: '/sanctions', label: 'Sanctions', icon: AlertTriangle },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const AIRPORT_TYPES = {
  large_airport: 'Large Airport',
  medium_airport: 'Medium Airport',
  small_airport: 'Small Airport',
  heliport: 'Heliport',
  seaplane_base: 'Seaplane Base',
  balloonport: 'Balloonport',
  closed: 'Closed',
};

export const RUNWAY_SURFACES = {
  ASP: 'Asphalt',
  CON: 'Concrete',
  GRS: 'Grass',
  GVL: 'Gravel',
  TURF: 'Turf',
  DIRT: 'Dirt',
  WATER: 'Water',
};

export function getScoreLevel(score) {
  if (score == null) return SCORE_THRESHOLDS[SCORE_THRESHOLDS.length - 1];
  for (const threshold of SCORE_THRESHOLDS) {
    if (score >= threshold.min) return threshold;
  }
  return SCORE_THRESHOLDS[SCORE_THRESHOLDS.length - 1];
}
