import sys

import httpx


DOC_TEXT = """pgvector is a PostgreSQL extension that adds a vector data type and vector similarity search.
It supports distance functions like cosine distance and L2 distance.
"""


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8010'

    r = httpx.get(base_url + '/health', timeout=10)
    r.raise_for_status()
    print('health:', r.json())

    # ingest as text (baseline)
    ingest = httpx.post(
        base_url + '/api/ingest-text',
        json={'source': 'smoke_doc', 'text': DOC_TEXT, 'metadata': {'type': 'smoke'}},
        timeout=30,
    )

    # ingest as file (new path)
    file_ingest = httpx.post(
        base_url + '/api/ingest-file',
        files={'file': ('smoke.md', DOC_TEXT.encode('utf-8'), 'text/markdown')},
        timeout=30,
    )
    file_ingest.raise_for_status()
    print('ingest_file:', file_ingest.json())
    ingest.raise_for_status()
    print('ingest:', ingest.json())

    ask = httpx.post(
        base_url + '/api/ask',
        json={'question': 'What is pgvector?', 'top_k': 3},
        timeout=30,
    )
    ask.raise_for_status()
    payload = ask.json()
    print('answer:', payload.get('answer', '')[:240])
    print('citations:', payload.get('citations', [])[:2])

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
