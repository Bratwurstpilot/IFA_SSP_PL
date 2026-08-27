# Finding #5: extract_api_data_disturbances hat keine Guards gegen fehlende/kaputte Felder.
# load_data_disturbance faengt Fehler zwar global ab, aber nur mit einem breiten try/except,
# das jede Ursache (auch echte Bugs) still mit einer leeren Fallback-DataFrame verschluckt.
import datetime

import pandas as pd
import pytest

import data_disturbances


def _selection():
    return {'date': datetime.date(2026, 7, 30), 'shift_id': 'early_shift', 'workplaces': []}


def _make_request(properties):
    return {"_embedded": {"ifareportsOperating_state_log": [{"properties": properties}]}}


_VALID_PROPS = {
    "workplaceId": "W1 - Machine 1",
    "startTs": "30/07/2026, 06:15",
    "endTs": "30/07/2026, 06:45",
    "operatingStatusMnemonic": "8098005",
    "operatingStatusText": "Stoerung",
    "ticketTitle": "Kommentar",
}


@pytest.mark.xfail(strict=True, reason="Finding #5: workplaceId=None -> AttributeError bei .split()")
def test_extract_disturbance_none_workplace_id_raises():
    props = dict(_VALID_PROPS, workplaceId=None)
    data_disturbances.extract_api_data_disturbances(_make_request(props), _selection())


@pytest.mark.xfail(strict=True, reason="Finding #5: startTs=None -> TypeError bei strptime()")
def test_extract_disturbance_none_start_ts_raises():
    props = dict(_VALID_PROPS, startTs=None)
    data_disturbances.extract_api_data_disturbances(_make_request(props), _selection())


@pytest.mark.xfail(strict=True, reason="Finding #5: falsches Datumsformat -> ValueError bei strptime()")
def test_extract_disturbance_wrong_date_format_raises():
    props = dict(_VALID_PROPS, startTs="2026-07-30 06:15")
    data_disturbances.extract_api_data_disturbances(_make_request(props), _selection())


def test_extract_disturbance_happy_path():
    result = data_disturbances.extract_api_data_disturbances(_make_request(_VALID_PROPS), _selection())
    assert result[0]['workplace_id'] == "W1"
    assert result[0]['duration_minutes'] == 30


def test_load_data_disturbance_swallows_extraction_errors_silently(monkeypatch):
    # known_issue (kein Crash): wenn extract_api_data_disturbances Zeilen ohne 'duration_minutes'
    # liefert, faengt das breite try/except in load_data_disturbance JEDEN Fehler ab -- auch
    # einen echten Bug -- und gibt kommentarlos eine leere Fallback-DataFrame zurueck.
    import db
    import forcam_api

    monkeypatch.setattr(db, "get_forcam_uuid_maps", lambda: ({}, {}))
    monkeypatch.setattr(forcam_api, "get_auth_header", lambda request, accept_header: {})

    class _FakeResponse:
        def json(self):
            return {"_embedded": {"ifareportsOperating_state_log": []}, "pagination": {"total": 0}}

    class _FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def get(self, url, **kwargs):
            return _FakeResponse()

    monkeypatch.setattr(data_disturbances.requests, "Session", lambda: _FakeSession())
    monkeypatch.setattr(data_disturbances, "extract_api_data_disturbances", lambda data_request, selection: [{"date_id": "2026-07-30"}])  # fehlt: duration_minutes

    progressbar = type("FakeProgressBar", (), {"progress": lambda self, *a, **k: None})()
    result = data_disturbances.load_data_disturbance(_selection(), progressbar, "loading...")

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ['date_id', 'shift_id', 'workplace_id', 'start', 'end', 'code', 'status',
                                     'sf_comment', 'duration_minutes', 'source', 'last_updated']
