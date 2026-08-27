# Finding #14: meta_data.csv wird ohne Existenzpruefung gelesen (FileNotFoundError bei
# fehlender/verschobener Datei) und aktuell mit latin1 statt utf-8 dekodiert -- polnische
# Sonderzeichen (a, e, l...) werden dabei falsch interpretiert.
import datetime

import pytest

import config
import meta


def _selection():
    return {'subline': 'NICHT_VORHANDEN', 'shift_id': 'early_shift', 'date': datetime.date(2026, 7, 30)}


@pytest.mark.xfail(strict=True, reason="Finding #14: meta_data.csv fehlt -> FileNotFoundError wird nicht abgefangen")
def test_collect_data_meta_information_missing_csv_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "META_DATA_PATH", str(tmp_path / "does_not_exist.csv"))
    meta.collect_data_meta_information(_selection())


def test_latin1_encoding_mangles_polish_diacritics(tmp_path):
    # known_issue: solange config.META_DATA_ENCODING == 'latin1' ist, werden polnische
    # Sonderzeichen beim Einlesen mit UTF-8-Bytes falsch dekodiert. Dieser Test dient als
    # Stolperdraht: sobald META_DATA_ENCODING auf 'utf-8' umgestellt wird, faellt er positiv aus
    # und bestaetigt damit, dass die Umstellung konsistent vorgenommen wurde.
    original_text_with_diacritics = "Zakład produkcyjny w Łodzi"
    csv_path = tmp_path / "meta_data_utf8.csv"
    csv_path.write_text(
        f"subline_id;responsible;email_verteiler\nS1;{original_text_with_diacritics};team@ifa-group.com\n",
        encoding="utf-8",
    )

    read_with_configured_encoding = csv_path.read_text(encoding=config.META_DATA_ENCODING)

    if config.META_DATA_ENCODING == "latin1":
        assert original_text_with_diacritics not in read_with_configured_encoding
    else:
        assert original_text_with_diacritics in read_with_configured_encoding
