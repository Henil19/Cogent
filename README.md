# Cogent: Epistemic & Multi-Source Research Engine

Cogent is an enterprise-grade, calibrated epistemic research and reasoning architecture. It leverages a rigorous **10-Layer Pipeline** to decompose complex inquiries, cross-reference local document corpora and live web scientific literature, evaluate contradictions without winner-forcing, and present mathematically bounded epistemic confidence.

---

## 🌟 Key Architecture Capabilities

- **10-Layer Epistemic Pipeline**:
  1. **Layer 1 — User Interaction**: Intent classification, ambiguity detection, entity resolution, session management.
  2. **Layer 2 — Query Understanding & Planning**: Sub-query decomposition, dense phrasings, sparse keywords, source routing.
  3. **Layer 3 — Knowledge Acquisition**: Multi-format document parser (PDF, TXT, MD) with cryptographic provenance hashing; live web acquisition via Tavily + arXiv.
  4. **Layer 4 — Hybrid Knowledge Retrieval**: Dense neural embeddings (all-MiniLM-L6-v2, 384-dim, FAISS IndexFlatIP) fused with sparse BM25 via Reciprocal Rank Fusion (RRF, k=60).
  5. **Layer 5 — Evidence Intelligence**: Cross-encoder reranking (ms-marco-MiniLM-L-6-v2), NLI entailment grounding, deduplication, conflict graph construction, coverage selection.
  6. **Layer 6 — Transparent Reasoning & Synthesis**: LLM-assisted evidence-to-claim chaining, multi-hop DAG inference, dialectical conflict reconciliation, comparative analysis, epistemic gap evaluation.
  7. **Layer 7 — Trust Intelligence**: Statistical source credibility, evidence reliability, reasoning-chain trust, uncertainty quantification, confidence calibration, hallucination risk detection. Global Trust Index (GTI) computation. No LLM dependency.
  8. **Layer 8 — Explainability & Attribution**: Rule-based claim attribution, DAG-to-narrative translation, citation mapping, counterfactual sensitivity analysis, multi-fidelity audience adaptation (executive, researcher, layperson, domain-expert). No LLM dependency.
  9. **Layer 9 — Response Generation & Presentation**: LLM-synthesized BLUF summaries and evidence narratives; citation badge rendering; trust badge presentation; safety validation; graceful epistemic abstention fallback.
  10. **Layer 10 — Analytics & Learning**: Continuous attribution calibration, telemetry logging, quality feedback.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ or Docker (used for relational data: users, sessions, documents, chunks)

### Running Locally

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env  # Configure your database and API keys
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Running with Docker Compose
```bash
docker-compose up --build
```

---

## 🧪 Testing

```bash
cd backend
pytest -v
```

---

## 📄 License
Apache-2.0
