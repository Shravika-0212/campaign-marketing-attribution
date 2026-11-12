import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw } from 'lucide-react';
import { fetchHealth } from '../services/api';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, onRefresh, isRefreshing }) => {
  const [health, setHealth] = useState<string>('Checking...');

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth(h.status === 'HEALTHY' ? 'API Online' : 'Degraded'))
      .catch(() => setHealth('Offline'));
  }, []);

  return (
    <header className="h-16 px-8 border-b border-slate-800 bg-slate-900/50 backdrop-blur flex items-center justify-between sticky top-0 z-20">
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* System Health */}
        <div className="flex items-center space-x-2 text-xs font-mono px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700">
          <span className={`w-2 h-2 rounded-full ${health === 'API Online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
          <span className="text-slate-300">{health}</span>
        </div>

        {/* Refresh Action */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Sync</span>
          </button>
        )}
      </div>
    </header>
  );
};
