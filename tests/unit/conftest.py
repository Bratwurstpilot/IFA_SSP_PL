# Gemeinsame Fixtures fuer alle Unit-Tests: Fake st.session_state, DB-/API-Mocking-Helfer.
# Unit-Tests duerfen NIE die echte DWH/Forcam-API oder credentials.json anfassen.
import pandas as pd
import pytest
import streamlit as st

import db


class _FakeSessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __contains__(self, key):
        return dict.__contains__(self, key)


@pytest.fixture(autouse=True)
def fake_session_state(monkeypatch):
    # st.session_state ausserhalb einer laufenden Streamlit-App ist versions-/kontextabhaengig --
    # deshalb fuer alle Unit-Tests durch ein simples dict-basiertes Fake ersetzt.
    monkeypatch.setattr(st, "session_state", _FakeSessionState(), raising=False)
    yield


@pytest.fixture(autouse=True)
def clear_streamlit_caches():
    # get_hierarchy/get_forcam_uuid_maps/... sind @st.cache_data/@st.cache_resource --
    # ohne Clear wuerde der erste Test-Mock fuer alle folgenden Tests im Prozess "einfrieren".
    st.cache_data.clear()
    st.cache_resource.clear()
    yield
    st.cache_data.clear()
    st.cache_resource.clear()


@pytest.fixture
def mock_engine(monkeypatch):
    fake_engine = object()
    monkeypatch.setattr(db, "get_engine", lambda: fake_engine)
    return fake_engine


@pytest.fixture
def spy_read_sql(monkeypatch):
    """Ersetzt app_logging.log_and_read_sql durch einen steuerbaren Spion.

    Nutzung: spy_read_sql.result = <DataFrame>  (oder eine Liste von DataFrames fuer mehrere Aufrufe)
    spy_read_sql.calls enthaelt alle empfangenen SQL-Strings.
    """
    import app_logging

    class Spy:
        def __init__(self):
            self.calls = []
            self.result = pd.DataFrame()
            self._queue = None

        def __call__(self, sql, engine, label=""):
            self.calls.append(sql)
            if self._queue:
                return self._queue.pop(0)
            return self.result

        def queue(self, results):
            self._queue = list(results)

    spy = Spy()
    monkeypatch.setattr(app_logging, "log_and_read_sql", spy)
    return spy


@pytest.fixture
def no_real_credentials(monkeypatch):
    # Verhindert, dass Unit-Tests versehentlich credentials.json lesen.
    import config
    monkeypatch.setattr(config, "get_credential", lambda key: f"dummy-{key}")
    return None
