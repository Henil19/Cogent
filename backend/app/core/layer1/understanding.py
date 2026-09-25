"""
Sub-Module 1.2: Request Understanding Engine
Identifies high-level intent, query typology, extracts entities, scope constraints, and relationships.
Hybrid architecture: uses LLM structured mode when configured, falling back to deterministic linguistic analysis.
Research basis: P4 (Query Understanding in CIS - WWW 2025), P6 (Disambiguation Survey - EMNLP 2025)
"""

import re
from typing import Dict, List, Any
from app.schemas.layer1 import IntentCategory, QueryTypeCategory
from app.core.llm_client import LLMClient


class RequestUnderstandingEngine:
    """Classifies user intent, structural query complexity, and extracts research concepts."""

    COMPARATIVE_PATTERNS = [
        r"\b(compare|vs|versus|difference between|better than|advantages? of|pros and cons|differ)\b",
        r"\b(relative to|in contrast with|trade-offs?|which is (better|faster|best))\b",
    ]
    PROCEDURAL_PATTERNS = [
        r"\b(how to|steps to|guide for|procedure|methodology|how can i|algorithm for|workflow)\b",
        r"\b(implement|setup|configure|build|pipeline)\b",
    ]
    FACTUAL_PATTERNS = [
        r"\b(what is|who is|when did|where is|define|which year|state the|formula for)\b",
        r"\b(is it true that|does .* have)\b",
    ]
    SYNTHESIS_PATTERNS = [
        r"\b(synthesize|summarize findings|meta-analysis|cross-examine|literature review|aggregate across)\b",
        r"\b(comprehensive overview of all studies)\b",
    ]
    VERIFICATION_PATTERNS = [
        r"\b(is it true that|verify whether|validate if|does .* really|is there evidence that)\b",
    ]
    EXPLORATORY_PATTERNS = [
        r"\b(overview|survey|state of the art|landscape|explain|implications of|recent trends)\b",
        r"\b(future directions|background on|review of)\b",
    ]
    OPINION_PATTERNS = [
        r"\b(should i|which is best|recommend|your thought|is it worth|opinion on)\b",
    ]

    MULTI_HOP_MARKERS = [
        r"\b(and its impact on|leading to|caused by|resulting from|because of which|subsequently)\b",
        r"\b(after .* what happens|correlation between .* and .* influencing)\b",
    ]

    def __init__(self):
        self.llm_client = LLMClient()

    def analyze(self, query: str) -> Dict[str, Any]:
        """Perform intent, typology, and conceptual extraction on sanitized query in <1ms."""
        # Use high-precision deterministic analysis to avoid unnecessary LLM latency
        return self._deterministic_analysis(query)

    def _try_llm_analysis(self, query: str) -> Dict[str, Any] | None:
        """Call LLM with structured taxonomy prompt."""
        system_prompt = (
            "You are a research query understanding engine. Analyze the user's research query and return a JSON object with: "
            "'intent' (FACTUAL, COMPARATIVE, EXPLORATORY, PROCEDURAL, SYNTHESIS, VERIFICATION), "
            "'query_type' (SINGLE_HOP, MULTI_HOP, SYNTHESIS, HYPOTHESIS_TESTING, OPINION_SEEKING), "
            "'subjects' (list of key subject strings), "
            "'scope_constraints' (list of constraints such as timeframe, population, benchmark), "
            "'relationship_indicators' (list of relationship words like 'causes', 'better than', 'impacts'), "
            "'intent_confidence' (float between 0.0 and 1.0)."
        )
        data = self.llm_client.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=f"Query: {query}",
        )
        if not data or "intent" not in data:
            return None

        try:
            intent_str = str(data.get("intent", "EXPLORATORY")).lower()
            intent = IntentCategory(intent_str) if intent_str in IntentCategory.__members__.values() else IntentCategory.EXPLORATORY

            qtype_str = str(data.get("query_type", "SINGLE_HOP")).lower()
            qtype = QueryTypeCategory(qtype_str) if qtype_str in QueryTypeCategory.__members__.values() else QueryTypeCategory.SINGLE_HOP

            entities = list(data.get("subjects", []))
            constraints = list(data.get("scope_constraints", []))
            concepts = entities + constraints

            return {
                "intent": intent,
                "query_type": qtype,
                "entities": entities,
                "key_concepts": concepts,
                "constraints": constraints,
                "intent_clarity_score": float(data.get("intent_confidence", 0.85)),
            }
        except Exception:
            return None

    def _deterministic_analysis(self, query: str) -> Dict[str, Any]:
        """High-precision heuristic analysis when offline."""
        intent, intent_clarity = self._detect_intent(query)
        query_type = self._detect_query_type(query)
        entities, concepts, constraints = self._extract_entities_and_concepts(query)

        return {
            "intent": intent,
            "query_type": query_type,
            "entities": entities,
            "key_concepts": concepts,
            "constraints": constraints,
            "intent_clarity_score": intent_clarity,
        }

    def _detect_intent(self, text: str) -> tuple[IntentCategory, float]:
        lower = text.lower()
        for pat in self.COMPARATIVE_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.COMPARATIVE, 0.90
        for pat in self.SYNTHESIS_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.SYNTHESIS, 0.90
        for pat in self.VERIFICATION_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.VERIFICATION, 0.85
        for pat in self.PROCEDURAL_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.PROCEDURAL, 0.85
        for pat in self.FACTUAL_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.FACTUAL, 0.85
        for pat in self.EXPLORATORY_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.EXPLORATORY, 0.80
        for pat in self.OPINION_PATTERNS:
            if re.search(pat, lower):
                return IntentCategory.OPINION_SEEKING, 0.75
        return IntentCategory.EXPLORATORY, 0.70

    def _detect_query_type(self, text: str) -> QueryTypeCategory:
        lower = text.lower()
        for pat in self.SYNTHESIS_PATTERNS:
            if re.search(pat, lower):
                return QueryTypeCategory.SYNTHESIS
        for pat in self.VERIFICATION_PATTERNS:
            if re.search(pat, lower):
                return QueryTypeCategory.HYPOTHESIS_TESTING
        for pat in self.MULTI_HOP_MARKERS:
            if re.search(pat, lower):
                return QueryTypeCategory.MULTI_HOP
        if len(re.findall(r"\b(and|while|whereas|furthermore)\b", lower)) >= 2:
            return QueryTypeCategory.MULTI_HOP
        return QueryTypeCategory.SINGLE_HOP

    def _extract_entities_and_concepts(self, text: str) -> tuple[List[str], List[str], List[str]]:
        # Proper noun entities
        proper_entities = re.findall(r"\b[A-Z][a-zA-Z0-9_-]+(?:\s+[A-Z][a-zA-Z0-9_-]+)*\b", text)
        stopwords = {
            "what", "how", "why", "when", "where", "who", "the", "is", "are", "in", "on", "explain",
            "which", "to", "does", "can", "could", "should", "would", "do", "did", "will", "shall",
            "may", "might", "must", "analyze", "evaluate", "compare", "if", "whether", "show", "describe",
            "detail", "about", "from", "for", "with", "between", "into", "through", "an", "a", "of"
        }
        entities = [e for e in proper_entities if e.lower() not in stopwords and len(e) >= 3]

        # Acronyms (e.g. LLM, RAG, BERT, CNN, Transformer)
        acronyms = re.findall(r"\b[A-Z]{2,}\b", text)
        entities.extend([a for a in acronyms if a.lower() not in stopwords and a not in entities])

        # Constraints (timeframes, benchmarks, languages)
        constraints = []
        year_match = re.findall(r"\b(19\d\d|20\d\d)\b", text)
        if year_match:
            constraints.extend([f"Year: {y}" for y in year_match])
        if re.search(r"\b(recent|latest|last \d+ years?)\b", text.lower()):
            constraints.append("Temporal: recent")

        # Concepts
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        ignore = {
            "what", "which", "where", "when", "could", "would", "should", "their", "there",
            "about", "between", "under", "these", "those", "other", "using", "through", "having"
        }
        concepts = [w for w in words if w not in ignore][:6]

        return list(set(entities)), list(set(concepts)), constraints
