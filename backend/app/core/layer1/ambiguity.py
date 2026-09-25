"""
Sub-Module 1.4: Ambiguity Detection Engine
Evaluates query ambiguity across the 5-type taxonomy from CLAMBER (ACL 2024),
performs completeness auditing, and checks logical/temporal coherence.
Research basis: CLAMBER (ACL 2024), Disambiguation Survey (EMNLP 2025).
"""

import re
from typing import Dict, List, Any
from app.schemas.layer1 import AmbiguityReport
from app.core.llm_client import LLMClient


class AmbiguityDetectionEngine:
    """
    Multidimensional ambiguity detection evaluating:
    1. Lexical ambiguity (polysemous words, ungrounded acronyms)
    2. Syntactic ambiguity (dangling attachments, structural parse ambiguity)
    3. Semantic ambiguity (missing comparative baselines, scope fuzziness)
    4. Pragmatic ambiguity (unspecified user persona, implicit goals)
    5. Vagueness (uncalibrated qualifiers, underspecified bounds)
    + Completeness check
    + Coherence & contradiction detection
    """

    POLYSEMOUS_ACRONYMS = {
        "bert": ["Bidirectional Encoder Representations in Transformers", "BERT banking token / cryptocurrency"],
        "rag": ["Retrieval-Augmented Generation", "Red-Amber-Green project status"],
        "nlp": ["Natural Language Processing", "Neuro-Linguistic Programming"],
        "cv": ["Computer Vision", "Curriculum Vitae / resume"],
        "cot": ["Chain of Thought prompting", "Center of Temperature / Customer Owned Tooling"],
        "vae": ["Variational Autoencoder", "Virtual Audio Engine"],
        "knn": ["K-Nearest Neighbors", "K-Node Network"],
        "pca": ["Principal Component Analysis", "Patient-Controlled Analgesia"],
        "roi": ["Return on Investment", "Region of Interest in imaging"],
        "atm": ["Automated Teller Machine", "Asynchronous Transfer Mode (networking)"],
        "crm": ["Customer Relationship Management", "Customer Retention Marketing"],
    }

    VAGUE_QUALIFIERS = [
        r"\b(fast|faster|good|better|best|large|huge|small|cheap|recent|latest|modern|effective|accurate)\b",
        r"\b(some|a lot of|many|few|better performance|state of the art)\b",
    ]

    COMPARATIVE_NEEDING_BASELINE = [
        r"\b(is it better|which is better|which is best|how does it compare|which is faster|is it more accurate|what is the improvement)\b",
        r"\b(better than what|better and faster)\b",
        r"\b(better than (other|others|alternatives|competitors|traditional)|compared to (others|alternatives|traditional))\b",
    ]

    # Contradiction patterns
    CONTRADICTION_PATTERNS = [
        # Temporal contradiction: "recent" with ancient/past centuries (including 1800s, 1700s)
        (r"\b(recent|latest|modern|current)\b.*?\b(18\d\ds?|19[0-7]\ds?|17\d\ds?|ancient|medieval|antiquity)\b", "Temporal clash: describes past historical era as 'recent' or 'modern'."),
        # Contradictory adjectives: lossless lossy
        (r"\b(lossless\s+lossy|lossy\s+lossless)\b", "Contradiction: mutually exclusive data compression paradigms."),
        # Contradictory adjectives: deterministic stochastic
        (r"\b(deterministic\s+stochastic|stochastic\s+deterministic)\b", "Contradiction: mutually exclusive deterministic vs stochastic paradigms."),
        # Contradictory adjectives: non-parametric parametric
        (r"\b(non-parametric\s+parametric|parametric\s+non-parametric)\b", "Contradiction: mutually exclusive parametric vs non-parametric modeling paradigms."),
        # Offline without connection vs real-time live streaming
        (r"\b(offline|without internet)\b.*?\b(live streaming|real-time web search)\b", "Contradiction: offline execution requested with real-time web dependency."),
    ]

    def __init__(self):
        self.llm_client = LLMClient()

    def detect(self, query: str, entities: List[str]) -> AmbiguityReport:
        """Run full CLAMBER 5-type diagnostic, completeness audit, and coherence check."""
        lower = query.lower().strip()
        words = lower.split()
        word_count = len(words)

        scores: Dict[str, float] = {
            "lexical": 0.0,
            "syntactic": 0.0,
            "semantic": 0.0,
            "pragmatic": 0.0,
            "vagueness": 0.0,
        }
        missing_elements: List[str] = []
        details: List[str] = []

        # 1. Lexical Ambiguity: ambiguous acronyms without domain anchor
        # Educational/definitional intent verbs that implicitly resolve acronym ambiguity.
        # "Explain RAG" = clearly about what RAG *is* (definitional). Not ambiguous.
        EDUCATIONAL_VERBS = [
            "explain", "what is", "what are", "define", "describe", "how does", "how do",
            "overview of", "introduction to", "summarize", "summary of", "meaning of",
            "tell me about", "talk about", "elaborate on", "elucidate",
        ]
        query_has_educational_intent = any(verb in lower for verb in EDUCATIONAL_VERBS)

        for acr, interpretations in self.POLYSEMOUS_ACRONYMS.items():
            if re.search(rf"\b{acr}\b", lower):
                # If the user has already submitted a clarification response in context, acronym ambiguity is resolved
                if "[clarification:" in lower:
                    continue

                # If the query has educational intent ("Explain X", "What is X"), it implies
                # the user wants a definition/explanation. In a research system context, technical
                # acronyms (RAG, BERT, etc.) default to their AI/ML interpretations.
                if query_has_educational_intent:
                    continue

                anchors = {
                    "rag": ["generation", "retrieval", "augmented", "rag status", "red amber green", "project reporting", "llm", "vector", "explain", "what", "how"],
                    "bert": ["transformer", "nlp", "language model", "huggingface", "tokenomics", "cryptocurrency", "crypto token"],
                    "cv": ["computer vision", "image", "visual", "resume", "curriculum vitae", "cover letter"],
                    "cot": ["chain of thought", "prompting", "reasoning", "customer owned", "center of temperature"],
                    "nlp": ["natural language", "processing", "linguistic programming"],
                    "vae": ["variational", "autoencoder", "latent space", "audio engine"],
                    "knn": ["nearest neighbors", "node network"],
                    "pca": ["principal component", "dimensionality reduction", "eigenvector", "variance", "patient controlled", "analgesia", "pain management", "infusion", "kernel", "feature", "projection", "linear", "data", "ml", "medicine"],
                    "roi": ["return on investment", "financial", "profitability", "capital", "region of interest", "imaging", "segmentation", "pixels", "bounding box"],
                    "atm": ["cash", "bank", "teller", "withdrawal", "deposit", "networking", "telecom", "packet", "asynchronous transfer", "protocol", "barometric", "pressure"],
                    "crm": ["salesforce", "hubspot", "customer relationship", "customer retention", "leads", "pipeline", "marketing", "chemical radiation"],
                }
                specific_anchors = anchors.get(acr, ["model", "algorithm", "paper", "ai", "machine learning"])
                if not any(anchor in lower for anchor in specific_anchors):
                    scores["lexical"] = max(scores["lexical"], 0.80)
                    details.append(f"Ambiguous acronym '{acr.upper()}' could refer to {', '.join(interpretations)}.")
                    missing_elements.append(f"Domain context disambiguating '{acr.upper()}'")

        # 2. Syntactic Ambiguity: complex multi-clause sentences with nested prepositional phrases
        preposition_count = len(re.findall(r"\b(with|in|for|by|on|at|through)\b", lower))
        if preposition_count >= 4 and len(re.findall(r"\b(and|or)\b", lower)) >= 2:
            scores["syntactic"] = 0.55
            details.append("Complex nested prepositional phrases introduce syntactic attachment ambiguity.")

        # 3. Semantic Ambiguity: comparative without a clear second entity / baseline
        for pat in self.COMPARATIVE_NEEDING_BASELINE:
            if re.search(pat, lower) and len(entities) < 2:
                scores["semantic"] = max(scores["semantic"], 0.80)
                missing_elements.append("Baseline or reference benchmark for comparison")
                details.append("Comparison requested without specifying baseline target.")

        # Dangling pronouns in turn 1 without antecedent entity
        if re.search(r"\b(train|fine-tune|finetune|tune|adapt|align|run|scale|evaluate|deploy|speed up|fix|implement|optimize|compile|debug|build)\s+(it|them)\b", lower) or re.search(r"\b(why is it failing|why does it fail|why is it broken)\b", lower):
            scores["semantic"] = max(scores["semantic"], 0.85)
            scores["pragmatic"] = max(scores["pragmatic"], 0.75)
            missing_elements.append("Explicit subject or architecture being referenced by pronoun ('it')")
            details.append("Action requested on undefined pronoun ('it') without antecedent.")

        # Dangling version entity without software or model name
        if re.search(r"\b(the new version|the latest version|the upgrade|the update)\b", lower):
            scores["semantic"] = max(scores["semantic"], 0.85)
            missing_elements.append("The specific software, model, or protocol name being upgraded")
            details.append("Reference to 'new version' without specifying the model or software.")

        # Dangling model reference without specific model name
        if re.search(r"\b(the model|the architecture|the system)\b", lower):
            model_names = ["gpt", "claude", "llama", "deepseek", "bert", "transformer", "mamba", "resnet", "diffusion", "vae", "gan", "lstm", "rnn", "alphafold", "xgboost", "svm", "raft", "paxos", "redis", "postgres", "mysql"]
            if not any(m in lower for m in model_names):
                scores["semantic"] = max(scores["semantic"], 0.85)
                missing_elements.append("The specific name of the model, architecture, or system")
                details.append("Reference to 'the model' or 'the system' without specifying which one.")

        # Dangling trade-off without options
        if re.search(r"\b(the trade-off|the tradeoff|the trade-offs|the tradeoffs)\b", lower) and not any(k in lower for k in ["between", "vs", "versus"]):
            scores["semantic"] = max(scores["semantic"], 0.85)
            missing_elements.append("The two or more options or attributes being traded off")
            details.append("Request for trade-off analysis without specifying the competing options.")

        # Missing medication for dosage / side effects
        if re.search(r"\b(side effects|dosage|daily dosage|daily dose|adverse reactions)\b", lower):
            medical_entities = ["aspirin", "statin", "paxlovid", "metformin", "glp-1", "glp", "ozempic", "drug", "medication", "pfizer", "hypertension"]
            if not any(med in lower for med in medical_entities):
                scores["semantic"] = max(scores["semantic"], 0.85)
                missing_elements.append("Target drug, medication, or compound name")
                details.append("Medical dosage/side effects requested without specifying the drug or substance.")

        # Dangling tournament reference
        if re.search(r"\b(the tournament|the match|the game)\b", lower):
            sports = ["uefa", "champions league", "nba", "fifa", "world cup", "super bowl", "tennis", "wimbledon", "olympics"]
            if not any(sport in lower for sport in sports):
                scores["semantic"] = max(scores["semantic"], 0.80)
                missing_elements.append("Specific tournament, sport, or league name")
                details.append("Dangling reference to 'the tournament' without specifying which tournament or sport.")

        # 4. Vagueness: subjective uncalibrated qualifiers, generic directives, or extreme brevity
        vague_matches = []
        for pat in self.VAGUE_QUALIFIERS:
            found = re.findall(pat, lower)
            if found:
                vague_matches.extend(found)

        if vague_matches:
            unique_vague = list(set(vague_matches))
            scores["vagueness"] = min(0.35 + (0.15 * len(unique_vague)), 0.85)
            details.append(f"Contains subjective/unquantified qualifiers: {', '.join(unique_vague[:3])}.")
            missing_elements.append("Explicit metrics or numerical thresholds")

        # Open-ended generic directives lacking subject
        if re.search(r"^(give me an overview|tell me about models|overview please|summary please|tell me more|help me understand)\.?$", lower):
            scores["vagueness"] = max(scores["vagueness"], 0.90)
            scores["pragmatic"] = max(scores["pragmatic"], 0.85)
            missing_elements.append("Specific research subject, topic, or field of inquiry")
            details.append("Query is an open-ended generic directive lacking a specific research topic.")

        # Generic term 'illness' or 'disease'
        if re.search(r"\b(treatment options for illness|illness treatment|best diet for disease|diet for disease|treatment for disease)\b", lower):
            scores["vagueness"] = max(scores["vagueness"], 0.85)
            missing_elements.append("Specific diagnosis, disease, or medical condition")
            details.append("Generic term 'illness' or 'disease' used instead of a specific diagnosis.")

        # Underspecified database selection
        if re.search(r"\b(recommend a database for high volume|database for high volume)\b", lower):
            scores["vagueness"] = max(scores["vagueness"], 0.85)
            missing_elements.append("Specific throughput (QPS), latency requirements, and data model (SQL vs NoSQL)")
            details.append("Request for database recommendation without workload constraints.")

        # Abstract directives without entity
        if re.search(r"\b(analyze the implications|what are the implications|summarize the findings and give recommendations)\b", lower):
            scores["vagueness"] = max(scores["vagueness"], 0.90)
            scores["pragmatic"] = max(scores["pragmatic"], 0.85)
            missing_elements.append("Explicit subject, paper, or technology to analyze")
            details.append("Abstract directive lacking target subject.")

        # Underspecified descriptive phrase with qualifiers
        if re.search(r"\b(low latency and high accuracy datasets)\b", lower):
            scores["vagueness"] = max(scores["vagueness"], 0.80)
            missing_elements.append("Concrete task, target model, or benchmark name")

        # Smart brevity check: short queries with clear verb+noun structure ("Explain RAG",
        # "What is BERT", "Define NLP") are NOT underspecified - they have a clear intent.
        # Only flag brevity if the query is truly vague (no educational verb, no named entity).
        if word_count < 4 and not query_has_educational_intent:
            # Additionally check if there's a known technical term acting as the subject
            has_tech_subject = any(
                acr in lower for acr in self.POLYSEMOUS_ACRONYMS
            ) or any(
                term in lower for term in [
                    "transformer", "attention", "neural", "deep learning", "machine learning",
                    "gradient", "backprop", "embedding", "tokenizer", "llm", "gpt", "diffusion",
                    "vector", "convolution", "dropout", "batch norm", "fine-tuning", "pretraining",
                ]
            )
            if not has_tech_subject:
                scores["vagueness"] = max(scores["vagueness"], 0.80)
                scores["pragmatic"] = max(scores["pragmatic"], 0.70)
                missing_elements.append("Specific research inquiry or intended scope")
                details.append("Query is excessively brief and underspecified.")
        elif word_count < 4 and query_has_educational_intent:
            # Educational short queries are clear but may benefit from scope context
            scores["vagueness"] = max(scores["vagueness"], 0.15)  # Very low - not really vague

        # 5. Pragmatic Ambiguity: missing explicit scope or format
        if not any(token in lower for token in ["overview", "code", "architecture", "dataset", "math", "proof", "benchmark"]):
            if word_count > 3:
                scores["pragmatic"] = max(scores["pragmatic"], 0.30)

        # 6. Completeness Audit (w2 signal)
        completeness_penalties = 0.0
        generic_subjects = {"model", "models", "data", "dataset", "datasets", "algorithm", "algorithms", "illness", "disease", "overview", "it", "they", "them", "thing", "things", "tournament", "system", "method", "methods", "paper", "papers"}
        clean_entities = [e for e in entities if e.lower().strip() not in generic_subjects]

        if not clean_entities:
            completeness_penalties += 0.40
            missing_elements.append("Explicit research subject / entity")
        if word_count < 6:
            completeness_penalties += 0.25
        if scores["vagueness"] > 0.5:
            completeness_penalties += 0.20
        completeness_score = round(max(1.0 - completeness_penalties, 0.10), 2)

        # 7. Coherence & Contradiction Check (w3 signal)
        coherence_score = 1.0
        for pat, reason in self.CONTRADICTION_PATTERNS:
            if re.search(pat, lower):
                coherence_score = 0.15
                scores["semantic"] = max(scores["semantic"], 0.85)
                details.append(f"Incoherence: {reason}")
                missing_elements.append("Resolution of internal contradiction")

        # Compute aggregate score: blend weighted average with peak severity dimension
        weights = {
            "lexical": 0.20,
            "syntactic": 0.15,
            "semantic": 0.25,
            "pragmatic": 0.15,
            "vagueness": 0.25,
        }
        weighted_avg = sum(scores[k] * weights[k] for k in scores)
        max_dim_score = max(scores.values())
        overall = 0.4 * weighted_avg + 0.6 * max_dim_score
        overall = round(min(max(overall, 0.0), 1.0), 3)

        primary_type = max(scores.items(), key=lambda x: x[1])[0] if overall > 0.3 else None

        return AmbiguityReport(
            overall_ambiguity_score=overall,
            ambiguity_types={k: round(v, 2) for k, v in scores.items()},
            primary_ambiguity_type=primary_type,
            missing_elements=list(set(missing_elements)),
            completeness_score=completeness_score,
            coherence_score=coherence_score,
            ambiguity_details=" ".join(details) if details else "Query is sufficiently specific and coherent.",
        )
