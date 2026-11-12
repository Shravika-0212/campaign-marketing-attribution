import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  DollarSign,
  Award,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';

import { KpiCard } from '../components/KpiCard';
import { fetchDashboardSummary, fetchChannelAnalytics, fetchCampaigns } from '../services/api';
import { DashboardSummary, CampaignItem } from '../types';

export const RoiPage: React.FC = () => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [channelAnalytics, setChannelAnalytics] = useState<any[]>([]);
  const [topCampaigns, setTopCampaigns] = useState<CampaignItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sum, ch, cmp] = await Promise.all([
        fetchDashboardSummary(),
        fetchChannelAnalytics('MDL-MULTI-TOUCH'),
        fetchCampaigns({ sort_by: 'roi', sort_order: 'desc', limit: 8 })
      ]);
      setSummary(sum);
      setChannelAnalytics(ch);
      setTopCampaigns(cmp.items);
    } catch (err) {
      console.error('Failed to load ROI analytics', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3" />
        <span>Loading ROI analytics...</span>
      </div>
    );
  }

  const formatCurrency = (val: number) => `$${(val / 1000).toFixed(0)}k`;

  return (
    <div className="space-y-6">
      {/* Top Financial KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Overall Marketing ROI"
          value={summary.overall_roi !== null ? `${summary.overall_roi > 0 ? '+' : ''}${summary.overall_roi}%` : 'N/A'}
          subtitle="Net return on media spend"
          icon={Award}
          badge={{
            text: (summary.overall_roi || 0) >= 0 ? 'Profitable' : 'Loss',
            variant: (summary.overall_roi || 0) >= 0 ? 'positive' : 'negative'
          }}
        />
        <KpiCard
          title="Cost Per Acquisition (CPA)"
          value={`$${summary.cost_per_acquisition.toFixed(2)}`}
          subtitle={`${summary.total_conversions} paying customers`}
          icon={TrendingUp}
          badge={{ text: 'Acquisition', variant: 'neutral' }}
        />
        <KpiCard
          title="Cost Per Lead (CPL)"
          value={`$${summary.cost_per_lead.toFixed(2)}`}
          subtitle={`${summary.total_leads} generated leads`}
          icon={DollarSign}
          badge={{ text: 'Lead Gen', variant: 'neutral' }}
        />
        <KpiCard
          title="Attributed Revenue"
          value={`$${summary.attributed_revenue_multi_touch.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          subtitle={`Spend: $${summary.total_campaign_spend.toLocaleString()}`}
          icon={TrendingUp}
          badge={{ text: '100% Reconciled', variant: 'positive' }}
        />
      </div>

      {/* Channel ROI Breakdown Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Channel ROI & Capital Allocation</h3>
            <p className="text-xs text-slate-400">Comparing marketing spend, revenue return, and ROI across channels</p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={channelAnalytics} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="channel_name" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tickFormatter={formatCurrency} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [`$${Number(val).toLocaleString()}`, '']}
              />
              <Legend />
              <Bar dataKey="spend" name="Spend ($)" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="attributed_revenue" name="Revenue ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Channel Efficiency Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h4 className="text-sm font-semibold text-white mb-3">Channel Efficiency Scorecard</h4>
          <div className="space-y-3">
            {channelAnalytics.map((ch) => (
              <div key={ch.channel_id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-white">{ch.channel_name}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
                    Spend: ${ch.spend.toLocaleString()} | Rev: ${ch.attributed_revenue.toLocaleString()}
                  </div>
                </div>

                <div className="text-right">
                  <div className={`text-sm font-bold font-mono ${ch.roi !== null && ch.roi >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {ch.roi !== null ? `${ch.roi > 0 ? '+' : ''}${ch.roi}%` : 'N/A'}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase">{ch.conversions} Orders</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Highest ROI Campaigns */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h4 className="text-sm font-semibold text-white mb-3">Top Performing Campaigns by ROI</h4>
          <div className="space-y-3">
            {topCampaigns.map((cmp) => (
              <div key={cmp.campaign_id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex items-center justify-between">
                <div className="max-w-[70%]">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono text-emerald-400">{cmp.campaign_id}</span>
                    <span className="text-xs font-semibold text-white truncate">{cmp.campaign_name}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
                    Spend: ${cmp.actual_spend.toLocaleString()} &rarr; Rev: ${cmp.attributed_revenue.toLocaleString()}
                  </div>
                </div>

                <div className="text-right">
                  {cmp.roi_status === 'UNAVAILABLE_MISSING_COST' ? (
                    <span className="text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                      Missing Cost
                    </span>
                  ) : (
                    <span className="text-sm font-bold font-mono text-emerald-400">
                      +{cmp.roi}%
                    </span>
                  )}
                  <div className="text-[10px] text-slate-500">{cmp.conversions} Convs</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
