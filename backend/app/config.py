from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'dev'
    app_version: str = '0.9.0'
    app_host: str = '0.0.0.0'
    app_port: int = 8010

    database_url: str

    allowed_origins: str = 'http://localhost:3001,http://127.0.0.1:3001'
    admin_api_key: str | None = None
    max_upload_bytes: int = 10 * 1024 * 1024
    max_text_chars: int = 2_000_000

    embeddings_provider: str = 'hash'
    embedding_model: str = 'text-embedding-3-small'
    embedding_dim: int = 384

    llm_provider: str = 'local'
    llm_model: str = 'gpt-4o-mini'
    gemini_api_key: str | None = None
    gemini_model: str = 'gemini-2.5-flash'
    openai_api_key: str | None = None
    openai_compat_api_key: str | None = None
    openai_compat_base_url: str | None = None
    openai_compat_model: str = 'gpt-4o-mini'

    chunk_size: int = 220
    chunk_overlap: int = 40
    default_top_k: int = 5

    retrieval_mode: str = 'hybrid'  # vector|fts|hybrid
    vector_weight: float = 1.0
    fts_weight: float = 0.2

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]

    @field_validator('database_url')
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith('postgres://'):
            return 'postgresql+asyncpg://' + value.removeprefix('postgres://')
        if value.startswith('postgresql://'):
            return 'postgresql+asyncpg://' + value.removeprefix('postgresql://')
        return value

    @field_validator('max_upload_bytes', 'max_text_chars')
    @classmethod
    def validate_positive_limits(cls, value: int) -> int:
        if value <= 0:
            raise ValueError('request limits must be positive')
        return value


SETTINGS = Settings()
