import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')


def _parse_bool(value, default):
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


@dataclass
class Settings:
    pg_dsn: str
    embedding_model: str
    embedding_dim: int
    chunk_size: int
    chunk_overlap: int
    default_top_k: int
    llm_model: str
    use_mock_llm: bool
    docs_dir: Path


with open(BASE_DIR / 'config' / 'config.json', 'r', encoding='utf-8') as f:
    _cfg = json.load(f)

SETTINGS = Settings(
    pg_dsn=os.getenv('PG_DSN', _cfg['pg_dsn']),
    embedding_model=os.getenv('EMBEDDING_MODEL', _cfg['embedding_model']),
    embedding_dim=int(os.getenv('EMBEDDING_DIM', _cfg['embedding_dim'])),
    chunk_size=int(os.getenv('CHUNK_SIZE', _cfg['chunk_size'])),
    chunk_overlap=int(os.getenv('CHUNK_OVERLAP', _cfg['chunk_overlap'])),
    default_top_k=int(os.getenv('DEFAULT_TOP_K', _cfg['default_top_k'])),
    llm_model=os.getenv('LLM_MODEL', _cfg['llm_model']),
    use_mock_llm=_parse_bool(os.getenv('USE_MOCK_LLM'), _cfg['use_mock_llm']),
    docs_dir=BASE_DIR / os.getenv('DOCS_DIR', _cfg['docs_dir']),
)
