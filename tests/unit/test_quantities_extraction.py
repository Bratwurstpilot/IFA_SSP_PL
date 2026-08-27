# Finding #4: extract_api_data_quantity_machine hat keinerlei Guards gegen fehlende/kaputte
# Felder in der Forcam-Antwort (None-Werte, unbekannter workplaceId).
import datetime

import pytest

import data_quantities
import db


def _selection():
    return {'date': datetime.date(2026, 7, 30), 'shift_id': 'early_shift'}


def _make_request(properties):
    return {"_embedded": {"ifareportsSsp": [{"properties": properties}]}}


_VALID_PROPS = {
    "workplaceId": "UUID-1",
    "targetQuantity": "100.00",
    "yieldQtyShift": "90.00",
    "scrapQtyShift": "10.00",
    "prodDuration": "07:30",
    "setupDuration": "00:10",
    "interuptDuration": "00:20",
    "breakDuration": "00:30",
    "timePerUnitSec": "12.5",
    "realTimePerUnitSec": "13.0",
    "pph": "288.0",
}


@pytest.mark.xfail(strict=True, reason="Finding #4: targetQuantity=None -> AttributeError bei .replace()")
def test_extract_quantity_none_target_quantity_raises(monkeypatch):
    monkeypatch.setattr(db, "get_forcam_uuid_maps", lambda: ({}, {"UUID-1": "W1"}))
    props = dict(_VALID_PROPS, targetQuantity=None)
    list(data_quantities.extract_api_data_quantity_machine(_make_request(props), _selection()))


@pytest.mark.xfail(strict=True, reason="Finding #4: unbekannter workplaceId (kein Forcam-UUID-Mapping) -> KeyError")
def test_extract_quantity_unmapped_workplace_raises(monkeypatch):
    monkeypatch.setattr(db, "get_forcam_uuid_maps", lambda: ({}, {}))
    list(data_quantities.extract_api_data_quantity_machine(_make_request(_VALID_PROPS), _selection()))


def test_extract_quantity_happy_path(monkeypatch):
    monkeypatch.setattr(db, "get_forcam_uuid_maps", lambda: ({}, {"UUID-1": "W1"}))
    result = data_quantities.extract_api_data_quantity_machine(_make_request(_VALID_PROPS), _selection())
    assert result[0]['workplace_id'] == "W1"
    assert result[0]['target'] == 100
    assert result[0]['OK'] == 90
    assert result[0]['NOK'] == 10
