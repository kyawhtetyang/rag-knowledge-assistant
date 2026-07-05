from src.embeddings import EmbeddingClient


def test_hash_embedding_dimension():
    client = EmbeddingClient(model_name='__missing_model__', dim=32)
    client.model = None
    vec = client.embed_query('hello world')

    assert len(vec) == 32
    assert all(isinstance(v, float) for v in vec)
