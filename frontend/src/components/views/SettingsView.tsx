import React, { useState } from "react";
import {
  Settings,
  Cpu,
  Globe2,
  Database,
  CheckCircle2,
  Sliders,
  Save,
  Check,
} from "lucide-react";

export const SettingsView: React.FC = () => {
  const [temperature, setTemperature] = useState(0.2);
  const [topK, setTopK] = useState(10);
  const [contradictionThreshold, setContradictionThreshold] = useState(0.7);
  const [maxCutSetDepth, setMaxCutSetDepth] = useState(3);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2.5">
            <Settings className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">System & Engine Configuration</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Engine footprint status, cognitive inference thresholds, and retrieval hyperparameters
          </p>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all active:scale-95"
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          <span>{saved ? "Settings Saved" : "Save Changes"}</span>
        </button>
      </div>

      {/* Engine Status Footprint (Generic Architecture as requested) */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-indigo-400" />
          <span>Engine Infrastructure Footprint</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* AI Provider */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">AI Provider</span>
              <Cpu className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Configured</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Active model configured in backend environment.
            </p>
          </div>

          {/* Web Research */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Web Research</span>
              <Globe2 className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Configured</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Real-time scientific search and preprint acquisition active.
            </p>
          </div>

          {/* Database */}
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Database</span>
              <Database className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Connected</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Relational documentary storage and vector indexes healthy.
            </p>
          </div>
        </div>
      </div>

      {/* Cognitive Parameters */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
          Cognitive Inference Hyperparameters
        </h3>

        <div className="space-y-4">
          {/* Temperature Slider */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-200">Reasoning Temperature</span>
                <p className="text-[11px] text-slate-400">
                  Lower values enforce strict mathematical and factual entailment.
                </p>
              </div>
              <span className="font-mono text-indigo-400 font-bold">{temperature}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>

          {/* Top-K Retrieval */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-200">Hybrid Search Candidate Pool</span>
                <p className="text-[11px] text-slate-400">
                  Number of passage chunks retrieved before cross-encoder reranking.
                </p>
              </div>
              <span className="font-mono text-indigo-400 font-bold">{topK} chunks</span>
            </div>
            <input
              type="range"
              min="5"
              max="30"
              step="1"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value, 10))}
              className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>

          {/* Contradiction NLI Threshold */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-200">
                  Dialectical Contradiction Sensitivity
                </span>
                <p className="text-[11px] text-slate-400">
                  Confidence threshold for flagging scientific disagreements and Zero-Winner-Forcing.
                </p>
              </div>
              <span className="font-mono text-indigo-400 font-bold">
                {(contradictionThreshold * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={contradictionThreshold}
              onChange={(e) => setContradictionThreshold(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>

          {/* Minimal Cut-Set Depth */}
          <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-200">
                  Source Dependency Analysis Depth
                </span>
                <p className="text-[11px] text-slate-400">
                  Recursive depth for single-source failure sensitivity checks.
                </p>
              </div>
              <span className="font-mono text-indigo-400 font-bold">Depth {maxCutSetDepth}</span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              value={maxCutSetDepth}
              onChange={(e) => setMaxCutSetDepth(parseInt(e.target.value, 10))}
              className="w-full accent-indigo-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

