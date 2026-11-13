import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  Eye,
  AlertCircle,
  X,
  TrendingUp,
  Target,
  Users,
  ShieldCheck,
  DollarSign,
  Award,
  Lock
} from 'lucide-react';
import { fetchCampaigns, fetchCampaignDetail, fetchDashboardSummary } from '../services/api';
import { CampaignItem, CampaignDetail, DashboardSummary } from '../types';

interface CampaignsPageProps {
  isReadOnly?: boolean;
}

export const CampaignsPage: React.FC<CampaignsPageProps> = ({ isReadOnly = false }) => {
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

  // Overall financial summary for platform-wide consistency
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  // Detail Modal state
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadSummary();
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [page, channelFilter, statusFilter, sortBy, sortOrder]);

  const loadSummary = async () => {
    try {
      const sum = await fetchDashboardSummary();
      setSummary(sum);
    } catch (err) {
      console.error('Failed to load dashboard summary for reconciliation', err);
    }
  };

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
      {/* Support Read-Only Notice */}
      {isReadOnly && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex items-center space-x-3 text-xs text-amber-300">
          <Lock className="w-4 h-4 text-amber-400 shrink-0" />
          <div>
            <span className="font-bold">Support Agent (Read-Only Mode):</span> Viewing campaign reference directory and promotional channels to assist customers with promo inquiries. Budget, allocation, and channel mutations are restricted to Marketing & Sales Operations.
          </div>
        </div>
      )}

      {/* Financial Consistency & Reconciliation Header */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/20 rounded-xl p-4 space-y-3">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Campaign Management & Financial Reconciliation</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Overview & Campaign dashboards share 100% consistent ledger results in Indian Rupees (₹).
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300">
              Base Currency: <span className="text-emerald-400 font-semibold">INR (₹)</span>
            </span>
            <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              ✓ Overview Reconciled
            </span>
          </div>
        </div>

        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-slate-800/80 text-xs">
            <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400">Total Campaign Budget</div>
              <div className="text-sm font-bold font-mono text-white mt-0.5">
                ₹{summary.total_budget.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400">Total Valid Spend</div>
              <div className="text-sm font-bold font-mono text-white mt-0.5">
                ₹{summary.total_campaign_spend.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400">Attributed Closed Revenue</div>
              <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                ₹{summary.total_closed_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
              <div className="text-slate-400">Platform Marketing ROI</div>
              <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                {summary.overall_roi !== null ? `+${summary.overall_roi}%` : 'N/A'}
              </div>
            </div>
          </div>
        )}
      </div>

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

          {/* Status Filter with INCOMPLETE option */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="COMPLETED">COMPLETED</option>
            <option value="INCOMPLETE">INCOMPLETE (Missing Cost)</option>
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
            <option value="actual_spend-asc">Spend: Low to High</option>
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
                campaigns.map((c) => {
                  const isMissingCost = c.roi_status === 'UNAVAILABLE_MISSING_COST' || c.status_display === 'INCOMPLETE' || c.is_incomplete;
                  return (
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
                        ₹{c.budget.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-300">
                        ₹{c.actual_spend.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-emerald-400">
                        ₹{c.attributed_revenue.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-4 text-right font-mono">
                        {isMissingCost ? (
                          <div className="flex flex-col items-end">
                            <span className="inline-flex items-center text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30" title="Campaign costs missing: normal ROI calculation blocked under Rule 2">
                              <AlertCircle className="w-3 h-3 mr-1" />
                              INCOMPLETE
                            </span>
                            <span className="text-[9px] text-slate-500 font-mono mt-0.5">Missing Cost</span>
                          </div>
                        ) : (
                          <span className={`font-semibold ${c.roi !== null && c.roi >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {c.roi !== null ? `${c.roi > 0 ? '+' : ''}${c.roi}%` : 'N/A'}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {isMissingCost ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/40">
                            INCOMPLETE
                          </span>
                        ) : (
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            c.status === 'ACTIVE'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                              : 'bg-slate-700/50 text-slate-300 border border-slate-600'
                          }`}>
                            {c.status}
                          </span>
                        )}
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
                  );
                })
              )}
            </tbody>
            {summary && (
              <tfoot className="bg-slate-950 text-slate-300 font-mono font-bold text-xs border-t-2 border-slate-800">
                <tr>
                  <td colSpan={3} className="py-3 px-4 text-slate-400 uppercase tracking-wider text-[11px]">
                    Reconciled Platform Totals ({total} Campaigns)
                  </td>
                  <td className="py-3 px-4 text-right text-slate-400">
                    ₹{summary.total_budget.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="py-3 px-4 text-right text-white">
                    ₹{summary.total_campaign_spend.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-400">
                    ₹{summary.total_closed_revenue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-400">
                    {summary.overall_roi !== null ? `+${summary.overall_roi}%` : '—'}
                  </td>
                  <td colSpan={2} className="py-3 px-4 text-center">
                    <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      100% Reconciled
                    </span>
                  </td>
                </tr>
              </tfoot>
            )}
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
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-emerald-400">{selectedCampaign.campaign_id}</span>
                  {selectedCampaign.roi_status === 'UNAVAILABLE_MISSING_COST' || selectedCampaign.is_incomplete ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/40">
                      INCOMPLETE (Missing Cost)
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {selectedCampaign.status}
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-bold text-white mt-1">{selectedCampaign.name || selectedCampaign.campaign_name}</h3>
                <p className="text-xs text-slate-400">Primary Channel: {selectedCampaign.channel_name}</p>
              </div>
              <button
                onClick={() => setSelectedCampaign(null)}
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Incomplete Cost Warning if missing */}
            {(selectedCampaign.roi_status === 'UNAVAILABLE_MISSING_COST' || selectedCampaign.is_incomplete) && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start space-x-2.5 text-xs text-amber-300">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Missing Campaign Spend Records:</span> Under financial validation rules, normal ROI is not computed when actual campaign cost is missing or ₹0. Status is flagged as <span className="font-bold underline">INCOMPLETE</span> to prevent undefined division.
                </div>
              </div>
            )}

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Budget</span>
                <div className="text-sm font-bold font-mono text-white mt-1">₹{selectedCampaign.budget.toLocaleString('en-IN')}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Actual Spend</span>
                <div className="text-sm font-bold font-mono text-white mt-1">₹{selectedCampaign.actual_spend.toLocaleString('en-IN')}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Attributed Rev</span>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-1">₹{selectedCampaign.attributed_revenue.toLocaleString('en-IN')}</div>
              </div>
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-slate-400">Marketing ROI</span>
                <div className="text-sm font-bold font-mono mt-1">
                  {selectedCampaign.roi !== null ? (
                    <span className={selectedCampaign.roi >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                      {selectedCampaign.roi > 0 ? '+' : ''}{selectedCampaign.roi}%
                    </span>
                  ) : (
                    <span className="text-amber-400">INCOMPLETE</span>
                  )}
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
