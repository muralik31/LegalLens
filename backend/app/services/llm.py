from __future__ import annotations

from abc import ABC, abstractmethod

import anthropic
import openai

from app.config import settings
from app.schemas import SupportedLanguage

ANALYSIS_SYSTEM_PROMPT = """You are a legal document analyzer helping people understand complex legal contracts.
Analyze the provided legal document and return a structured analysis in the specified language.

Focus on:
1. Document type identification
2. Plain language summary
3. Key clauses with risk assessment
4. Financial obligations
5. Risk alerts and red flags
6. Negotiation suggestions
7. Overall risk score (1-10)

Be clear, accurate, and helpful. Use plain language appropriate for non-lawyers."""

ANALYSIS_PROMPT_TEMPLATE = """Analyze this legal document and provide a comprehensive analysis in {language}.

Document text:
{document_text}

Return your analysis as a JSON object with these fields:
- document_type: string (e.g., "rental_agreement", "employment_contract", "service_agreement")
- summary: string (2-3 sentences in plain language)
- key_clauses: array of objects with {{"title": string, "details": string, "risk_level": "low"|"medium"|"high"}}
- financial_obligations: array of strings (monetary amounts found)
- risk_alerts: array of strings (red flags or concerning clauses)
- negotiation_points: array of strings (suggestions for negotiation)
- contract_risk_score: integer (1-10, where 10 is highest risk)

Language codes: en=English, hi=Hindi, te=Telugu, ta=Tamil, kn=Kannada, mr=Marathi"""

QA_SYSTEM_PROMPT = """You are a helpful legal assistant. Answer questions about legal documents clearly and concisely.
Base your answers only on the provided document text. If the answer isn't in the document, say so."""

QA_PROMPT_TEMPLATE = """Document context:
{document_text}

User question: {question}

Provide a clear, accurate answer in {language}. Keep it concise (2-3 sentences)."""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def analyze_document(
        self, document_text: str, language: SupportedLanguage
    ) -> dict:
        """Analyze a legal document and return structured results."""
        pass

    @abstractmethod
    async def answer_question(
        self, document_text: str, question: str, language: SupportedLanguage
    ) -> str:
        """Answer a question about a document."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def analyze_document(
        self, document_text: str, language: SupportedLanguage
    ) -> dict:
        """Analyze document using OpenAI."""
        # Truncate document if too long
        max_chars = 15000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "...[truncated]"

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            language=language, document_text=document_text
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )

        # Parse JSON response
        import json

        result = json.loads(response.choices[0].message.content or "{}")
        return result

    async def answer_question(
        self, document_text: str, question: str, language: SupportedLanguage
    ) -> str:
        """Answer question using OpenAI."""
        # Truncate document if too long
        max_chars = 10000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "...[truncated]"

        prompt = QA_PROMPT_TEMPLATE.format(
            document_text=document_text, question=question, language=language
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=500,
        )

        return response.choices[0].message.content or "Unable to answer."


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def analyze_document(
        self, document_text: str, language: SupportedLanguage
    ) -> dict:
        """Analyze document using Claude."""
        # Truncate document if too long
        max_chars = 15000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "...[truncated]"

        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            language=language, document_text=document_text
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON response
        import json

        content = response.content[0].text
        result = json.loads(content)
        return result

    async def answer_question(
        self, document_text: str, question: str, language: SupportedLanguage
    ) -> str:
        """Answer question using Claude."""
        # Truncate document if too long
        max_chars = 10000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "...[truncated]"

        prompt = QA_PROMPT_TEMPLATE.format(
            document_text=document_text, question=question, language=language
        )

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=settings.LLM_TEMPERATURE,
            system=QA_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text


def get_llm_provider() -> LLMProvider | None:
    """Factory function to get the configured LLM provider."""
    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
    elif settings.LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
        return AnthropicProvider(settings.ANTHROPIC_API_KEY, settings.ANTHROPIC_MODEL)
    else:
        # Return None for local/heuristic mode
        return None


# Global LLM instance
llm_provider = get_llm_provider()
