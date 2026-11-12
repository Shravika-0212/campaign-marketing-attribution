import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  Eye,
  AlertCircle,
  X,
  TrendingUp,
  Target,
  Users
} from 'lucide-react';
import { fetchCampaigns, fetchCampaignDetail } from '../services/api';
import { CampaignItem, CampaignDetail } from '../types';

export const CampaignsPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<CampaignItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(12);
  const [search, setSearch] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('attributed_revenue');
  const [sortOrder, setSortOrder] = useState('desc');
  const [loading, setLoading] = useState(true);

  // Detail Modal state
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadCampaigns();
  }, [page, channelFilter, statusFilter, sortBy, sortOrder]);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const res = await fetchCampaigns({
        page,
        limit,
        channel_id: channelFilter || undefined,
        status: statusFilter || undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder
      });
      setCampaigns(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load campaigns', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadCampaigns();
  };

  const handleOpenDetail = async (campaignId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await fetchCampaignDetail(campaignId);
      setSelectedCampaign(detail);
    } catch (err) {
      console.error('Failed to load campaign detail', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search & Filter Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search campaign ID or name..."
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition"
          />
        </form>

        <div className="flex items-center space-x-3 w-full md:w-auto">
          {/* Channel Filter */}
          <select
            value={channelFilter}
            onChange={(e) => { setChannelFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Channels</option>
            <option value="CHN-PAID-SEARCH">Paid Search</option>
            <option value="CHN-ORGANIC">Organic Search</option>
            <option value="CHN-EMAIL">Email</option>
            <option value="CHN-SOCIAL">Paid Social</option>
            <option value="CHN-DISPLAY">Display</option>
            <option value="CHN-EVENT">Events & Webinars</option>
            <option value="CHN-REFERRAL">Referral</option>
            <option value="CHN-DIRECT">Direct Outreach</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="COMPLETED">COMPLETED</option>
          </select>

          {/* Sort Field */}
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [f, o] = e.target.value.split('-');
              setSortBy(f);
              setSortOrder(o);
            }}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="attributed_revenue-desc">Revenue: High to Low</option>
            <option value="attributed_revenue-asc">Revenue: Low to High</option>
            <option value="actual_spend-desc">Spend: High to Low</option>
            <option value="roi-desc">ROI: High to Low</option>
            <option value="conversions-desc">Conversions: High to Low</option>
          </select>
        </div>
      </div>

      {/* Campaigns Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-mono">
              <tr>
                <th className="py-3 px-4">Campaign ID</th>
                <th className="py-3 px-4">Campaign Name</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4 text-right">Budget</th>
                <th className="py-3 px-4 text-right">Actual Spend</th>
                <th className="py-3 px-4 text-right">Attributed Rev</th>
                <th className="py-3 px-4 text-right">ROI (%)</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    Loading campaigns...
                  </td>
                </tr>
              ) : campaigns.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    No campaigns found matching criteria.
                  </td>
                </tr>
              ) : (
                campaigns.map((c) => (
                  <tr key={c.campaign_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-medium text-emerald-400">
                      {c.campaign_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-white max-w-xs truncate">
                      {c.campaign_name}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 text-slate-300">
                        {c.channel_id.replace('CHN-', '')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-400">
                      ${c.budget.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-300">
                      ${c.actual_spend.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-emerald-400">
                      ${c.attributed_revenue.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {c.roi_status === 'UNAVAILABLE_MISSING_COST' ? (
                        <span className="inline-flex items-center text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20" title="Missing campaign costs detected">
                          <AlertCircle className="w-3 h-3 mr-1" />
                          Missing Cost
                        </span>
                      ) : (
                        <span className={`font-semibold ${c.roi !== null && c.roi >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {c.roi !== null ? `${c.roi > 0 ? '+' : ''}${c.roi}%` : 'N/A'}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        c.status === 'ACTIVE'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-slate-700/50 text-slate-300 border border-slate-600'
                      }`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleOpenDetail(c.campaign_id)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                        title="View Full Campaign Breakdown"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing {campaigns.length > 0 ? (page - 1) * limit + 1 : 0} to{' '}
            {Math.min(page * limit, total)} of {total} campaigns
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition"
            >
              Previous
            </button>
            <span className="px-3 py-1.5 font-mono text-slate-300">
              Page {page} of {Math.max(1, Math.ceil(total / limit))}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(Math.ceil(total / limit), p + 1))}
              disabled={page >= Math.ceil(total / limit)}
              className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Campaign Detail Modal */}
      {selectedCampaign && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <span className="text-xs font-mono text-emerald-400">{selectedCampaign.campaign_id}</span>
                <h3 className="text-lg font-bold text-white mt-0.5">{selectedCampaign.name || selectedCampaign.campaign_name}</h3>
                <p className="text-xs text-slate-400">Primary Channel: {selectedCampaign.channel_name}</p>
              </div>
              <button
                onClick={() => setSelectedCampaign(null)}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Budget</span>
                <div className="text-sm font-bold font-mono text-white mt-1">${selectedCampaign.budget.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Actual Spend</span>
                <div className="text-sm font-bold font-mono text-white mt-1">${selectedCampaign.actual_spend.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Attributed Rev</span>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-1">${selectedCampaign.attributed_revenue.toLocaleString()}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Marketing ROI</span>
                <div className="text-sm font-bold font-mono text-white mt-1">
                  {selectedCampaign.roi !== null ? `${selectedCampaign.roi}%` : 'N/A (Missing Cost)'}
                </div>
              </div>
            </div>

            {/* Funnel Counters */}
            <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800">
              <h4 className="text-xs font-semibold text-slate-200 mb-3 uppercase tracking-wider font-mono">Conversion Funnel</h4>
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div>
                  <div className="text-base font-bold text-white">{selectedCampaign.touchpoints_count}</div>
                  <div className="text-[11px] text-slate-400">Touchpoints</div>
                </div>
                <div>
                  <div className="text-base font-bold text-white">{selectedCampaign.leads_count}</div>
                  <div className="text-[11px] text-slate-400">Leads</div>
                </div>
                <div>
                  <div className="text-base font-bold text-white">{selectedCampaign.opportunities_count}</div>
                  <div className="text-[11px] text-slate-400">Opportunities</div>
                </div>
                <div>
                  <div className="text-base font-bold text-emerald-400">{selectedCampaign.conversions_count}</div>
                  <div className="text-[11px] text-slate-400">Conversions</div>
                </div>
              </div>
            </div>

            {/* Linked Creatives & Audiences */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800">
                <h4 className="font-semibold text-slate-200 mb-2">Creatives Deployed</h4>
                <div className="space-y-1.5">
                  {selectedCampaign.creatives.map((cr) => (
                    <div key={cr.creative_id} className="p-2 rounded bg-slate-900 border border-slate-800 flex justify-between">
                      <span className="text-slate-300 truncate">{cr.name}</span>
                      <span className="font-mono text-slate-500 text-[10px]">{cr.format}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-slate-950/60 rounded-lg border border-slate-800">
                <h4 className="font-semibold text-slate-200 mb-2">Target Audiences</h4>
                <div className="space-y-1.5">
                  {selectedCampaign.audiences.map((aud) => (
                    <div key={aud.audience_id} className="p-2 rounded bg-slate-900 border border-slate-800 flex justify-between">
                      <span className="text-slate-300 truncate">{aud.name}</span>
                      <span className="font-mono text-slate-500 text-[10px]">{aud.segment}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedCampaign(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
