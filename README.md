# Cogent: Epistemic & Multi-Source Research Engine

Cogent is an enterprise-grade, calibrated epistemic research and reasoning architecture. It leverages a rigorous **10-Layer Pipeline** to decompose complex inquiries, cross-reference local document corpora and live web scientific literature, evaluate contradictions without winner-forcing, and present mathematically bounded epistemic confidence.

---

## 🌟 Key Architecture Capabilities

- **10-Layer Epistemic Pipeline**:
  1. **Layer 1 (Query Understanding)**: Ambiguity detection, scope classification, entity resolution.
  2. **Layer 2 (Retrieval Planning)**: Dynamic query topological expansion & target routing.
  3. **Layer 3 (Acquisition)**: Multi-format document parser (PDF, TXT, MD) with cryptographic hashing.
  4. **Layer 4 (Retrieval)**: Hybrid search combining dense neural vector embeddings (FAISS) with sparse BM25 and Reciprocal Rank Fusion (RRF).
  5. **Layer 5 (Evidence Verification)**: NLI entailment auditing and verbatim span grounding.
  6. **Layer 6 (Contradiction & Dialectic)**: Disagreement identification preserving empirical variance.
  7. **Layer 7 (Multi-Hop Deduction)**: Direct acyclic graph (DAG) reasoning with weakest-link sensitivity.
  8. **Layer 8 (Epistemic Calibration)**: Multi-dimensional Global Trust Index (GTI) computation.
  9. **Layer 9 (Multi-Fidelity Packaging)**: Interactive citation badges, BLUF summaries, and progressive drawers.
  10. **Layer 10 (Evaluation & Quality)**: Continuous attribution calibration and safety feedback.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (with `pgvector`) or Docker

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
