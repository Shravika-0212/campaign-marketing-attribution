import React from 'react';
import {
  LayoutDashboard,
  Layers,
  GitFork,
  PieChart,
  TrendingUp,
  AlertTriangle,
  Database,
  FileSpreadsheet,
  CheckCircle2,
  Lock,
  UserCheck
} from 'lucide-react';
import { ActorProfile } from '../types';

export type PageId =
  | 'overview'
  | 'campaigns'
  | 'journey'
  | 'attribution'
  | 'roi'
  | 'anomalies'
  | 'generator'
  | 'reports';

interface SidebarProps {
  activePage: PageId;
  onSelectPage: (page: PageId) => void;
  datasetScale: string;
  currentActor: ActorProfile | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  datasetScale,
  currentActor
}) => {
  const allNavItems = [
    {
      id: 'overview' as PageId,
      label: 'Overview Dashboard',
      icon: LayoutDashboard
    },
    {
      id: 'campaigns' as PageId,
      label: currentActor?.role === 'SUPPORT_AGENT' ? 'Campaigns (Read-Only)' : 'Campaign Management',
      icon: Layers
    },
    {
      id: 'journey' as PageId,
      label: currentActor?.role === 'CUSTOMER_PROSPECT' ? 'My Customer Journey' : currentActor?.role === 'SUPPORT_AGENT' ? 'Customer Journeys (Read-Only)' : 'Customer Journeys',
      icon: GitFork
    },
    {
      id: 'attribution' as PageId,
      label: 'Attribution Analysis',
      icon: PieChart
    },
    {
      id: 'roi' as PageId,
      label: 'ROI Analytics',
      icon: TrendingUp
    },
    {
      id: 'anomalies' as PageId,
      label: 'Quality & Anomalies',
      icon: AlertTriangle,
      badge: '5 Scenarios'
    },
    {
      id: 'generator' as PageId,
      label: 'Synthetic Generator',
      icon: Database
    },
    {
      id: 'reports' as PageId,
      label: 'Data Export & Reports',
      icon: FileSpreadsheet
    },
  ];

  // Filter navigation items strictly based on current actor's allowed pages
  const allowedPages = currentActor?.allowed_pages || allNavItems.map(i => i.id);
  const navItems = allNavItems.filter((item) => allowedPages.includes(item.id));

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white tracking-wide">Marketing Attribution</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">ROI Analytics Platform</p>
          </div>
        </div>
      </div>

      {/* Role Scope Notice */}
      {currentActor && (
        <div className="px-4 pt-3 pb-1">
          <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] space-y-1">
            <div className="flex items-center justify-between text-slate-400">
              <span className="font-mono text-[10px] uppercase tracking-wider">Active Actor Scope</span>
              <span className="text-[10px] text-emerald-400 font-semibold font-mono">
                {navItems.length} / {allNavItems.length} Views
              </span>
            </div>
            <div className="font-semibold text-white truncate">{currentActor.name}</div>
            <div className="text-[10px] text-slate-400 truncate">{currentActor.role_name}</div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30 shrink-0">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Environment Status Badge */}
      <div className="p-4 border-t border-slate-800">
        <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] text-slate-400 font-mono">Dataset Profile</span>
            <span className="inline-flex items-center text-[10px] font-semibold text-emerald-400">
              <CheckCircle2 className="w-3 h-3 mr-1" />
              {datasetScale}
            </span>
          </div>
          <div className="text-[10px] text-slate-400 space-y-0.5 font-mono">
            <div>Seed: <span className="text-slate-300">20261022</span></div>
            <div>Base: <span className="text-slate-300">INR (₹)</span> | Lookback: <span className="text-slate-300">90d</span></div>
          </div>
        </div>
      </div>
    </aside>
  );
};
