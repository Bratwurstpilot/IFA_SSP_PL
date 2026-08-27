# Finding #11: unbekannter shift_id fuehrt zu UnboundLocalError (shift_start/shift_end nie zugewiesen).
# Finding #12: keine DST-Anpassung -- an den Zeitumstellungstagen bleibt das Schichtfenster
# rechnerisch 8h breit, auch wenn die reale Uhrzeit-Verschiebung eine Stunde betraegt.
import datetime

import pytest

import forcam_api


@pytest.mark.xfail(strict=True, reason="Finding #11: unbekannte shift_id wird nicht validiert, UnboundLocalError")
def test_get_shift_window_unknown_shift_id_raises():
    selection = {'shift_id': 'unexpected_value', 'date': datetime.date(2026, 7, 30)}
    forcam_api.get_shift_window(selection, datetime.time(22, 0, 0))


@pytest.mark.parametrize("transition_date", [
    datetime.date(2026, 3, 29),   # letzter Sonntag Maerz 2026 (CET -> CEST)
    datetime.date(2026, 10, 25),  # letzter Sonntag Oktober 2026 (CEST -> CET)
])
def test_get_shift_window_no_dst_adjustment_on_transition_dates(transition_date):
    # Dokumentiert bewusst das aktuelle (naive) Verhalten: keine automatische DST-Korrektur.
    selection = {'shift_id': 'early_shift', 'date': transition_date}
    shift_start, shift_end = forcam_api.get_shift_window(selection, datetime.time(22, 0, 0))
    assert shift_end - shift_start == datetime.timedelta(hours=8)


def test_get_shift_window_late_shift_window():
    selection = {'shift_id': 'late_shift', 'date': datetime.date(2026, 7, 30)}
    shift_start, shift_end = forcam_api.get_shift_window(selection, datetime.time(22, 0, 0))
    assert shift_start == datetime.datetime(2026, 7, 30, 14, 0, 0)
    assert shift_end == datetime.datetime(2026, 7, 30, 22, 0, 0)


def test_get_shift_window_night_shift_spans_previous_day():
    selection = {'shift_id': 'night_shift', 'date': datetime.date(2026, 7, 30)}
    shift_start, shift_end = forcam_api.get_shift_window(selection, datetime.time(22, 2, 0))
    assert shift_start == datetime.datetime(2026, 7, 29, 22, 2, 0)
    assert shift_end == datetime.datetime(2026, 7, 30, 6, 0, 0)
