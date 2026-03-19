import React from 'react';
import { Trophy, TrendingDown } from 'lucide-react';
import ScoreGauge from '../common/ScoreGauge';
import { getScoreLevel } from '../../utils/constants';

const COMPONENT_KEYS = [
  { key: 'accident_score', label: 'Accident History' },
  { key: 'sdr_score', label: 'Service Difficulty Reports' },
  { key: 'enforcement_score', label: 'Enforcement Actions' },
  { key: 'fleet_age_score', label: 'Fleet Age' },
  { key: 'certificate_tenure_score', label: 'Certificate Tenure' },
  { key: 'ad_compliance_score', label: 'AD Compliance' },
];

function findBestWorst(operators, key) {
  let bestIdx = -1;
  let worstIdx = -1;
  let bestVal = -1;
  let worstVal = 101;

  operators.forEach((op, idx) => {
    const val = op.score?.[key];
    if (val == null) return;
    if (val > bestVal) {
      bestVal = val;
      bestIdx = idx;
    }
    if (val < worstVal) {
      worstVal = val;
      worstIdx = idx;
    }
  });

  // Only highlight if there are at least 2 operators with values
  const validCount = operators.filter((op) => op.score?.[key] != null).length;
  if (validCount < 2) return { bestIdx: -1, worstIdx: -1 };

  // Don't highlight if all are equal
  if (bestVal === worstVal) return { bestIdx: -1, worstIdx: -1 };

  return { bestIdx, worstIdx };
}

function ComparisonBar({ score, isBest, isWorst }) {
  const level = getScoreLevel(score);
  const normalizedWidth = score != null ? Math.max(score, 2) : 0;

  return (
    <div className="relative">
      <div className="flex items-center gap-2 mb-0.5">
        <span
          className="text-xs font-mono font-bold min-w-[2rem] text-right"
          style={{ color: level.color }}
        >
          {score != null ? Math.round(score) : '--'}
        </span>
        {isBest && (
          <Trophy className="w-3 h-3 text-green-400" />
        )}
        {isWorst && (
          <TrendingDown className="w-3 h-3 text-red-400" />
        )}
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
 * Side-by-side operator safety comparison.
 *
 * Props:
 * - operators: array of { name, score: { overall_score, ...component_scores } }
 */
export default function ComparisonView({ operators = [] }) {
  if (!operators.length) {
    return (
      <div className="text-center py-10 text-gray-500 text-sm">
        No operators selected for comparison.
      </div>
    );
  }

  // Determine best/worst for overall and each component
  const overallBW = findBestWorst(operators, 'overall_score');

  return (
    <div className="space-y-6">
      {/* Column headers with gauges */}
      <div
        className="grid gap-4"
        style={{ gridTemplateColumns: `repeat(${operators.length}, minmax(0, 1fr))` }}
      >
        {operators.map((op, idx) => {
          const isBest = idx === overallBW.bestIdx;
          const isWorst = idx === overallBW.worstIdx;

          return (
            <div
              key={op.name || idx}
              className={`flex flex-col items-center p-4 rounded-lg border
                ${isBest ? 'border-green-500/30 bg-green-500/5' :
                  isWorst ? 'border-red-500/30 bg-red-500/5' :
                  'border-zinc-700 bg-zinc-900/30'}`}
            >
              <h3 className="text-sm font-semibold text-gray-200 mb-3 text-center truncate w-full">
                {op.name || 'Unknown Operator'}
              </h3>
              <div className="relative">
                <ScoreGauge
                  score={op.score?.overall_score}
                  label="Overall"
                  size={120}
                />
              </div>
              {isBest && (
                <div className="flex items-center gap-1 mt-2 text-green-400">
                  <Trophy className="w-3 h-3" />
                  <span className="text-xxs font-semibold uppercase tracking-wider">Best Overall</span>
                </div>
              )}
              {isWorst && (
                <div className="flex items-center gap-1 mt-2 text-red-400">
                  <TrendingDown className="w-3 h-3" />
                  <span className="text-xxs font-semibold uppercase tracking-wider">Lowest Overall</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Component comparison rows */}
      <div className="space-y-4">
        {COMPONENT_KEYS.map(({ key, label }) => {
          const { bestIdx, worstIdx } = findBestWorst(operators, key);
          // Only show components where at least one operator has data
          const hasData = operators.some((op) => op.score?.[key] != null);
          if (!hasData) return null;

          return (
            <div key={key}>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                {label}
              </p>
              <div
                className="grid gap-4"
                style={{ gridTemplateColumns: `repeat(${operators.length}, minmax(0, 1fr))` }}
              >
                {operators.map((op, idx) => (
                  <ComparisonBar
                    key={op.name || idx}
                    score={op.score?.[key]}
                    isBest={idx === bestIdx}
                    isWorst={idx === worstIdx}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
