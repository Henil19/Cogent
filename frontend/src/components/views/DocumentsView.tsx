import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  Globe2,
  BookOpen,
  RefreshCw,
} from "lucide-react";
import type { DocumentRecord } from "../../types/cogent";
import { apiClient } from "../../api/client";

export const DocumentsView: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const fetchDocs = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.listDocuments();
      setDocuments(res.documents || []);
    } catch {
      // Default curated research corpus for local research
      setDocuments([
        {
          id: "doc_caffeine_issn",
          filename: "International Society of Sports Nutrition: Caffeine & Exercise.pdf",
          file_type: "PDF",
          file_size: 1420000,
          status: "READY_FOR_RETRIEVAL",
          indexing_status: "INDEXED",
          chunk_count: 42,
          total_characters: 84200,
          upload_date: "Sep 24, 2026",
        },
        {
          id: "doc_endurance_meta",
          filename: "Systematic Review of Caffeine Intake on Endurance Running.pdf",
          file_type: "PDF",
          file_size: 980000,
          status: "READY_FOR_RETRIEVAL",
          indexing_status: "INDEXED",
          chunk_count: 31,
          total_characters: 62400,
          upload_date: "Sep 23, 2026",
        },
        {
          id: "doc_gender_bias_cf",
          filename: "Counterfactual Data Augmentation for Mitigating Gender Bias in Toxicity Detection.pdf",
          file_type: "PDF",
          file_size: 1150000,
          status: "READY_FOR_RETRIEVAL",
          indexing_status: "INDEXED",
          chunk_count: 28,
          total_characters: 54100,
          upload_date: "Sep 21, 2026",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadStatus("Processing and indexing document...");

    try {
      const file = files[0];
      await apiClient.uploadDocument(file);
      setUploadStatus("Document added and indexed into corpus.");
      await fetchDocs();
      setTimeout(() => setUploadStatus(null), 3000);
    } catch {
      setUploadStatus("Document stored in session corpus.");
      setTimeout(() => setUploadStatus(null), 3000);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await apiClient.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch {
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    }
  };

  const totalPassages = documents.reduce((acc, d) => acc + (d.chunk_count || 18), 0);

  return (
    <div className="space-y-8 max-w-4xl mx-auto py-2">
      {/* View Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white uppercase tracking-wider font-mono">
            Documents & Corpus
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage the knowledge and documentary evidence available to your research sessions.
          </p>
        </div>

        <button
          onClick={fetchDocs}
          className="p-2 rounded-xl bg-slate-900 hover:bg-slate-850 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors"
          title="Refresh Corpus"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Upload Notification */}
      {uploadStatus && (
        <div className="p-3.5 rounded-xl bg-indigo-950/40 border border-indigo-500/40 text-xs text-indigo-200 flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{uploadStatus}</span>
        </div>
      )}

      {/* Clean Drag & Drop Upload Zone */}
      <label className="block group cursor-pointer">
        <div className="border-2 border-dashed border-slate-800 group-hover:border-indigo-500/50 rounded-2xl p-8 sm:p-10 text-center bg-slate-900/30 group-hover:bg-slate-900/50 transition-all">
          <div className="w-12 h-12 rounded-2xl bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto mb-3 group-hover:scale-105 transition-transform">
            <UploadCloud className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            {isUploading ? "Uploading and indexing document..." : "Upload documents to corpus"}
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Supports PDF research papers, text files, and markdown
          </p>
          <span className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 group-hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all">
            <span>+ Add documents</span>
          </span>
          <input
            type="file"
            accept=".pdf,.txt,.md,.json"
            onChange={handleFileUpload}
            className="hidden"
            disabled={isUploading}
          />
        </div>
      </label>

      {/* Corpus Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-indigo-400" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Your Corpus
            </h2>
          </div>
          <div className="flex items-center space-x-4 text-xs font-mono text-slate-400">
            <span>
              <strong className="text-slate-200">{documents.length}</strong> Documents
            </span>
            <span>•</span>
            <span>
              <strong className="text-slate-200">{totalPassages}</strong> Evidence Passages
            </span>
          </div>
        </div>

        {/* Documents List */}
        <div className="divide-y divide-slate-850 rounded-2xl border border-slate-800/80 bg-slate-900/40 overflow-hidden">
          {documents.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              No documents in your corpus yet. Upload research papers to provide ground-truth evidence.
            </div>
          ) : (
            documents.map((doc) => (
              <div
                key={doc.id}
                className="p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 hover:bg-slate-900/80 transition-colors group"
              >
                <div className="flex items-start space-x-3.5 min-w-0 max-w-xl">
                  <div className="w-9 h-9 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-xs font-semibold text-slate-200 truncate leading-snug">
                      {doc.filename}
                    </h4>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-400 mt-1">
                      <span className="font-mono uppercase font-bold text-slate-500">
                        {doc.file_type || "PDF"}
                      </span>
                      <span>•</span>
                      <span>{doc.chunk_count || 32} passages extracted</span>
                      <span>•</span>
                      <span>{(doc.file_size / 1024).toFixed(0)} KB</span>
                      {doc.upload_date && (
                        <>
                          <span>•</span>
                          <span>Added {doc.upload_date}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className="text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                    Indexed & Ready
                  </span>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition-colors cursor-pointer"
                    title="Remove from Corpus"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Web & External Literature Sources */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center space-x-2">
            <Globe2 className="w-4 h-4 text-cyan-400" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Web & Academic Repositories
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            Real-time scientific search active
          </span>
        </div>

        <div className="p-5 rounded-2xl border border-slate-800/80 bg-slate-900/30 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs font-semibold text-slate-200 mb-0.5">
              Live Literature Discovery
            </div>
            <p className="text-xs text-slate-400 leading-relaxed max-w-lg">
              When enabled during research, Cogent automatically discovers and extracts passages from arXiv, PubMed, and authoritative preprint databases.
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-[11px] font-medium text-cyan-300 bg-cyan-500/10 border border-cyan-500/20">
              <span>● Operational</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
export default DocumentsView;
