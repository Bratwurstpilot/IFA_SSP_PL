# Read-only Stammdaten-Abfragen gegen die echte DWH. Prueft NUR Typ/keine-Exception --
# nicht len() > 0, weil PLANT_ID='UjaP' fuer Polen aktuell noch ein Platzhalter ist und
# legitim (noch) keine Treffer liefern kann (siehe config.py TODO(PL)-Kommentare).
import pandas as pd

import db


def test_get_hierarchy_returns_dict_without_raising():
    result = db.get_hierarchy()
    assert isinstance(result, dict)


def test_get_forcam_uuid_maps_returns_tuple_of_dicts_without_raising():
    ifa_to_uuid, uuid_to_ifa = db.get_forcam_uuid_maps()
    assert isinstance(ifa_to_uuid, dict)
    assert isinstance(uuid_to_ifa, dict)


def test_get_operating_state_codes_returns_dataframe_without_raising():
    result = db.get_operating_state_codes("en")
    assert isinstance(result, pd.DataFrame)


def test_get_wpl_info_returns_dataframe_without_raising():
    result = db.get_wpl_info()
    assert isinstance(result, pd.DataFrame)
