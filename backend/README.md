# Phase 1 Backend (FastAPI)

Implements the Phase 1 MVP from `ai_legal_document_explainer_architecture.md`:

- `/upload` for document upload + text extraction
- `/analyze` for summary, key clauses, risk score, risk alerts
- `/document/{id}` to fetch stored analysis
- `/ask-question` simple keyword-aware document Q&A scaffold
- Language support: English (`en`) and Hindi (`hi`)

## Current Phase 1 constraints

- In-memory document store (non-persistent)
- 10MB upload size limit
- Supported input types: `text/plain`, `application/pdf`, DOCX, JPEG, PNG
- Deterministic heuristic analysis (no external LLM requirement)

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
cd backend
PYTHONPATH=. pytest
```
