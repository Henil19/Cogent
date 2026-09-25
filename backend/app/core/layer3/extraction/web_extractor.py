"""
Sub-Module 3.3b: Noise-Resilient Web Content Extractor
Research Basis: Mathematical Model for Accurate Main Content Extraction (IEEE Access 2025)
Strips DOM boilerplate (navigation, menus, ads, footers, scripts) and extracts clean article text,
author, and publication date for live web sources.
"""

import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from app.core.layer3.extraction.pdf_extractor import ExtractedDocumentUnit


class WebExtractor:
    """DOM-based main content extractor stripping web boilerplate."""

    BOILERPLATE_TAGS = [
        "script", "style", "nav", "header", "footer", "aside", "form",
        "noscript", "iframe", "svg", "button", "input"
    ]

    def __init__(self, timeout_sec: float = 8.0):
        self.timeout_sec = timeout_sec

    def extract_from_html(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        Extract clean main article text, metadata, and structural units from raw HTML.
        Implements IEEE Access 2025 DOM noise removal.
        """
        soup = BeautifulSoup(html, "html.parser")

        # 1. Extract metadata (Title, Author, Date)
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        else:
            title = url or "Web Document"

        author = None
        author_meta = soup.find("meta", attrs={"name": re.compile(r"author", re.I)})
        if author_meta and author_meta.get("content"):
            author = author_meta["content"].strip()

        pub_date = None
        date_meta = soup.find("meta", attrs={"property": re.compile(r"published_time|date", re.I)})
        if not date_meta:
            date_meta = soup.find("meta", attrs={"name": re.compile(r"date", re.I)})
        if date_meta and date_meta.get("content"):
            pub_date = date_meta["content"].strip()

        # 2. Strip all boilerplate elements
        for tag in soup.find_all(self.BOILERPLATE_TAGS):
            tag.decompose()

        # 3. Locate main article container (<article>, <main>, or body)
        main_container = soup.find("article") or soup.find("main") or soup.find("body") or soup

        # 4. Extract structural sections and paragraphs
        units: List[ExtractedDocumentUnit] = []
        current_section = title or "Web Article"

        for element in main_container.find_all(["h1", "h2", "h3", "h4", "p", "table"]):
            if element.name in ["h1", "h2", "h3", "h4"]:
                heading_text = element.get_text().strip()
                if heading_text:
                    current_section = heading_text
            elif element.name == "p":
                para_text = re.sub(r"\s+", " ", element.get_text()).strip()
                # Filter short navigation breadcrumbs or single-word noise
                if len(para_text) > 25:
                    units.append(ExtractedDocumentUnit(
                        content=para_text,
                        page_number=1,
                        section_title=current_section
                    ))
            elif element.name == "table":
                # Extract simple web tables
                rows = []
                for tr in element.find_all("tr"):
                    cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
                    if cells:
                        rows.append(cells)
                if len(rows) >= 2:
                    table_md = self._table_to_md(rows)
                    if table_md:
                        units.append(ExtractedDocumentUnit(
                            content=table_md,
                            page_number=1,
                            section_title=f"{current_section} (Table)",
                            has_table=True
                        ))

        # Fallback if no clean paragraphs were found
        if not units:
            fallback_text = re.sub(r"\s+", " ", main_container.get_text()).strip()
            if fallback_text:
                units.append(ExtractedDocumentUnit(
                    content=fallback_text,
                    page_number=1,
                    section_title=current_section
                ))

        parsed_url = urlparse(url)
        domain = parsed_url.netloc if url else "web"

        return {
            "title": title,
            "author": author,
            "publication_date": pub_date,
            "domain": domain,
            "source_uri": url,
            "units": units
        }

    def fetch_and_extract(self, url: str) -> Dict[str, Any]:
        """Fetch URL via HTTP and extract clean main content."""
        headers = {
            "User-Agent": "Cogent-Research-Agent/1.0 (Explainable RAG Corpus Ingestion; https://github.com/cogent)"
        }
        with httpx.Client(timeout=self.timeout_sec, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                raise ValueError(f"HTTP fetch failed with status {resp.status_code} for {url}")
            return self.extract_from_html(resp.text, url=url)

    def _table_to_md(self, rows: List[List[str]]) -> Optional[str]:
        max_cols = max(len(r) for r in rows)
        if max_cols == 0:
            return None
        norm = [r + [""] * (max_cols - len(r)) for r in rows]
        headers = norm[0]
        sep = ["---"] * max_cols
        lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
        for r in norm[1:]:
            lines.append("| " + " | ".join(r) + " |")
        return "\n".join(lines)
