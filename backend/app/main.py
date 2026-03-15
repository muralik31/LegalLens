from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    AskQuestionRequest,
    AskQuestionResponse,
    ChatRequest,
    ChatResponse,
    DocumentRecord,
    UploadResponse,
)
from app.services.analysis import analyze_document
from app.services.document_processing import UnsupportedFileTypeError, extract_text
from app.services.qa import answer_question, build_chat_reply
from app.store import store

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
DISCLAIMER = "This AI analysis is for informational purposes only and not legal advice."

app = FastAPI(title="AI Legal Document Explainer - Phase 2")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "phase": "2"}


@app.get("/disclaimer")
def get_disclaimer() -> dict[str, str]:
    return {"disclaimer": DISCLAIMER}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    content_type = file.content_type or "application/octet-stream"

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10MB upload limit")

    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=Path(file.filename or "upload.bin").suffix) as temp:
            temp.write(payload)
            temp_path = Path(temp.name)

        text = extract_text(temp_path, content_type)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Could not decode uploaded text file") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {exc}") from exc
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

    document_id = str(uuid4())
    record = DocumentRecord(
        document_id=document_id,
        filename=file.filename or "unknown",
        content_type=content_type,
        uploaded_at=datetime.now(timezone.utc),
        extracted_text=text,
    )
    store.save(record)

    return UploadResponse(
        document_id=document_id,
        filename=record.filename,
        content_type=record.content_type,
        uploaded_at=record.uploaded_at,
        extracted_characters=len(record.extracted_text),
    )


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalyzeRequest) -> AnalysisResponse:
    record = store.get(request.document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    if not record.extracted_text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in document")

    result = analyze_document(record.document_id, record.extracted_text, request.language)
    record.analysis = result
    store.save(record)
    return result


@app.get("/document/{document_id}", response_model=DocumentRecord)
def get_document(document_id: str) -> DocumentRecord:
    record = store.get(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return record


@app.post("/ask-question", response_model=AskQuestionResponse)
def ask_question(request: AskQuestionRequest) -> AskQuestionResponse:
    record = store.get(request.document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    return AskQuestionResponse(
        document_id=request.document_id,
        answer=answer_question(record.extracted_text, request.question, request.language),
        language=request.language,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    record = store.get(request.document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    return ChatResponse(
        document_id=request.document_id,
        reply=build_chat_reply(record.extracted_text, request.messages, request.language),
        language=request.language,
    )
