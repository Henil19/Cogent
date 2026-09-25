import React, { useState, useEffect } from "react";
import { History, Plus, Trash2, X, MessageSquare } from "lucide-react";
import type { SessionRecord } from "../types/cogent";
import { apiClient } from "../api/client";

interface SessionDrawerProps {
  isOpen: boolean;
  activeSessionId?: string;
  onSelectSession: (session: SessionRecord) => void;
  onClose: () => void;
}

export const SessionDrawer: React.FC<SessionDrawerProps> = ({
  isOpen,
  activeSessionId,
  onSelectSession,
  onClose,
}) => {
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const loadSessions = async () => {
    setIsLoading(true);
    try {
      const list = await apiClient.getSessions();
      setSessions(list);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadSessions();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const created = await apiClient.createSession(newTitle.trim());
      setNewTitle("");
      await loadSessions();
      onSelectSession(created);
    } catch {
      // ignore
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await apiClient.deleteSession(id);
      await loadSessions();
    } catch {
      // ignore
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm">
      <div className="w-full max-w-sm h-full glass-panel border-l border-slate-800 p-6 flex flex-col justify-between animate-in slide-in-from-right duration-200 bg-slate-900/95">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <History className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-slate-100">Research Sessions</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* New Session Form */}
          <form onSubmit={handleCreate} className="mb-4 flex space-x-2">
            <input
              type="text"
              placeholder="Session topic or title..."
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="flex-1 bg-slate-950 text-xs rounded-lg px-3 py-2 border border-slate-800 focus:border-indigo-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!newTitle.trim()}
              className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50"
            >
              <Plus className="w-4 h-4" />
            </button>
          </form>

          {/* Session List */}
          <div className="space-y-2 overflow-y-auto max-h-[70vh] pr-1">
            {isLoading ? (
              <div className="p-4 text-center text-xs text-slate-500">Loading...</div>
            ) : sessions.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500">No sessions found.</div>
            ) : (
              sessions.map((s) => {
                const isActive = s.id === activeSessionId;
                return (
                  <div
                    key={s.id}
                    onClick={() => {
                      onSelectSession(s);
                      onClose();
                    }}
                    className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      isActive
                        ? "bg-indigo-950/40 border-indigo-500/50"
                        : "bg-slate-950/40 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center space-x-2.5 truncate">
                      <MessageSquare className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <div className="truncate">
                        <p className="text-xs font-medium text-slate-200 truncate">
                          {s.title}
                        </p>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {s.query_count} inquiries
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={(e) => handleDelete(e, s.id)}
                      className="p-1 text-slate-500 hover:text-red-400 rounded transition-colors"
                      title="Delete Session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800 text-[11px] text-slate-500 text-center">
          Persisted in PostgreSQL/SQLite schema
        </div>
      </div>
    </div>
  );
};
