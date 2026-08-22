from app.llm import redact_sensitive


def test_redact_sensitive_hides_email():
    assert redact_sensitive('Contact me at user@example.com') == 'Contact me at [email redacted]'


def test_redact_sensitive_hides_phone():
    redacted = redact_sensitive('Phone +1 415 555 1212')
    assert '[phone redacted]' in redacted
    assert '415 555 1212' not in redacted
