# Finding #9: Passwort/Client-Secret wurden roh in Connection-String bzw. Token-URL eingesetzt --
# Sonderzeichen (@ : / &) haetten das Parsing gebrochen. Fix: urllib.parse.quote_plus() vor dem Einsetzen.
import urllib.parse

import db
import forcam_api


def test_get_engine_escapes_special_characters_in_password(monkeypatch, no_real_credentials):
    captured = {}

    def fake_create_engine(url, *args, **kwargs):
        captured["url"] = url
        return object()

    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    monkeypatch.setattr(db.config, "get_credential", lambda key: "p@ss:w/rd&1")

    db.get_engine()

    expected_password = urllib.parse.quote_plus("p@ss:w/rd&1")
    assert expected_password in captured["url"]
    assert "p@ss:w/rd&1" not in captured["url"]  # unescaped Rohform darf nicht mehr vorkommen


def test_get_auth_header_escapes_special_characters_in_client_secret(monkeypatch):
    monkeypatch.setattr(forcam_api.config, "get_credential", lambda key: "sec&ret=value")

    captured = {}

    class FakeResponse:
        def json(self):
            return {"access_token": "dummy-token"}

    class FakeRequest:
        def get(self, url, **kwargs):
            captured["url"] = url
            return FakeResponse()

    forcam_api.get_auth_header(FakeRequest(), ("Accept", "application/json"))

    expected_secret = urllib.parse.quote_plus("sec&ret=value")
    assert f"client_secret={expected_secret}" in captured["url"]
    assert "client_secret=sec&ret=value" not in captured["url"]
