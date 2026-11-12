import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badge?: {
    text: string;
    variant: 'positive' | 'negative' | 'neutral' | 'warning';
  };
}

export const KpiCard: React.FC<KpiCardProps> = ({ title, value, subtitle, icon: Icon, badge }) => {
  const badgeStyles = {
    positive: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    negative: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    neutral: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 tracking-wide">{title}</span>
        <div className="p-2 rounded-lg bg-slate-800/80 text-emerald-400 border border-slate-700/50">
          <Icon className="w-4 h-4" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div className="text-2xl font-bold text-white tracking-tight">{value}</div>
        {badge && (
          <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full border ${badgeStyles[badge.variant]}`}>
            {badge.text}
          </span>
        )}
      </div>

      {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
};
