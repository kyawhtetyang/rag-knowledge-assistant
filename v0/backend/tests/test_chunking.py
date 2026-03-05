from src.chunking import chunk_text


def test_chunk_text_with_overlap():
    text = ' '.join(f'w{i}' for i in range(30))
    chunks = chunk_text(text, chunk_size=10, chunk_overlap=2)

    assert len(chunks) >= 3
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


def test_chunk_text_empty_input():
    assert chunk_text('', chunk_size=10, chunk_overlap=2) == []
