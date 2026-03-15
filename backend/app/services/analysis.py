from __future__ import annotations

import re

from app.schemas import AnalysisResponse, Clause, SupportedLanguage

RISK_TERMS = {
    "high": ["penalty", "indemnity", "liability", "termination without notice"],
    "medium": ["lock-in", "non-compete", "late fee", "arbitration"],
}


def analyze_document(document_id: str, text: str, language: SupportedLanguage) -> AnalysisResponse:
    lowered = text.lower()

    high_hits = _count_hits(lowered, RISK_TERMS["high"])
    medium_hits = _count_hits(lowered, RISK_TERMS["medium"])
    risk_score = min(10, 3 + high_hits * 2 + medium_hits)

    clauses = _extract_clauses(text)
    financial = _extract_financial_obligations(text)
    alerts = _build_alerts(high_hits, medium_hits, text)

    if language == "hi":
        summary = "यह दस्तावेज़ का सरल सारांश है: " + _first_sentences(text, 2)
    else:
        summary = "Plain language summary: " + _first_sentences(text, 2)

    return AnalysisResponse(
        document_id=document_id,
        document_type=_detect_document_type(lowered),
        summary=summary,
        key_clauses=clauses,
        financial_obligations=financial,
        risk_alerts=alerts,
        negotiation_points=_negotiation_points(alerts, language),
        contract_risk_score=risk_score,
        language=language,
    )


def _detect_document_type(text: str) -> str:
    if "rent" in text or "landlord" in text or "tenant" in text:
        return "rental_agreement"
    if "employment" in text or "employee" in text:
        return "employment_contract"
    if "service" in text and "provider" in text:
        return "service_agreement"
    return "general_contract"


def _first_sentences(text: str, limit: int) -> str:
    parts = [segment.strip() for segment in re.split(r"[.!?]", text) if segment.strip()]
    return ". ".join(parts[:limit])[:600]


def _count_hits(text: str, terms: list[str]) -> int:
    return sum(text.count(term) for term in terms)


def _extract_clauses(text: str) -> list[Clause]:
    lines = [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
    selected = lines[:5]
    clauses: list[Clause] = []

    for line in selected:
        lowered = line.lower()
        risk = "low"
        if any(term in lowered for term in RISK_TERMS["high"]):
            risk = "high"
        elif any(term in lowered for term in RISK_TERMS["medium"]):
            risk = "medium"

        title = line[:60] + ("..." if len(line) > 60 else "")
        clauses.append(Clause(title=title, details=line[:200], risk_level=risk))

    if not clauses:
        clauses.append(
            Clause(
                title="No explicit clauses extracted",
                details="Upload a clearer or text-rich document for better extraction.",
                risk_level="low",
            )
        )

    return clauses


def _extract_financial_obligations(text: str) -> list[str]:
    matches = re.findall(r"(?:₹|rs\.?|inr|\$)\s?[\d,]+", text.lower())
    obligations = [m.upper().replace("RS", "Rs") for m in matches[:5]]
    return obligations or ["No explicit monetary obligations found"]


def _build_alerts(high_hits: int, medium_hits: int, text: str) -> list[str]:
    alerts: list[str] = []
    if high_hits:
        alerts.append("High-risk legal terms detected (penalty/liability/indemnity).")
    if medium_hits:
        alerts.append("Moderate-risk terms detected (lock-in/non-compete/arbitration).")
    if "termination" in text.lower() and "notice" not in text.lower():
        alerts.append("Termination clause may not specify a clear notice period.")
    return alerts or ["No major red flags detected in Phase 1 heuristic scan."]


def _negotiation_points(alerts: list[str], language: SupportedLanguage) -> list[str]:
    if language == "hi":
        return [
            "नोटिस अवधि लिखित रूप में स्पष्ट कराने को कहें।",
            "दंड/जुर्माने की सीमा तय करने पर बातचीत करें।",
        ]
    base = [
        "Ask to explicitly define notice periods for termination.",
        "Negotiate a cap on penalties or liability where possible.",
    ]
    if alerts and "No major" in alerts[0]:
        base.append("Request clearer wording for ambiguous obligations before signing.")
    return base
