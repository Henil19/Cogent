import React, { useState, useRef } from "react";
import {
  Paperclip,
  ArrowRight,
  BookOpen,
  Globe2,
  Layers,
  X,
  FileText,
  Sparkles,
  Search,
} from "lucide-react";
import type { SourceMode, AttachedFile } from "../types/cogent";

interface QueryCockpitProps {
  onSubmit: (params: {
    query: string;
    sourceMode: SourceMode;
    attachedFiles: AttachedFile[];
  }) => void;
  isProcessing: boolean;
}

const SAMPLE_RESEARCH_QUESTIONS = [
  "Does caffeine improve or impair athletic endurance in distance runners?",
  "Does deep learning outperform gradient boosted trees on tabular data?",
  "What is the empirical trade-off of intermittent fasting on muscle preservation?",
];

export const QueryCockpit: React.FC<QueryCockpitProps> = ({ onSubmit, isProcessing }) => {
  const [query, setQuery] = useState("");
  const [sourceMode, setSourceMode] = useState<SourceMode>("HYBRID");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newAttached: AttachedFile[] = Array.from(files).map((f) => ({
      id: `file_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      name: f.name,
      size: f.size,
      type: f.name.endsWith(".pdf") ? "PDF" : "TXT",
      status: "UPLOADED",
      file: f,
    }));

    setAttachedFiles((prev) => [...prev, ...newAttached]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removeFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || isProcessing) return;
    onSubmit({
      query: query.trim(),
      sourceMode,
      attachedFiles,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 sm:py-14 space-y-8 animate-in fade-in duration-300">
      {/* Centered Hero Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Evidence-Based Research Intelligence</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
          What would you like to research?
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
          Ask a complex question. Cogent investigates peer literature, detects conflicting studies, and explains its exact reasoning.
        </p>
      </div>

      {/* Main Research Input Card */}
      <form
        onSubmit={handleSubmit}
        className="glass-panel rounded-2xl p-4 sm:p-5 border border-slate-800/80 shadow-2xl space-y-4 focus-within:border-indigo-500/50 transition-all bg-slate-900/60"
      >
        <div className="relative">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a scientific, clinical, or technical question..."
            rows={3}
            disabled={isProcessing}
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-base sm:text-lg focus:outline-none resize-none leading-relaxed p-1"
          />
        </div>

        {/* Attached Files List */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/60">
            {attachedFiles.map((file) => (
              <span
                key={file.id}
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300"
              >
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span className="truncate max-w-[180px]">{file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(file.id)}
                  className="p-0.5 text-slate-400 hover:text-rose-400 rounded cursor-pointer"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Controls Bar: Source Mode + Attach + Submit */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/60">
          {/* Source Selection Mode */}
          <div className="flex items-center space-x-1 bg-slate-950/70 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              type="button"
              onClick={() => setSourceMode("HYBRID")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                sourceMode === "HYBRID"
                  ? "bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Hybrid Literature</span>
            </button>

            <button
              type="button"
              onClick={() => setSourceMode("LIVE_WEB")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                sourceMode === "LIVE_WEB"
                  ? "bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Globe2 className="w-3.5 h-3.5" />
              <span>Live Academic</span>
            </button>

            <button
              type="button"
              onClick={() => setSourceMode("DOCUMENTS")}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                sourceMode === "DOCUMENTS"
                  ? "bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Local Documents</span>
            </button>
          </div>

          {/* Right: Attach Files & Submit Button */}
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isProcessing}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <Paperclip className="w-4 h-4" />
              <span className="hidden sm:inline">Add files</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".txt,.pdf,.md"
              multiple
              className="hidden"
            />

            <button
              type="submit"
              disabled={!query.trim() || isProcessing}
              className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                !query.trim() || isProcessing
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                  : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 border border-indigo-500/40 active:scale-[0.98]"
              }`}
            >
              <span>{isProcessing ? "Researching..." : "Research"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Questions */}
      <div className="space-y-3 pt-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block text-center">
          Or try a sample inquiry:
        </span>
        <div className="space-y-2">
          {SAMPLE_RESEARCH_QUESTIONS.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuery(sample)}
              className="w-full p-3 rounded-xl bg-slate-900/40 hover:bg-slate-900/80 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-slate-100 text-left transition-all flex items-center justify-between group cursor-pointer"
            >
              <span className="truncate pr-2">{sample}</span>
              <Search className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 shrink-0 transition-colors" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
