# Read-only Forcam-Konnektivitaetspruefung: echter OAuth2-Token-Abruf, keine Report-Daten,
# keine Schreiboperation.
import requests

import forcam_api


def test_forcam_token_fetch_succeeds():
    with requests.Session() as request:
        request_head = forcam_api.get_auth_header(request, ("Accept", "application/json;charset=UTF-8"))

    assert "Authorization" in request_head
    assert request_head["Authorization"].startswith("Bearer ")
