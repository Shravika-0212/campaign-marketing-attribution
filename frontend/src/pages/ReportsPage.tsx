import React, { useEffect, useState } from 'react';
import {
  FileSpreadsheet,
  Download,
  FileCode,
  Database,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { fetchExportsManifest } from '../services/api';

export const ReportsPage: React.FC = () => {
  const [manifest, setManifest] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'manifest' | 'dictionary' | 'ground_truth' | 'charts'>('manifest');
  const [chartRefreshKey, setChartRefreshKey] = useState<number>(Date.now());
  const [isGeneratingCharts, setIsGeneratingCharts] = useState<boolean>(false);

  useEffect(() => {
    fetchExportsManifest()
      .then((data) => setManifest(data))
      .catch((err) => console.error('Failed to load export manifest', err));
  }, []);

  const dataDictionary = [
    { table: 'campaigns', desc: 'Marketing initiatives with channels, budgets, and dates.', pk: 'campaign_id', fks: 'channel_id' },
    { table: 'channels', desc: 'Acquisition channels (Search, Social, Email, Events, Direct).', pk: 'channel_id', fks: '-' },
    { table: 'creatives', desc: 'Ad creative assets, copy themes, and media formats.', pk: 'creative_id', fks: '-' },
    { table: 'audiences', desc: 'Target audience segments and firmographic criteria.', pk: 'audience_id', fks: '-' },
    { table: 'contacts', desc: 'Leads, prospects, and paying customer identity records.', pk: 'contact_id', fks: '-' },
    { table: 'web_sessions', desc: 'Browsing sessions with cookie IDs, device types, referrers.', pk: 'session_id', fks: 'contact_id' },
    { table: 'touchpoints', desc: 'Discrete online & offline interactions with costs & timestamps.', pk: 'touchpoint_id', fks: 'contact_id, campaign_id, channel_id' },
    { table: 'leads', desc: 'Form fills & qualified inquiry conversions.', pk: 'lead_id', fks: 'contact_id, campaign_id' },
    { table: 'opportunities', desc: 'Deal pipeline stages with expected revenue.', pk: 'opportunity_id', fks: 'contact_id, lead_id, campaign_id' },
    { table: 'orders', desc: 'Closed-won transactions recognizing finalized revenue.', pk: 'order_id', fks: 'opportunity_id, contact_id' },
    { table: 'cost_records', desc: 'Media spend and production expenditures by campaign.', pk: 'cost_id', fks: 'campaign_id, channel_id' },
    { table: 'attribution_results', desc: 'Calculated credit allocation & attributed revenue.', pk: 'result_id', fks: 'model_id, order_id, touchpoint_id, campaign_id' },
  ];

  return (
    <div className="space-y-6">
      {/* Export Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-white">Exports, Data Dictionary & Compliance Manifest</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Download relational seed data, audit manifests, SHA-256 reproducibility checksums, and evaluation ground truth.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <a
              href="/api/exports/download/sql/seed_data.sql"
              download
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs transition"
            >
              <Database className="w-3.5 h-3.5" />
              <span>Download SQL Seed</span>
            </a>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center space-x-2 border-b border-slate-800 mt-6 pt-2">
          {[
            { id: 'manifest', label: 'Export Files & SHA-256 Manifest' },
            { id: 'dictionary', label: '12-Entity Relational Data Dictionary' },
            { id: 'ground_truth', label: 'Evaluation Ground Truth (Separate)' },
            { id: 'charts', label: 'Python Matplotlib Charts' }
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`px-4 py-2 text-xs font-medium border-b-2 transition ${
                activeTab === t.id
                  ? 'border-emerald-500 text-emerald-400 font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab 1: Manifest & Downloads */}
      {activeTab === 'manifest' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
            <div>
              <h4 className="text-sm font-semibold text-white">Reproducibility Checksums & Exported Artifacts</h4>
              <p className="text-xs text-slate-400">
                Seed: <span className="font-mono text-emerald-400">{manifest?.seed || 20261022}</span> | Profile: <span className="font-mono text-emerald-400">{manifest?.generation_config || 'STARTER'}</span>
              </p>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Total Exported Files: {manifest?.total_files || 0}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Dataset Name</th>
                  <th className="py-2.5 px-3">Format</th>
                  <th className="py-2.5 px-3 text-right">Records</th>
                  <th className="py-2.5 px-3">SHA-256 Checksum</th>
                  <th className="py-2.5 px-3 text-center">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/40 font-mono">
                {manifest?.files?.map((f: any) => (
                  <tr key={f.file_name} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 font-sans font-medium text-white">{f.dataset_name}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                        {f.format}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-slate-300">{f.record_count.toLocaleString()}</td>
                    <td className="py-2.5 px-3 font-mono text-[10px] text-slate-400 truncate max-w-xs" title={f.sha256}>
                      {f.sha256}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <a
                        href={`/api/exports/download/${f.file_name}`}
                        download
                        className="inline-flex items-center p-1 rounded bg-slate-800 hover:bg-slate-700 text-emerald-400 hover:text-emerald-300 transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Data Dictionary */}
      {activeTab === 'dictionary' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-white">Relational Data Dictionary (12 Core Entities)</h4>
            <p className="text-xs text-slate-400">Strictly normalized entity relationships and constraint mappings</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {dataDictionary.map((item) => (
              <div key={item.table} className="p-4 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-emerald-400">{item.table}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    PK: {item.pk}
                  </span>
                </div>
                <p className="text-xs text-slate-300">{item.desc}</p>
                <div className="text-[11px] font-mono text-slate-500">
                  Foreign Keys: <span className="text-slate-400">{item.fks}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Separate Ground Truth */}
      {activeTab === 'ground_truth' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-start space-x-3 p-4 bg-slate-950 rounded-xl border border-slate-800">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 space-y-1">
              <h4 className="font-semibold text-white">Evaluation-Only Ground Truth Repository</h4>
              <p className="text-slate-400">
                Ground truth files (<code className="text-emerald-400">ground_truth.json</code> and <code className="text-emerald-400">ground_truth.csv</code>) contain known injected anomaly scenarios and expected system mitigations.
                In compliance with strict data leakage guidelines, these files are completely segregated from attribution and anomaly detection feature inputs.
              </p>
            </div>
          </div>

          <div className="flex space-x-3 pt-2">
            <a
              href="/data/ground_truth/ground_truth.csv"
              target="_blank"
              download="ground_truth.csv"
              className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium border border-slate-700 transition"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span>Download ground_truth.csv</span>
            </a>
            <a
              href="/data/ground_truth/ground_truth.json"
              target="_blank"
              download="ground_truth.json"
              className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium border border-slate-700 transition"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span>Download ground_truth.json</span>
            </a>
          </div>
        </div>
      )}

      {/* Tab 4: Python Matplotlib Charts */}
      {activeTab === 'charts' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-sm font-semibold text-white">Python Matplotlib Data Visualizations</h4>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  Pandas + NumPy + Matplotlib
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Publication-quality analytics plots rendered server-side in Python. Demonstrating data science workflows, multi-channel ROI analysis, and journey progression.
              </p>
            </div>
            <button
              onClick={async () => {
                setIsGeneratingCharts(true);
                try {
                  await fetch('/api/analytics/charts/generate');
                  setChartRefreshKey(Date.now());
                } catch (e) {
                  console.error('Failed to regenerate charts', e);
                } finally {
                  setIsGeneratingCharts(false);
                }
              }}
              disabled={isGeneratingCharts}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs transition disabled:opacity-50"
            >
              <span>{isGeneratingCharts ? 'Rendering Plots...' : 'Regenerate Matplotlib Charts'}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1 */}
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-xs font-bold text-white">1. Attribution Models Comparison</h5>
                  <p className="text-[11px] text-slate-400">First-Touch vs Last-Touch vs Multi-Touch Credited Revenue</p>
                </div>
                <a
                  href={`/api/analytics/charts/view/attribution_model_comparison.png?t=${chartRefreshKey}`}
                  download="attribution_model_comparison.png"
                  className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PNG</span>
                </a>
              </div>
              <div className="rounded-lg overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center min-h-[200px]">
                <img
                  src={`/api/analytics/charts/view/attribution_model_comparison.png?t=${chartRefreshKey}`}
                  alt="Attribution Models Comparison"
                  className="w-full h-auto object-contain"
                  onError={(e: any) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            </div>

            {/* Chart 2 */}
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-xs font-bold text-white">2. Monthly Revenue vs. Spend Progression (2026)</h5>
                  <p className="text-[11px] text-slate-400">Chronological 12-month financial trajectory & ROI</p>
                </div>
                <a
                  href={`/api/analytics/charts/view/monthly_revenue_vs_spend.png?t=${chartRefreshKey}`}
                  download="monthly_revenue_vs_spend.png"
                  className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PNG</span>
                </a>
              </div>
              <div className="rounded-lg overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center min-h-[200px]">
                <img
                  src={`/api/analytics/charts/view/monthly_revenue_vs_spend.png?t=${chartRefreshKey}`}
                  alt="Monthly Revenue vs Spend"
                  className="w-full h-auto object-contain"
                  onError={(e: any) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            </div>

            {/* Chart 3 */}
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-xs font-bold text-white">3. Channel Acquisition Efficiency (Spend vs. Revenue)</h5>
                  <p className="text-[11px] text-slate-400">Horizontal bar plot comparing spend and return by channel</p>
                </div>
                <a
                  href={`/api/analytics/charts/view/channel_efficiency_roi.png?t=${chartRefreshKey}`}
                  download="channel_efficiency_roi.png"
                  className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PNG</span>
                </a>
              </div>
              <div className="rounded-lg overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center min-h-[200px]">
                <img
                  src={`/api/analytics/charts/view/channel_efficiency_roi.png?t=${chartRefreshKey}`}
                  alt="Channel Efficiency ROI"
                  className="w-full h-auto object-contain"
                  onError={(e: any) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            </div>

            {/* Chart 4 */}
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="text-xs font-bold text-white">4. Customer Journey Timeline: Shravika Kavati</h5>
                  <p className="text-[11px] text-slate-400">Chronological touchpoint progression from discovery to order</p>
                </div>
                <a
                  href={`/api/analytics/charts/view/shravika_kavati_journey.png?t=${chartRefreshKey}`}
                  download="shravika_kavati_journey.png"
                  className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center space-x-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download PNG</span>
                </a>
              </div>
              <div className="rounded-lg overflow-hidden border border-slate-800 bg-slate-900 flex items-center justify-center min-h-[200px]">
                <img
                  src={`/api/analytics/charts/view/shravika_kavati_journey.png?t=${chartRefreshKey}`}
                  alt="Shravika Kavati Customer Journey"
                  className="w-full h-auto object-contain"
                  onError={(e: any) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
