# Finding #1: leere db.get_hierarchy() liess die App mit KeyError/IndexError abstuerzen.
# Fix in ui.py: Guard nach dem hierarchy-Load zeigt eine Warnung und stoppt sauber (st.stop()).
import pytest
from streamlit.testing.v1 import AppTest

import db


def test_empty_hierarchy_shows_warning_instead_of_crashing(monkeypatch):
    monkeypatch.setattr(db, "get_hierarchy", lambda: {})

    # main_v3_1.py (Entrypoint) statt ui.py direkt: ui.py definiert nur main(),
    # der Aufruf passiert erst im Entrypoint (Streamlit fuehrt das Skript als __main__ aus)
    at = AppTest.from_file("main_v3_1.py")
    at.run()

    assert not at.exception, f"App crashed instead of showing the guard warning: {at.exception}"
    assert len(at.warning) >= 1


def test_nonempty_hierarchy_still_renders_department_selectbox(monkeypatch):
    fake_hierarchy = {"OMA": {"L1 - Line 1": {"L1 - Line 1": ["W1", "W2"]}}}
    monkeypatch.setattr(db, "get_hierarchy", lambda: fake_hierarchy)

    at = AppTest.from_file("main_v3_1.py")
    at.run()

    assert not at.exception
    assert len(at.selectbox) >= 1
