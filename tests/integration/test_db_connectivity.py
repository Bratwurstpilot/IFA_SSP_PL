# Reine Konnektivitaetspruefung -- die eigentliche Pruefung passiert bereits in der
# real_engine-Fixture (pytest.fail bei Unreachable). Wenn dieser Test laeuft, war der Connect ok.
def test_dwh_connection_ok(real_engine):
    assert real_engine is not None
