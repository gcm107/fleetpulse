import React, { useEffect, useState } from 'react';
import { getScoreLevel } from '../../utils/constants';

/**
 * SVG radial gauge showing a score from 0-100.
 *
 * Props:
 * - score: number (0-100)
 * - label: string
 * - size: number (px, default 120)
 */
export default function ScoreGauge({ score, label, size = 120 }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const level = getScoreLevel(score);

  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const strokeWidth = 8;
  const center = 50;

  // Animate from 0 to the target arc length (270 degrees = 3/4 of circle)
  const arcFraction = 0.75; // 270 degrees
  const arcLength = circumference * arcFraction;
  const normalizedScore = score != null ? Math.min(Math.max(score, 0), 100) : 0;
  const filledLength = (normalizedScore / 100) * arcLength;
  const dashOffset = arcLength - (animatedScore / 100) * arcLength;

  useEffect(() => {
    if (score == null) return;
    const target = Math.min(Math.max(score, 0), 100);
    let start = 0;
    const duration = 800;
    const startTime = performance.now();

    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * target));
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    requestAnimationFrame(animate);
  }, [score]);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        className="transform -rotate-[135deg]"
      >
        {/* Background arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#27272a"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={level.color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      {/* Score text overlay */}
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: size, height: size }}
      >
        <span
          className="font-mono font-bold text-gray-100"
          style={{ fontSize: size * 0.22, color: level.color }}
        >
          {score != null ? animatedScore : '--'}
        </span>
        <span
          className="text-gray-500 uppercase tracking-wider font-semibold"
          style={{ fontSize: size * 0.08 }}
        >
          {level.label}
        </span>
      </div>
      {label && (
        <span className="text-xs text-gray-400 font-medium -mt-2">{label}</span>
      )}
    </div>
  );
}
