"""
Sub-Module 2.4: Structured Multi-Representation Query Expander
Research Basis:
- MuGI (EMNLP 2024): Dual-channel sparse (BM25) and dense pseudo-reference expansion
- DeCoR (CIKM 2025/2026): Structured query expansion via explicit reasoning steps
- Knowledge-Aware QE (NAACL 2025): Relational triples and structural entity predicates
"""

import re
from typing import List, Dict, Any
from app.schemas.layer2 import SubQueryPlan
from app.core.llm_client import LLMClient


class MultiRepresentationExpander:
    """Expands sub-queries into sparse BM25 keywords, dense phrasings, and relational triples."""

    # Curated technical acronym dictionary (DeCoR / Knowledge-Aware grounding)
    ACRONYM_MAP = {
        "mla": "Multi-Head Latent Attention",
        "mha": "Multi-Head Attention",
        "gqa": "Grouped Query Attention",
        "moe": "Mixture of Experts",
        "rag": "Retrieval-Augmented Generation",
        "lora": "Low-Rank Adaptation",
        "qlora": "Quantized Low-Rank Adaptation",
        "kv": "Key-Value cache",
        "fp8": "8-bit Floating Point format",
        "int4": "4-bit Integer quantization",
        "vram": "Video Random Access Memory",
        "tpu": "Tensor Processing Unit",
        "gpu": "Graphics Processing Unit",
        "mrr": "Mean Reciprocal Rank",
        "ndcg": "Normalized Discounted Cumulative Gain",
        "cot": "Chain of Thought",
        "rlhf": "Reinforcement Learning from Human Feedback",
        "dpo": "Direct Preference Optimization",
        "grpo": "Group Relative Policy Optimization"
    }

    # Relational predicate templates
    PREDICATE_MAP = {
        "compare": "differs_from",
        "vs": "contrasted_with",
        "architecture": "architecturally_defined_by",
        "latency": "measured_by_latency",
        "throughput": "measured_by_throughput",
        "vram": "requires_memory",
        "quantization": "quantized_via",
        "benchmark": "evaluated_on_benchmark",
        "performance": "achieves_performance_score"
    }

    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    def expand(self, subquery: SubQueryPlan) -> SubQueryPlan:
        """Enrich a SubQueryPlan with sparse, dense, and relational representations."""
        self._expand_deterministic(subquery)
        return subquery

    def _expand_with_llm(self, subquery: SubQueryPlan) -> Dict[str, Any] | None:
        system_prompt = (
            "You are an expert Information Retrieval Query Expander (MuGI EMNLP 2024, DeCoR CIKM 2025).\n"
            "Given a sub-query, generate 3 structured representations:\n"
            "1. 'sparse_keywords': list of 4-8 exact search keywords, acronyms, and technical terms for BM25\n"
            "2. 'dense_phrasings': list of 2-3 natural language sentence variants for semantic vector search\n"
            "3. 'relational_predicates': list of 1-3 entity-relation-object triples, e.g. '(DeepSeek-V3, utilizes, Multi-Head Latent Attention)'\n"
            "Keep expansions strictly factual without hallucination."
        )
        user_prompt = (
            f"Sub-Query: {subquery.raw_sub_query}\n"
            f"Description: {subquery.description}\n"
            f"Expected Output: {subquery.expected_output_type.value}"
        )

        result = self.llm_client.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema_name="query_expansion"
        )
        if result and isinstance(result, dict) and "sparse_keywords" in result:
            return result
        return None

    def _expand_deterministic(self, subquery: SubQueryPlan):
        text = subquery.raw_sub_query
        words = re.findall(r"\b[A-Za-z0-9\-_]{2,}\b", text)
        stop_words = {"what", "are", "the", "and", "for", "with", "how", "why", "does", "from", "between", "which", "about", "that", "this"}
        
        # 1. Sparse keywords
        sparse = set()
        for w in words:
            w_lower = w.lower()
            if w_lower not in stop_words and len(w_lower) > 2:
                sparse.add(w)
                # Acronym expansion (DeCoR)
                if w_lower in self.ACRONYM_MAP:
                    sparse.add(f'"{self.ACRONYM_MAP[w_lower]}"')

        subquery.sparse_keywords = sorted(list(sparse))[:8]

        # 2. Dense semantic phrasings (MuGI)
        clean_prompt = text.rstrip("?").strip()
        phrasings = [
            text,
            f"Comprehensive technical analysis and empirical metrics for {clean_prompt}",
            f"Architectural implementation details and benchmark findings on {clean_prompt}"
        ]
        subquery.dense_phrasings = phrasings

        # 3. Relational predicates (Knowledge-Aware QE)
        relations = []
        words_lower = [w.lower() for w in words]
        entities_found = [w for w in words if w.isupper() or (len(w) > 3 and w[0].isupper())]
        
        rel_verb = "associated_with"
        for kw, verb in self.PREDICATE_MAP.items():
            if kw in words_lower:
                rel_verb = verb
                break

        if len(entities_found) >= 2:
            relations.append(f"({entities_found[0]}, {rel_verb}, {entities_found[1]})")
        elif len(entities_found) == 1:
            relations.append(f"({entities_found[0]}, {rel_verb}, {subquery.expected_output_type.value})")
        else:
            relations.append(f"(QuerySubject, {rel_verb}, {subquery.expected_output_type.value})")

        subquery.relational_predicates = relations
