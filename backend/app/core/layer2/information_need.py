"""
Sub-Module 2.1: Information Need Analyzer
Research Basis: Analyze, Generate and Refine (AGR) - ACL 2024
Diagnoses the exact informational deficit before query decomposition and expansion:
1. Isolates known anchors (stated premises, entities, models).
2. Isolates unknown targets (quantities, architectures, comparisons, mechanisms).
3. Extracts evaluation criteria (benchmarks, latency, accuracy, FLOPs).
4. Determines target technical domains and complexity.
"""

import re
from typing import List, Dict, Any
from app.schemas.layer1 import StructuredUserInput, IntentCategory, QueryTypeCategory
from app.schemas.layer2 import InformationNeedProfile
from app.core.llm_client import LLMClient


class InformationNeedAnalyzer:
    """Diagnoses information deficits from Layer 1 structured input."""

    METRIC_KEYWORDS = [
        "latency", "throughput", "vram", "memory", "accuracy", "perplexity",
        "speed", "flops", "cost", "benchmark", "mmu", "gsm8k", "tokens/sec",
        "parameters", "quantization", "efficiency", "context length", "loss"
    ]

    DOMAIN_TAXONOMY = {
        "Machine Learning / AI": ["llm", "transformer", "attention", "fine-tuning", "rag", "lora", "diffusion", "deepseek", "llama", "gpt"],
        "Computer Systems / Hardware": ["gpu", "cuda", "vram", "cpu", "tpu", "cache", "latency", "fp8", "int4", "fp16", "bandwidth"],
        "Data Engineering / Retrieval": ["vector database", "faiss", "bm25", "embeddings", "indexing", "chunking", "sql", "postgres"],
        "Software Architecture": ["microservices", "api", "docker", "pipeline", "concurrency", "distributed", "rest"],
        "Biomedical / Science": ["protein", "gene", "variant", "clinical", "molecular", "dna", "rna", "alphafold"]
    }

    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    def analyze(self, user_input: StructuredUserInput) -> InformationNeedProfile:
        """Run instant information deficit analysis using deterministic AGR analysis (<1ms)."""
        return self._analyze_deterministic(user_input)

    def _analyze_with_llm(self, user_input: StructuredUserInput) -> InformationNeedProfile | None:
        system_prompt = (
            "You are an expert Research Information Need Analyzer (AGR framework, ACL 2024).\n"
            "Given a user query and its detected entities, diagnose the knowledge deficit.\n"
            "Return a JSON object with:\n"
            "- 'known_anchors': list of known entities or assumptions provided in the query\n"
            "- 'unknown_targets': list of specific factual/mechanistic things the user wants to know\n"
            "- 'evaluation_criteria': list of metrics, benchmarks, or comparison angles\n"
            "- 'target_domains': list of academic or technical domains\n"
            "- 'complexity_level': 'LOW', 'MODERATE', or 'HIGH'"
        )
        user_prompt = (
            f"Query: {user_input.resolved_query}\n"
            f"Entities: {user_input.entities}\n"
            f"Intent: {user_input.intent.value}\n"
            f"Query Type: {user_input.query_type.value}\n"
            f"Constraints: {user_input.constraints}"
        )
        
        result = self.llm_client.generate_structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema_name="information_need_profile"
        )
        if result and isinstance(result, dict) and "unknown_targets" in result:
            try:
                return InformationNeedProfile(
                    known_anchors=result.get("known_anchors", user_input.entities),
                    unknown_targets=result.get("unknown_targets", []),
                    evaluation_criteria=result.get("evaluation_criteria", []),
                    target_domains=result.get("target_domains", ["General AI"]),
                    complexity_level=result.get("complexity_level", "MODERATE")
                )
            except Exception:
                return None
        return None

    def _analyze_deterministic(self, user_input: StructuredUserInput) -> InformationNeedProfile:
        query_lower = user_input.resolved_query.lower()
        
        # Known anchors: entities from Layer 1
        known_anchors = list(user_input.entities) if user_input.entities else []
        if not known_anchors:
            # Fallback noun-chunk heuristics
            words = [w for w in re.findall(r"\b[A-Za-z0-9\-_]{3,}\b", user_input.resolved_query) 
                     if w.lower() not in {"what", "how", "why", "when", "where", "which", "compare", "difference", "between", "does"}]
            known_anchors = words[:3]

        # Evaluation criteria extraction
        criteria = []
        for kw in self.METRIC_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                criteria.append(kw)

        # Unknown targets: formulate what information is missing based on intent
        unknown_targets = []
        if user_input.intent == IntentCategory.COMPARATIVE:
            if len(known_anchors) >= 2:
                unknown_targets.append(f"Comparative trade-offs between {known_anchors[0]} and {known_anchors[1]}")
            else:
                unknown_targets.append("Performance and architectural trade-offs across comparison targets")
        elif user_input.intent == IntentCategory.PROCEDURAL:
            unknown_targets.append(f"Step-by-step procedure and technical prerequisites for {user_input.resolved_query}")
        elif user_input.intent == IntentCategory.FACTUAL:
            target = criteria[0] if criteria else "factual value or description"
            unknown_targets.append(f"Empirical or definitive {target} for {', '.join(known_anchors) if known_anchors else 'query'}")
        else:
            unknown_targets.append(f"Comprehensive analysis and evidence for: {user_input.resolved_query}")

        # Domain categorization
        domains = []
        for domain, keywords in self.DOMAIN_TAXONOMY.items():
            if any(re.search(r"\b" + re.escape(k) + r"\b", query_lower) for k in keywords):
                domains.append(domain)
        if not domains:
            domains.append("Computer Science / General AI")

        # Complexity estimation
        if user_input.query_type == QueryTypeCategory.SINGLE_HOP:
            complexity = "LOW"
        elif user_input.query_type == QueryTypeCategory.MULTI_HOP or len(known_anchors) > 2:
            complexity = "HIGH"
        else:
            complexity = "MODERATE"

        return InformationNeedProfile(
            known_anchors=known_anchors,
            unknown_targets=unknown_targets,
            evaluation_criteria=criteria,
            target_domains=domains,
            complexity_level=complexity
        )
