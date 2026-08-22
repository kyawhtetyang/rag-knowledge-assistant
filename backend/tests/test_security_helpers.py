import pytest
from fastapi import HTTPException

from app import main


def test_admin_endpoint_is_hidden_without_configured_key(monkeypatch):
    monkeypatch.setattr(main.SETTINGS, 'admin_api_key', None)
    with pytest.raises(HTTPException) as exc:
        main.require_admin(None)
    assert exc.value.status_code == 404


def test_admin_endpoint_rejects_wrong_key(monkeypatch):
    monkeypatch.setattr(main.SETTINGS, 'admin_api_key', 'expected')
    with pytest.raises(HTTPException) as exc:
        main.require_admin('wrong')
    assert exc.value.status_code == 403
