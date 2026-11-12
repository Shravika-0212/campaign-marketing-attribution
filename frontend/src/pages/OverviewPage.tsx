import React, { useEffect, useState } from 'react';
import {
  DollarSign,
  TrendingUp,
  Target,
  Users,
  ShieldCheck,
  Award
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';

import { KpiCard } from '../components/KpiCard';
import { fetchDashboardSummary, fetchDashboardTrends, fetchChannelAnalytics } from '../services/api';
import { DashboardSummary, TrendDataPoint } from '../types';

export const OverviewPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);
  const [channelData, setChannelData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sum, tr, ch] = await Promise.all([
        fetchDashboardSummary(),
        fetchDashboardTrends(),
        fetchChannelAnalytics()
      ]);
      setSummary(sum);
      setTrends(tr);
      setChannelData(ch);
    } catch (err) {
      console.error('Failed to load overview data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3" />
        <span>Loading analytics dashboard...</span>
      </div>
    );
  }

  // Model comparison data for chart
  const modelCompData = [
    {
      name: 'First-Touch',
      revenue: summary.revenue_by_model['FIRST_TOUCH'] || 0,
      description: '100% to discovery touch'
    },
    {
      name: 'Last-Touch',
      revenue: summary.revenue_by_model['LAST_TOUCH'] || 0,
      description: '100% to conversion touch'
    },
    {
      name: 'Multi-Touch (Linear)',
      revenue: summary.revenue_by_model['MULTI_TOUCH_LINEAR'] || 0,
      description: 'Equal credit across touches'
    }
  ];

  const formatCurrency = (val: number) => `$${(val / 1000).toFixed(1)}k`;

  return (
    <div className="space-y-6">
      {/* Top Banner: Anomaly and Integrity Guard Notice */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/20 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Financial Integrity Guard Active</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Prevented double-counting: <span className="text-emerald-400 font-mono font-medium">${summary.excluded_duplicate_revenue.toLocaleString()}</span> duplicate revenue quarantined across {summary.excluded_duplicate_orders_count} orders.
            </p>
          </div>
        </div>
        <div className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300">
          Base: <span className="text-emerald-400">USD</span> | 90-Day Lookback
        </div>
      </div>

      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Closed Revenue"
          value={`$${summary.total_closed_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtitle="Validated non-duplicate orders"
          icon={DollarSign}
          badge={{ text: 'Reconciled', variant: 'positive' }}
        />
        <KpiCard
          title="Total Campaign Spend"
          value={`$${summary.total_campaign_spend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtitle={`Across ${summary.total_campaigns} campaigns`}
          icon={TrendingUp}
          badge={{ text: 'USD Validated', variant: 'neutral' }}
        />
        <KpiCard
          title="Reconciled Marketing ROI"
          value={summary.overall_roi !== null ? `${summary.overall_roi > 0 ? '+' : ''}${summary.overall_roi}%` : 'N/A'}
          subtitle="Multi-Touch Equal-Weight Model"
          icon={Award}
          badge={{
            text: (summary.overall_roi || 0) >= 0 ? 'Profitable' : 'Deficit',
            variant: (summary.overall_roi || 0) >= 0 ? 'positive' : 'negative'
          }}
        />
        <KpiCard
          title="Total Conversions"
          value={summary.total_conversions}
          subtitle={`CPA: $${summary.cost_per_acquisition.toFixed(2)} | CPL: $${summary.cost_per_lead.toFixed(2)}`}
          icon={Target}
          badge={{ text: `${summary.total_leads} Leads`, variant: 'neutral' }}
        />
      </div>

      {/* Main Charts: Revenue Trend & Channel Spend vs Revenue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Revenue vs. Marketing Spend Trend (2026)</h3>
              <p className="text-xs text-slate-400">Monthly chronological financial progression</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              12 Months
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="period" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tickFormatter={formatCurrency} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, '']}
                />
                <Legend />
                <Area type="monotone" dataKey="revenue" name="Closed Revenue ($)" stroke="#10b981" fillOpacity={1} fill="url(#revGrad)" />
                <Area type="monotone" dataKey="spend" name="Campaign Spend ($)" stroke="#6366f1" fillOpacity={1} fill="url(#spendGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Attribution Model Comparison */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Attribution Models Comparison</h3>
            <p className="text-xs text-slate-400 mb-4">Total credited revenue across 3 models</p>

            <div className="space-y-4">
              {modelCompData.map((m) => (
                <div key={m.name} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-200">{m.name}</span>
                    <span className="font-mono text-emerald-400 font-bold">${m.revenue.toLocaleString()}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">{m.description}</p>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all"
                      style={{ width: `${summary.total_closed_revenue > 0 ? (m.revenue / summary.total_closed_revenue) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex justify-between">
            <span>Unattributed Revenue:</span>
            <span className="font-mono text-slate-300">${summary.unattributed_revenue.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Channel Performance Bar Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Channel Efficiency (Spend vs. Attributed Revenue)</h3>
            <p className="text-xs text-slate-400">Comparing marketing channel acquisition performance</p>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={channelData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="channel_name" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tickFormatter={formatCurrency} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [`$${Number(val).toLocaleString()}`, '']}
              />
              <Legend />
              <Bar dataKey="spend" name="Spend ($)" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="attributed_revenue" name="Attributed Revenue ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
