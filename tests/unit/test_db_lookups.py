# Finding #2: DB-Lookups liessen OperationalError roh durchschlagen (App-Crash bei DB-Ausfall).
# Fix: try/except je Funktion, Fallback auf leeres/sicheres Ergebnis + Log statt Crash.
import pandas as pd
import pytest

import db


def _raise(*args, **kwargs):
    raise Exception("DWH unreachable (simulated)")


def test_get_hierarchy_returns_empty_dict_on_db_error(monkeypatch, mock_engine):
    monkeypatch.setattr("app_logging.log_and_read_sql", _raise)
    assert db.get_hierarchy() == {}


def test_get_forcam_uuid_maps_returns_empty_dicts_on_db_error(monkeypatch, mock_engine):
    monkeypatch.setattr("app_logging.log_and_read_sql", _raise)
    ifa_to_uuid, uuid_to_ifa = db.get_forcam_uuid_maps()
    assert ifa_to_uuid == {}
    assert uuid_to_ifa == {}


def test_get_operating_state_codes_returns_empty_df_on_db_error(monkeypatch, mock_engine):
    monkeypatch.setattr("app_logging.log_and_read_sql", _raise)
    result = db.get_operating_state_codes("en")
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ['code', 'title', 'color']
    assert len(result) == 0


def test_get_wpl_info_returns_empty_df_on_db_error(monkeypatch, mock_engine):
    monkeypatch.setattr("app_logging.log_and_read_sql", _raise)
    result = db.get_wpl_info()
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ['workplace_id', 'process', 'machine_name', 'output_relevant', 'line_name']
    assert len(result) == 0


def test_get_hierarchy_builds_correct_structure(monkeypatch, mock_engine, spy_read_sql):
    df_hierarchy = pd.DataFrame([
        {"department": "OMA", "line_id": "L1 - Line 1", "subline_id": "S1 - Sub 1"},
        {"department": "OMA", "line_id": "L1 - Line 1", "subline_id": None},
    ])
    df_wpl = pd.DataFrame([
        {"workplace_id": "W1", "line_id": "L1 - Line 1", "subline_id": "S1 - Sub 1"},
        {"workplace_id": "W2", "line_id": "L1 - Line 1", "subline_id": None},
    ])
    spy_read_sql.queue([df_hierarchy, df_wpl])

    hierarchy = db.get_hierarchy()

    assert hierarchy["OMA"]["L1 - Line 1"]["S1 - Sub 1"] == ["W1"]
    # workplaces_by_line gruppiert nur nach line_id (nicht nach subline_id) -- die
    # "keine Subline"-Zeile bekommt deshalb ALLE Workplaces der Linie, nicht nur die
    # ohne Subline. Das entspricht dem tatsaechlichen Verhalten von db.get_hierarchy().
    assert hierarchy["OMA"]["L1 - Line 1"]["L1 - Line 1"] == ["W1", "W2"]


def test_get_forcam_uuid_maps_duplicate_uuid_silently_overwrites_reverse_mapping(monkeypatch, mock_engine, spy_read_sql):
    # known_issue (kein Crash): zwei ifa-Workplaces auf dieselbe Forcam-UUID -> die reverse map
    # (forcam_uuid_to_ifa_wpl) behaelt nur den letzten Eintrag, ohne dass die UI das sichtbar macht.
    spy_read_sql.result = pd.DataFrame([
        {"workplace_ifa_id": "W1", "workplace_forcam_uuid": "UUID-A"},
        {"workplace_ifa_id": "W2", "workplace_forcam_uuid": "UUID-A"},
    ])

    _, forcam_uuid_to_ifa_wpl = db.get_forcam_uuid_maps()

    assert forcam_uuid_to_ifa_wpl["UUID-A"] == "W2"
