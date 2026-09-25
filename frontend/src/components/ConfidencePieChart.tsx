import React, { useState } from "react";
import { ShieldCheck, BookOpen, Layers, Clock, Scale, Info, PieChart as PieIcon } from "lucide-react";
import type { EpistemicBounds } from "../types/cogent";

interface ConfidencePieChartProps {
  bounds?: EpistemicBounds;
  className?: string;
}

export const ConfidencePieChart: React.FC<ConfidencePieChartProps> = ({
  bounds,
  className = "",
}) => {
  const [activeSegmentIndex, setActiveSegmentIndex] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"pie" | "radial">("pie");

  const rawTrust = bounds?.epistemic_trust_index ?? 0.82;
  const trustPct = Math.round(rawTrust * 100);

  // Five calibrated dimensions
  const coverageVal = Math.round((bounds?.evidence_coverage ?? 0.88) * 100);
  const authorityVal = Math.round((1 - (bounds?.source_uncertainty ?? 0.18)) * 100);
  const depthVal = Math.round((1 - (bounds?.reasoning_uncertainty ?? 0.22)) * 100);
  const recencyVal = Math.round((1 - (bounds?.temporal_uncertainty ?? 0.08)) * 100);
  const consistencyVal = Math.round((1 - (bounds?.conflict ?? 0.05)) * 100);

  const segments = [
    {
      id: "coverage",
      label: "Evidence Coverage",
      score: coverageVal,
      weight: 30, // 30% contribution to confidence composition
      color: "#6366f1", // Indigo
      gradient: "from-indigo-500 to-indigo-600",
      strokeColor: "#818cf8",
      icon: BookOpen,
      desc: "Density and sufficiency of empirical passages across sub-questions",
      status: coverageVal >= 80 ? "Sufficient" : "Partial",
    },
    {
      id: "authority",
      label: "Source Authority",
      score: authorityVal,
      weight: 25, // 25% contribution
      color: "#10b981", // Emerald
      gradient: "from-emerald-500 to-emerald-600",
      strokeColor: "#34d399",
      icon: ShieldCheck,
      desc: "Reputational index, peer-review prestige, and domain consensus",
      status: authorityVal >= 80 ? "Peer-Reviewed" : "Preprint Regimes",
    },
    {
      id: "reasoning",
      label: "Reasoning Rigor",
      score: depthVal,
      weight: 20, // 20% contribution
      color: "#a855f7", // Purple
      gradient: "from-purple-500 to-purple-600",
      strokeColor: "#c084fc",
      icon: Layers,
      desc: "Multi-hop deductive entailment soundness without leaps",
      status: depthVal >= 75 ? "Sound Entailment" : "Contingent",
    },
    {
      id: "recency",
      label: "Temporal Recency",
      score: recencyVal,
      weight: 15, // 15% contribution
      color: "#06b6d4", // Cyan
      gradient: "from-cyan-500 to-cyan-600",
      strokeColor: "#22d3ee",
      icon: Clock,
      desc: "Freshness and time-stability of empirical observations",
      status: recencyVal >= 85 ? "Up-to-Date" : "Historical",
    },
    {
      id: "consistency",
      label: "Consensus / Dialectic",
      score: consistencyVal,
      weight: 10, // 10% contribution
      color: "#f59e0b", // Amber
      gradient: "from-amber-500 to-amber-600",
      strokeColor: "#fbbf24",
      icon: Scale,
      desc: "Absence of unresolved contradictions across literature",
      status: consistencyVal >= 85 ? "High Consensus" : "Preserved Divergence",
    },
  ];

  // SVG Geometry Constants for Pie / Donut
  const center = 100;
  const outerRadius = 82;
  const innerRadius = 54;
  const totalWeight = segments.reduce((sum, s) => sum + s.weight, 0);

  // Helper to calculate SVG donut arc path
  const getCoordinatesForPercent = (percent: number, radius: number) => {
    const x = center + radius * Math.cos(2 * Math.PI * percent - Math.PI / 2);
    const y = center + radius * Math.sin(2 * Math.PI * percent - Math.PI / 2);
    return [x, y];
  };

  let cumulativeWeight = 0;
  const piePaths = segments.map((seg, idx) => {
    const startPercent = cumulativeWeight / totalWeight;
    cumulativeWeight += seg.weight;
    const endPercent = cumulativeWeight / totalWeight;

    // Add tiny gap between slices
    const gap = 0.005;
    const adjStart = startPercent + gap;
    const adjEnd = endPercent - gap;

    const [startXOuter, startYOuter] = getCoordinatesForPercent(adjStart, outerRadius);
    const [endXOuter, endYOuter] = getCoordinatesForPercent(adjEnd, outerRadius);
    const [startXInner, startYInner] = getCoordinatesForPercent(adjEnd, innerRadius);
    const [endXInner, endYInner] = getCoordinatesForPercent(adjStart, innerRadius);

    const largeArcFlag = adjEnd - adjStart > 0.5 ? 1 : 0;

    const pathData = [
      `M ${startXOuter} ${startYOuter}`,
      `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${endXOuter} ${endYOuter}`,
      `L ${startXInner} ${startYInner}`,
      `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${endXInner} ${endYInner}`,
      "Z",
    ].join(" ");

    return {
      ...seg,
      pathData,
      idx,
    };
  });

  const activeSegment = activeSegmentIndex !== null ? segments[activeSegmentIndex] : null;

  return (
    <div className={`glass-panel rounded-2xl p-6 border border-slate-800/80 bg-slate-900/60 shadow-xl space-y-6 ${className}`}>
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <PieIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Confidence & Uncertainty Breakdown
            </h3>
            <p className="text-[11px] text-slate-400">
              Multi-dimensional epistemic calibration across 5 research metrics
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 p-1 rounded-xl bg-slate-950/70 border border-slate-800/80 text-[11px]">
          <button
            onClick={() => setViewMode("pie")}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all cursor-pointer ${
              viewMode === "pie"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Donut Graph
          </button>
          <button
            onClick={() => setViewMode("radial")}
            className={`px-2.5 py-1 rounded-lg font-medium transition-all cursor-pointer ${
              viewMode === "radial"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Radial Bars
          </button>
        </div>
      </div>

      {/* Main Visualization Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Left: SVG Pie / Donut Chart */}
        <div className="md:col-span-5 flex flex-col items-center justify-center relative py-2">
          {viewMode === "pie" ? (
            <div className="relative w-52 h-52 sm:w-56 sm:h-56">
              <svg viewBox="0 0 200 200" className="w-full h-full filter drop-shadow-md">
                {/* Background Ring */}
                <circle
                  cx={center}
                  cy={center}
                  r={(outerRadius + innerRadius) / 2}
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth={outerRadius - innerRadius}
                  opacity="0.4"
                />

                {/* Pie Slices */}
                {piePaths.map((slice) => {
                  const isHovered = activeSegmentIndex === slice.idx;
                  return (
                    <path
                      key={slice.id}
                      d={slice.pathData}
                      fill={slice.color}
                      opacity={activeSegmentIndex === null || isHovered ? 0.92 : 0.35}
                      className="transition-all duration-200 cursor-pointer hover:opacity-100"
                      style={{
                        transform: isHovered ? "scale(1.04)" : "scale(1)",
                        transformOrigin: `${center}px ${center}px`,
                        filter: isHovered ? `drop-shadow(0 0 8px ${slice.color}88)` : "none",
                      }}
                      onMouseEnter={() => setActiveSegmentIndex(slice.idx)}
                      onMouseLeave={() => setActiveSegmentIndex(null)}
                    />
                  );
                })}
              </svg>

              {/* Center Donut Hub */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                  Confidence
                </span>
                <span className="text-3xl sm:text-4xl font-black text-white font-mono tracking-tight leading-none my-0.5">
                  {trustPct}%
                </span>
                <span className="text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  {bounds?.trust_status === "HIGH_CONFIDENCE"
                    ? "High Calibrated"
                    : bounds?.trust_status === "CONDITIONAL"
                    ? "Conditional"
                    : "Calibrated"}
                </span>
              </div>
            </div>
          ) : (
            /* Radial Multi-Ring Gauge */
            <div className="relative w-52 h-52 sm:w-56 sm:h-56 flex items-center justify-center">
              <svg viewBox="0 0 200 200" className="w-full h-full -rotate-90">
                {segments.map((seg, idx) => {
                  const ringRadius = 40 + idx * 9.5;
                  const circumference = 2 * Math.PI * ringRadius;
                  const strokeDashoffset = circumference - (seg.score / 100) * circumference;
                  const isHovered = activeSegmentIndex === idx;

                  return (
                    <g
                      key={seg.id}
                      className="cursor-pointer"
                      onMouseEnter={() => setActiveSegmentIndex(idx)}
                      onMouseLeave={() => setActiveSegmentIndex(null)}
                    >
                      {/* Ring Track */}
                      <circle
                        cx="100"
                        cy="100"
                        r={ringRadius}
                        fill="none"
                        stroke="#1e293b"
                        strokeWidth="5.5"
                        opacity="0.5"
                      />
                      {/* Ring Progress */}
                      <circle
                        cx="100"
                        cy="100"
                        r={ringRadius}
                        fill="none"
                        stroke={seg.color}
                        strokeWidth={isHovered ? "7.5" : "5.5"}
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        opacity={activeSegmentIndex === null || isHovered ? 1 : 0.35}
                        className="transition-all duration-300"
                        style={{
                          filter: isHovered ? `drop-shadow(0 0 6px ${seg.color})` : "none",
                        }}
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Center Value */}
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                <span className="text-[9px] font-mono uppercase text-slate-400">Score</span>
                <span className="text-2xl sm:text-3xl font-black text-white font-mono leading-none">
                  {trustPct}%
                </span>
              </div>
            </div>
          )}

          <span className="text-[11px] text-slate-500 mt-2 text-center">
            {activeSegment ? `Inspecting ${activeSegment.label}` : "Hover on slices to inspect parameters"}
          </span>
        </div>

        {/* Right: Interactive Dimension Breakdown & Legend */}
        <div className="md:col-span-7 space-y-2.5">
          {segments.map((seg, idx) => {
            const isHovered = activeSegmentIndex === idx;

            return (
              <div
                key={seg.id}
                onMouseEnter={() => setActiveSegmentIndex(idx)}
                onMouseLeave={() => setActiveSegmentIndex(null)}
                className={`p-2.5 rounded-xl border transition-all cursor-pointer ${
                  isHovered
                    ? "bg-slate-800/90 border-slate-700 shadow-md scale-[1.01]"
                    : "bg-slate-900/40 border-slate-800/70 hover:bg-slate-900/80"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: seg.color }}
                    />
                    <span className="font-semibold text-slate-200">{seg.label}</span>
                    <span className="text-[10px] text-slate-500 font-mono">({seg.weight}% weight)</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-slate-400 hidden sm:inline">{seg.status}</span>
                    <span className="font-mono font-bold text-slate-100 text-xs">{seg.score}%</span>
                  </div>
                </div>

                {/* Progress Track */}
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${seg.score}%`,
                      backgroundColor: seg.color,
                      boxShadow: isHovered ? `0 0 8px ${seg.color}` : "none",
                    }}
                  />
                </div>

                {/* Hover Detail Expansion */}
                {isHovered && (
                  <p className="text-[11px] text-slate-400 mt-2 leading-relaxed pt-1.5 border-t border-slate-800/60 animate-in fade-in duration-150">
                    {seg.desc}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Uncertainty Drivers / Active Inspection Card */}
      {bounds?.uncertainty_drivers && bounds.uncertainty_drivers.length > 0 && (
        <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/80 flex items-start space-x-2.5 text-xs text-slate-300">
          <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div className="min-w-0">
            <strong className="text-slate-200 font-medium">Epistemic Grounding Note: </strong>
            <span className="text-slate-400">{bounds.uncertainty_drivers[0]}</span>
          </div>
        </div>
      )}
    </div>
  );
};
export default ConfidencePieChart;
