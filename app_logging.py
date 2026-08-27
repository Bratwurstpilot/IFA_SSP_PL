# Zentrales Logging fuer alle Datenbank- und Forcam-API-Abfragen.
# Schreibt nach Konsole (Streamlit-Terminal) und in ssp_logfile.log im Projektordner.
import logging
import re

import pandas as pd

import config

logger = logging.getLogger("ssp")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    try:
        # BASE_DIR ist ein lokaler Laufwerksbuchstabe (E:\...), der nur auf dem App-Server selbst
        # existiert -- auf Dev-/Testmaschinen (Zugriff nur ueber UNC-Pfad) schlaegt das fehl.
        # Konsolen-Logging reicht fuer Tests/lokale Entwicklung; auf dem Server bleibt die Datei aktiv.
        file_handler = logging.FileHandler(config.BASE_DIR + r"\logs\ssp_logfile.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        logger.warning(f"Could not open log file under {config.BASE_DIR}, logging to console only: {e}")

    logger.propagate = False


def _condense(text):
    return re.sub(r"\s+", " ", text).strip()


def log_and_read_sql(sql, engine, label=""):
    # Zentrale Stelle fuer alle pd.read_sql-Aufrufe: loggt Query + Anzahl zurueckgegebener Zeilen.
    logger.info(f"SQL [{label}]: {_condense(sql)}")
    df = pd.read_sql(sql, engine)
    logger.info(f"SQL [{label}]: {len(df)} row(s) returned")
    return df


def log_write(label, detail=""):
    logger.info(f"WRITE [{label}]: {detail}")


def log_api_request(label, url):
    # client_secret/Passwoerter aus URLs vor dem Loggen maskieren
    safe_url = re.sub(r"(client_secret=)[^&]*", r"\1***", url)
    logger.info(f"API [{label}]: GET {safe_url}")


def log_api_response(label, data_request):
    try:
        total = data_request.get("pagination", {}).get("total")
        logger.info(f"API [{label}]: response total={total}")
    except Exception:
        logger.info(f"API [{label}]: response received (no pagination info)")
