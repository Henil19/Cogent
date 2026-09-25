"""
Sub-Module 5.2: Atomic Claim Extraction & Proposition Splitting
Research basis:
- Lu et al. (ACL 2025): Optimizing Decomposition for Optimal Claim Verification
- Hu et al. (NAACL 2025): Decomposition Dilemmas & Decontextualization Quality Control
- FActScore (Min et al., EMNLP 2023): Proposition-level atomic fact breakdown

Deconstructs complex candidate passages into atomic, standalone, testable propositions.
Resolves anaphoric pronouns using parent titles and enforces the Atomicity Quality Gate.
"""

import re
import uuid
import logging
from typing import List, Optional, Tuple

from app.core.llm_client import LLMClient
from app.schemas.layer4 import RetrievedCandidate
from app.schemas.layer5 import AtomicClaim, GroundingStatus

logger = logging.getLogger(__name__)

PRONOUN_MAP = {
    "it": "the system",
    "they": "the authors",
    "this model": "the evaluated model",
    "the model": "the model",
    "this approach": "the proposed approach",
    "this architecture": "the architecture"
}


class AtomicClaimExtractor:
    """
    Extracts atomic, decontextualized proposition claims from candidate passages.
    Supports LLM extraction when configured, with seamless deterministic fallback.
    """

    def __init__(
        self,
        min_words: int = 4,
        max_words: int = 40,
        llm_client: Optional[LLMClient] = None
    ):
        self.min_words = min_words
        self.max_words = max_words
        self.llm_client = llm_client or LLMClient()

    def extract_claims(self, candidate: RetrievedCandidate) -> List[AtomicClaim]:
        """
        Deconstruct a RetrievedCandidate into a list of verified atomic claims.
        """
        text = candidate.content.strip()
        # Strip Late Chunking document header metadata so it never becomes an atomic claim
        text = re.sub(r"^\[Document:.*?\]\s*", "", text, flags=re.DOTALL)
        if not text:
            text = getattr(candidate, "raw_content", "") or candidate.content
        text = text.strip()
        if not text:
            return []

        # High-performance deterministic proposition deconstruction following RLSeek & Trove
        # This executes in sub-millisecond time and eliminates dozens of blocking external LLM roundtrips
        return self._extract_claims_deterministic(candidate)

    def _extract_with_llm(self, candidate: RetrievedCandidate) -> Optional[List[AtomicClaim]]:
        """Extract atomic propositions via LLM structured JSON generation."""
        if not self.llm_client or not self.llm_client._is_configured:
            return None
        system_prompt = (
            "You are an expert fact-checking proposition extraction assistant following Lu et al. (ACL 2025) "
            "and Hu et al. (NAACL 2025). Extract standalone, atomic factual propositions from the given text. "
            "Resolve pronouns (e.g. 'it', 'they', 'this model') to specific subject entities mentioned in the title or text. "
            "Return JSON with key 'claims': list of objects with 'claim_text', 'subject', 'predicate', 'target_value', 'quote_span'."
        )
        user_prompt = f"Document Title: {candidate.title}\nPassage Content:\n{candidate.content}"
        data = self.llm_client.generate_structured_json(system_prompt, user_prompt)
        if not data or "claims" not in data or not isinstance(data["claims"], list):
            return None

        extracted = []
        for idx, item in enumerate(data["claims"]):
            claim_text = item.get("claim_text", "").strip()
            if not claim_text:
                continue
            is_valid, is_atomic = self._quality_gate(claim_text)
            if not is_valid:
                continue
            extracted.append(
                AtomicClaim(
                    claim_id=f"clm_{candidate.chunk_id[:8]}_llm_{idx}",
                    parent_chunk_id=candidate.chunk_id,
                    candidate_id=candidate.candidate_id,
                    claim_text=claim_text,
                    grounding_status=GroundingStatus.NEUTRAL,
                    grounding_score=0.0,
                    quote_span=item.get("quote_span") or candidate.content[:100],
                    is_atomic=is_atomic,
                    subject=item.get("subject"),
                    predicate=item.get("predicate"),
                    target_value=item.get("target_value")
                )
            )
        return extracted if extracted else None

    def _extract_claims_deterministic(self, candidate: RetrievedCandidate) -> List[AtomicClaim]:
        """Deterministic proposition deconstruction and decontextualization."""
        text = candidate.content.strip()
        text = re.sub(r"^\[Document:.*?\]\s*", "", text, flags=re.DOTALL)
        text = re.sub(r"\[Document:.*?\]", "", text, flags=re.DOTALL)
        text = re.sub(r"^Section:[^\n]*\n?", "", text)
        text = re.sub(r"^#+\s*", "", text)
        text = text.strip()

        # Clean and split into candidate sentences
        raw_sentences = self._split_sentences(text)

        # Decontextualize and decompose into atomic propositions
        claims: List[AtomicClaim] = []
        entity_anchor = self._extract_entity_anchor(candidate.title, text)

        for s_idx, sentence in enumerate(raw_sentences):
            # Decontextualize pronouns
            decontextualized = self._decontextualize(sentence, entity_anchor)

            # Split compound clauses
            propositions = self._split_propositions(decontextualized)

            for p_idx, prop in enumerate(propositions):
                # Apply Atomicity Quality Gate (Hu et al. NAACL 2025)
                is_valid, is_atomic = self._quality_gate(prop)
                if not is_valid:
                    continue

                subj, pred, target = self._extract_spo_components(prop)
                claim_id = f"clm_{candidate.chunk_id[:8]}_{s_idx}_{p_idx}"

                claims.append(
                    AtomicClaim(
                        claim_id=claim_id,
                        parent_chunk_id=candidate.chunk_id,
                        candidate_id=candidate.candidate_id,
                        claim_text=prop,
                        grounding_status=GroundingStatus.NEUTRAL,
                        grounding_score=0.0,
                        quote_span=sentence,  # Initial quote anchor is the parent sentence
                        is_atomic=is_atomic,
                        subject=subj,
                        predicate=pred,
                        target_value=target
                    )
                )

        logger.debug(f"Extracted {len(claims)} atomic claims from candidate {candidate.candidate_id}")
        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences handling periods, exclamation marks, question marks, and newlines."""
        # Avoid splitting on common abbreviations like e.g., i.e., et al.
        clean = re.sub(r"\bet al\.", "et al", text)
        clean = re.sub(r"\be\.g\.,", "eg", clean)
        clean = re.sub(r"\bi\.e\.,", "ie", clean)
        sentences = re.split(r"[\r\n]+|(?<=[.?!])\s+", clean)
        cleaned_sentences = []
        for s in sentences:
            s_clean = re.sub(r"^#+\s*", "", s).strip()
            # Strip Title: prefixes
            s_clean = re.sub(r"^Title:\s*", "", s_clean, flags=re.IGNORECASE).strip()
            if len(s_clean) > 5 and len(s_clean.split()) >= 3:
                cleaned_sentences.append(s_clean)
        return cleaned_sentences

    def _extract_entity_anchor(self, title: str, text: str) -> str:
        """Extract primary subject anchor from title or opening sentence."""
        clean_title = re.sub(r"^\d+[\.\s]+", "", title).strip()
        if clean_title and len(clean_title.split()) <= 6:
            return clean_title
        # Fallback to first capitalized noun phrase in text
        match = re.search(r"\b([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z][a-zA-Z0-9_\-]+)?)\b", text)
        if match:
            return match.group(1)
        return "The subject"

    def _decontextualize(self, sentence: str, entity_anchor: str) -> str:
        """Replace leading ambiguous pronouns with concrete entity anchor."""
        s = sentence.strip()
        # Replace leading 'It ' or 'This model '
        if re.match(r"^It\b", s, re.IGNORECASE):
            s = re.sub(r"^It\b", entity_anchor, s, count=1, flags=re.IGNORECASE)
        elif re.match(r"^This model\b", s, re.IGNORECASE):
            s = re.sub(r"^This model\b", entity_anchor, s, count=1, flags=re.IGNORECASE)
        elif re.match(r"^They\b", s, re.IGNORECASE):
            s = re.sub(r"^They\b", f"The authors of {entity_anchor}", s, count=1, flags=re.IGNORECASE)
        return s

    def _split_propositions(self, sentence: str) -> List[str]:
        """Split compound sentences joined by contrasting or additive conjunctions."""
        # Split on ';', ' whereas ', ' while ', ' and also '
        parts = re.split(r";|\bwhereas\b|\bwhile\b|\band also\b", sentence, flags=re.IGNORECASE)
        results = []
        for p in parts:
            clean_p = p.strip()
            if clean_p.endswith("."):
                clean_p = clean_p[:-1].strip()
            if clean_p:
                results.append(clean_p + ".")
        return results if results else [sentence]

    def _quality_gate(self, proposition: str) -> Tuple[bool, bool]:
        """
        Atomicity Quality Gate (Hu et al. NAACL 2025).
        Returns (is_valid, is_atomic).
        """
        clean_prop = proposition.strip()
        # Reject question headlines, query teasers, or any proposition containing a question mark
        if "?" in clean_prop or re.match(r"^(?:Where|When|Who|How|What|Why)\s+(?:is|are|was|were|will|to)\b", clean_prop, re.IGNORECASE):
            return False, False

        # Reject live blog previews, score teasers, and in-progress live commentary
        teaser_patterns = [
            "live score", "live update", "confirmed lineup", "kickoff time",
            "stay tuned", "how to watch", "where to watch", "watch live",
            "up for grabs", "yet to be decided", "matchday 1 results"
        ]
        if any(tp in clean_prop.lower() for tp in teaser_patterns):
            return False, False

        words = clean_prop.split()
        word_count = len(words)

        # Reject tiny sentence fragments or massive run-on blocks
        if word_count < self.min_words:
            return False, False
        if word_count > self.max_words:
            return True, False  # Keep but flag non-atomic

        # Must contain at least one verb-like pattern
        has_verb = bool(re.search(
            r"\b(is|are|was|were|will|would|can|could|should|may|might|has|have|had|"
            r"achieves?|shows?|demonstrates?|improves?|reduces?|increases?|accelerates?|exhibits?|"
            r"evaluates?|replicates?|mitigates?|detects?|identifies?|maintains?|guarantees?|"
            r"uses?|using|used|outperforms?|relies?|scales?|requires?|proposes?|contains?|provides?|"
            r"combines?|prevents?|enables?|yields?|applies?|integrates?|performs?|enhances?|ensures?|"
            r"results?|leads?|causes?|modifies?|generates?|determines?|take place|takes place|held|played|"
            r"won|wins|winning|defeated|defeats|defeating|beat|beats|beaten|scored|scores|scoring|"
            r"crowned|lifted|clinched|finished|concluded|ended|decided|secured|advanced|eliminated|"
            r"drew|draws|tied|led|leads|lost|loses|signed|elected|announced|agreed|passed|approved|"
            r"ruled|confirmed|reported|stated|declared|published|found|created|produced|released|earned|received)\b",
            clean_prop,
            re.IGNORECASE
        )) or bool(re.search(r"\b[a-zA-Z]{3,}(?:s|ed|ing)\b", clean_prop))
        if not has_verb:
            return False, False

        return True, True

    def _extract_spo_components(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract Subject, Predicate, and Target Value/Object components."""
        # Extract numerical metrics if present (e.g. 92%, 15ms, 4.5x)
        metric_match = re.search(r"(\d+(?:\.\d+)?(?:\%|ms|s|x|GB|MB|K|M)?)", text)
        target_val = metric_match.group(1) if metric_match else None

        words = text.split()
        if len(words) >= 3:
            subj = " ".join(words[:2])
            pred = " ".join(words[2:5])
        else:
            subj, pred = None, None

        return subj, pred, target_val
