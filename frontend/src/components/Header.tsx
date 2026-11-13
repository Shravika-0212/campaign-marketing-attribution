import React, { useEffect, useState } from 'react';
import { RefreshCw, UserCheck, ChevronDown, ShieldAlert, Shield } from 'lucide-react';
import { fetchHealth } from '../services/api';
import { ActorProfile, UserRole } from '../types';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  currentActor: ActorProfile | null;
  availableActors: ActorProfile[];
  onSelectActor: (actor: ActorProfile) => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  onRefresh,
  isRefreshing,
  currentActor,
  availableActors,
  onSelectActor
}) => {
  const [health, setHealth] = useState<string>('Checking...');
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth(h.status === 'HEALTHY' ? 'API Online' : 'Degraded'))
      .catch(() => setHealth('Offline'));
  }, []);

  const getRoleBadgeStyle = (role: UserRole) => {
    switch (role) {
      case 'CUSTOMER_PROSPECT':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'MARKETING_SALES_OPS':
        return 'bg-sky-500/15 text-sky-400 border-sky-500/30';
      case 'SUPPORT_AGENT':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'ANALYST':
        return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
      case 'SYSTEM_ADMIN':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <header className="h-16 px-8 border-b border-slate-800 bg-slate-900/60 backdrop-blur flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-lg font-bold text-white tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-3">
        {/* System Health Status */}
        <div className="hidden md:flex items-center space-x-2 text-xs font-mono px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700">
          <span className={`w-2 h-2 rounded-full ${health === 'API Online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
          <span className="text-slate-300">{health}</span>
        </div>

        {/* Sync Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
            title="Synchronize Database Records"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>
        )}

        {/* Actor & Role Selector Dropdown */}
        {currentActor && (
          <div className="relative">
            <button
              onClick={() => setShowRoleMenu(!showRoleMenu)}
              className="flex items-center space-x-2.5 px-3 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-800 border border-slate-700 text-left transition"
            >
              <div className="w-6 h-6 rounded-md bg-slate-900 border border-slate-700 flex items-center justify-center text-slate-300 font-bold text-[10px]">
                {currentActor.name.split(' ').map((n) => n[0]).join('')}
              </div>
              <div className="hidden lg:block">
                <div className="text-xs font-semibold text-white leading-tight flex items-center space-x-1.5">
                  <span>{currentActor.name}</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  {currentActor.title}
                </div>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded border font-mono font-semibold ${getRoleBadgeStyle(currentActor.role)}`}>
                {currentActor.avatar_badge}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {/* Dropdown Menu */}
            {showRoleMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowRoleMenu(false)}
                />
                <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-2 z-50 space-y-1">
                  <div className="px-3 py-2 border-b border-slate-800 text-xs">
                    <div className="font-semibold text-white flex items-center space-x-1.5">
                      <Shield className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Role-Based Access Control</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Switch between the 5 primary business actors to test permission boundaries:
                    </p>
                  </div>

                  <div className="space-y-1 max-h-80 overflow-y-auto pt-1">
                    {availableActors.map((actor) => {
                      const isSelected = actor.role === currentActor.role;
                      return (
                        <button
                          key={actor.role}
                          onClick={() => {
                            onSelectActor(actor);
                            setShowRoleMenu(false);
                          }}
                          className={`w-full text-left p-2.5 rounded-lg text-xs transition flex flex-col space-y-1 ${
                            isSelected
                              ? 'bg-emerald-500/10 border border-emerald-500/30'
                              : 'hover:bg-slate-800 border border-transparent'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-white">{actor.name}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono ${getRoleBadgeStyle(actor.role)}`}>
                              {actor.avatar_badge}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-300 font-medium">
                            {actor.role_name}
                          </div>
                          <p className="text-[10px] text-slate-400 line-clamp-2">
                            {actor.description}
                          </p>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
