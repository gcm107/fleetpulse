import React from 'react';
import { AlertTriangle, XCircle, Info, X } from 'lucide-react';

const VARIANTS = {
  critical: {
    bg: 'bg-red-500/10 border-red-500/30',
    icon: XCircle,
    iconColor: 'text-red-400',
    textColor: 'text-red-200',
  },
  warning: {
    bg: 'bg-orange-500/10 border-orange-500/30',
    icon: AlertTriangle,
    iconColor: 'text-orange-400',
    textColor: 'text-orange-200',
  },
  info: {
    bg: 'bg-blue-500/10 border-blue-500/30',
    icon: Info,
    iconColor: 'text-blue-400',
    textColor: 'text-blue-200',
  },
};

/**
 * Alert banner for sanctions, warnings, or critical notices.
 *
 * Props:
 * - variant: 'critical' | 'warning' | 'info'
 * - message: string
 * - title?: string
 * - action?: { label: string, onClick: () => void }
 * - onDismiss?: () => void
 */
export default function AlertBanner({
  variant = 'warning',
  message,
  title,
  action,
  onDismiss,
}) {
  const style = VARIANTS[variant] || VARIANTS.warning;
  const Icon = style.icon;

  return (
    <div className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${style.bg}`}>
      <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${style.iconColor}`} />
      <div className="flex-1 min-w-0">
        {title && (
          <div className={`text-sm font-semibold ${style.textColor} mb-0.5`}>
            {title}
          </div>
        )}
        <p className={`text-sm ${style.textColor} opacity-90`}>{message}</p>
      </div>
      {action && (
        <button
          onClick={action.onClick}
          className="shrink-0 text-xs font-medium px-3 py-1.5 rounded bg-white/10 hover:bg-white/20 text-gray-200 transition-colors"
        >
          {action.label}
        </button>
      )}
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="shrink-0 text-gray-500 hover:text-gray-300 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
