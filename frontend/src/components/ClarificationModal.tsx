import React, { useState } from "react";
import { Send, X, AlertTriangle, PenLine } from "lucide-react";
import type { ClarificationQuestion } from "../types/cogent";

interface ClarificationModalProps {
  isOpen: boolean;
  questions: ClarificationQuestion[];
  onSubmit: (responses: Record<string, string>) => void;
  onClose: () => void;
}

export const ClarificationModal: React.FC<ClarificationModalProps> = ({
  isOpen,
  questions,
  onSubmit,
  onClose,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [customTexts, setCustomTexts] = useState<Record<string, string>>({});

  if (!isOpen || questions.length === 0) return null;

  const handleSelect = (questionId: string, option: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
  };

  const handleTextChange = (questionId: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(answers);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="w-full max-w-xl glass-panel rounded-2xl p-6 border border-amber-500/40 shadow-2xl bg-slate-900/95 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Layer 1 Ambiguity Clarification Required
              </h3>
              <p className="text-xs text-slate-400">
                Your research query contains under-specified constraints
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
          {questions.map((q) => {
            const currentAnswer = answers[q.clarification_id] || "";
            const isOptionChosen = q.options && q.options.includes(currentAnswer);
            const isCustomActive =
              !isOptionChosen &&
              (currentAnswer.length > 0 || customTexts[q.clarification_id] !== undefined);

            return (
              <div
                key={q.clarification_id}
                className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">{q.question}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400">
                    {q.dimension}
                  </span>
                </div>
                <p className="text-xs text-slate-400 italic">{q.reason}</p>

                {/* Options List */}
                {q.options && q.options.length > 0 ? (
                  <div className="space-y-2">
                    {q.options.map((opt, oIdx) => {
                      const isChosen = currentAnswer === opt;
                      return (
                        <button
                          key={oIdx}
                          type="button"
                          onClick={() => handleSelect(q.clarification_id, opt)}
                          className={`w-full text-left p-2.5 rounded-lg text-xs font-medium border transition-all flex items-center justify-between ${
                            isChosen
                              ? "bg-indigo-600/30 border-indigo-500 text-indigo-200 shadow-sm ring-1 ring-indigo-500/40"
                              : "bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-850 hover:border-slate-750"
                          }`}
                        >
                          <span>{opt}</span>
                          {isChosen && (
                            <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                          )}
                        </button>
                      );
                    })}

                    {/* Last Option: Custom Typing Box */}
                    <div
                      onClick={() => {
                        const existing = customTexts[q.clarification_id] || "";
                        handleTextChange(q.clarification_id, existing);
                      }}
                      className={`p-3 rounded-lg border transition-all ${
                        isCustomActive
                          ? "bg-indigo-950/30 border-indigo-500 ring-1 ring-indigo-500/40 shadow-sm"
                          : "bg-slate-900/90 border-slate-800 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center space-x-1.5">
                          <PenLine className="w-3.5 h-3.5 text-indigo-400" />
                          <span className="text-xs font-medium text-slate-300">
                            Option not listed? Specify custom clarification:
                          </span>
                        </div>
                        {isCustomActive && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            Selected
                          </span>
                        )}
                      </div>
                      <input
                        type="text"
                        placeholder="Type your clarification if not listed above..."
                        value={
                          customTexts[q.clarification_id] ??
                          (isCustomActive ? answers[q.clarification_id] || "" : "")
                        }
                        onChange={(e) => {
                          const val = e.target.value;
                          setCustomTexts((prev) => ({ ...prev, [q.clarification_id]: val }));
                          handleTextChange(q.clarification_id, val);
                        }}
                        onFocus={() => {
                          const currentVal = customTexts[q.clarification_id] ?? "";
                          handleTextChange(q.clarification_id, currentVal);
                        }}
                        className="w-full bg-slate-950/90 text-xs rounded-md px-3 py-2 border border-slate-700/70 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all"
                      />
                    </div>
                  </div>
                ) : (
                  <input
                    type="text"
                    placeholder="Specify clarification detail..."
                    value={answers[q.clarification_id] || ""}
                    onChange={(e) => handleTextChange(q.clarification_id, e.target.value)}
                    className="w-full bg-slate-900 text-xs rounded-lg p-2.5 border border-slate-800 focus:border-indigo-500 focus:outline-none"
                  />
                )}
              </div>
            );
          })}

          <div className="pt-3 border-t border-slate-800 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20"
            >
              <span>Submit & Resume Pipeline</span>
              <Send className="w-3 h-3" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
