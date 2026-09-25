"""
Sub-Module 9.8b & 9.8c: Multi-Fidelity Bundler, Streaming & Export Engine
Bundles 4-audience multi-fidelity views and formats responses for Markdown, HTML, PDF-ready, and SSE streaming.
Research: RAG+ (EMNLP 2025), Searching for Best Practices in RAG (EMNLP 2024).
"""

from typing import List, Dict, Any, Generator
from app.schemas.layer8 import ExplanationPackage
from app.schemas.layer9 import (
    MultiFidelityViewsPayload,
    RenderedSection,
    CitationBadgeEntry,
    TrustBadgePayload,
    PresentationFormat,
    ResponseSectionType
)


class ResponsePackagingEngine:
    """
    Sub-Module 9.8b & 9.8c: Handles multi-fidelity view bundling and multi-format exports.
    """

    def __init__(self):
        pass

    def bundle_multi_fidelity_views(
        self,
        explanation_pkg: ExplanationPackage
    ) -> MultiFidelityViewsPayload:
        """
        Extracts and bundles pre-rendered text for all 4 audience tiers from Layer 8.
        Guarantees Epistemic Invariance during instantaneous frontend tab switching.
        """
        multi = explanation_pkg.multi_fidelity
        return MultiFidelityViewsPayload(
            executive=multi.executive_summary,
            technical_researcher=multi.researcher_narrative,
            layperson=multi.layperson_narrative,
            domain_expert=multi.domain_expert_narrative
        )

    def export_content(
        self,
        sections: List[RenderedSection],
        citation_registry: List[CitationBadgeEntry],
        trust_badges: TrustBadgePayload,
        format_type: PresentationFormat = PresentationFormat.MARKDOWN
    ) -> str:
        """
        Serializes the rendered sections into the requested presentation format.
        """
        # Body sections only for primary synthesized reading view.
        # References & source details are cleanly provided via interactive citation pills [1] and the citation drawer.
        body_sections = [
            sec for sec in sections
            if sec.section_type != ResponseSectionType.REFERENCES_FOOTNOTES
        ]
        raw_markdown = "\n\n".join(sec.content_markdown for sec in body_sections if sec.content_markdown.strip())

        if format_type == PresentationFormat.MARKDOWN:
            return raw_markdown

        elif format_type == PresentationFormat.HTML:
            return self._convert_to_semantic_html(sections, trust_badges)

        elif format_type == PresentationFormat.PDF_SEMANTIC:
            # Semantic structure ready for headless browser or PDF generator
            return raw_markdown

        return raw_markdown

    def _convert_to_semantic_html(
        self,
        sections: List[RenderedSection],
        trust_badges: TrustBadgePayload
    ) -> str:
        """Generates clean, semantic HTML representation with header metadata."""
        html_parts = [
            "<article class=\"cogent-response-document\">",
            f"  <header class=\"cogent-trust-header\">",
            f"    <span class=\"badge confidence-{trust_badges.confidence_tier.value.lower()}\">Confidence: {trust_badges.calibrated_confidence:.2f} ({trust_badges.confidence_tier.value})</span>",
            f"    <span class=\"badge trust-index\">Trust Index: {trust_badges.trust_index:.2f}</span>",
            f"    <span class=\"badge risk-level\">Risk: {trust_badges.risk_level}</span>",
            f"  </header>"
        ]

        for sec in sections:
            html_parts.append(f"  <section class=\"response-section\" data-type=\"{sec.section_type.value}\">")
            html_parts.append(f"    <h2>{sec.section_title}</h2>")
            # Simple line-to-paragraph mapping
            paragraphs = sec.content_markdown.split("\n\n")
            for p in paragraphs:
                p_clean = p.strip()
                if p_clean:
                    if p_clean.startswith(">"):
                        html_parts.append(f"    <blockquote>{p_clean.lstrip('> ')}</blockquote>")
                    elif p_clean.startswith("-"):
                        items = p_clean.split("\n")
                        html_parts.append("    <ul>")
                        for it in items:
                            html_parts.append(f"      <li>{it.lstrip('- ')}</li>")
                        html_parts.append("    </ul>")
                    elif not p_clean.startswith("#"):
                        html_parts.append(f"    <p>{p_clean}</p>")
            html_parts.append("  </section>")

        html_parts.append("</article>")
        return "\n".join(html_parts)

    def stream_response_chunks(
        self,
        rendered_content: str,
        chunk_size: int = 40
    ) -> Generator[str, None, None]:
        """
        Yields incremental SSE streaming chunks of the validated response text.
        """
        words = rendered_content.split(" ")
        buffer = []
        for word in words:
            buffer.append(word)
            if len(buffer) >= chunk_size:
                yield " ".join(buffer) + " "
                buffer = []
        if buffer:
            yield " ".join(buffer)
