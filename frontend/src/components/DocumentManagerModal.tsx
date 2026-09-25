import React, { useState, useEffect } from "react";
import { FolderOpen, Upload, Database, CheckCircle, AlertCircle, X, RefreshCw, FileText } from "lucide-react";
import type { DocumentRecord } from "../types/cogent";
import { apiClient } from "../api/client";

interface DocumentManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentManagerModal: React.FC<DocumentManagerModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [indexingDocId, setIndexingDocId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.getDocuments();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDocs();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      await apiClient.uploadDocument(file);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message || "Upload and Layer 3 acquisition failed");
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const handleExplicitIndex = async (docId: string) => {
    setIndexingDocId(docId);
    setError(null);
    try {
      await apiClient.indexDocument(docId);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message || "Layer 4 indexing failed");
    } finally {
      setIndexingDocId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="w-full max-w-3xl glass-panel rounded-2xl p-6 border border-slate-800 shadow-2xl bg-slate-900/95 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <FolderOpen className="w-4 h-4 text-cyan-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Corpus Management & Layer 4 Indexing
              </h3>
              <p className="text-xs text-slate-400">
                L3 Acquisition & structural chunking separated from explicit L4 FAISS/BM25 indexing
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={fetchDocs}
              disabled={isLoading}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-950/40 border border-red-500/30 text-xs text-red-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Upload Zone */}
        <div className="mb-6 p-4 rounded-xl bg-slate-950/60 border border-dashed border-slate-800 hover:border-cyan-500/50 transition-all flex flex-col items-center justify-center text-center">
          <Upload className="w-8 h-8 text-cyan-400 mb-2 opacity-80" />
          <p className="text-xs font-semibold text-slate-200 mb-1">
            Ingest Knowledge Unit into Layer 3
          </p>
          <p className="text-[11px] text-slate-500 mb-3 max-w-sm">
            Parses text/PDF with Late Chunking and TROVE provenance breadcrumbs
          </p>
          <label className="cursor-pointer px-4 py-2 rounded-lg text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-500 shadow-md shadow-cyan-600/20 transition-all flex items-center space-x-2">
            <span>{isUploading ? "Extracting Chunks..." : "Choose File to Upload"}</span>
            <input
              type="file"
              accept=".txt,.pdf,.md"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
            />
          </label>
        </div>

        {/* Documents Table */}
        <div className="flex-1 overflow-y-auto pr-1">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Acquired Documents ({documents.length})
          </h4>

          {isLoading && documents.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 border border-slate-800 rounded-xl">
              No documents acquired yet. Ingest documents to ground your research engine.
            </div>
          ) : (
            <div className="space-y-2.5">
              {documents.map((doc) => {
                const isIndexed = doc.indexing_status === "INDEXED";
                const isIndexing = indexingDocId === doc.id;

                return (
                  <div
                    key={doc.id}
                    className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center space-x-3 truncate">
                      <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4 text-slate-400" />
                      </div>
                      <div className="truncate">
                        <p className="text-xs font-semibold text-slate-200 truncate">
                          {doc.filename}
                        </p>
                        <div className="flex items-center space-x-2 text-[10px] text-slate-400 font-mono">
                          <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                          <span>•</span>
                          <span>{doc.chunk_count} Chunks</span>
                          <span>•</span>
                          <span className="text-cyan-400">{doc.status}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 shrink-0">
                      {isIndexed ? (
                        <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          <CheckCircle className="w-3 h-3" />
                          <span>INDEXED (L4)</span>
                        </span>
                      ) : (
                        <button
                          onClick={() => handleExplicitIndex(doc.id)}
                          disabled={isIndexing}
                          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 transition-all disabled:opacity-50"
                        >
                          {isIndexing ? (
                            <>
                              <RefreshCw className="w-3 h-3 animate-spin" />
                              <span>Indexing...</span>
                            </>
                          ) : (
                            <>
                              <Database className="w-3 h-3" />
                              <span>Index into FAISS/BM25</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
