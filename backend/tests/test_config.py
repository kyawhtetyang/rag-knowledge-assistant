from app.config import SETTINGS


def test_cors_origins_are_explicit_by_default():
    assert '*' not in SETTINGS.cors_origins
    assert 'http://localhost:3001' in SETTINGS.cors_origins


def test_request_limits_are_positive():
    assert SETTINGS.max_upload_bytes > 0
    assert SETTINGS.max_text_chars > 0
