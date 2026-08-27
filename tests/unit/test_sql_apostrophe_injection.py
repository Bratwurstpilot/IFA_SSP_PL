# Finding #6: SQL wird per f-String gebaut, Werte nicht escaped/parametrisiert. Ein Apostroph
# in einem eingesetzten Wert (z.B. PLANT_ID, Linienname) wuerde die WHERE-Klausel syntaktisch
# brechen. known_issue: bricht nur bei echtem SQL Server (kein Crash in Python selbst), deshalb
# hier nur ueber einen SQL-Spion nachgewiesen, nicht gegen eine echte DB getestet.
import pandas as pd

import config
import db


def test_get_hierarchy_builds_syntactically_broken_sql_with_apostrophe_in_plant_id(monkeypatch, mock_engine, spy_read_sql):
    monkeypatch.setattr(config, "PLANT_ID", "Uja'P")
    # Leere, aber mit Spalten versehene Ergebnisse -- wie eine echte (leere) DB-Antwort,
    # nicht wie ein komplett spaltenloses pd.DataFrame().
    spy_read_sql.queue([
        pd.DataFrame(columns=['department', 'line_id', 'subline_id']),
        pd.DataFrame(columns=['workplace_id', 'line_id', 'subline_id']),
    ])

    db.get_hierarchy()

    assert spy_read_sql.calls, "get_hierarchy hat keine SQL-Abfrage ausgefuehrt"
    sql = spy_read_sql.calls[0]
    # Ungerade Anzahl Apostrophe = eine WHERE-Bedingung ist nicht mehr korrekt geschlossen
    assert sql.count("'") % 2 != 0
