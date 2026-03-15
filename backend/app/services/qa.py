from __future__ import annotations

import re

from app.schemas import SupportedLanguage


def answer_question(text: str, question: str, language: SupportedLanguage) -> str:
    snippet = _most_relevant_sentence(text, question)
    if language == "hi":
        return f"दस्तावेज़ में संबंधित जानकारी: {snippet}"
    return f"Relevant information from the document: {snippet}"


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
