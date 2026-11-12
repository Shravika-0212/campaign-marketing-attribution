import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Filter,
  Info,
  Layers,
  ArrowRight
} from 'lucide-react';
import { fetchAnomalies } from '../services/api';
import { AnomalyDashboardData, AnomalyIssueItem } from '../types';

export const AnomaliesPage: React.FC = () => {
  const [data, setData] = useState<AnomalyDashboardData | null>(null);
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [typeFilter, severityFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchAnomalies(typeFilter || undefined, severityFilter || undefined);
      setData(res);
    } catch (err) {
      console.error('Failed to load anomalies data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3" />
        <span>Loading anomaly detection audit...</span>
      </div>
    );
  }

  const { overall_metrics, by_anomaly_type } = data.evaluation_metrics;

  const severityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
      case 'HIGH':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'MEDIUM':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Explanation Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-start space-x-3">
        <Info className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <h3 className="font-semibold text-white">Automated Anomaly Detection & Ground Truth Architecture</h3>
          <p className="text-slate-400">
            The platform executes deterministic rule-based anomaly detection completely independently of ground truth labels.
            Ground truth is stored separately in <code className="text-emerald-400 font-mono">ground_truth.json</code> and is never leaked into detection or attribution feature inputs.
            It is utilized strictly for post-detection validation to measure Precision, Recall, and F1.
          </p>
        </div>
      </div>

      {/* Ground Truth Evaluation Scorecard */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-emerald-500/30 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Ground Truth Evaluation Scorecard
              </h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Comparing engine detection decisions against verified ground truth baseline
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-center px-4 py-2 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Precision</span>
              <span className="text-lg font-bold font-mono text-emerald-400">{(overall_metrics.precision * 100).toFixed(1)}%</span>
            </div>
            <div className="text-center px-4 py-2 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Recall</span>
              <span className="text-lg font-bold font-mono text-emerald-400">{(overall_metrics.recall * 100).toFixed(1)}%</span>
            </div>
            <div className="text-center px-4 py-2 bg-slate-950 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">F1-Score</span>
              <span className="text-lg font-bold font-mono text-emerald-400">{(overall_metrics.f1_score * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Breakdown by 5 Anomaly Scenarios */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Mandatory Scenario</th>
                <th className="py-2.5 px-3 text-right">Ground Truth</th>
                <th className="py-2.5 px-3 text-right">Detected</th>
                <th className="py-2.5 px-3 text-right">True Pos (TP)</th>
                <th className="py-2.5 px-3 text-right">False Pos (FP)</th>
                <th className="py-2.5 px-3 text-right">False Neg (FN)</th>
                <th className="py-2.5 px-3 text-right text-emerald-400">Precision</th>
                <th className="py-2.5 px-3 text-right text-emerald-400">Recall</th>
                <th className="py-2.5 px-3 text-right text-emerald-400">F1 Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 font-mono">
              {Object.entries(by_anomaly_type).map(([type, stats]) => (
                <tr key={type} className="hover:bg-slate-800/20">
                  <td className="py-2.5 px-3 font-sans font-medium text-white flex items-center space-x-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>{type.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-300">{stats.ground_truth_count}</td>
                  <td className="py-2.5 px-3 text-right text-slate-300">{stats.detected_count}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">{stats.true_positives}</td>
                  <td className="py-2.5 px-3 text-right text-slate-400">{stats.false_positives}</td>
                  <td className="py-2.5 px-3 text-right text-slate-400">{stats.false_negatives}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-emerald-400">{(stats.precision * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-right font-bold text-emerald-400">{(stats.recall * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-right font-bold text-emerald-400">{(stats.f1_score * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Filter and Table of Anomaly Issue Records */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden space-y-4 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h4 className="text-sm font-semibold text-white">Quarantined Anomaly Records Log ({data.total_anomalies})</h4>
            <p className="text-xs text-slate-400">Audit trail of isolated exception records and mitigation actions</p>
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Issue Types</option>
              <option value="DUPLICATE_REVENUE">Duplicate Revenue</option>
              <option value="POST_CONVERSION_TOUCHPOINT">Post-Conversion Touchpoint</option>
              <option value="CURRENCY_MISMATCH">Currency Mismatch</option>
              <option value="MISSING_CAMPAIGN_COST">Missing Campaign Cost</option>
              <option value="UNSUPPORTED_IDENTITY_LINK">Unsupported Identity Link</option>
            </select>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto -mx-5">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-y border-slate-800">
              <tr>
                <th className="py-2.5 px-4">Issue ID</th>
                <th className="py-2.5 px-4">Entity Type</th>
                <th className="py-2.5 px-4">Entity ID</th>
                <th className="py-2.5 px-4">Issue Type</th>
                <th className="py-2.5 px-4">Severity</th>
                <th className="py-2.5 px-4">Description</th>
                <th className="py-2.5 px-4">Actual Mitigation</th>
                <th className="py-2.5 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 font-sans">
              {data.issues.slice(0, 30).map((iss) => (
                <tr key={iss.issue_id} className="hover:bg-slate-800/30">
                  <td className="py-2.5 px-4 font-mono text-emerald-400 font-medium">{iss.issue_id}</td>
                  <td className="py-2.5 px-4 font-mono text-slate-400">{iss.entity_type}</td>
                  <td className="py-2.5 px-4 font-mono text-white max-w-[140px] truncate">{iss.entity_id}</td>
                  <td className="py-2.5 px-4 font-medium text-slate-200">{iss.issue_type.replace(/_/g, ' ')}</td>
                  <td className="py-2.5 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${severityBadge(iss.severity)}`}>
                      {iss.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-slate-300 max-w-sm truncate" title={iss.description}>
                    {iss.description}
                  </td>
                  <td className="py-2.5 px-4 font-mono text-[11px] text-emerald-300">
                    {iss.actual_decision}
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30">
                      {iss.resolution_status}
                    </span>
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
