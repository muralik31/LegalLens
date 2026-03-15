# Phase 2 Backend (FastAPI)

Implements the Phase 2 scope from `ai_legal_document_explainer_architecture.md`:

- `/upload` for document upload + text extraction
- `/analyze` for summary, key clauses, risk score, risk alerts
- `/ask-question` for single-turn Q&A
- `/chat` for lightweight interactive contract chat (message-list input)
- `/document/{id}` to fetch stored analysis
- `/disclaimer` for mandatory legal disclaimer text

## Phase 2 Additions

- Expanded language support: English (`en`), Hindi (`hi`), Telugu (`te`), Tamil (`ta`), Kannada (`kn`), Marathi (`mr`)
- Analysis now includes:
  - `risk_heatmap`
  - `clause_comparisons` (against generic market-standard framing)
  - `legal_terms_dictionary`
- Deterministic, local implementation without external LLM dependencies

## Current Constraints

- In-memory document store (non-persistent)
- 10MB upload size limit
- Supported input types: `text/plain`, `application/pdf`, DOCX, JPEG, PNG

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
