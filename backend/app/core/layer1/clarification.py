"""
Sub-Module 1.6: Clarification Generator
Implements the 5-aspect decomposition from ASK (ACL 2025) and
ask-vs-act balancing from SpeakRL (arXiv Dec 2025).
"""

import re
from typing import List, Optional, Dict, Any
from app.schemas.layer1 import AmbiguityReport, ClarificationPlan


class ClarificationGenerator:
    """
    Decomposes ambiguous query into 5 aspects:
    1. Subject Aspect (what concept or entity?)
    2. Scope Aspect (academic literature, empirical code, high-level overview?)
    3. Temporal Aspect (specific year, decade, or recent?)
    4. Constraint Aspect (hardware, latency, accuracy, cost?)
    5. Comparison Aspect (baseline model or benchmark?)
    Targets ONLY the single aspect with the highest ambiguity.
    """

    MAX_CLARIFICATION_ROUNDS = 2

    ASPECT_REGISTRY: Dict[str, Dict[str, Any]] = {
        "Comparison": {
            "keywords": ["compare", "vs", "versus", "better", "faster", "baseline", "difference"],
            "question": "Which baseline model or benchmark are you comparing against?",
            "options": [
                "Vanilla RAG without reranking",
                "Dense Passage Retrieval (DPR) baseline",
                "Standard GPT-4 / Claude 3.5 baseline",
                "BM25 lexical retrieval",
            ],
            "default_assumption": "Comparing against standard Dense Passage Retrieval (DPR)",
        },
        "Temporal": {
            "keywords": ["recent", "latest", "past", "history", "trend", "current"],
            "question": "What publication timeframe or temporal window should the search target?",
            "options": [
                "Recent papers (2024–2026)",
                "Last 5 years (2021–2026)",
                "Foundational / all-time literature",
            ],
            "default_assumption": "Focusing on recent state-of-the-art literature (2024–2026)",
        },
        "Subject": {
            "keywords": ["this", "that", "it", "algorithm", "model", "paper"],
            "question": "Which specific model, algorithm, or technical subject are you referring to?",
            "options": [
                "Transformer attention architectures",
                "Diffusion / Generative vision models",
                "Reinforcement Learning (RLHF / PPO / GRPO)",
                "Retrieval-Augmented Generation (RAG)",
            ],
            "default_assumption": "Focusing on modern Transformer-based RAG architectures",
        },
        "Scope": {
            "keywords": ["overview", "explain", "tell me about", "survey", "how"],
            "question": "What level of research depth and presentation format do you need?",
            "options": [
                "Deep mathematical and architectural derivation",
                "Empirical benchmark results & latency comparisons",
                "Practical implementation details & code patterns",
                "Executive conceptual overview",
            ],
            "default_assumption": "Providing architectural design and empirical benchmark analysis",
        },
        "Constraint": {
            "keywords": ["fast", "cheap", "scale", "memory", "efficient", "optimal"],
            "question": "Which operational constraint is your primary optimization priority?",
            "options": [
                "Inference latency & throughput (tokens/sec)",
                "Factual grounding & zero hallucination",
                "GPU VRAM / memory footprint",
                "Minimal training / compute budget",
            ],
            "default_assumption": "Optimizing for factual grounding and inference latency",
        },
    }

    def _is_already_asked(self, candidate_question: str, prior_questions: Optional[List[str]]) -> bool:
        """Checks if the candidate question or its core theme was already presented to the user."""
        if not prior_questions:
            return False
        cand_clean = re.sub(r"[^\w\s]", "", candidate_question.lower()).strip()
        for pq in prior_questions:
            if not pq:
                continue
            pq_clean = re.sub(r"[^\w\s]", "", str(pq).lower()).strip()
            if cand_clean == pq_clean:
                return True
            # Word overlap ratio check
            c_words = set(cand_clean.split())
            p_words = set(pq_clean.split())
            if c_words and p_words:
                overlap = len(c_words.intersection(p_words)) / max(len(c_words), len(p_words))
                if overlap > 0.65:
                    return True
        return False

    def generate(
        self,
        query: str,
        ambiguity: AmbiguityReport,
        current_round: int = 1,
        prior_questions: Optional[List[str]] = None,
        prior_aspects: Optional[List[str]] = None,
    ) -> Optional[ClarificationPlan]:
        """
        Generate targeted aspect clarification if current_round <= MAX_CLARIFICATION_ROUNDS.
        Ensures that questions are never repeated across turns, generating progressive follow-up options.
        """
        if current_round > self.MAX_CLARIFICATION_ROUNDS:
            return None

        if prior_questions is None:
            prior_questions = []
        if prior_aspects is None:
            prior_aspects = []

        lower = query.lower().strip()

        # Tailored disambiguation for high-ambiguity polysemous acronyms (P2 CLAMBER / P5 ASK)
        # RAG
        if "rag" in lower.split():
            q1 = "Are you inquiring about Retrieval-Augmented Generation (AI architecture) or Red-Amber-Green project reporting status?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Retrieval-Augmented Generation (AI)", "Red-Amber-Green Project Status"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["Which component of the Retrieval-Augmented Generation pipeline do you want to optimize?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Chunking & Embedding strategy", "Hybrid retrieval & Reranking (BM25 + ColBERT)", "Context compression & hallucination guardrails"],
                )

        # BERT
        if "bert" in lower.split():
            q1 = "Are you referring to the BERT language model (Transformer NLP) or the BERT cryptocurrency/banking token?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["BERT Transformer Language Model", "BERT Cryptocurrency / Banking Token"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["What type of BERT architecture analysis do you need?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Pretraining objectives (MLM / NSP)", "Fine-tuning on downstream GLUE tasks", "Inference optimization & model quantization"],
                )

        # CV
        if "cv" in lower.split():
            q1 = "Are you inquiring about Computer Vision algorithms or Curriculum Vitae (job resume / hiring documents)?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Computer Vision in Automated Hiring", "Curriculum Vitae / Resume Screening"],
                )

        # COT
        if "cot" in lower.split():
            q1 = "Are you referring to Chain-of-Thought prompting in LLMs or Customer-Owned Tooling / Center of Temperature?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Chain of Thought Prompting (LLMs)", "Center of Temperature / Industrial Tooling"],
                )

        # PCA
        if re.search(r"\bpca\b", lower):
            q1 = "Are you inquiring about Principal Component Analysis (ML dimensionality reduction) or Patient-Controlled Analgesia (medicine)?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Principal Component Analysis (ML)", "Patient-Controlled Analgesia (Medicine)"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["Which technical focus or implementation depth do you require for Principal Component Analysis?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Scikit-learn / Python implementation code", "Mathematical derivation & SVD eigenvector proof", "Incremental / streaming PCA for large datasets", "Kernel PCA for non-linear dimensionality reduction"],
                )

        # ROI
        if re.search(r"\broi\b", lower):
            q1 = "Are you inquiring about Return on Investment (financial metric) or Region of Interest (imaging / computer vision)?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Return on Investment (Finance)", "Region of Interest (Computer Vision / Imaging)"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["Which financial return evaluation methodology should be applied?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Standard Accounting ROI & Payback Period", "Discounted Cash Flow (DCF) & NPV / IRR", "Technology / IT Investment ROI benchmarks"],
                )

        # ATM
        if re.search(r"\batm\b", lower):
            q1 = "Are you referring to Automated Teller Machines (banking hardware) or Asynchronous Transfer Mode (telecom/networking protocol)?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Automated Teller Machine (Banking)", "Asynchronous Transfer Mode (Networking Protocol)"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["Which aspect of Automated Teller Machine architecture are you focusing on?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["ATM application software & EMV/NFC security standards", "Interbank payment network protocol (ISO 8583)", "Hardware cash dispenser & peripheral interface"],
                )

        # CRM
        if re.search(r"\bcrm\b", lower):
            q1 = "Are you inquiring about Customer Relationship Management (sales/software) or Customer Retention Marketing?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Customer Relationship Management (Software & Platforms)", "Customer Retention Marketing Strategy"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["What is your primary requirement for Customer Relationship Management software?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Enterprise SaaS platform evaluation (Salesforce vs Dynamics)", "Data schema, pipeline & API integration architecture", "Open-source self-hosted deployment"],
                )

        # NLP
        if re.search(r"\bnlp\b", lower) and not any(k in lower for k in ["natural language", "linguistic programming"]):
            q1 = "Are you referring to Natural Language Processing (AI/computational linguistics) or Neuro-Linguistic Programming (psychology)?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Natural Language Processing (AI / Machine Learning)", "Neuro-Linguistic Programming (Psychology & Behavioral)"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["Which subfield of Natural Language Processing do you want to explore?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Large Language Models & Transformer architectures", "Retrieval, Vector Embeddings & RAG", "Named Entity Recognition & Information Extraction"],
                )

        # Tailored disambiguation for missing medical entity (dosage / side effects)
        if ("side effects" in lower or "dosage" in lower) and "Target drug" in str(ambiguity.missing_elements):
            q1 = "Which medication, pharmaceutical compound, or substance are you seeking dosage and side effect information for?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Paxlovid (nirmatrelvir/ritonavir)", "GLP-1 receptor agonists (Ozempic/Wegovy)", "Statin therapy (Atorvastatin)", "Specify another medication"],
                )

        # Tailored disambiguation for generic illness
        if "illness" in lower or "disease" in lower:
            q1 = "Which specific medical condition, symptom, or diagnosis are you seeking treatment options for?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Subject"],
                    suggested_options=["Stage 2 Essential Hypertension", "Type 2 Diabetes Mellitus", "Major Depressive Disorder", "Specify another condition"],
                )
            else:
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=["Which clinical management aspect do you need?"],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["First-line pharmacological therapeutics & dosing", "Lifestyle, nutritional & non-pharmacological interventions", "Contraindications, safety warnings & drug interactions"],
                )

        # Contradiction resolution
        if "deterministic" in lower and "stochastic" in lower:
            q1 = "Are you investigating deterministic optimization algorithms or stochastic optimization methods?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Deterministic Optimization (e.g., Gradient Descent)", "Stochastic Optimization (e.g., SGD / Adam)"],
                )

        if "non-parametric" in lower and "parametric" in lower:
            q1 = "Are you studying parametric statistical models or non-parametric regression methods?"
            if not self._is_already_asked(q1, prior_questions):
                return ClarificationPlan(
                    needs_clarification=True,
                    round_number=current_round,
                    clarification_questions=[q1],
                    aspects_to_clarify=["Scope"],
                    suggested_options=["Parametric Models (e.g., ARIMA / Linear Regression)", "Non-Parametric Models (e.g., Gaussian Processes / Splines)"],
                )

        # Step 1 & 2: Score the 5 aspects to find the single most ambiguous facet not already clarified
        selected_aspect_name = self._identify_highest_ambiguity_aspect(query, ambiguity, prior_aspects, prior_questions)
        aspect_info = self.ASPECT_REGISTRY[selected_aspect_name]

        # Step 3: Generate the single targeted question and concrete selectable options
        question = aspect_info["question"]
        options = list(aspect_info["options"])

        return ClarificationPlan(
            needs_clarification=True,
            round_number=current_round,
            clarification_questions=[question],
            aspects_to_clarify=[selected_aspect_name],
            suggested_options=options,
        )

    def _identify_highest_ambiguity_aspect(
        self,
        query: str,
        ambiguity: AmbiguityReport,
        prior_aspects: Optional[List[str]] = None,
        prior_questions: Optional[List[str]] = None,
    ) -> str:
        """Determines which of the 5 aspects has the highest uncertainty, skipping previously clarified aspects."""
        lower = query.lower()
        excluded = set(prior_aspects or [])

        # Priority order based on uncertainty signals
        candidates = []

        # Check for semantic comparative missing baseline first
        if "Comparison" not in excluded and ambiguity.ambiguity_types.get("semantic", 0.0) >= 0.5:
            if any(k in lower for k in ["better", "faster", "compare", "vs", "versus"]):
                candidates.append("Comparison")

        # Check for missing subject (lexical or brevity)
        if "Subject" not in excluded:
            if len(query.split()) < 4 or ambiguity.ambiguity_types.get("lexical", 0.0) >= 0.5:
                candidates.append("Subject")

        # Check for constraint ambiguity (vagueness qualifiers like fast, cheap)
        if "Constraint" not in excluded and ambiguity.ambiguity_types.get("vagueness", 0.0) >= 0.5:
            candidates.append("Constraint")

        # Check for temporal ambiguity
        if "Temporal" not in excluded and any(w in lower for w in ["recent", "latest", "newest", "modern"]):
            if not any(yr in lower for yr in ["2023", "2024", "2025", "2026"]):
                candidates.append("Temporal")

        # Scope
        if "Scope" not in excluded:
            candidates.append("Scope")

        # Fallback to any remaining aspect in ASPECT_REGISTRY
        for aspect in ["Scope", "Constraint", "Comparison", "Subject", "Temporal"]:
            if aspect not in excluded:
                candidates.append(aspect)

        # Check if the question for this candidate was already asked
        for cand in candidates:
            cand_q = self.ASPECT_REGISTRY[cand]["question"]
            if not self._is_already_asked(cand_q, prior_questions):
                return cand

        # If all candidates exhausted, pick Scope or Constraint
        return candidates[0] if candidates else "Scope"
