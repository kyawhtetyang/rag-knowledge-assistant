from typing import List


def chunk_text(text: str, chunk_size: int = 220, chunk_overlap: int = 40) -> List[str]:
    text = (text or '').strip()
    if not text:
        return []

    tokens = text.split()
    if chunk_size <= 0:
        raise ValueError('chunk_size must be > 0')
    if chunk_overlap < 0:
        raise ValueError('chunk_overlap must be >= 0')
    if chunk_overlap >= chunk_size:
        raise ValueError('chunk_overlap must be smaller than chunk_size')

    step = chunk_size - chunk_overlap
    chunks = []

    for start in range(0, len(tokens), step):
        window = tokens[start:start + chunk_size]
        if not window:
            break
        chunks.append(' '.join(window))
        if start + chunk_size >= len(tokens):
            break

    return chunks
