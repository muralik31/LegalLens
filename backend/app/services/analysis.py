from __future__ import annotations

import re

from app.schemas import (
    AnalysisResponse,
    Clause,
    ClauseBenchmark,
    LegalTermDefinition,
    RiskHeatmapItem,
    SupportedLanguage,
)
from app.services.llm import llm_provider

RISK_TERMS = {
    "high": ["penalty", "indemnity", "liability", "termination without notice"],
    "medium": ["lock-in", "non-compete", "late fee", "arbitration"],
}

TERM_DICTIONARY = {
    "indemnity": "You may have to cover losses or legal costs for the other side.",
    "liability": "Your legal responsibility if something goes wrong.",
    "arbitration": "A private dispute process instead of court.",
    "termination": "How and when the contract can be ended.",
    "notice period": "Time you must inform the other party before ending the contract.",
    "lock-in": "Minimum period before you can exit the contract.",
}

LANG_LABELS = {
    "en": {
        "summary_prefix": "Plain language summary: ",
        "negotiate_notice": "Ask to explicitly define notice periods for termination.",
        "negotiate_cap": "Negotiate a cap on penalties or liability where possible.",
        "negotiate_clarity": "Request clearer wording for ambiguous obligations before signing.",
    },
    "hi": {
        "summary_prefix": "यह दस्तावेज़ का सरल सारांश है: ",
        "negotiate_notice": "नोटिस अवधि को लिखित रूप में स्पष्ट करने को कहें।",
        "negotiate_cap": "दंड या देयता की अधिकतम सीमा तय करने पर बातचीत करें।",
        "negotiate_clarity": "हस्ताक्षर से पहले अस्पष्ट शर्तों को स्पष्ट कराएं।",
    },
    "te": {
        "summary_prefix": "ఈ పత్రం సరళ సారాంశం: ",
        "negotiate_notice": "రద్దు నోటీసు గడువు స్పష్టంగా రాయాలని అడగండి.",
        "negotiate_cap": "పెనాల్టీ లేదా బాధ్యతకు పరిమితి పెట్టాలని చర్చించండి.",
        "negotiate_clarity": "సంతకం ముందు అస్పష్ట నిబంధనలు క్లియర్ చేయించండి.",
    },
    "ta": {
        "summary_prefix": "இந்த ஆவணத்தின் எளிய சுருக்கம்: ",
        "negotiate_notice": "ரத்து செய்யும் முன் நோட்டீஸ் காலத்தை தெளிவாக குறிப்பிட சொல்லுங்கள்.",
        "negotiate_cap": "அபராதம் அல்லது பொறுப்புக்கு உச்சவரம்பு குறித்து பேச்சுவார்த்தை நடத்துங்கள்.",
        "negotiate_clarity": "கையெழுத்துக்கு முன் குழப்பமான நிபந்தனைகளை தெளிவுபடுத்துங்கள்.",
    },
    "kn": {
        "summary_prefix": "ಈ ದಸ್ತಾವೇಜಿನ ಸರಳ ಸಾರಾಂಶ: ",
        "negotiate_notice": "ರದ್ದುಪಡಿಸುವ ನೋಟಿಸ್ ಅವಧಿಯನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಬರೆಯಲು ಕೇಳಿ.",
        "negotiate_cap": "ದಂಡ ಅಥವಾ ಹೊಣೆಗಾರಿಕೆಗೆ ಗರಿಷ್ಠ ಮಿತಿ ನಿಗದಿ ಕುರಿತು ಮಾತುಕತೆ ಮಾಡಿ.",
        "negotiate_clarity": "ಸಹಿ ಮಾಡುವ ಮೊದಲು ಅಸ್ಪಷ್ಟ ಷರತ್ತುಗಳನ್ನು ಸ್ಪಷ್ಟಪಡಿಸಿ.",
    },
    "mr": {
        "summary_prefix": "या दस्तऐवजाचा सोपा सारांश: ",
        "negotiate_notice": "करार रद्द करण्यापूर्वी नोटीस कालावधी स्पष्ट लिहून घ्यावा.",
        "negotiate_cap": "दंड किंवा जबाबदारीवर मर्यादा ठरवण्याबाबत चर्चा करा.",
        "negotiate_clarity": "स्वाक्षरीपूर्वी अस्पष्ट अटी स्पष्ट करून घ्या.",
    },
}


async def analyze_document(document_id: str, text: str, language: SupportedLanguage) -> AnalysisResponse:
    """Analyze document using LLM if available, otherwise fall back to heuristic analysis."""
    if llm_provider:
        return await _analyze_with_llm(document_id, text, language)
    else:
        return _analyze_heuristic(document_id, text, language)


async def _analyze_with_llm(document_id: str, text: str, language: SupportedLanguage) -> AnalysisResponse:
    """Analyze document using LLM provider."""
    try:
        result = await llm_provider.analyze_document(text, language)

        # Convert LLM response to AnalysisResponse format
        clauses = [
            Clause(
                title=c.get("title", ""),
                details=c.get("details", ""),
                risk_level=c.get("risk_level", "low"),
            )
            for c in result.get("key_clauses", [])
        ]

        return AnalysisResponse(
            document_id=document_id,
            document_type=result.get("document_type", "general_contract"),
            summary=result.get("summary", ""),
            key_clauses=clauses,
            financial_obligations=result.get("financial_obligations", []),
            risk_alerts=result.get("risk_alerts", []),
            negotiation_points=result.get("negotiation_points", []),
            contract_risk_score=result.get("contract_risk_score", 5),
            risk_heatmap=_build_risk_heatmap(clauses),
            clause_comparisons=_build_clause_comparisons(clauses),
            legal_terms_dictionary=_build_legal_dictionary(text.lower()),
            language=language,
        )
    except Exception:
        # Fall back to heuristic if LLM fails
        return _analyze_heuristic(document_id, text, language)


def _analyze_heuristic(document_id: str, text: str, language: SupportedLanguage) -> AnalysisResponse:
    """Heuristic analysis (original implementation)."""
    lowered = text.lower()

    high_hits = _count_hits(lowered, RISK_TERMS["high"])
    medium_hits = _count_hits(lowered, RISK_TERMS["medium"])
    risk_score = min(10, 3 + high_hits * 2 + medium_hits)

    clauses = _extract_clauses(text)
    financial = _extract_financial_obligations(text)
    alerts = _build_alerts(high_hits, medium_hits, text)
    summary = LANG_LABELS[language]["summary_prefix"] + _first_sentences(text, 2)

    return AnalysisResponse(
        document_id=document_id,
        document_type=_detect_document_type(lowered),
        summary=summary,
        key_clauses=clauses,
        financial_obligations=financial,
        risk_alerts=alerts,
        negotiation_points=_negotiation_points(alerts, language),
        contract_risk_score=risk_score,
        risk_heatmap=_build_risk_heatmap(clauses),
        clause_comparisons=_build_clause_comparisons(clauses),
        legal_terms_dictionary=_build_legal_dictionary(lowered),
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
    selected = lines[:6]
    clauses: list[Clause] = []

    for line in selected:
        lowered = line.lower()
        risk = "low"
        if any(term in lowered for term in RISK_TERMS["high"]):
            risk = "high"
        elif any(term in lowered for term in RISK_TERMS["medium"]):
            risk = "medium"

        title = line[:60] + ("..." if len(line) > 60 else "")
        clauses.append(Clause(title=title, details=line[:220], risk_level=risk))

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
    return alerts or ["No major red flags detected in heuristic scan."]


def _negotiation_points(alerts: list[str], language: SupportedLanguage) -> list[str]:
    base = [
        LANG_LABELS[language]["negotiate_notice"],
        LANG_LABELS[language]["negotiate_cap"],
    ]
    if alerts and "No major" in alerts[0]:
        base.append(LANG_LABELS[language]["negotiate_clarity"])
    return base


def _build_risk_heatmap(clauses: list[Clause]) -> list[RiskHeatmapItem]:
    return [RiskHeatmapItem(clause_title=item.title, risk_level=item.risk_level) for item in clauses]


def _build_clause_comparisons(clauses: list[Clause]) -> list[ClauseBenchmark]:
    comparisons: list[ClauseBenchmark] = []
    for clause in clauses[:4]:
        standard = "Clearly bounded rights/obligations with time limits"
        assessment = "neutral"
        if clause.risk_level == "high":
            assessment = "needs_attention"
        elif clause.risk_level == "low":
            assessment = "favorable"

        comparisons.append(
            ClauseBenchmark(
                clause_title=clause.title,
                market_standard=standard,
                document_value=clause.details,
                assessment=assessment,
            )
        )
    return comparisons


def _build_legal_dictionary(lowered_text: str) -> list[LegalTermDefinition]:
    found: list[LegalTermDefinition] = []
    for term, meaning in TERM_DICTIONARY.items():
        if term in lowered_text:
            found.append(LegalTermDefinition(term=term, plain_explanation=meaning))
    return found[:6]
