# Integrationstests laufen READ-ONLY gegen die echte DWH/Forcam-Instanz.
# Kein INSERT/UPDATE/DELETE hier -- nur die *_get_*/collect_*-Lesefunktionen werden aufgerufen.
# Nicht erreichbare DB = Test-FAILURE (nicht skip), damit der naechtliche Health-Check das sichtbar meldet.
import pytest
from sqlalchemy import text

import db


@pytest.fixture(scope="session")
def real_engine():
    engine = db.get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.fail(f"DWH nicht erreichbar: {e}")
    return engine
