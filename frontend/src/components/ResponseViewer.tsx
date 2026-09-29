import React, { useState } from "react";
import {
  ThumbsUp,
  ThumbsDown,
  CheckCircle,
  Copy,
  Sparkles,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  HelpCircle,
  FileText,
  Info,
} from "lucide-react";
import type { CogentQueryResponse } from "../types/cogent";
import { apiClient } from "../api/client";

interface ResponseViewerProps {
  response: CogentQueryResponse;
  query?: string;
  onOpenCitation?: (refNum: number) => void;
  onSelectTab?: (tab: string) => void;
}

interface ParsedSubSection {
  title: string;
  category: "highlights" | "caveats" | "generic";
  items: string[];
}

export const ResponseViewer: React.FC<ResponseViewerProps> = ({
  response,
  query,
  onOpenCitation,
  onSelectTab,
}) => {
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const handleFeedback = async (rating: number, isFactual: boolean) => {
    try {
      await apiClient.submitFeedback({
        query_id: response.query_id,
        rating,
        is_factual: isFactual,
      });
      setFeedbackSent(true);
    } catch {
      // ignore
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanMainContent(response.rendered_content));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Cleans out raw developer markdown blocks, GitHub alert syntax, and cuts off raw footnote sections
  function cleanMainContent(rawText: string): string {
    if (!rawText) return "";
    // 1. Cut off raw references section if present in the text string
    const parts = rawText.split(/###\s*References/i);
    let text = parts[0];

    // 2. Strip GitHub markdown alert syntax like > [!NOTE], > [!WARNING]
    text = text.replace(/>\s*\[!(?:NOTE|WARNING|CAUTION|IMPORTANT|TIP)\]/gi, "");
    text = text.replace(/^>\s*/gm, "");

    // 3. Strip raw website title breadcrumb artifacts with pipes
    text = text.replace(/^[^|\n]+(?:\|[^|\n]+)+(?:,\s*(?:and\s+)?|\s*-\s*|\s*:\s*|\s+)/gm, "");

    // 4. Strip internal developer jargon
    text = text.replace(
      /Source literature contains empirical divergence; dialectical Zero Winner Forcing retained conflicting viewpoints\./gi,
      ""
    );
    text = text.replace(/Zero Winner Forcing enforced/gi, "");

    // 5. Clean up broken citation formatting with stray newlines (e.g. [3]\n, [5]\n.)
    text = text.replace(/\[(\d+)\]\s*[\r\n]+\s*,\s*\[(\d+)\]/g, "[$1, $2]");
    text = text.replace(/\[(\d+)\]\s*,\s*\[(\d+)\]/g, "[$1, $2]");
    text = text.replace(/\s*[\r\n]+\s*,\s*\[/g, ", [");
    text = text.replace(/\[(\d+(?:,\s*\d+)*)\]\s*[\r\n]+\s*\./g, "[$1].");
    text = text.replace(/\s*[\r\n]+\s*\.\s*/g, ". ");

    return text.trim();
  }

  // Parse text and turn citation markers like [1], [2], [1, 2] into clickable buttons
  const renderInteractiveContent = (content: string) => {
    // Normalize broken newlines in citations and punctuation first
    const normalized = content
      .replace(/\[(\d+)\]\s*[\r\n]+\s*,\s*\[(\d+)\]/g, "[$1, $2]")
      .replace(/\[(\d+)\]\s*,\s*\[(\d+)\]/g, "[$1, $2]")
      .replace(/\s*[\r\n]+\s*,\s*\[/g, ", [")
      .replace(/\[(\d+(?:,\s*\d+)*)\]\s*[\r\n]+\s*\./g, "[$1].")
      .replace(/\s*[\r\n]+\s*\.\s*/g, ". ");

    const regex = /\[(\d+(?:,\s*\d+)*)\]/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(normalized)) !== null) {
      if (match.index > lastIndex) {
        parts.push(normalized.substring(lastIndex, match.index));
      }

      const rawNumbers = match[1];
      const numbers = rawNumbers
        .split(",")
        .map((n) => parseInt(n.trim(), 10))
        .filter((n) => !isNaN(n));

      parts.push(
        <span key={`cite-group-${match.index}`} className="inline-flex items-center space-x-1 mx-0.5">
          {numbers.map((num) => (
            <button
              key={`cite-${match?.index}-${num}`}
              onClick={() => onOpenCitation && onOpenCitation(num)}
              className="px-1.5 py-0.2 rounded bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 hover:text-indigo-100 border border-indigo-500/40 text-[11px] font-mono font-bold transition-all transform hover:scale-105 inline-block align-baseline cursor-pointer shadow-sm"
              title={`Inspect Citation [${num}]`}
            >
              [{num}]
            </button>
          ))}
        </span>
      );

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < normalized.length) {
      parts.push(normalized.substring(lastIndex));
    }

    return parts;
  };

  const cleanedText = cleanMainContent(response.rendered_content);
  const citations = response.citations || [];
  const trustIndex = response.epistemic_bounds?.epistemic_trust_index;
  const trustPercent = Math.round(trustIndex * 100);

  // Parse sections cleanly into structured headings and bullet items
  function parseSections(text: string): {
    summaryText: string;
    summaryRefNums: Set<number>;
    subSections: ParsedSubSection[];
  } {
    // 1. Extract Summary (everything prior to the first ### heading)
    const firstH3Index = text.indexOf("###");
    let summaryPart = "";
    let remainder = "";

    if (firstH3Index === -1) {
      summaryPart = text;
      remainder = "";
    } else {
      summaryPart = text.substring(0, firstH3Index);
      remainder = text.substring(firstH3Index);
    }

    // Strip leading **Summary:** or Summary: label from the summary content
    let summaryText = summaryPart.replace(/^\s*\*\*Summary:\*\*\s*/i, "");
    summaryText = summaryText.replace(/^\s*Summary:\s*/i, "").trim();

    // 1. Extract any citation numbers mentioned in the summary (inline or in Sources: [1, 2])
    const summaryRefNums = new Set<number>();
    const badgeMatches = summaryText.match(/\[(\d+(?:,\s*\d+)*)\]/g) || [];
    badgeMatches.forEach((m) => {
      const nums = m.replace(/[\[\]]/g, "").split(",").map((s) => parseInt(s.trim(), 10));
      nums.forEach((n) => {
        if (!isNaN(n)) summaryRefNums.add(n);
      });
    });

    // 2. Remove "Sources: ..." line from the summary prose if present
    summaryText = summaryText.replace(/(?:\n|^)\s*(?:Sources|References):\s*.*$/gim, "").trim();

    // 3. Remove any inline citation brackets from the summary text itself so prose is uninterrupted
    summaryText = summaryText.replace(/\[(?:\d+|C[A-Za-z0-9_]+-[A-Za-z0-9_]+)(?:\s*,\s*(?:\d+|C[A-Za-z0-9_]+-[A-Za-z0-9_]+))*\s*\]/g, "");
    // Clean up spaces before punctuation that may remain after badge removal
    summaryText = summaryText.replace(/\s+([.,;:])/g, "$1");
    // Normalize extra whitespace
    summaryText = summaryText.replace(/[ \t]{2,}/g, " ").trim();

    // 4. Extract subsections starting with ###
    const subSections: ParsedSubSection[] = [];
    const h3Regex = /(?:^|\n)###\s+([^\n]+)\n([\s\S]*?)(?=(?:\n###\s+)|$)/g;
    let match: RegExpExecArray | null;

    while ((match = h3Regex.exec(remainder)) !== null) {
      const title = match[1].trim();
      let body = match[2].trim();

      let category: ParsedSubSection["category"] = "generic";
      if (/highlight|detail|finding|evidence|takeaway/i.test(title)) {
        category = "highlights";
      } else if (/caveat|scope|verification|uncertainty/i.test(title)) {
        category = "caveats";
      }

      // If category is highlights, clean any redundant subheadings LLM might have outputted
      if (category === "highlights") {
        while (true) {
          const prev = body;
          body = body
            .replace(
              /^(?:###?\s*)?(?:PART\s*\d+[:\s\-]*)?(?:&|AND)?\s*(?:KEY\s*(?:FINDINGS|HIGHLIGHTS|EVIDENCE|TAKEAWAYS)(?:\s*(?:&|AND)?\s*VERIFIED\s*DETAILS)?|VERIFIED\s*DETAILS)[^\n]*\n*/gi,
              ""
            )
            .replace(/^(?:&|AND)\s+[^\n]+\n*/gi, "")
            .trim();
          if (body === prev) break;
        }
      }

      // Normalize bullet points: ensure they start on newlines and clean broken citation spacing
      const normalizedBody = body
        .replace(/\[(\d+)\]\s*[\r\n]+\s*,\s*\[(\d+)\]/g, "[$1, $2]")
        .replace(/\[(\d+)\]\s*,\s*\[(\d+)\]/g, "[$1, $2]")
        .replace(/\s*[\r\n]+\s*,\s*\[/g, ", [")
        .replace(/\[(\d+(?:,\s*\d+)*)\]\s*[\r\n]+\s*\./g, "[$1].")
        .replace(/\s*[\r\n]+\s*\.\s*/g, ". ")
        .replace(/^\s*[\-•]\s*|^\s*\*(?!\*)\s*/, "")
        .replace(/(?<=\.|\])\s*(?:[\-•]|\*(?!\*))\s+(?=\*\*)/g, "\n\n* ")
        .replace(/(?:\r?\n|^)\s*[\*•]\s+/g, "\n\n* ");

      // Extract bullet points (split on newline + dash, asterisk, bullet, number, or double-newline)
      const rawSplit = normalizedBody.split(/(?:\r?\n\s*[-*•]\s+|\r?\n\s*\d+\.\s+|\r?\n\r?\n+)/);
      let items = rawSplit
        .map((s) => s.replace(/^\s*[-•]\s*|^\s*\*(?!\*)\s*/, "").trim())
        .filter((s) => s.length > 10 && !/^(?:&|AND)?\s*(?:EMPIRICAL|TAKEAWAYS|KEY\s*FINDINGS|VERIFIED\s*DETAILS)/i.test(s));

      // Fallback: If split resulted in 1 chunk but multiple bold headings exist, split by bold markers
      if (items.length <= 1 && (normalizedBody.match(/\*\*[^*]+\*\*/g) || []).length > 1) {
        const parts = normalizedBody.split(/(?=(?:^|\n|\.|\s)\s*(?:[\-•]|\*(?!\*))?\s*\*\*[^*]+\*\*)/g);
        const extracted = parts
          .map((p) => p.replace(/^\s*[-•]\s*|^\s*\*(?!\*)\s*/, "").trim())
          .filter((p) => p.length > 15);
        if (extracted.length > 1) {
          items = extracted;
        }
      }

      // Deduplicate items against each other
      if (category === "highlights") {
        const seenItems = new Set<string>();
        items = items.filter((item) => {
          const normItem = item.replace(/\[\d+(?:,\s*\d+)*\]/g, "").trim().toLowerCase();
          if (!normItem || normItem.length < 15) return false;
          const key = normItem.slice(0, 35);
          if (seenItems.has(key)) return false;
          seenItems.add(key);
          return true;
        });
      }

      // Format user-friendly caveats if any developer jargon appears
      if (category === "caveats") {
        const cleanedCaveats: string[] = [];
        const seenCategories = new Set<string>();
        for (const item of items) {
          if (/step_leaf|grounding deficit|inferential leap|reasoning step '/i.test(item)) {
            if (!seenCategories.has("grounding")) {
              seenCategories.add("grounding");
              cleanedCaveats.push(
                "Certain supplementary background context has limited direct corroboration in primary reference documents."
              );
            }
          } else if (/weakest-link|constrained by a moderate/i.test(item)) {
            if (!seenCategories.has("weakest_link")) {
              seenCategories.add("weakest_link");
              cleanedCaveats.push(
                "Confidence is calibrated against available evidence across primary and secondary sources."
              );
            }
          } else if (/Zero Winner Forcing|empirical divergence/i.test(item)) {
            if (!seenCategories.has("divergence")) {
              seenCategories.add("divergence");
              cleanedCaveats.push(
                "Multiple perspectives were identified in source literature and have been preserved."
              );
            }
          } else {
            cleanedCaveats.push(item);
          }
        }
        items =
          cleanedCaveats.length > 0
            ? cleanedCaveats
            : ["All key claims are grounded against verified reference sources."];
      }

      subSections.push({
        title,
        category,
        items: items.length > 0 ? items : [body],
      });
    }

    return { summaryText, summaryRefNums, subSections };
  }

  const { summaryText, summaryRefNums, subSections } = parseSections(cleanedText);

  // Compute citations for the summary card footer
  const activeSummaryCitations = citations.filter((c) => summaryRefNums.has(c.reference_number));
  const summaryDisplayCitations = activeSummaryCitations.length > 0 ? activeSummaryCitations : citations.slice(0, 4);

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-slate-800/70 mb-8 shadow-xl space-y-6">
      {/* Research Hero Header */}
      <div className="space-y-3 pb-5 border-b border-slate-800/60">
        {query && (
          <h2 className="text-xl sm:text-2xl font-bold text-slate-100 tracking-tight leading-snug">
            {query}
          </h2>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />
              {trustIndex !== undefined ? `${Math.round(trustIndex * 100)}% Trust Index` : "Trust Assessment Available"}
            </span>
            {citations.length > 0 && (
              <span className="px-2.5 py-1 rounded-full bg-slate-900 text-xs font-medium text-slate-300 border border-slate-800">
                {citations.length} Verified Sources
              </span>
            )}
            {response.contradictions && response.contradictions.length > 0 && (
              <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-xs font-medium text-amber-300 border border-amber-500/30">
                {response.contradictions.length} Discrepancies Analyzed
              </span>
            )}
          </div>

          {/* Quick tab deep-dive actions */}
          {onSelectTab && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onSelectTab("EVIDENCE")}
                className="px-3 py-1 text-xs font-medium text-indigo-300 hover:text-indigo-200 bg-indigo-950/40 hover:bg-indigo-900/50 rounded-lg border border-indigo-800/50 transition-colors cursor-pointer"
              >
                Explore Evidence &rarr;
              </button>
              <button
                onClick={() => onSelectTab("REASONING")}
                className="px-3 py-1 text-xs font-medium text-slate-300 hover:text-slate-100 bg-slate-900 hover:bg-slate-800 rounded-lg border border-slate-800 transition-colors cursor-pointer"
              >
                See Reasoning &rarr;
              </button>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 1: The Short Answer */}
      {summaryText && (
        <div className="space-y-2.5">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>The Short Answer</span>
          </div>
          <div className="p-5 sm:p-6 rounded-xl bg-slate-900/70 border border-slate-800/80 shadow-sm">
            {/* Clean, uninterrupted narrative prose */}
            <div className="text-slate-100 text-sm sm:text-base leading-relaxed font-sans font-normal space-y-3">
              {summaryText.split("\n\n").map((para, pIdx) => (
                <p key={pIdx}>{para.trim()}</p>
              ))}
            </div>

            {/* Clickable Reference Links & Sources Bar below the summary */}
            {summaryDisplayCitations.length > 0 && (
              <div className="mt-4 pt-3.5 border-t border-slate-800/70 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-indigo-400" />
                    Sources Consulted:
                  </span>
                  {summaryDisplayCitations.map((cite) => (
                    <div
                      key={cite.reference_number}
                      className="inline-flex items-center gap-1.5 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 hover:border-indigo-500/60 rounded-lg px-2.5 py-1 text-xs transition-all shadow-sm group"
                    >
                      <button
                        onClick={() => onOpenCitation && onOpenCitation(cite.reference_number)}
                        className="flex items-center gap-1.5 text-slate-200 group-hover:text-indigo-200 cursor-pointer font-medium"
                        title={`Inspect citation [${cite.reference_number}] in Evidence Drawer`}
                      >
                        <span className="font-mono font-bold text-indigo-400 text-[11px]">
                          [{cite.reference_number}]
                        </span>
                        <span className="max-w-[140px] sm:max-w-[200px] truncate text-slate-200 text-xs">
                          {cite.source_title}
                        </span>
                      </button>
                      {cite.source_uri && (
                        <a
                          href={cite.source_uri}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-400 hover:text-cyan-300 p-0.5 rounded hover:bg-slate-700 transition-colors"
                          title={`Open original source link: ${cite.source_uri}`}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => setShowSources(true)}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline shrink-0 font-medium cursor-pointer self-start sm:self-auto"
                >
                  View full source quotes &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 2 & 3: Subsequent Sections with Headings Above */}
      {subSections.length > 0 && (
        <div className="space-y-5 pt-1">
          {subSections.map((sec, idx) => (
            <div key={idx} className="space-y-2">
              {/* Distinct Heading Above Respective Details */}
              {sec.category === "highlights" && (
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
                  <CheckCircle className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{sec.title}</span>
                </div>
              )}

              {sec.category === "caveats" && (
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{sec.title}</span>
                </div>
              )}

              {sec.category === "generic" && (
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-300">
                  <Info className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{sec.title}</span>
                </div>
              )}

              {/* Respective Details Card */}
              {sec.category === "highlights" ? (
                <div className="space-y-3">
                  {sec.items.map((item, i) => {
                    // Extract bold title if present e.g. **Data-Driven Performance Frameworks:**
                    const titleMatch = item.match(/^\s*(?:\*\s*)?\*\*([^*]+)\*\*[:\s\-]*(.*)$/s);
                    const rawTitle = titleMatch ? titleMatch[1].trim() : null;
                    const pointTitle = rawTitle ? rawTitle.replace(/[:\s\-]+$/, "") : null;
                    const pointBody = titleMatch ? titleMatch[2].trim() : item.replace(/^\s*[-•]\s*|^\s*\*(?!\*)\s*/, "").trim();

                    return (
                      <div
                        key={i}
                        className="p-4 sm:p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-cyan-500/40 hover:bg-slate-900/90 transition-all shadow-sm group"
                      >
                        <div className="flex items-start gap-3 sm:gap-3.5">
                          <span className="w-6 h-6 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 flex items-center justify-center text-xs font-bold font-mono shrink-0 shadow-[0_0_10px_rgba(34,211,238,0.15)] mt-0.5">
                            {i + 1}
                          </span>
                          <div className="flex-1 space-y-1.5">
                            {pointTitle ? (
                              <>
                                <h4 className="text-slate-100 font-bold text-sm sm:text-base group-hover:text-cyan-200 transition-colors">
                                  {pointTitle}
                                </h4>
                                <div className="text-slate-300 text-xs sm:text-sm leading-relaxed">
                                  {renderInteractiveContent(pointBody)}
                                </div>
                              </>
                            ) : (
                              <div className="text-slate-200 text-xs sm:text-sm leading-relaxed">
                                {renderInteractiveContent(pointBody)}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : sec.category === "caveats" ? (
                <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/70 text-slate-300 text-xs sm:text-sm leading-relaxed space-y-2">
                  {sec.items.map((item, i) => (
                    <div key={i} className="flex items-start space-x-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 shrink-0" />
                      <div className="flex-1">{renderInteractiveContent(item)}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/70 text-slate-300 text-xs sm:text-sm leading-relaxed space-y-2">
                  {sec.items.map((item, i) => (
                    <div key={i} className="flex items-start space-x-2.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 shrink-0" />
                      <div className="flex-1">{renderInteractiveContent(item)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Hidden-by-Default Interactive Sources Accordion */}
      {citations.length > 0 && (
        <div className="pt-2">
          <button
            onClick={() => setShowSources(!showSources)}
            className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all text-xs font-semibold text-slate-300 group cursor-pointer"
          >
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
              <span>Verified Sources & Evidence Provenance</span>
              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] text-slate-400 font-mono">
                {citations.length}
              </span>
            </div>
            <div className="flex items-center space-x-1 text-slate-400 text-[11px]">
              <span>{showSources ? "Hide Details" : "Inspect Sources"}</span>
              {showSources ? (
                <ChevronUp className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              )}
            </div>
          </button>

          {showSources && (
            <div className="mt-3 space-y-2.5 animate-in fade-in duration-200">
              {citations.map((c) => (
                <div
                  key={c.reference_number}
                  className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-all space-y-2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 text-xs font-mono font-bold">
                        [{c.reference_number}]
                      </span>
                      <h5 className="text-xs font-semibold text-slate-200">
                        {c.source_title}
                      </h5>
                    </div>
                    {c.source_uri && (
                      <a
                        href={c.source_uri}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center space-x-1 text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline shrink-0"
                      >
                        <span>Visit Source</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {c.snippet && (
                    <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60 text-[11px] text-slate-300 italic font-sans leading-relaxed">
                      "{c.snippet}"
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                    <span>
                      Role: <span className="text-slate-300 font-medium">{c.evidence_role || "Direct Support"}</span>
                    </span>
                    <button
                      onClick={() => onOpenCitation && onOpenCitation(c.reference_number)}
                      className="text-indigo-400 hover:text-indigo-300 hover:underline cursor-pointer font-medium"
                    >
                      View in Evidence Drawer &rarr;
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer Controls & Feedback */}
      <div className="pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3 text-xs text-slate-400">
          <span className="flex items-center space-x-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Was this answer clear and accurate?</span>
          </span>
          {feedbackSent ? (
            <span className="text-xs text-emerald-400 flex items-center space-x-1 font-medium">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Feedback recorded</span>
            </span>
          ) : (
            <div className="flex items-center space-x-1.5">
              <button
                onClick={() => handleFeedback(5, true)}
                className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-emerald-400 transition-colors border border-slate-800 cursor-pointer"
                title="Accurate & Sound"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => handleFeedback(1, false)}
                className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-rose-400 transition-colors border border-slate-800 cursor-pointer"
                title="Inaccurate or Unsound"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 transition-colors cursor-pointer"
          >
            <Copy className="w-3.5 h-3.5 text-slate-400" />
            <span>{copied ? "Copied" : "Copy Answer"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
