import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingSpinner({ size = 'md', message = 'Loading...' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3">
      <Loader2 className={`${sizeClasses[size]} text-blue-400 animate-spin`} />
      {message && (
        <p className="text-sm text-gray-500 font-mono">{message}</p>
      )}
    </div>
  );
}
