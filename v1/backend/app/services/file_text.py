from __future__ import annotations

import io
from pathlib import Path

from PyPDF2 import PdfReader

SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf'}


def extract_text_from_upload(filename: str, content: bytes) -> str:
    suffix = Path(filename or '').suffix.lower()

    if suffix in {'.txt', '.md'}:
        return content.decode('utf-8', errors='ignore')

    if suffix == '.pdf':
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or '' for page in reader.pages]
        return '\n'.join(pages)

    raise ValueError(
        f'Unsupported file type: {suffix or "(no extension)"}. Supported: {sorted(SUPPORTED_EXTENSIONS)}'
    )
