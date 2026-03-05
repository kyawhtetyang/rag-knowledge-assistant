from pathlib import Path
from typing import Dict, List

from PyPDF2 import PdfReader

from src.chunking import chunk_text
from src.db import upsert_chunks
from src.embeddings import EMBEDDINGS
from src.settings import SETTINGS

SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf'}


def _read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {'.txt', '.md'}:
        return path.read_text(encoding='utf-8', errors='ignore')
    if suffix == '.pdf':
        reader = PdfReader(str(path))
        pages = [page.extract_text() or '' for page in reader.pages]
        return '\n'.join(pages)
    raise ValueError(f'Unsupported file type: {path.suffix}')


def list_document_paths(base_dir: Path) -> List[Path]:
    if not base_dir.exists():
        return []
    candidates = []
    for path in sorted(base_dir.rglob('*')):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            candidates.append(path)
    return candidates


def ingest_paths(paths: List[Path], chunk_size: int, chunk_overlap: int) -> Dict[str, int]:
    total_chunks = 0
    ingested_docs = 0

    for doc_path in paths:
        raw_text = _read_text(doc_path)
        chunks = chunk_text(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            continue

        vectors = EMBEDDINGS.embed_texts(chunks)
        rows = []
        rel_name = str(doc_path)

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            rows.append(
                {
                    'doc_name': rel_name,
                    'chunk_index': idx,
                    'content': chunk,
                    'metadata': {
                        'source': rel_name,
                        'chunk_size': chunk_size,
                        'chunk_overlap': chunk_overlap,
                    },
                    'embedding': vector,
                }
            )

        total_chunks += upsert_chunks(rows)
        ingested_docs += 1

    return {'documents': ingested_docs, 'chunks': total_chunks}


def ingest_default_docs():
    paths = list_document_paths(SETTINGS.docs_dir)
    return ingest_paths(paths, SETTINGS.chunk_size, SETTINGS.chunk_overlap)
