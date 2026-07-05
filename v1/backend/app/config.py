from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'dev'
    app_host: str = '0.0.0.0'
    app_port: int = 8010

    database_url: str

    embeddings_provider: str = 'hash'
    embedding_model: str = 'text-embedding-3-small'
    embedding_dim: int = 384

    llm_model: str = 'gpt-4o-mini'

    chunk_size: int = 220
    chunk_overlap: int = 40
    default_top_k: int = 5

    retrieval_mode: str = 'hybrid'  # vector|fts|hybrid
    vector_weight: float = 1.0
    fts_weight: float = 0.2


SETTINGS = Settings()
