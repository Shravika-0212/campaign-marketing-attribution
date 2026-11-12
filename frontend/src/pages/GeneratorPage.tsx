import React, { useEffect, useState } from 'react';
import {
  Database,
  Play,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Hash,
  Activity
} from 'lucide-react';
import {
  fetchGeneratorStatus,
  runGenerator,
  fetchValidationReport,
  runValidation
} from '../services/api';
import { GeneratorStatus, ValidationReport } from '../types';

export const GeneratorPage: React.FC = () => {
  const [status, setStatus] = useState<GeneratorStatus | null>(null);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [scale, setScale] = useState<'STARTER' | 'FULL'>('STARTER');
  const [seed, setSeed] = useState(20261022);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const [st, val] = await Promise.all([
        fetchGeneratorStatus(),
        fetchValidationReport().catch(() => null)
      ]);
      setStatus(st);
      setValidationReport(val);
    } catch (err) {
      console.error('Failed to load generator status', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunGenerator = async () => {
    if (!window.confirm(`Are you sure you want to run the ${scale} generator? This will reset the database and regenerate all deterministic entities using seed ${seed}.`)) {
      return;
    }

    setIsGenerating(true);
    try {
      await runGenerator(scale, seed);
      await loadStatus();
      alert(`Generation completed successfully! All entities, attribution models, and anomalies have been recomputed.`);
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunValidation = async () => {
    setIsValidating(true);
    try {
      const val = await runValidation();
      setValidationReport(val);
    } catch (err: any) {
      alert(`Validation failed: ${err.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Control Configuration Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-white">Deterministic Synthetic Data Generator</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Configurable dataset scale with seed reproducibility. Both STARTER and FULL scales follow identical deterministic relational logic.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Scale Choice: STARTER */}
          <div
            onClick={() => setScale('STARTER')}
            className={`p-4 rounded-xl border cursor-pointer transition ${
              scale === 'STARTER'
                ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400'
                : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="flex justify-between items-center">
              <span className="text-sm font-bold text-white">STARTER Scale</span>
              {scale === 'STARTER' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              ~50 Campaigns, 1,000 Contacts, 4,000+ Touchpoints, 200 Opportunities.
            </p>
            <span className="inline-block mt-3 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
              Instant Generation (~1.2s)
            </span>
          </div>

          {/* Scale Choice: FULL */}
          <div
            onClick={() => setScale('FULL')}
            className={`p-4 rounded-xl border cursor-pointer transition ${
              scale === 'FULL'
                ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400'
                : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="flex justify-between items-center">
              <span className="text-sm font-bold text-white">FULL Baseline Scale</span>
              {scale === 'FULL' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              500 Campaigns, 50,000 Contacts, 200,000 Touchpoints, 10,000 Opportunities.
            </p>
            <span className="inline-block mt-3 text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300">
              Production Volume (~45s)
            </span>
          </div>

          {/* Seed Configuration */}
          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-xs font-semibold text-white">Controlled Random Seed</span>
              <p className="text-xs text-slate-400 mt-1">
                Enforces exact determinism across random generators.
              </p>
            </div>
            <div className="mt-3 flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5">
              <Hash className="w-4 h-4 text-slate-500" />
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full bg-transparent text-white font-mono text-sm focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Action Triggers */}
        <div className="flex items-center space-x-4 pt-2">
          <button
            onClick={handleRunGenerator}
            disabled={isGenerating}
            className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl transition shadow-lg shadow-emerald-950/30"
          >
            {isGenerating ? <RotateCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{isGenerating ? 'Generating Records...' : `Generate ${scale} Dataset`}</span>
          </button>

          <button
            onClick={handleRunValidation}
            disabled={isValidating}
            className="flex items-center space-x-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-semibold text-xs rounded-xl border border-slate-700 transition"
          >
            {isValidating ? <RotateCw className="w-4 h-4 animate-spin text-emerald-400" /> : <ShieldCheck className="w-4 h-4 text-emerald-400" />}
            <span>{isValidating ? 'Validating 15 Rules...' : 'Run 15 Automated Validation Rules'}</span>
          </button>
        </div>
      </div>

      {/* Generation Audit Status */}
      {status && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800">
            <div>
              <h4 className="text-sm font-semibold text-white">Active Database State & Entity Volumes</h4>
              <p className="text-xs text-slate-400">Current record counts generated under {status.config_name || 'N/A'}</p>
            </div>
            <div className="text-xs font-mono text-slate-400">
              Last Run ID: <span className="text-emerald-400">{status.last_run_id || 'N/A'}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {Object.entries(status.row_counts).map(([entity, count]) => (
              <div key={entity} className="p-3 bg-slate-950 rounded-lg border border-slate-800/80">
                <span className="text-[10px] text-slate-400 font-mono uppercase block">{entity.replace(/_/g, ' ')}</span>
                <span className="text-base font-bold font-mono text-white mt-0.5 block">{count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Report Section */}
      {validationReport && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div>
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h4 className="text-sm font-semibold text-white">15 Automated Integrity Validation Rules</h4>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated: {validationReport.summary.total_records_checked.toLocaleString()} records across database entities
              </p>
            </div>

            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                {validationReport.summary.rules_passed} PASS
              </span>
              <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-bold">
                {validationReport.summary.rules_warned} WARN (Quarantined)
              </span>
              <span className="px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold">
                {validationReport.summary.rules_failed} FAIL
              </span>
            </div>
          </div>

          <div className="space-y-2">
            {validationReport.rule_results.map((r) => (
              <div key={r.rule_code} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex items-start justify-between text-xs">
                <div className="space-y-0.5 max-w-[80%]">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-slate-500 text-[11px]">{r.rule_code}</span>
                    <span className="font-semibold text-white">{r.rule_name}</span>
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    Checked: {r.records_checked} | Passed: {r.records_passed} | Failed/Flagged: {r.records_failed}
                  </div>
                  {r.details.map((d, i) => (
                    <p key={i} className="text-[11px] text-slate-300 italic">{d}</p>
                  ))}
                </div>

                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                  r.status === 'PASS'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
                }`}>
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
