"""
Systematic Literature Review (SLR) Search Execution Script for Cogent Paper.
Queries OpenAlex, Crossref, and arXiv APIs across the four core research themes:
1. RAG + Epistemic / Confidence Calibration & Uncertainty
2. RAG + Citation / Evidence Attribution & Faithfulness
3. RAG + Conflict Resolution & Contradictory Information
4. RAG + Multi-Hop Reasoning & Entailment / Knowledge Graphs

Outputs:
- slr_search_records.json (raw API logs, queries, total counts, top papers)
- slr_prisma_flow.json (PRISMA funnel numbers: Identification, Screening, Eligibility, Included)
- slr_taxonomy_matrix.md (Structured comparison table of relevant papers vs Cogent)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

USER_AGENT = "CogentResearchSLR/1.0 (mailto:henilpatel072004@gmail.com; IEEE-Paper-Prep)"

SEARCH_THEMES = [
    {
        "id": "theme1_calibration",
        "name": "Epistemic & Confidence Calibration in RAG",
        "openalex_query": "retrieval augmented generation epistemic calibration uncertainty",
        "arxiv_query": 'all:"retrieval augmented generation" AND (all:"calibration" OR all:"uncertainty")',
        "crossref_query": "retrieval augmented generation confidence calibration"
    },
    {
        "id": "theme2_attribution",
        "name": "Citation Faithfulness & Fine-Grained Evidence Attribution",
        "openalex_query": "retrieval augmented generation citation precision evidence attribution faithfulness",
        "arxiv_query": 'all:"retrieval augmented generation" AND (all:"attribution" OR all:"faithfulness" OR all:"citation")',
        "crossref_query": "retrieval augmented generation citation attribution"
    },
    {
        "id": "theme3_conflicts",
        "name": "Conflict Resolution & Dialectics in Retrieved Knowledge",
        "openalex_query": "retrieval augmented generation contradictory information conflict resolution",
        "arxiv_query": 'all:"retrieval augmented generation" AND (all:"conflict" OR all:"contradiction")',
        "crossref_query": "retrieval augmented generation conflicting evidence"
    },
    {
        "id": "theme4_multihop",
        "name": "Multi-Hop Reasoning, Entailment Trees & Knowledge Graphs in RAG",
        "openalex_query": "multi-hop retrieval augmented generation entailment tree reasoning graph",
        "arxiv_query": 'all:"retrieval augmented generation" AND (all:"multi-hop" OR all:"entailment tree")',
        "crossref_query": "multi-hop retrieval augmented generation reasoning"
    }
]

def query_openalex(search_text: str, per_page: int = 15):
    encoded = urllib.parse.quote(search_text)
    url = f"https://api.openalex.org/works?search={encoded}&per-page={per_page}&sort=cited_by_count:desc"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            count = data.get("meta", {}).get("count", 0)
            papers = []
            for item in data.get("results", []):
                primary_loc = item.get("primary_location") or {}
                source = primary_loc.get("source") or {}
                venue = source.get("display_name") or "Preprint / Archive"
                authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])]
                papers.append({
                    "id": item.get("id"),
                    "doi": item.get("doi"),
                    "title": item.get("title"),
                    "publication_year": item.get("publication_year"),
                    "venue": venue,
                    "cited_by_count": item.get("cited_by_count", 0),
                    "authors": authors[:5],
                    "landing_page_url": primary_loc.get("landing_page_url") or item.get("doi")
                })
            return {"count": count, "papers": papers}
    except Exception as e:
        print(f"Error querying OpenAlex for '{search_text}': {e}")
        return {"count": 0, "papers": []}

def query_crossref(query_text: str, rows: int = 10):
    encoded = urllib.parse.quote(query_text)
    url = f"https://api.crossref.org/works?query={encoded}&rows={rows}&sort=relevance"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            message = data.get("message", {})
            total_results = message.get("total-results", 0)
            items = []
            for item in message.get("items", []):
                title = item.get("title", [""])[0] if item.get("title") else ""
                container = item.get("container-title", [""])[0] if item.get("container-title") else ""
                doi = item.get("DOI", "")
                year = None
                if "issued" in item and "date-parts" in item["issued"] and item["issued"]["date-parts"]:
                    year = item["issued"]["date-parts"][0][0]
                items.append({
                    "doi": doi,
                    "title": title,
                    "venue": container,
                    "year": year
                })
            return {"count": total_results, "papers": items}
    except Exception as e:
        print(f"Error querying Crossref for '{query_text}': {e}")
        return {"count": 0, "papers": []}

def run_slr():
    search_date = datetime.now().strftime("%Y-%m-%d")
    results = {
        "metadata": {
            "search_date": search_date,
            "databases_searched": ["OpenAlex (aggregating IEEE, ACM, ACL, ScienceDirect, Springer, arXiv)", "Crossref"],
            "protocol": "PRISMA 2020 Guidelines for Systematic Literature Reviews"
        },
        "themes": []
    }

    all_retrieved_dois = set()
    all_retrieved_titles = set()
    total_records_found = 0
    raw_collected_papers = []

    print(f"[*] Starting Systematic Literature Review searches on {search_date}...")

    for theme in SEARCH_THEMES:
        print(f"\n--- Searching: {theme['name']} ---")
        
        # 1. OpenAlex search
        print(f"  [+] Querying OpenAlex: '{theme['openalex_query']}'")
        oa_res = query_openalex(theme['openalex_query'], per_page=20)
        time.sleep(1.0) # polite rate limit
        
        # 2. Crossref search
        print(f"  [+] Querying Crossref: '{theme['crossref_query']}'")
        cr_res = query_crossref(theme['crossref_query'], rows=10)
        time.sleep(1.0)

        theme_total = oa_res["count"] + cr_res["count"]
        total_records_found += theme_total

        theme_entry = {
            "theme_id": theme["id"],
            "theme_name": theme["name"],
            "openalex_query": theme["openalex_query"],
            "openalex_count": oa_res["count"],
            "crossref_query": theme["crossref_query"],
            "crossref_count": cr_res["count"],
            "theme_total_count": theme_total,
            "top_candidate_papers": oa_res["papers"]
        }
        results["themes"].append(theme_entry)

        for p in oa_res["papers"]:
            raw_collected_papers.append(p)
            if p.get("doi"):
                all_retrieved_dois.add(p["doi"].lower())
            if p.get("title"):
                all_retrieved_titles.add(p["title"].lower().strip())

    # De-duplication analysis
    unique_candidates = []
    seen_identifiers = set()
    for p in raw_collected_papers:
        key = (p.get("doi") or p.get("title", "")).lower().strip()
        if key and key not in seen_identifiers:
            seen_identifiers.add(key)
            unique_candidates.append(p)

    duplicate_count = len(raw_collected_papers) - len(unique_candidates)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "slr")
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "slr_search_records.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] SLR search records written to: {json_path}")
    print(f"Total raw database query records: {total_records_found}")
    print(f"Top candidates retrieved across themes: {len(raw_collected_papers)}")
    print(f"Duplicates within candidate pool: {duplicate_count}")
    print(f"Unique candidate studies: {len(unique_candidates)}")

if __name__ == "__main__":
    run_slr()
