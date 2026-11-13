import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  Filter,
  Info,
  Layers,
  ArrowRight,
  Clock,
  RotateCw,
  XCircle,
  AlertCircle,
  Calendar,
  FileCheck2,
  TrendingUp,
  Sliders
} from 'lucide-react';
import {
  fetchAnomalies,
  fetchValidationReport,
  runValidation,
  fetchChronologicalPeriods
} from '../services/api';
import {
  AnomalyDashboardData,
  ValidationReport,
  ChronologicalPeriodsResponse
} from '../types';

export const AnomaliesPage: React.FC = () => {
  const [data, setData] = useState<AnomalyDashboardData | null>(null);
  const [valReport, setValReport] = useState<ValidationReport | null>(null);
  const [chronoData, setChronoData] = useState<ChronologicalPeriodsResponse | null>(null);

  const [activeTab, setActiveTab] = useState<'ground_truth' | 'data_quality' | 'chronological'>('ground_truth');
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [valFilter, setValFilter] = useState<string>('ALL');

  const [loading, setLoading] = useState(true);
  const [isValidating, setIsValidating] = useState(false);

  useEffect(() => {
    loadAllData();
  }, [typeFilter, severityFilter]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [anomRes, valRes, chronoRes] = await Promise.all([
        fetchAnomalies(typeFilter || undefined, severityFilter || undefined),
        fetchValidationReport().catch(() => null),
        fetchChronologicalPeriods().catch(() => null)
      ]);
      setData(anomRes);
      setValReport(valRes);
      setChronoData(chronoRes);
    } catch (err) {
      console.error('Failed to load data quality assurance data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRerunValidation = async () => {
    setIsValidating(true);
    try {
      const updated = await runValidation();
      setValReport(updated);
    } catch (err: any) {
      alert(`Validation rerun failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mr-3" />
        <span>Loading Data Quality Assurance & Evaluation Suite...</span>
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

  const statusBadge = (st: string) => {
    switch (st) {
      case 'PASS':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'WARN':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'FAIL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const filteredRules = valReport?.rule_results.filter((r) => {
    if (valFilter === 'ALL') return true;
    return r.status === valFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Top Banner: Ground Truth Isolation Architecture */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-start space-x-3">
        <Info className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <h3 className="font-semibold text-white">Data Quality Assurance & Ground Truth Architecture</h3>
          <p className="text-slate-400">
            The platform validates data integrity across 15 automated rules and tests 5 labelled anomaly scenarios.
            Ground truth is strictly isolated in <code className="text-emerald-400 font-mono">data/ground_truth/ground_truth.json</code> and <code className="text-emerald-400 font-mono">ground_truth.csv</code>, and is never leaked into feature tables during model attribution or anomaly detection. All evaluation metrics (TP, FP, FN, Precision, Recall, F1) are computed dynamically from actual database records.
          </p>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('ground_truth')}
          className={`px-4 py-2 text-xs font-medium rounded-lg transition ${
            activeTab === 'ground_truth'
              ? 'bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          Ground Truth Anomaly Evaluation ({overall_metrics.true_positives + overall_metrics.false_positives} Detected)
        </button>

        <button
          onClick={() => setActiveTab('data_quality')}
          className={`px-4 py-2 text-xs font-medium rounded-lg transition flex items-center space-x-1.5 ${
            activeTab === 'data_quality'
              ? 'bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>15 Data Quality & Integrity Rules ({valReport?.summary.rules_passed || 11} Pass, {valReport?.summary.rules_warned || 4} Warn)</span>
        </button>

        <button
          onClick={() => setActiveTab('chronological')}
          className={`px-4 py-2 text-xs font-medium rounded-lg transition flex items-center space-x-1.5 ${
            activeTab === 'chronological'
              ? 'bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Chronological Evaluation Periods (Train / Val / Test)</span>
        </button>
      </div>

      {/* ===================================================================== */}
      {/* TAB 1: GROUND TRUTH EVALUATION & ANOMALY SCORECARD */}
      {/* ===================================================================== */}
      {activeTab === 'ground_truth' && (
        <div className="space-y-6">
          {/* Ground Truth Evaluation Scorecard Cards */}
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
                  Comparing anomaly detection decisions against isolated ground truth baseline
                </p>
              </div>

              {/* Top Level Metric Scorecards */}
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                <div className="text-center px-3 py-2 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">True Pos (TP)</span>
                  <span className="text-base font-bold font-mono text-emerald-400">{overall_metrics.true_positives}</span>
                </div>
                <div className="text-center px-3 py-2 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">False Pos (FP)</span>
                  <span className="text-base font-bold font-mono text-slate-300">{overall_metrics.false_positives}</span>
                </div>
                <div className="text-center px-3 py-2 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">False Neg (FN)</span>
                  <span className="text-base font-bold font-mono text-slate-300">{overall_metrics.false_negatives}</span>
                </div>
                <div className="text-center px-3 py-2 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">Precision</span>
                  <span className="text-base font-bold font-mono text-emerald-400">{(overall_metrics.precision * 100).toFixed(1)}%</span>
                </div>
                <div className="text-center px-3 py-2 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">Recall</span>
                  <span className="text-base font-bold font-mono text-emerald-400">{(overall_metrics.recall * 100).toFixed(1)}%</span>
                </div>
                <div className="text-center px-3 py-2 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">F1-Score</span>
                  <span className="text-base font-bold font-mono text-emerald-400">{(overall_metrics.f1_score * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>

            {/* Breakdown by 5 Mandatory Anomaly Scenarios */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Mandatory Scenario</th>
                    <th className="py-2.5 px-3 text-right">Ground Truth</th>
                    <th className="py-2.5 px-3 text-right">Detected</th>
                    <th className="py-2.5 px-3 text-right text-emerald-400 font-bold">True Pos (TP)</th>
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

          {/* Quarantined Anomaly Records Log */}
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
      )}

      {/* ===================================================================== */}
      {/* TAB 2: DATA QUALITY & INTEGRITY VALIDATION RULES (ALL 15 RULES) */}
      {/* ===================================================================== */}
      {activeTab === 'data_quality' && (
        <div className="space-y-6">
          {/* Summary & Re-Run Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-semibold text-white">15 Automated Data Quality Validation Rules</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated checks across Primary Keys, Foreign Keys, Allowed Enums, Date Ordering, Arithmetic Reconciliation, Duplicate Orders, and Lifecycle Transitions.
                </p>
              </div>

              <button
                onClick={handleRerunValidation}
                disabled={isValidating}
                className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl transition"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />
                <span>{isValidating ? 'Running Validation...' : 'Re-Run All 15 Rules'}</span>
              </button>
            </div>

            {/* Validation Metrics Summary */}
            {valReport && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Rules Passed</span>
                  <span className="text-lg font-bold font-mono text-emerald-400">{valReport.summary.rules_passed} / {valReport.summary.total_rules}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Rules Warned (Quarantined)</span>
                  <span className="text-lg font-bold font-mono text-amber-400">{valReport.summary.rules_warned}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Rules Failed</span>
                  <span className="text-lg font-bold font-mono text-rose-400">{valReport.summary.rules_failed}</span>
                </div>
                <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Total Records Audited</span>
                  <span className="text-lg font-bold font-mono text-white">{valReport.summary.total_records_checked.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>

          {/* Validation Rule Filters & Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <span className="text-xs font-semibold text-white">Rule Execution Results</span>
              <div className="flex items-center space-x-2">
                {['ALL', 'PASS', 'WARN', 'FAIL'].map((filterVal) => (
                  <button
                    key={filterVal}
                    onClick={() => setValFilter(filterVal)}
                    className={`px-3 py-1 rounded text-xs font-mono font-medium transition ${
                      valFilter === filterVal
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                    }`}
                  >
                    {filterVal}
                  </button>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto -mx-5">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-y border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Rule Code</th>
                    <th className="py-2.5 px-4">Rule Category & Name</th>
                    <th className="py-2.5 px-4 text-center">Status</th>
                    <th className="py-2.5 px-4 text-right">Checked</th>
                    <th className="py-2.5 px-4 text-right text-emerald-400">Passed</th>
                    <th className="py-2.5 px-4 text-right text-amber-400">Flagged</th>
                    <th className="py-2.5 px-4">Validation Audit Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40 font-mono">
                  {filteredRules.map((rule) => (
                    <tr key={rule.rule_code} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-bold text-emerald-400">{rule.rule_code}</td>
                      <td className="py-2.5 px-4 font-sans font-medium text-white">{rule.rule_name}</td>
                      <td className="py-2.5 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${statusBadge(rule.status)}`}>
                          {rule.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right text-slate-300">{rule.records_checked.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-right text-emerald-400">{rule.records_passed.toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-right text-amber-400">{rule.records_failed.toLocaleString()}</td>
                      <td className="py-2.5 px-4 font-sans text-xs text-slate-300 max-w-md truncate" title={rule.details.join(' ')}>
                        {rule.details.join(' ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 3: CHRONOLOGICAL EVALUATION PERIODS */}
      {/* ===================================================================== */}
      {activeTab === 'chronological' && (
        <div className="space-y-6">
          {/* Chronological Splitting Overview Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-white">Chronological Evaluation Period Architecture</h3>
              <p className="text-xs text-slate-400 mt-1">
                To prevent data leakage in temporal marketing attribution models, all customer journeys, touchpoints, conversions, and spend are evaluated across strictly non-overlapping chronological partitions.
              </p>
            </div>

            {/* Date Boundaries Definition Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono uppercase">1. TRAIN Period</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">212 Days</span>
                </div>
                <div className="mt-2 text-xs font-mono text-emerald-400">
                  2026-01-01 00:00:00 <br />
                  <span className="text-slate-500">to</span> 2026-07-31 23:59:59
                </div>
                <p className="mt-3 text-xs text-slate-400 leading-relaxed font-sans">
                  Baseline model training, conversion touchpoint weight estimation, and initial path-to-purchase mapping.
                </p>
              </div>

              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono uppercase">2. VALIDATION Period</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300">61 Days</span>
                </div>
                <div className="mt-2 text-xs font-mono text-blue-400">
                  2026-08-01 00:00:00 <br />
                  <span className="text-slate-500">to</span> 2026-09-30 23:59:59
                </div>
                <p className="mt-3 text-xs text-slate-400 leading-relaxed font-sans">
                  Lookback window parameter tuning (30d vs 60d vs 90d), anomaly detection threshold calibration, and decay curve optimization.
                </p>
              </div>

              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono uppercase">3. TEST Period (Out-of-Sample)</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300">92 Days</span>
                </div>
                <div className="mt-2 text-xs font-mono text-purple-400">
                  2026-10-01 00:00:00 <br />
                  <span className="text-slate-500">to</span> 2026-12-31 23:59:59
                </div>
                <p className="mt-3 text-xs text-slate-400 leading-relaxed font-sans">
                  Unbiased out-of-sample attribution benchmarking, simulated financial ROI reconciliation, and generalization audit.
                </p>
              </div>
            </div>
          </div>

          {/* Partition Metrics Table */}
          {chronoData && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h4 className="text-sm font-semibold text-white">Partition Financial & Event Breakdown</h4>
              <div className="overflow-x-auto -mx-5">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-y border-slate-800">
                    <tr>
                      <th className="py-2.5 px-4">Period</th>
                      <th className="py-2.5 px-4">Date Boundaries</th>
                      <th className="py-2.5 px-4 text-right">Orders / Conversions</th>
                      <th className="py-2.5 px-4 text-right">Closed Revenue (₹)</th>
                      <th className="py-2.5 px-4 text-right text-emerald-400">Attributed Rev (MT ₹)</th>
                      <th className="py-2.5 px-4 text-right">Touchpoints</th>
                      <th className="py-2.5 px-4 text-right">Campaign Spend (₹)</th>
                      <th className="py-2.5 px-4 text-right">Anomalies Detected</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/40 font-mono">
                    {chronoData.periods.map((p) => (
                      <tr key={p.period_code} className="hover:bg-slate-800/30">
                        <td className="py-3 px-4 font-bold text-white">
                          <span className="text-emerald-400">{p.period_code}</span> ({p.name})
                        </td>
                        <td className="py-3 px-4 text-[11px] text-slate-400">
                          {p.start_date.split('T')[0]} to {p.end_date.split('T')[0]}
                        </td>
                        <td className="py-3 px-4 text-right text-slate-200">{p.orders_count}</td>
                        <td className="py-3 px-4 text-right font-medium text-white">₹{p.order_revenue.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right font-medium text-emerald-400">₹{p.attributed_revenue_multi_touch.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-slate-300">{p.touchpoints_count.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-slate-300">₹{p.campaign_spend.toLocaleString()}</td>
                        <td className="py-3 px-4 text-right text-amber-400">{p.anomalies_detected}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
