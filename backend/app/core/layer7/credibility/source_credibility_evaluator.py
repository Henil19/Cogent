"""
Sub-Module 7.1: Source Credibility & Authority Evaluator
Research Basis:
- RA-RAG: Retrieval-Augmented Generation with Estimation of Source Reliability (Hwang et al., EMNLP 2025)
- CONFACT: Resolving Conflicting Evidence in Automated Fact-Checking (Ge et al., IJCAI 2025)
- Source Credibility Theory & Web Assessment (Metzger & Flanagin, 2013)

Evaluates source characteristics: venue tiering, domain authority heuristics,
configurable domain-aware temporal decay, and cross-source corroboration.
"""

import math
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Dict, List, Optional

from app.schemas.layer3 import SourceType
from app.schemas.layer5 import VerifiedEvidenceSet, EvidenceItem
from app.schemas.layer7 import SourceTier, SourceCredibilityAssessment

logger = logging.getLogger(__name__)

# Initial heuristic baseline tier weights (subject to empirical calibration)
DEFAULT_TIER_WEIGHTS: Dict[SourceTier, float] = {
    SourceTier.PEER_REVIEWED_PAPER: 1.00,
    SourceTier.GOVERNMENT_OFFICIAL: 0.95,
    SourceTier.INSTITUTIONAL_REPORT: 0.92,
    SourceTier.TECHNICAL_DOCUMENTATION: 0.88,
    SourceTier.NEWS_MEDIA: 0.82,
    SourceTier.PREPRINT: 0.75,
    SourceTier.BLOG_POST: 0.45,
    SourceTier.FORUM_DISCUSSION: 0.25,
    SourceTier.UNKNOWN: 0.60
}

# Configurable domain temporal decay rates (lambda)
DEFAULT_DOMAIN_LAMBDAS: Dict[str, float] = {
    "MACHINE_LEARNING": 0.40,     # Fast-decaying benchmark domain (half-life ~1.7 yrs)
    "COMPUTER_SCIENCE": 0.25,     # Half-life ~2.8 yrs
    "BIOMEDICAL": 0.15,           # Half-life ~4.6 yrs
    "GENERAL_SCIENCE": 0.10,      # Half-life ~6.9 yrs
    "HISTORY": 0.02,              # Negligible decay (half-life ~35 yrs)
    "GENERAL": 0.20               # Default decay
}


class SourceCredibilityEvaluator:
    """
    Computes a source credibility assessment score based on predefined provenance,
    venue authority, domain-aware temporal decay, and cross-source corroboration.
    """

    def __init__(
        self,
        tier_weights: Optional[Dict[SourceTier, float]] = None,
        domain_lambdas: Optional[Dict[str, float]] = None
    ):
        self.tier_weights = tier_weights or DEFAULT_TIER_WEIGHTS
        self.domain_lambdas = domain_lambdas or DEFAULT_DOMAIN_LAMBDAS

    def evaluate_sources(
        self,
        evidence_set: VerifiedEvidenceSet,
        target_domain: str = "GENERAL"
    ) -> List[SourceCredibilityAssessment]:
        """
        Evaluate credibility for all unique sources backing selected evidence items.
        """
        assessments: List[SourceCredibilityAssessment] = []
        seen_source_uris = set()

        # Group evidence items by source/domain for corroboration analysis
        all_evidence = evidence_set.selected_evidence
        total_sources = len(all_evidence)

        for ev in all_evidence:
            source_uri = ev.source_uri or f"doc_{ev.document_id}"
            if source_uri in seen_source_uris:
                continue
            seen_source_uris.add(source_uri)

            # 1. Classify Source Tier & Extract Domain
            tier, domain = self._classify_tier_and_domain(ev)

            # 2. Compute Authority Score based on tier and recognized venue
            base_tier_score = self.tier_weights.get(tier, 0.30)
            authority_score = self._compute_authority(tier, domain, ev)

            # 3. Compute Domain-Aware Temporal Recency Decay
            recency_score, recency_factor = self._compute_recency(ev.publication_date, target_domain)

            # 4. Compute Cross-Source Corroboration Fraction
            corrob_score, corrob_factor = self._compute_corroboration(ev, all_evidence)

            # 5. Composite Source Credibility Assessment Score
            # Multi-attribute weighted combination
            composite = (
                0.45 * authority_score +
                0.30 * recency_score +
                0.25 * corrob_score
            )
            overall_credibility = max(0.0, min(1.0, composite))

            factors = [
                f"Source Tier: {tier.value} (Base authority weight: {base_tier_score:.2f})",
                f"Domain: {domain}",
                recency_factor,
                corrob_factor
            ]
            if ev.author:
                factors.append(f"Document attribution: {ev.author}")

            assessment = SourceCredibilityAssessment(
                source_id=f"src_{ev.document_id[:8]}",
                source_uri=source_uri,
                source_type=tier,
                domain=domain,
                authority_score=round(authority_score, 4),
                recency_score=round(recency_score, 4),
                corroboration_score=round(corrob_score, 4),
                overall_credibility=round(overall_credibility, 4),
                credibility_factors=factors
            )
            assessments.append(assessment)

        logger.debug(f"SourceCredibilityEvaluator evaluated {len(assessments)} unique sources.")
        return assessments

    def _classify_tier_and_domain(self, ev: EvidenceItem) -> tuple[SourceTier, str]:
        """Categorize evidence into SourceTier and extract clean domain."""
        uri = (ev.source_uri or "").lower()
        title = (ev.title or "").lower()

        # Parse network domain if URL
        domain = "local_document"
        if uri.startswith("http://") or uri.startswith("https://"):
            try:
                parsed = urlparse(uri)
                domain = parsed.netloc or "web"
            except Exception:
                domain = "web"

        # Heuristic classification
        if "arxiv.org" in uri or "biorxiv.org" in uri or "medrxiv.org" in uri:
            return SourceTier.PREPRINT, domain
        if ".gov" in domain or "who.int" in domain or "nih.gov" in domain or "fda.gov" in domain:
            return SourceTier.GOVERNMENT_OFFICIAL, domain
        if ".edu" in domain or "acm.org" in domain or "ieee.org" in domain or "nature.com" in domain or "sciencedirect.com" in domain:
            return SourceTier.PEER_REVIEWED_PAPER, domain
        if any(auth in domain for auth in ["uefa.com", "fifa.com", "olympics.com", "wikipedia.org", "britannica.com", "un.org"]):
            return SourceTier.INSTITUTIONAL_REPORT, domain
        if "docs." in domain or "developer." in domain or "github.com" in domain or "documentation" in title:
            return SourceTier.TECHNICAL_DOCUMENTATION, domain
        if ev.source_type == SourceType.LOCAL_PDF or "paper" in title or "proceedings" in title:
            return SourceTier.PEER_REVIEWED_PAPER, domain
        if any(news in domain for news in ["reuters.com", "bbc.", "apnews.com", "bloomberg.com", "yahoo.com", "espn.com", "theguardian.com", "skysports.com", "nytimes.com", "cnn.com"]):
            return SourceTier.NEWS_MEDIA, domain
        if "medium.com" in domain or "substack.com" in domain or "blog" in uri or "blog" in domain:
            return SourceTier.BLOG_POST, domain
        if "reddit.com" in domain or "stackoverflow.com" in domain or "forum" in domain:
            return SourceTier.FORUM_DISCUSSION, domain

        return SourceTier.UNKNOWN, domain

    def _compute_authority(self, tier: SourceTier, domain: str, ev: EvidenceItem) -> float:
        """Calculate authority score incorporating tier and domain signals."""
        base = self.tier_weights.get(tier, 0.30)
        bonus = 0.0

        # Provenance richness bonuses
        if ev.document_hash and ev.content_hash:
            bonus += 0.03
        if ev.author:
            bonus += 0.02

        # Recognizable authoritative domains
        if any(auth in domain for auth in [".gov", ".edu", "arxiv.org", "ieee.org", "acm.org", "nature.com"]):
            bonus += 0.05

        return min(1.0, base + bonus)

    def _compute_recency(self, publication_date: Optional[str], domain_key: str) -> tuple[float, str]:
        """Compute domain-aware exponential temporal decay exp(-lambda * delta_t)."""
        decay_lambda = self.domain_lambdas.get(domain_key.upper(), self.domain_lambdas["GENERAL"])
        
        if not publication_date:
            # Neutral recency when date is unrecorded
            return 0.70, f"Publication date unrecorded; assigned neutral recency (0.70, lambda={decay_lambda})"

        try:
            # Parse publication year/date
            dt = None
            for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
                try:
                    dt = datetime.strptime(publication_date.strip()[:10], fmt)
                    break
                except ValueError:
                    continue

            if not dt:
                return 0.70, f"Unparseable publication date '{publication_date}'; assigned neutral recency (0.70)"

            now_year = datetime.now(timezone.utc).year
            years_old = max(0.0, now_year - dt.year)

            # Exponential decay: exp(-lambda * delta_years)
            decay_score = math.exp(-decay_lambda * years_old)
            clamped = max(0.10, min(1.0, decay_score))
            
            desc = (
                f"Published {publication_date} (~{years_old:.1f} yrs ago). "
                f"Domain decay (lambda={decay_lambda:.2f}) yields recency score {clamped:.2f}"
            )
            return clamped, desc

        except Exception as e:
            logger.warning(f"Error computing recency for {publication_date}: {e}")
            return 0.70, "Neutral recency applied due to date calculation error"

    def _compute_corroboration(self, target_ev: EvidenceItem, all_evidence: List[EvidenceItem]) -> tuple[float, str]:
        """Check how many other independent sources affirm or share similar atomic claims."""
        if len(all_evidence) <= 1:
            return 0.60, "Single retrieved source; cross-source corroboration unmeasured (0.60)"

        other_sources = [ev for ev in all_evidence if ev.evidence_id != target_ev.evidence_id]
        if not other_sources:
            return 0.60, "No external sources to corroborate with"

        # Check semantic overlap of atomic claims across different sources
        target_claims = [c.claim_text.lower() for c in target_ev.atomic_claims]
        corrob_count = 0

        for other in other_sources:
            other_text = other.content.lower()
            # If any target claim words/tokens appear substantially in the other source
            matched = any(
                any(token in other_text for token in c.split() if len(token) > 5)
                for c in target_claims
            )
            if matched:
                corrob_count += 1

        corrob_fraction = corrob_count / len(other_sources)
        score = min(1.0, 0.50 + 0.50 * corrob_fraction)
        desc = f"Corroborated by {corrob_count}/{len(other_sources)} independent sources in candidate pool ({score:.2f})"
        return score, desc
