from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


SupportedLanguage = Literal["en", "hi", "te", "ta", "kn", "mr"]


# ============= Authentication Schemas =============


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    subscription_tier: str
    documents_analyzed: int
    is_active: bool
    created_at: datetime


# ============= Document Schemas =============


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


class ClauseBenchmark(BaseModel):
    clause_title: str
    market_standard: str
    document_value: str
    assessment: Literal["favorable", "neutral", "needs_attention"]


class RiskHeatmapItem(BaseModel):
    clause_title: str
    risk_level: Literal["low", "medium", "high"]


class LegalTermDefinition(BaseModel):
    term: str
    plain_explanation: str


class AnalysisResponse(BaseModel):
    document_id: str
    document_type: str
    summary: str
    key_clauses: list[Clause]
    financial_obligations: list[str]
    risk_alerts: list[str]
    negotiation_points: list[str]
    contract_risk_score: int = Field(..., ge=1, le=10)
    risk_heatmap: list[RiskHeatmapItem]
    clause_comparisons: list[ClauseBenchmark]
    legal_terms_dictionary: list[LegalTermDefinition]
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


class ChatRequest(BaseModel):
    document_id: str
    messages: list[str] = Field(..., min_length=1)
    language: SupportedLanguage = "en"


class ChatResponse(BaseModel):
    document_id: str
    reply: str
    language: SupportedLanguage
