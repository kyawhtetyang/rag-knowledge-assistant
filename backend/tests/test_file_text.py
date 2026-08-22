import pytest

from app.services.file_text import extract_text_from_upload


def test_extract_text_accepts_plain_text():
    assert extract_text_from_upload('note.txt', b'hello world') == 'hello world'


def test_extract_text_accepts_markdown():
    assert extract_text_from_upload('note.md', b'# Title') == '# Title'


def test_extract_text_rejects_unsupported_extension():
    with pytest.raises(ValueError, match='Unsupported file type'):
        extract_text_from_upload('payload.exe', b'not executable content')
