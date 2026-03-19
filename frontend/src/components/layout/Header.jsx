import React from 'react';
import { Activity } from 'lucide-react';
import SearchBar from '../common/SearchBar';

export default function Header() {
  return (
    <header className="h-14 bg-zinc-900/80 backdrop-blur-sm border-b border-zinc-800 flex items-center justify-between px-6 sticky top-0 z-30">
      {/* Left: breadcrumb area */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-xs font-mono text-gray-500 uppercase tracking-wider hidden lg:block">
          Aviation Intelligence Platform
        </span>
      </div>

      {/* Center: search */}
      <div className="flex-1 max-w-xl mx-4">
        <SearchBar />
      </div>

      {/* Right: status */}
      <div className="flex items-center gap-4 shrink-0">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Activity className="w-3.5 h-3.5 text-green-400" />
          <span className="hidden sm:inline">System Online</span>
          <span className="relative flex h-2 w-2">
            <span className="status-dot absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
        </div>
      </div>
    </header>
  );
}
