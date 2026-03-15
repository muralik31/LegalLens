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
    DocumentRecord,
    UploadResponse,
)
from app.services.analysis import analyze_document
from app.services.document_processing import UnsupportedFileTypeError, extract_text

app = FastAPI(title="AI Legal Document Explainer - Phase 1")

DOCUMENT_STORE: dict[str, DocumentRecord] = {}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    content_type = file.content_type or "application/octet-stream"

    with NamedTemporaryFile(delete=False, suffix=Path(file.filename or "upload.bin").suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)

    try:
        text = extract_text(temp_path, content_type)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    document_id = str(uuid4())
    record = DocumentRecord(
        document_id=document_id,
        filename=file.filename or "unknown",
        content_type=content_type,
        uploaded_at=datetime.now(timezone.utc),
        extracted_text=text,
    )
    DOCUMENT_STORE[document_id] = record

    return UploadResponse(
        document_id=document_id,
        filename=record.filename,
        content_type=record.content_type,
        uploaded_at=record.uploaded_at,
        extracted_characters=len(record.extracted_text),
    )


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalyzeRequest) -> AnalysisResponse:
    record = DOCUMENT_STORE.get(request.document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    result = analyze_document(record.document_id, record.extracted_text, request.language)
    record.analysis = result
    return result


@app.get("/document/{document_id}", response_model=DocumentRecord)
def get_document(document_id: str) -> DocumentRecord:
    record = DOCUMENT_STORE.get(document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return record


@app.post("/ask-question", response_model=AskQuestionResponse)
def ask_question(request: AskQuestionRequest) -> AskQuestionResponse:
    record = DOCUMENT_STORE.get(request.document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    context = record.extracted_text[:400]
    if request.language == "hi":
        answer = f"दस्तावेज़ के आधार पर: {context}"
    else:
        answer = f"Based on the uploaded document: {context}"

    return AskQuestionResponse(
        document_id=request.document_id,
        answer=answer,
        language=request.language,
    )
