from __future__ import annotations

import hashlib
import os
from typing import Literal

import numpy as np

from app.config import SETTINGS

SCHEMA_VECTOR_DIM = 384
if SETTINGS.embedding_dim != SCHEMA_VECTOR_DIM:
    raise RuntimeError(
        f'EMBEDDING_DIM={SETTINGS.embedding_dim} does not match DB schema VECTOR({SCHEMA_VECTOR_DIM}). '
        'Change requires a migration + re-embedding.'
    )

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


Provider = Literal['hash', 'sentence_transformers', 'openai']


class EmbeddingClient:
    def __init__(self, provider: Provider, *, model: str, dim: int):
        self.provider: Provider = provider
        self.model = model
        self.dim = int(dim)

        self._openai: OpenAI | None = None
        self._st_model = None

        if self.provider == 'openai':
            if OpenAI is None:
                raise RuntimeError('openai package is not installed')
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise RuntimeError('OPENAI_API_KEY is required when EMBEDDINGS_PROVIDER=openai')

            kwargs: dict = {'api_key': api_key}
            base_url = os.getenv('OPENAI_BASE_URL')
            if base_url:
                kwargs['base_url'] = base_url
            self._openai = OpenAI(**kwargs)

        if self.provider == 'sentence_transformers':
            if SentenceTransformer is None:
                raise RuntimeError('sentence-transformers package is not installed')
            self._st_model = SentenceTransformer(self.model)
            detected_dim = getattr(self._st_model, 'get_sentence_embedding_dimension', lambda: None)()
            if detected_dim and int(detected_dim) != self.dim:
                raise RuntimeError(
                    f'SentenceTransformer dim={detected_dim} does not match EMBEDDING_DIM={self.dim}. '
                    'Pick a 384-dim model (or migrate DB + re-embed).'
                )

    def _hash_embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in (text or '').lower().split():
            digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
            idx = int(digest[:16], 16) % self.dim
            vec[idx] += 1.0

        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.provider == 'hash':
            return [self._hash_embed(t) for t in texts]

        if self.provider == 'sentence_transformers':
            assert self._st_model is not None
            vectors = self._st_model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return vectors.astype(np.float32).tolist()

        if self.provider == 'openai':
            assert self._openai is not None
            resp = self._openai.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dim,
            )
            vectors = [d.embedding for d in resp.data]
            if any(len(v) != self.dim for v in vectors):
                raise RuntimeError('embedding dim mismatch; check EMBEDDING_DIM and provider/model')
            return vectors

        raise RuntimeError(f'unsupported embeddings provider: {self.provider}')

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


def _normalized_provider(value: str) -> Provider:
    raw = (value or 'hash').strip().lower()
    if raw in {'hash', 'sentence_transformers', 'openai'}:
        return raw  # type: ignore[return-value]
    raise RuntimeError(
        f'Invalid EMBEDDINGS_PROVIDER={value!r}. Use: hash|sentence_transformers|openai'
    )


EMBEDDINGS = EmbeddingClient(
    _normalized_provider(SETTINGS.embeddings_provider),
    model=SETTINGS.embedding_model,
    dim=SETTINGS.embedding_dim,
)
