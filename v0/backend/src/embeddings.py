import hashlib
from typing import List

import numpy as np

from src.settings import SETTINGS

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


class EmbeddingClient:
    def __init__(self, model_name: str, dim: int):
        self.model_name = model_name
        self.dim = int(dim)
        self.model = None

        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
                detected_dim = self.model.get_sentence_embedding_dimension()
                if detected_dim:
                    self.dim = int(detected_dim)
            except Exception:
                self.model = None

    def _hash_embed(self, text: str) -> List[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in (text or '').lower().split():
            digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
            idx = int(digest[:16], 16) % self.dim
            vec[idx] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.model is not None:
            vectors = self.model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return vectors.astype(np.float32).tolist()

        return [self._hash_embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]


EMBEDDINGS = EmbeddingClient(SETTINGS.embedding_model, SETTINGS.embedding_dim)
