# Finding #3: Forcam-Token-Antworten ohne 'access_token' bzw. Verbindungsfehler lassen
# get_auth_header roh crashen (kein Retry/Fallback). Finding #7: leere Workplace-Liste
# ergibt eine komplett leere URL (kein Fehler, aber ein leises Fehlverhalten).
import requests
import pytest

import forcam_api


class _FakeResponseNoToken:
    def json(self):
        return {}


class _FakeRequestNoToken:
    def get(self, url, **kwargs):
        return _FakeResponseNoToken()


class _FakeRequestConnectionError:
    def get(self, url, **kwargs):
        raise requests.exceptions.ConnectionError("Forcam unreachable (simulated)")


@pytest.mark.xfail(strict=True, reason="Finding #3: fehlender access_token im Token-Response wird nicht abgefangen")
def test_get_auth_header_missing_access_token_raises(monkeypatch, no_real_credentials):
    forcam_api.get_auth_header(_FakeRequestNoToken(), ("Accept", "application/json"))


@pytest.mark.xfail(strict=True, reason="Finding #3: Verbindungsfehler zum Forcam-Token-Endpoint wird nicht abgefangen")
def test_get_auth_header_connection_error_propagates(monkeypatch, no_real_credentials):
    forcam_api.get_auth_header(_FakeRequestConnectionError(), ("Accept", "application/json"))


def test_build_workplace_url_empty_input_returns_empty_string():
    # known_issue (kein Crash): keine Workplaces -> keine "&workplace="-Parameter, still valid no-op
    assert forcam_api.build_workplace_url([], {}) == ""


def test_build_workplace_url_skips_unmapped_workplace_silently():
    # known_issue: ein Workplace ohne Forcam-UUID-Mapping wird stillschweigend ausgelassen
    result = forcam_api.build_workplace_url(["W1", "W2"], {"W1": "UUID-1"})
    assert result == "&workplace=UUID-1"
