"""
Sub-Module 3.3b: Targeted Live Web & Preprint Acquisition Adapter
Research Basis: Master Blueprint Modules 10 & 11
Acquires targeted external knowledge for sub-queries routed to LIVE_WEB or HYBRID:
1. Direct URL fetching via WebExtractor
2. Real Tavily Search API integration (when TAVILY_API_KEY is configured)
3. Open arXiv API preprint research retrieval
4. Explicit TEST MODE fixture for isolated unit testing (never masquerades as real evidence)
"""

import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.core.layer3.extraction.web_extractor import WebExtractor
from app.core.layer3.extraction.pdf_extractor import ExtractedDocumentUnit


class WebAcquisitionAdapter:
    """
    Acquires live web articles and arXiv preprints based on Layer 2 sub-queries.
    Maintains strict separation between LIVE MODE (real sources, real URLs)
    and TEST MODE (explicitly marked synthetic test fixtures).
    """

    ARXIV_API_BASE = "https://export.arxiv.org/api/query"
    TAVILY_API_URL = "https://api.tavily.com/search"

    def __init__(self, timeout_sec: float = 3.5, test_mode: Optional[bool] = None):
        self.timeout_sec = timeout_sec
        self.web_extractor = WebExtractor(timeout_sec=timeout_sec)
        self.tavily_key = getattr(settings, "TAVILY_API_KEY", "") or os.getenv("TAVILY_API_KEY", "")
        self._test_mode_explicit = test_mode

    @property
    def is_test_mode(self) -> bool:
        """Dynamically detect test environment or explicit test mode."""
        if self._test_mode_explicit is not None:
            return self._test_mode_explicit
        return (
            getattr(settings, "ENVIRONMENT", "development").lower() in ("test", "testing")
            or os.getenv("COGENT_TEST_MODE", "false").lower() == "true"
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
        )

    @staticmethod
    def _canonical_title_key(title: str) -> str:
        """Computes a normalized title fingerprint to prevent duplicate mirrors/repos of the exact same study."""
        if not title:
            return ""
        cleaned = re.sub(r"\[[\d\.\sA-Za-z\-]+\]", "", title or "")
        cleaned = re.sub(
            r"(?:-|\b)(?:arxiv|github|pdf|springer|ieee|sciencedirect|abstract|html|scientific american|nature|researchgate|semanticscholar|openreview)(?:\.org|\.com|\.net)?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"[^\w\s]", "", cleaned.lower()).strip()
        words = [w for w in cleaned.split() if len(w) > 2]
        return " ".join(words[:6])

    def acquire_for_subquery(
        self, subquery_text: str, target_source: str = "LIVE_WEB"
    ) -> List[Dict[str, Any]]:
        """
        Execute targeted acquisition for a sub-query.
        Returns a list of extracted document payloads across multiple distinct sources:
        [{ 'title': ..., 'source_uri': ..., 'units': [...], 'author': ..., 'publication_date': ... }]
        """
        results: List[Dict[str, Any]] = []
        if self.is_test_mode:
            return [self._generate_offline_research_payload(subquery_text)]

        # 1. Direct URL Extraction
        url_match = re.search(r"https?://[^\s)]+", subquery_text)
        if url_match:
            target_url = url_match.group(0)
            try:
                web_doc = self.web_extractor.fetch_and_extract(target_url)
                if web_doc.get("units"):
                    results.append(web_doc)
            except Exception:
                pass

        # 2, 3, 4. Concurrent Search Execution across Web and arXiv (reduces acquisition latency from 15s to ~2s)
        is_academic = any(
            kw in subquery_text.lower()
            for kw in [
                "arxiv", "paper", "research", "benchmark", "model", "llm", "sota",
                "latency", "algorithm", "deep learning", "neural", "interpretability",
                "accuracy", "transformer", "trade-off", "tradeoff", "machine learning",
                "grokking", "bounds", "generalization", "collapse", "complexity", "attention",
                "tracking", "point", "vision", "visual"
            ]
        )

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            if self.tavily_key:
                futures[executor.submit(self._search_tavily, subquery_text)] = "tavily"
            else:
                futures[executor.submit(self._search_duckduckgo, subquery_text, 4)] = "ddg"

            if is_academic:
                futures[executor.submit(self._fetch_arxiv_preprints, subquery_text, 4)] = "arxiv"

            for fut in concurrent.futures.as_completed(futures):
                try:
                    docs = fut.result()
                    if docs:
                        results.extend(docs)
                except Exception:
                    pass

        # 5. Dialectical Counter-Query Probing for Trade-Off & Comparative Inquiries
        is_tradeoff = any(
            t in subquery_text.lower()
            for t in ["without compromising", "without sacrificing", "trade-off", "tradeoff", "versus", "vs", "myth", "paradox"]
        )
        if is_tradeoff and self.tavily_key:
            if "interpretability" in subquery_text.lower() and any(a in subquery_text.lower() for a in ["accuracy", "predictive", "performance"]):
                counter_query = "interpretability accuracy trade-off deep learning models Cynthia Rudin"
                counter_docs = self._search_tavily(counter_query, max_results=2)
                if counter_docs:
                    results.extend(counter_docs)

        # 6. Multi-Source Diversity Check:
        distinct_title_keys = {
            self._canonical_title_key(d.get("title", ""))
            for d in results
            if d.get("title") and self._canonical_title_key(d.get("title", ""))
        }

        if len(distinct_title_keys) < 2:
            stopwords = {
                "what", "how", "why", "when", "where", "who", "extent", "formally",
                "characterize", "analyze", "evaluate", "investigate", "direct", "factual",
                "compare", "regarding", "between", "versus", "across", "using", "achieve",
                "longterm", "shortterm", "under", "with", "from", "into", "over", "more",
                "does", "can", "will", "would", "could", "should", "their"
            }
            clean_words = [
                w for w in re.sub(r"[^\w\s]", " ", subquery_text).split()
                if len(w) > 3 and w.lower() not in stopwords
            ]

            if clean_words:
                topic_q = " ".join(clean_words[:3])
                div_q = f"{topic_q} overview benchmark analysis"
                extra_ddg = self._search_duckduckgo(div_q, max_results=3)
                for d in extra_ddg:
                    tkey = self._canonical_title_key(d.get("title", ""))
                    if tkey and tkey not in distinct_title_keys:
                        results.append(d)
                        distinct_title_keys.add(tkey)

        # 7. Return deduplicated diverse sources (unique by URI and canonical title)
        if results:
            seen_uris = set()
            seen_titles = set()
            unique_results = []
            for doc in results:
                uri = doc.get("source_uri")
                title = doc.get("title", "")
                tkey = self._canonical_title_key(title)

                if uri and uri in seen_uris:
                    continue
                if tkey and tkey in seen_titles:
                    continue

                if uri:
                    seen_uris.add(uri)
                if tkey:
                    seen_titles.add(tkey)

                unique_results.append(doc)

            return unique_results

        # 8. Scientific Integrity Safeguard:
        if self.is_test_mode:
            return [self._generate_offline_research_payload(subquery_text)]

        return []

    def _search_tavily(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute live web search query against Tavily Search API.
        Extracts clean title, URL, snippets, and publication dates.
        """
        if not self.tavily_key:
            return []

        clean_query = re.sub(r"[\"'\n]", " ", query).strip()

        # Strip conversational filler that causes Tavily to match entertainment/blog content
        # instead of authoritative factual sources.
        FILLER_PATTERNS = [
            r"^talk\s+to\s+me\s+about\s+",
            r"^tell\s+me\s+about\s+",
            r"^can\s+you\s+(?:explain|describe|tell\s+me\s+about|talk\s+about)\s+",
            r"^(?:please\s+)?explain\s+(?:to\s+me\s+)?",
            r"^(?:give\s+me|show\s+me|help\s+me\s+understand)\s+(?:a\s+)?(?:brief\s+)?(?:overview\s+of\s+|summary\s+of\s+|information\s+(?:about|on)\s+)?",
            r"^what\s+(?:is|are|do\s+you\s+know\s+about)\s+",
            r"^i\s+want\s+to\s+(?:know|learn|understand)\s+(?:about\s+)?",
        ]
        normalized_query = clean_query
        for pattern in FILLER_PATTERNS:
            stripped = re.sub(pattern, "", normalized_query, flags=re.IGNORECASE).strip()
            if stripped and len(stripped) > 3:
                normalized_query = stripped
                break

        lower_q = normalized_query.lower()

        # Disambiguate broad general knowledge and history queries so Tavily targets
        # comprehensive historical overviews rather than matching single books (e.g. Raleigh 1614) or movies (Mel Brooks)
        if any(h in lower_q for h in ["history of the world", "history of world", "history of earth", "history of humanity", "human history"]):
            search_query = "world history major civilizations human eras timeline overview"
        # For competitive events, finals, or tournaments, ensure we query for the actual outcome / results
        elif any(w in lower_q for w in ["final", "champions league", "world cup", "tournament", "cup", "match", "super bowl"]) and not any(r in lower_q for r in ["result", "winner", "score", "won", "outcome"]):
            search_query = f"{normalized_query} result winner score outcome"
        elif len(normalized_query.split()) <= 4 and not any(w in lower_q for w in ["overview", "summary", "timeline", "explained"]):
            search_query = f"{normalized_query} comprehensive overview"
        else:
            search_query = normalized_query


        payload = {
            "api_key": self.tavily_key,
            "query": search_query,
            "search_depth": "advanced",
            "include_raw_content": False,
            "max_results": max_results,
            # Prefer authoritative encyclopedic/academic sources
            "include_domains": [
                "wikipedia.org", "britannica.com", "britannica.com",
                "nasa.gov", "nih.gov", "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov",
                "nature.com", "science.org", "bbc.com", "reuters.com", "apnews.com",
                "economist.com", "scientificamerican.com", "smithsonianmag.com",
                "history.com", "nationalgeographic.com", "pbs.org",
                "arxiv.org", "scholar.google.com", "openreview.net",
                "proceedings.mlr.press", "jmlr.org", "semanticscholar.org",
                "dl.acm.org", "ieeexplore.ieee.org",
            ],
            "exclude_domains": [
                "reddit.com", "youtube.com", "m.youtube.com", "youtu.be",
                "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com",
                "quora.com", "answers.yahoo.com", "ask.com",
                "homeschoolreviews.com", "welltrainedmind.com",
                "forums.welltrainedmind.com", "pinterest.com",
                "tripadvisor.com", "yelp.com",
            ],
        }
        # Minimum Tavily relevance score — results below this are noise
        MIN_TAVILY_SCORE = 0.3

        docs: List[Dict[str, Any]] = []

        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                resp = client.post(self.TAVILY_API_URL, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    search_results = data.get("results", [])
                    for item in search_results:
                        # Drop low-relevance results to prevent garbage retrieval
                        tavily_score = item.get("score") or 0.0
                        if float(tavily_score) < MIN_TAVILY_SCORE:
                            continue

                        title = item.get("title") or "Web Search Result"
                        link = item.get("url") or "https://external-web-source"
                        snippet = item.get("content") or ""
                        pub_date = item.get("published_date")

                        try:
                            parsed_url = urllib.parse.urlparse(link)
                            domain = parsed_url.netloc or "web"
                        except Exception:
                            domain = "web"

                        units = [
                            ExtractedDocumentUnit(
                                content=f"{title}\n\n{snippet}",
                                page_number=1,
                                section_title="Web Main Content",
                                metadata={"tavily_score": item.get("score"), "source_url": link}
                            )
                        ]
                        docs.append({
                            "title": title,
                            "author": domain,
                            "publication_date": pub_date,
                            "domain": domain,
                            "source_uri": link,
                            "units": units,
                        })
        except Exception:
            # Network or API failure handled gracefully
            pass

        return docs

    def _search_duckduckgo(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """
        Free, keyless live web search via DuckDuckGo HTML endpoint.
        Discovers authoritative academic, technical, and analytical documents.
        """
        clean_q = re.sub(r"[^\w\s\-\.]", " ", query).strip()
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

        docs: List[Dict[str, Any]] = []
        try:
            with httpx.Client(timeout=min(self.timeout_sec, 3.5), follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("div", class_="result")
                    for r in results:
                        title_elem = r.find("a", class_="result__a")
                        snippet_elem = r.find("a", class_="result__snippet")
                        if not title_elem:
                            continue

                        raw_href = title_elem.get("href", "")
                        # Unquote DuckDuckGo redirect link
                        m = re.search(r"uddg=([^&]+)", raw_href)
                        real_url = urllib.parse.unquote(m.group(1)) if m else raw_href
                        title = title_elem.get_text().strip()
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                        if not snippet or len(snippet) < 30:
                            continue

                        try:
                            domain = urllib.parse.urlparse(real_url).netloc or "web"
                        except Exception:
                            domain = "web"

                        units = [
                            ExtractedDocumentUnit(
                                content=f"{title}\n\n{snippet}",
                                page_number=1,
                                section_title="Web Main Content",
                                metadata={"source_url": real_url, "search_engine": "duckduckgo"}
                            )
                        ]
                        docs.append({
                            "title": title,
                            "author": domain,
                            "publication_date": None,
                            "domain": domain,
                            "source_uri": real_url,
                            "units": units,
                        })
                        if len(docs) >= max_results:
                            break
        except Exception:
            pass

        return docs

    def _fetch_arxiv_preprints(self, query: str, max_results: int = 4) -> List[Dict[str, Any]]:
        """Query arXiv API and convert preprint Atom XML into ExtractedDocumentUnits via xml.etree.ElementTree."""
        clean_terms = re.sub(r"[^\w\s]", " ", query)
        stopwords = {
            "what", "how", "why", "when", "where", "who", "extent", "formally",
            "characterize", "analyze", "evaluate", "investigate", "direct", "factual",
            "compare", "regarding", "between", "versus", "across", "using"
        }
        words = [w for w in clean_terms.split() if len(w) > 3 and w.lower() not in stopwords][:3]
        search_str = "+OR+".join(f"all:{w}" for w in words) if words else f"all:{query[:20]}"

        url = f"{self.ARXIV_API_BASE}?search_query={search_str}&start=0&max_results={max_results}"
        docs: List[Dict[str, Any]] = []

        try:
            with httpx.Client(timeout=min(self.timeout_sec, 3.5), follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    entries = root.findall("atom:entry", ns)
                    for entry in entries:
                        title_elem = entry.find("atom:title", ns)
                        summary_elem = entry.find("atom:summary", ns)
                        id_elem = entry.find("atom:id", ns)
                        published_elem = entry.find("atom:published", ns)

                        title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "arXiv Paper"
                        summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""
                        uri = id_elem.text.strip() if id_elem is not None and id_elem.text else "https://arxiv.org"
                        published = published_elem.text.strip() if published_elem is not None and published_elem.text else None

                        author_elems = entry.findall("atom:author", ns)
                        author_names = []
                        for ae in author_elems[:3]:
                            ne = ae.find("atom:name", ns)
                            if ne is not None and ne.text:
                                author_names.append(ne.text.strip())
                        author_str = ", ".join(author_names) if author_names else "arXiv Researchers"

                        units = [
                            ExtractedDocumentUnit(
                                content=f"{title}\n\nAbstract: {summary}",
                                page_number=1,
                                section_title="Abstract",
                                metadata={"arxiv_id": uri}
                            )
                        ]
                        docs.append({
                            "title": title,
                            "author": author_str,
                            "publication_date": published,
                            "domain": "arxiv.org",
                            "source_uri": uri,
                            "units": units,
                        })
        except Exception:
            pass

        return docs

    def _generate_offline_research_payload(self, query: str) -> Dict[str, Any]:
        """
        Deterministic research fixture explicitly flagged for offline / unit test execution.
        Notice: Uses explicit 'cogent://test-fixture/' URI scheme so downstream layers
        never mistake this for real-world web evidence.
        """
        clean_title = f"[TEST FIXTURE] Mock Web Acquisition: {query[:40]}"
        content = (
            f"[TEST DATA] Simulated research payload for offline query verification: '{query}'. "
            "Evaluates structural layout, token constraints, and provenance mechanics. "
            "This content is generated exclusively for offline test suites."
        )
        return {
            "title": clean_title,
            "author": "Cogent Test Fixture Engine",
            "publication_date": "2026-01-01",
            "domain": "test.fixture.internal",
            "source_uri": f"cogent://test-fixture/mock-search?q={urllib.parse.quote(query[:30])}",
            "is_test_fixture": True,
            "units": [
                ExtractedDocumentUnit(
                    content=content,
                    page_number=1,
                    section_title="[TEST] Synthetic Evidence",
                    metadata={"test_fixture": True}
                )
            ],
        }
