# Finding #8: die "reselect" nach dem Speichern liefert eine leere DataFrame -> IndexError.
# Finding #13: int(nan) in save_data_general crasht, wenn SHOPFLOOR_EMPLOYEES_AVAILABLE=True
# ist und die DB keine Zahl liefert (heute bei Polen nicht erreichbar, da Flag=False, aber
# die Funktion selbst validiert das nicht).
import numpy as np
import pandas as pd
import pytest

import config
import data_general
import db


def _selection():
    return {'date': __import__('datetime').date(2026, 7, 30), 'shift_id': 'early_shift', 'subline': 'S1 - Sub 1', 'department': 'OMA'}


class _FakeCol:
    def __eq__(self, other):
        return self

    def __and__(self, other):
        return self


class _FakeTable:
    class c:
        date_id = _FakeCol()
        shift_id = _FakeCol()
        line_id = _FakeCol()


@pytest.mark.xfail(strict=True, reason="Finding #8: leeres Reselect-Ergebnis -> IndexError bei .iloc[0]")
def test_collect_data_general_raises_on_empty_reselect(monkeypatch, mock_engine, spy_read_sql):
    monkeypatch.setattr(data_general, "save_data_general", lambda *a, **k: None)
    empty_df = pd.DataFrame(columns=['name', 'message', 'kpi_output_ok', 'kpi_output_nok', 'kpi_employees_present', 'kpi_output_per_employee'])
    spy_read_sql.result = empty_df

    data_quantity_machine = pd.DataFrame({'output_relevant': [], 'OK': [], 'NOK': []})
    data_general.collect_data_general(_selection(), data_quantity_machine)


@pytest.mark.xfail(strict=True, reason="Finding #13: int(nan) in save_data_general wird nicht abgefangen")
def test_save_data_general_raises_on_nan_kpi_when_shopfloor_employees_available(monkeypatch, mock_engine):
    monkeypatch.setattr(data_general, "Table", lambda *a, **k: _FakeTable)
    monkeypatch.setattr(db, "get_session", lambda: None)

    data = {
        'name': 'Max',
        'message': '',
        'kpi_output_ok': np.nan,
        'kpi_output_nok': 0,
        'kpi_employees_present': 5,
        'kpi_output_per_employee': 0,
    }
    data_general.save_data_general(_selection(), data)


def test_safe_int_conversion_nan_returns_default():
    assert data_general.safe_int_conversion(np.nan) == 0


def test_safe_int_conversion_valid_value():
    assert data_general.safe_int_conversion(7.0) == 7
