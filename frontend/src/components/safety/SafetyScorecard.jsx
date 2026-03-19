import React from 'react';
import { Shield, Info, Clock } from 'lucide-react';
import ScoreGauge from '../common/ScoreGauge';
import { getScoreLevel } from '../../utils/constants';
import { formatDate } from '../../utils/formatters';

const COMPONENT_LABELS = {
  accident_score: 'Accident History',
  sdr_score: 'Service Difficulty Reports',
  enforcement_score: 'Enforcement Actions',
  fleet_age_score: 'Fleet Age',
  certificate_tenure_score: 'Certificate Tenure',
  ad_compliance_score: 'AD Compliance',
};

function ScoreBar({ label, score }) {
  const level = getScoreLevel(score);
  const normalizedWidth = score != null ? Math.max(score, 2) : 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400 font-medium">{label}</span>
        <span
          className="text-xs font-mono font-bold"
          style={{ color: level.color }}
        >
          {score != null ? Math.round(score) : '--'}
        </span>
      </div>
      <div className="h-2 bg-zinc-800/50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${normalizedWidth}%`,
            backgroundColor: level.color,
          }}
        />
      </div>
    </div>
  );
}

/**
 * Full safety scorecard component.
 *
 * Props:
 * - score: object with overall_score, component scores, entity_name, calculation_date
 */
export default function SafetyScorecard({ score }) {
  if (!score) {
    return (
      <div className="text-center py-10">
        <Shield className="w-10 h-10 text-gray-600 mx-auto mb-3" />
        <p className="text-sm text-gray-400 font-medium mb-1">No safety data calculated yet</p>
        <p className="text-xs text-gray-500 max-w-md mx-auto">
          Safety scoring will be available once sufficient data has been ingested
          and processed for this entity.
        </p>
      </div>
    );
  }

  const overallLevel = getScoreLevel(score.overall_score);

  const components = Object.entries(COMPONENT_LABELS)
    .filter(([key]) => score[key] != null)
    .map(([key, label]) => ({
      key,
      label,
      value: score[key],
    }));

  return (
    <div className="space-y-6">
      {/* Header with entity name */}
      {score.entity_name && (
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-gray-200">
            {score.entity_name}
          </span>
        </div>
      )}

      {/* Overall score gauge */}
      <div className="flex flex-col items-center relative">
        <ScoreGauge
          score={score.overall_score}
          label="Overall Safety Score"
          size={160}
        />
        <div
          className="mt-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border"
          style={{
            color: overallLevel.color,
            borderColor: overallLevel.color + '40',
            backgroundColor: overallLevel.color + '15',
          }}
        >
          {overallLevel.label}
        </div>
      </div>

      {/* Component breakdown */}
      {components.length > 0 && (
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 mb-3">
            <Info className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Component Breakdown
            </span>
          </div>
          <div className="space-y-3">
            {components.map(({ key, label, value }) => (
              <ScoreBar key={key} label={label} score={value} />
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-zinc-800/50">
        <div className="flex items-center gap-1.5 text-gray-600">
          <Clock className="w-3 h-3" />
          <span className="text-xxs font-mono">
            {score.calculation_date
              ? `Calculated ${formatDate(score.calculation_date)}`
              : 'Calculation date unavailable'}
          </span>
        </div>
        {score.methodology_version && (
          <span className="text-xxs text-gray-600 font-mono">
            v{score.methodology_version}
          </span>
        )}
      </div>
    </div>
  );
}
