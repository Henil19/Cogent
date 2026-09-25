import React from "react";
import { BarChart3, Activity, Zap, ShieldCheck, TrendingUp } from "lucide-react";

export const AnalyticsView: React.FC = () => {
  const layerLatencies = [
    { code: "01", name: "Clarification & Scope", ms: 420, pct: 10 },
    { code: "02", name: "Research Strategy & DAG", ms: 610, pct: 15 },
    { code: "03", name: "Literature Acquisition", ms: 890, pct: 22 },
    { code: "04", name: "Hybrid Search & Fusion", ms: 380, pct: 9 },
    { code: "05", name: "Dialectical Verification", ms: 750, pct: 18 },
    { code: "06", name: "Logical Entailment DAG", ms: 510, pct: 12 },
    { code: "07", name: "Trust Calibration", ms: 240, pct: 6 },
    { code: "08", name: "Source Robustness", ms: 180, pct: 4 },
    { code: "09", name: "Synthesis & BLUF", ms: 120, pct: 3 },
    { code: "10", name: "System Diagnostics", ms: 40, pct: 1 },
  ];

  const totalMs = layerLatencies.reduce((sum, l) => sum + l.ms, 0);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2.5">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Telemetry & Longitudinal Analytics</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Aggregated empirical calibration curves, latency waterfall, and layer-by-layer telemetry
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono text-indigo-400 bg-indigo-950/40 px-3 py-1.5 rounded-xl border border-indigo-500/30">
          <span>Avg End-to-End Latency: {(totalMs / 1000).toFixed(2)}s</span>
        </div>
      </div>

      {/* Top Level Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl glass-panel border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Expected Calibration Error</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-emerald-400">0.041</div>
          <p className="text-[11px] text-slate-500">Target &le; 0.080 (Well-Calibrated)</p>
        </div>

        <div className="p-4 rounded-xl glass-panel border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Brier Score</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-cyan-400">0.086</div>
          <p className="text-[11px] text-slate-500">Quadratic scoring rule accuracy</p>
        </div>

        <div className="p-4 rounded-xl glass-panel border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Dialectical Resolution</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-indigo-300">92.4%</div>
          <p className="text-[11px] text-slate-500">Synthesized or contextualized</p>
        </div>

        <div className="p-4 rounded-xl glass-panel border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Cache Hit Rate</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold font-mono text-amber-300">68.5%</div>
          <p className="text-[11px] text-slate-500">Layer 4 semantic embeddings</p>
        </div>
      </div>

      {/* Cross-Execution Empirical Calibration Curve / Reliability Diagram */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Longitudinal Calibration Reliability Diagram
            </h3>
            <p className="text-[11px] text-slate-400">
              Predicted confidence vs empirical entailment accuracy across 150+ benchmark inquiries
            </p>
          </div>
          <span className="text-[10px] font-semibold text-emerald-300 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
            Calibrated Distribution
          </span>
        </div>

        {/* Reliability Bin Matrix */}
        <div className="space-y-2 pt-2">
          {[
            { bin: "0.0 - 0.2", count: 12, predicted: 0.12, observed: 0.11 },
            { bin: "0.2 - 0.4", count: 24, predicted: 0.32, observed: 0.34 },
            { bin: "0.4 - 0.6", count: 45, predicted: 0.51, observed: 0.49 },
            { bin: "0.6 - 0.8", count: 86, predicted: 0.73, observed: 0.75 },
            { bin: "0.8 - 1.0", count: 130, predicted: 0.91, observed: 0.92 },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs"
            >
              <div className="flex items-center space-x-3">
                <span className="font-mono text-indigo-400 font-semibold w-16">
                  {item.bin}
                </span>
                <span className="text-slate-400 text-[11px]">
                  ({item.count} evaluations)
                </span>
              </div>

              <div className="flex items-center space-x-6">
                <div className="text-[11px] text-slate-400">
                  <span>Pred Conf: </span>
                  <span className="font-mono text-slate-200">
                    {(item.predicted * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="text-[11px] text-slate-400">
                  <span>Empirical Entailment: </span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    {(item.observed * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-24 h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500"
                    style={{ width: `${item.observed * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Latency Waterfall Breakdown (L1 - L10) */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Cognitive Layer Latency Waterfall (L1 → L10)
            </h3>
            <p className="text-[11px] text-slate-400">
              Execution duration profiling per individual reasoning and acquisition stage
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Total: {(totalMs / 1000).toFixed(2)}s
          </span>
        </div>

        <div className="space-y-2.5">
          {layerLatencies.map((layer) => (
            <div key={layer.code} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                    {layer.code}
                  </span>
                  <span className="text-slate-300 font-medium">{layer.name}</span>
                </div>
                <div className="flex items-center space-x-3 font-mono text-[11px] text-slate-400">
                  <span>{layer.ms} ms</span>
                  <span className="text-slate-500 w-8 text-right">{layer.pct}%</span>
                </div>
              </div>

              <div className="w-full h-1.5 rounded-full bg-slate-900 overflow-hidden">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all"
                  style={{ width: `${layer.pct * 3}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
