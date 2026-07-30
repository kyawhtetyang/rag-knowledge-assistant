from __future__ import annotations

import re

import httpx
from openai import OpenAI

from app.config import SETTINGS


SYSTEM_PROMPT = (
    'You are a retrieval QA assistant. Answer only from provided context. '
    'Give a direct, concise answer. If context is insufficient, say what is missing. '
    'Do not include generic filler such as "based on the retrieved passages above".'
    'Do not reveal direct personal contact details such as phone numbers or email addresses.'
)


def redact_sensitive(text: str) -> str:
    text = re.sub(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', '[email redacted]', text)
    text = re.sub(r'\+?\d[\d\s().-]{7,}\d', '[phone redacted]', text)
    return text


def build_context(chunks: list[dict], limit: int = 5, chars_per_chunk: int = 1200) -> str:
    return '\n\n'.join(
        f"[{idx}] Source: {c.get('source', 'unknown')} chunk {c.get('chunk_index', '?')}\n"
        f"{redact_sensitive(str(c.get('content', ''))[:chars_per_chunk])}"
        for idx, c in enumerate(chunks[:limit], start=1)
    )


class GeminiAdapter:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def answer(self, question: str, chunks: list[dict]) -> str:
        context = build_context(chunks)
        response = httpx.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent',
            params={'key': self.api_key},
            json={
                'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                'contents': [
                    {
                        'role': 'user',
                        'parts': [{'text': f'Question: {question}\n\nContext:\n{context}'}],
                    }
                ],
                'generationConfig': {'temperature': 0.2},
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get('candidates') or []
        if not candidates:
            return 'I could not generate an answer from the retrieved context.'
        parts = candidates[0].get('content', {}).get('parts') or []
        text = ''.join(str(part.get('text', '')) for part in parts).strip()
        return text or 'I could not generate an answer from the retrieved context.'


class OpenAICompatibleAdapter:
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def answer(self, question: str, chunks: list[dict]) -> str:
        context = build_context(chunks)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f'Question: {question}\n\nContext:\n{context}'},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or 'I could not generate an answer from the retrieved context.'


class AnswerGenerator:
    def __init__(self):
        self.provider = SETTINGS.llm_provider.lower().strip()
        self.gemini = (
            GeminiAdapter(api_key=SETTINGS.gemini_api_key, model=SETTINGS.gemini_model)
            if SETTINGS.gemini_api_key
            else None
        )
        openai_key = SETTINGS.openai_compat_api_key or SETTINGS.openai_api_key
        openai_model = SETTINGS.openai_compat_model or SETTINGS.llm_model
        self.openai_compatible = (
            OpenAICompatibleAdapter(
                api_key=openai_key,
                model=openai_model,
                base_url=SETTINGS.openai_compat_base_url,
            )
            if openai_key
            else None
        )

    def answer(self, question: str, chunks: list[dict]) -> str:
        if not chunks:
            return 'I could not find relevant context in the indexed documents.'

        for adapter in self._provider_order():
            try:
                return adapter.answer(question, chunks)
            except Exception:
                continue

        return self._extractive_answer(question, chunks)

    def _provider_order(self):
        if self.provider == 'gemini':
            return [adapter for adapter in (self.gemini, self.openai_compatible) if adapter]
        if self.provider in {'openai', 'openai_compatible', 'openai-compatible'}:
            return [adapter for adapter in (self.openai_compatible, self.gemini) if adapter]
        return [adapter for adapter in (self.gemini, self.openai_compatible) if adapter]

    def _extractive_answer(self, question: str, chunks: list[dict]) -> str:
        context = ' '.join(redact_sensitive(str(c.get('content', ''))) for c in chunks[:5])
        compact_context = re.sub(r'\s+', ' ', context).strip()
        question_lower = question.lower()

        if any(term in question_lower for term in ('language', 'speak', 'spoken')):
            language_match = re.search(
                r'(?:^|[\n\r]|[|•-]\s*)(?:Languages?|Spoken languages?)\s*[:\-]\s*([^.|;\n]+)',
                context,
                re.IGNORECASE,
            )
            if language_match:
                return f"Kyaw's language information appears to be: {language_match.group(1).strip()}."
            return 'The retrieved context does not state how many languages Kyaw can speak.'

        if any(term in question_lower for term in ('name', 'called')):
            name_match = re.search(r'\b(KYAW HTET)\b', compact_context, re.IGNORECASE)
            if name_match:
                return 'His name is Kyaw Htet.'
            return 'The retrieved context does not state his name.'

        if any(term in question_lower for term in ('degree', 'education', 'university', 'college')):
            education_match = re.search(
                r'(?:Education|Degree|University|College)\s*[:\-]\s*([^.|;\n]+)',
                context,
                re.IGNORECASE,
            )
            if education_match:
                return f"His education information appears to be: {education_match.group(1).strip()}."
            return 'The retrieved context does not state his degree.'

        if any(term in question_lower for term in ('skill', 'stack', 'technology', 'tech')):
            skill_match = re.search(
                r'(Python|FastAPI|RAG|LLMs?|agent workflows?|AI product development|PostgreSQL|SQLite|Docker|Git|pgvector|Linux|VPS Deployment|React|TypeScript|AWS|Terraform)[^\.]*',
                compact_context,
                re.IGNORECASE,
            )
            if skill_match:
                return (
                    'Kyaw has skills across applied AI and backend engineering, including Python, FastAPI, RAG, LLM applications, '
                    'agent workflows, PostgreSQL, pgvector, Docker, Git, Linux/VPS deployment, React, TypeScript, AWS, and Terraform.'
                )

        if any(term in question_lower for term in ('who', 'kyaw')):
            profile_match = re.search(r'(KYAW HTET[^\.]+)', compact_context, re.IGNORECASE)
            if profile_match:
                return f"{profile_match.group(1).strip()}."
            return compact_context[:360] if compact_context else 'The retrieved context does not contain enough profile information.'

        return compact_context[:520] if compact_context else 'The retrieved context does not contain enough information to answer.'


LLM = AnswerGenerator()
