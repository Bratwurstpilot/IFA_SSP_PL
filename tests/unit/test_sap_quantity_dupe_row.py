# Finding #17: Wenn reported_quantities_workplace mehrere Zeilen fuer denselben workplace_id
# liefert (z.B. Datenfehler im SAP-Feed), gewinnt stillschweigend die erste Zeile (.values[0]).
import datetime

import pandas as pd

import data_quantities
import db


def test_insert_sap_quantity_silently_uses_first_matching_row(monkeypatch, mock_engine, spy_read_sql):
    spy_read_sql.result = pd.DataFrame([
        {'workplace_id': 'W1', 'yield_early_shift': 100, 'scrap_early_shift': 1},
        {'workplace_id': 'W1', 'yield_early_shift': 200, 'scrap_early_shift': 2},
    ])

    original_df = pd.DataFrame([{'workplace_id': 'W1', 'OK': 0, 'NOK': 0}])
    selection = {'date': datetime.date(2026, 7, 30), 'shift_id': 'early_shift'}

    result = data_quantities.insert_data_quantity_machine_sap(selection, "'W1'", original_df)

    assert result.loc[0, 'OK'] == 100
    assert result.loc[0, 'NOK'] == 1
