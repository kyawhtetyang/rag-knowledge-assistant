import os

from src.settings import SETTINGS

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


SYSTEM_PROMPT = (
    'You are a retrieval QA assistant. Answer only from provided context. '
    'If context is insufficient, say what is missing.'
)


class AnswerGenerator:
    def __init__(self):
        self.use_mock = SETTINGS.use_mock_llm
        self.client = None

        if not self.use_mock and OpenAI is not None and os.getenv('OPENAI_API_KEY'):
            kwargs = {'api_key': os.getenv('OPENAI_API_KEY')}
            base_url = os.getenv('OPENAI_BASE_URL')
            if base_url:
                kwargs['base_url'] = base_url
            self.client = OpenAI(**kwargs)

    def _mock_answer(self, question, chunks):
        if not chunks:
            return 'I could not find relevant context in the indexed documents.'

        lines = [f'Question: {question}', '', 'Relevant context summary:']
        for idx, c in enumerate(chunks[:3], start=1):
            snippet = c['content'][:240].replace('\n', ' ')
            lines.append(f'{idx}. {snippet}')
        lines.append('')
        lines.append('Answer: Based on the retrieved passages above, this is the most likely answer.')
        return '\n'.join(lines)

    def answer(self, question, chunks):
        if not chunks:
            return self._mock_answer(question, chunks)

        if self.client is None:
            return self._mock_answer(question, chunks)

        context = '\n\n'.join(
            f"[Source: {c['doc_name']} | Chunk: {c['chunk_index']} | Score: {c['score']:.4f}]\n{c['content']}"
            for c in chunks
        )

        user_prompt = (
            f'Question:\n{question}\n\n'
            f'Context:\n{context}\n\n'
            'Write a concise answer and cite source names inline.'
        )

        try:
            response = self.client.chat.completions.create(
                model=SETTINGS.llm_model,
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._mock_answer(question, chunks)


LLM = AnswerGenerator()
