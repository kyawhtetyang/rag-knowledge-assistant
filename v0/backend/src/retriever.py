from src.db import search_similar
from src.embeddings import EMBEDDINGS


def retrieve(question: str, top_k: int):
    query_embedding = EMBEDDINGS.embed_query(question)
    return search_similar(query_embedding, top_k)
