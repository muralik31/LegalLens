from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SupportedLanguage = Literal["en", "hi"]


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    uploaded_at: datetime
    extracted_characters: int


class AnalyzeRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    language: SupportedLanguage = "en"


class Clause(BaseModel):
    title: str
    details: str
    risk_level: Literal["low", "medium", "high"]


class AnalysisResponse(BaseModel):
    document_id: str
    document_type: str
    summary: str
    key_clauses: list[Clause]
    financial_obligations: list[str]
    risk_alerts: list[str]
    negotiation_points: list[str]
    contract_risk_score: int = Field(..., ge=1, le=10)
    language: SupportedLanguage


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    content_type: str
    uploaded_at: datetime
    extracted_text: str
    analysis: AnalysisResponse | None = None


class AskQuestionRequest(BaseModel):
    document_id: str
    question: str = Field(..., min_length=2)
    language: SupportedLanguage = "en"


class AskQuestionResponse(BaseModel):
    document_id: str
    answer: str
    language: SupportedLanguage
