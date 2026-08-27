# Finding #15: Aendert man ein Auswahl-Widget (z.B. Subline), ohne erneut auf "Load data" zu
# klicken, bleibt st.session_state['selection'] auf der alten Auswahl stehen -- das Dropdown
# zeigt bereits die neue Subline, die geladenen Daten gehoeren aber noch zur alten. known_issue
# (kein Crash), aber ein reales Datenintegritaets-/UX-Risiko fuer Schichtleiter.
import pandas as pd
from streamlit.testing.v1 import AppTest

import data_disturbances
import data_general
import data_quantities
import db
import meta


def _wire_up_mocks(monkeypatch):
    hierarchy = {"OMA": {"L1 - Line 1": {"SubA - Sub A": ["W1"], "SubB - Sub B": ["W2"]}}}
    monkeypatch.setattr(db, "get_hierarchy", lambda: hierarchy)
    monkeypatch.setattr(db, "get_wpl_info", lambda: pd.DataFrame(columns=['workplace_id', 'process', 'machine_name', 'output_relevant', 'line_name']))
    monkeypatch.setattr(meta, "collect_data_meta_information", lambda selection: {
        'responsible': 'Team Lead', 'mail': 'team@ifa-group.com', 'time_till_shift_end': '60 minutes remaining'})
    monkeypatch.setattr(data_quantities, "collect_data_quantity_machine", lambda selection, pb, txt: pd.DataFrame([{
        'workplace_id': 'W1', 'machine_name': 'M1', 'output_relevant': True, 'OK': 1, 'NOK': 0,
        'production_time': '00:10', 'halt_time': '00:00', 'setup_time': '00:00', 'comment': ''}]))
    monkeypatch.setattr(data_disturbances, "collect_data_disturbance", lambda selection, pb, txt: pd.DataFrame(columns=[
        'workplace_id', 'machine_name', 'source', 'problem', 'start', 'duration_minutes',
        'sf_comment', 'ssp_comment', 'solution', 'solved']))
    monkeypatch.setattr(data_general, "collect_data_general", lambda selection, dqm: {
        'name': '', 'message': '', 'kpi_output_ok': 1, 'kpi_output_nok': 0,
        'kpi_employees_present': 0, 'kpi_output_per_employee': 0})


def test_changing_subline_without_reload_leaves_loaded_selection_stale(monkeypatch):
    _wire_up_mocks(monkeypatch)

    at = AppTest.from_file("main_v3_1.py")
    at.run()
    assert not at.exception

    # Sprach-Selectbox nutzt format_func (Anzeige "English"/"Polski" != interner Wert "en"/"pl").
    # AppTest muss dieses Widget einmal explizit "anfassen", sonst bricht die interne
    # Index-Aufloesung bei jedem weiteren .run() mit ValueError ab (Streamlit-Testframework-
    # Eigenheit, kein App-Bug).
    at.selectbox[0].select("English").run()

    # Widget-Reihenfolge in ui.py: language, shift, department, line, subline
    subline_selectbox_index = 4
    at.selectbox[subline_selectbox_index].select("SubA - Sub A").run()
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["selection"]["subline"] == "SubA - Sub A"

    # Subline aendern, OHNE erneut auf "Load data" zu klicken
    at.selectbox[subline_selectbox_index].select("SubB - Sub B").run()
    assert not at.exception

    assert at.selectbox[subline_selectbox_index].value == "SubB - Sub B"
    # known_issue: die geladenen Daten haengen noch an der alten Subline
    assert at.session_state["selection"]["subline"] == "SubA - Sub A"
