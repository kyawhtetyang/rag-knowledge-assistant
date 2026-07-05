from __future__ import annotations

from app.config import SETTINGS


SYSTEM_PROMPT = (
    'You are a retrieval QA assistant. Answer only from provided context. '
    'If context is insufficient, say what is missing.'
)


class AnswerGenerator:
    def __init__(self):
        self.model = SETTINGS.llm_model

    def answer(self, question: str, chunks: list[dict]) -> str:
        if not chunks:
            return 'I could not find relevant context in the indexed documents.'

        lines = [f'Question: {question}', '', 'Relevant context summary:']
        for idx, c in enumerate(chunks[:3], start=1):
            snippet = str(c.get('content', ''))[:240].replace('\n', ' ')
            lines.append(f'{idx}. {snippet}')
        lines.append('')
        lines.append(
            'Answer: Use the cited context above. If the requested field is not visible there, '
            'the indexed document may not contain it or retrieval did not find the right chunk.'
        )
        return '\n'.join(lines)


LLM = AnswerGenerator()
