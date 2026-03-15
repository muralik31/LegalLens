from __future__ import annotations

import re

from app.schemas import SupportedLanguage
from app.services.llm import llm_provider

CHAT_PREFIX = {
    "en": "Relevant information from the document: ",
    "hi": "दस्तावेज़ में संबंधित जानकारी: ",
    "te": "పత్రంలో సంబంధించిన సమాచారం: ",
    "ta": "ஆவணத்தில் தொடர்புடைய தகவல்: ",
    "kn": "ದಸ್ತಾವೇಜಿನಲ್ಲಿ ಸಂಬಂಧಿತ ಮಾಹಿತಿ: ",
    "mr": "दस्तऐवजातील संबंधित माहिती: ",
}


async def answer_question(text: str, question: str, language: SupportedLanguage) -> str:
    """Answer a question about the document using LLM if available."""
    if llm_provider:
        try:
            return await llm_provider.answer_question(text, question, language)
        except Exception:
            # Fall back to heuristic
            pass

    # Heuristic fallback
    snippet = _most_relevant_sentence(text, question)
    return f"{CHAT_PREFIX[language]}{snippet}"


async def build_chat_reply(text: str, messages: list[str], language: SupportedLanguage) -> str:
    """Build a chat reply based on message history."""
    latest = messages[-1]
    answer = await answer_question(text, latest, language)
    return answer


def _most_relevant_sentence(text: str, question: str) -> str:
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+", text) if segment.strip()]
    if not sentences:
        return "No extractable content found in the document."

    keywords = [token for token in re.findall(r"[a-zA-Z]+", question.lower()) if len(token) > 2]
    if not keywords:
        return sentences[0][:400]

    ranked = sorted(
        sentences,
        key=lambda sentence: sum(1 for token in keywords if token in sentence.lower()),
        reverse=True,
    )
    best = ranked[0]
    return best[:400]
