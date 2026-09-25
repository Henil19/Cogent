import React, { useState, useEffect } from "react";
import {
  History,
  Search,
  ArrowRight,
  Calendar,
  Compass,
  RefreshCw,
  Trash2,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import type { SessionRecord } from "../../types/cogent";
import { apiClient } from "../../api/client";

interface HistoryViewProps {
  onSelectQuery?: (queryText: string) => void;
  onOpenSession?: (sessionId: string, queryTitle: string) => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  onSelectQuery,
  onOpenSession,
}) => {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [searchFilter, setSearchFilter] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchSessions = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.listSessions();
      setSessions(res.sessions || []);
    } catch (err) {
      console.error("Failed to fetch sessions from server:", err);
      // Clean empty list - never show fake fallback data
      setSessions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!window.confirm("Delete this research inquiry from database?")) return;
    setDeletingId(sessionId);
    try {
      await apiClient.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err) {
      console.error("Failed to delete session:", err);
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm("Are you sure you want to permanently clear all research session history from Docker PostgreSQL?")) return;
    setIsClearing(true);
    try {
      await apiClient.clearAllSessions();
      setSessions([]);
    } catch (err) {
      console.error("Failed to clear sessions:", err);
    } finally {
      setIsClearing(false);
    }
  };

  const filteredSessions = sessions
    .filter((s) => (s.query_count || 0) > 0 || (s.last_query_preview && s.last_query_preview.trim().length > 0))
    .filter(
      (s) =>
        s.title?.toLowerCase().includes(searchFilter.toLowerCase()) ||
        (s.last_query_preview &&
          s.last_query_preview.toLowerCase().includes(searchFilter.toLowerCase()))
    );

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100">Research History & Inquiries</h2>
              <p className="text-xs text-slate-400">
                Persisted in Docker PostgreSQL. Click any investigation to restore its full results and telemetry.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Filter inquiries..."
              className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <button
            onClick={fetchSessions}
            disabled={isLoading}
            title="Refresh history"
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>

          {sessions.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={isClearing}
              title="Clear all sessions from database"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-medium transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{isClearing ? "Clearing..." : "Clear All"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Sessions Timeline List */}
      <div className="space-y-3">
        {filteredSessions.length === 0 ? (
          <div className="p-12 text-center glass-panel rounded-2xl border border-slate-800/80 text-slate-400 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
              <History className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">
              {searchFilter ? "No matching inquiries found" : "No Research History Yet"}
            </h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
              {searchFilter
                ? `No inquiries matched "${searchFilter}". Try adjusting your query.`
                : "Every research inquiry submitted in the Cockpit is automatically recorded in Docker PostgreSQL. Completed inquiries will appear here ready to be inspected."}
            </p>
          </div>
        ) : (
          filteredSessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onOpenSession && onOpenSession(session.id, session.title)}
              className="glass-panel rounded-2xl p-5 border border-slate-800 hover:border-indigo-500/40 transition-all space-y-3 cursor-pointer group hover:bg-slate-900/60"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-105 transition-transform">
                    <Compass className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                      {session.title || "Research Inquiry"}
                    </h3>
                    <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5">
                      <span className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-500" />
                        <span>
                          {session.created_at
                            ? new Date(session.created_at).toLocaleString([], {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })
                            : "Recent"}
                        </span>
                      </span>
                      <span>•</span>
                      <span>{session.query_count || 1} query cycles</span>
                      {(session as any).confidence_score !== undefined && (session as any).confidence_score !== null && (
                        <>
                          <span>•</span>
                          <span className="flex items-center space-x-1 text-emerald-400">
                            <ShieldCheck className="w-3 h-3" />
                            <span>{Math.round(((session as any).confidence_score || 0) * 100)}% Confidence</span>
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                  {onOpenSession && (
                    <button
                      onClick={() => onOpenSession(session.id, session.title)}
                      className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 transition-all shadow-sm"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>View Results</span>
                    </button>
                  )}

                  {onSelectQuery && session.last_query_preview && (
                    <button
                      onClick={() => onSelectQuery(session.last_query_preview!)}
                      title="Re-open in Cockpit input to run or edit"
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl text-xs text-slate-400 hover:text-slate-200 bg-slate-900 hover:bg-slate-850 border border-slate-800 transition-colors"
                    >
                      <span>Re-run</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}

                  <button
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    disabled={deletingId === session.id}
                    title="Delete inquiry"
                    className="p-1.5 rounded-xl text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {session.last_query_preview && (
                <p className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 leading-relaxed font-sans">
                  "{session.last_query_preview}"
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

