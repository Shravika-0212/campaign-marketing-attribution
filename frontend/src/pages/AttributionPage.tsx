import React, { useEffect, useState } from 'react';
import {
  PieChart as PieIcon,
  RotateCw,
  Sliders,
  CheckCircle2,
  TrendingUp,
  Info
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

import { fetchAttributionComparison, runAttributionRecalculation } from '../services/api';
import { AttributionCompareItem } from '../types';

export const AttributionPage: React.FC = () => {
  const [comparisons, setComparisons] = useState<AttributionCompareItem[]>([]);
  const [selectedModel, setSelectedModel] = useState<'FIRST_TOUCH' | 'LAST_TOUCH' | 'MULTI_TOUCH'>('MULTI_TOUCH');
  const [lookbackDays, setLookbackDays] = useState(90);
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchAttributionComparison();
      setComparisons(data);
    } catch (err) {
      console.error('Failed to load attribution comparison', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    try {
      await runAttributionRecalculation(lookbackDays);
      await loadData();
    } catch (err) {
      console.error('Recalculation failed', err);
    } finally {
      setIsRecalculating(false);
    }
  };

  const modelDescriptions = {
    FIRST_TOUCH: 'Attributes 100% of conversion credit to the earliest eligible marketing touchpoint within the lookback window. Ideal for analyzing top-of-funnel brand discovery.',
    LAST_TOUCH: 'Attributes 100% of conversion credit to the final marketing touchpoint immediately prior to conversion. Emphasizes closing campaigns.',
    MULTI_TOUCH: 'Distributes equal weight (1/N) across all N eligible marketing touchpoints leading up to conversion. Total credit equals exactly 100%. Provides balanced journey attribution.'
  };

  const chartData = comparisons.slice(0, 10).map((c) => ({
    name: c.campaign_name.replace('Campaign ', 'CMP-').slice(0, 14),
    first_touch: c.first_touch_revenue,
    last_touch: c.last_touch_revenue,
    multi_touch: c.multi_touch_revenue
  }));

  const formatCurrency = (val: number) => `$${(val / 1000).toFixed(0)}k`;

  return (
    <div className="space-y-6">
      {/* Model Selector and Control Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Attribution Methodology & Parameters</h3>
            <p className="text-xs text-slate-400 mt-0.5">Select active model and configure conversion lookback window</p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg text-xs">
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-400">Lookback:</span>
              <input
                type="number"
                min={1}
                max={365}
                value={lookbackDays}
                onChange={(e) => setLookbackDays(Number(e.target.value))}
                className="w-14 bg-transparent text-white font-mono text-center focus:outline-none focus:border-b border-emerald-500"
              />
              <span className="text-slate-400">Days</span>
            </div>

            <button
              onClick={handleRecalculate}
              disabled={isRecalculating}
              className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-lg transition"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isRecalculating ? 'animate-spin' : ''}`} />
              <span>Recalculate Attribution</span>
            </button>
          </div>
        </div>

        {/* 3 Model Tabs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          {[
            { id: 'FIRST_TOUCH', label: 'First-Touch Attribution', sub: '100% to discovery' },
            { id: 'LAST_TOUCH', label: 'Last-Touch Attribution', sub: '100% to closer' },
            { id: 'MULTI_TOUCH', label: 'Multi-Touch (Linear / Equal)', sub: '1/N equal credit' }
          ].map((m) => (
            <button
              key={m.id}
              onClick={() => setSelectedModel(m.id as any)}
              className={`p-3.5 rounded-xl border text-left transition ${
                selectedModel === m.id
                  ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{m.label}</span>
                {selectedModel === m.id && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">{m.sub}</p>
            </button>
          ))}
        </div>

        <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 flex items-start space-x-2 text-xs text-slate-300">
          <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span>{modelDescriptions[selectedModel]}</span>
        </div>
      </div>

      {/* Top 10 Campaigns Revenue Comparison Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Model Comparison: Attributed Revenue</h3>
            <p className="text-xs text-slate-400">Comparing top 10 campaigns across First-Touch, Last-Touch, and Multi-Touch</p>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tickFormatter={formatCurrency} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val: any) => [`$${Number(val).toLocaleString()}`, '']}
              />
              <Legend />
              <Bar dataKey="first_touch" name="First-Touch ($)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="last_touch" name="Last-Touch ($)" fill="#a855f7" radius={[4, 4, 0, 0]} />
              <Bar dataKey="multi_touch" name="Multi-Touch ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Comparative Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800">
          <h4 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">Campaign Attribution Drilldown</h4>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[11px] font-mono uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Campaign</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4 text-right">Spend</th>
                <th className="py-3 px-4 text-right">First-Touch Rev</th>
                <th className="py-3 px-4 text-right">Last-Touch Rev</th>
                <th className="py-3 px-4 text-right text-emerald-400">Multi-Touch Rev</th>
                <th className="py-3 px-4 text-right">FT ROI</th>
                <th className="py-3 px-4 text-right">LT ROI</th>
                <th className="py-3 px-4 text-right text-emerald-400">MT ROI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">Loading attribution results...</td>
                </tr>
              ) : comparisons.map((c) => (
                <tr key={c.campaign_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-4 font-medium text-white max-w-xs truncate">
                    <span className="font-mono text-emerald-400 mr-2 text-[11px]">{c.campaign_id}</span>
                    {c.campaign_name}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {c.channel_name.split('(')[0].trim()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-300">
                    ${c.spend.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-blue-400">
                    ${c.first_touch_revenue.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-purple-400">
                    ${c.last_touch_revenue.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-emerald-400">
                    ${c.multi_touch_revenue.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right font-mono">
                    {c.first_touch_roi !== null ? `${c.first_touch_roi}%` : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-right font-mono">
                    {c.last_touch_roi !== null ? `${c.last_touch_roi}%` : 'N/A'}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-emerald-400">
                    {c.multi_touch_roi !== null ? `${c.multi_touch_roi}%` : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
