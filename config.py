# Zentrale Konstanten und Zugriff auf credentials.json
#
# Dieses Verzeichnis ist der "Clone and Own"-Klon fuer das polnische Werk.
# Alle Werte hier sind TODO(PL): sobald das Werk-Team echte Polen-Werksdaten
# liefert, die als "-- HdlP Platzhalter, bis Polen-Daten da sind --" markierten
# Werte ersetzen. Bis dahin sind sie bewusst identisch zu HdlP, damit die App
# fuer Regressionstests unveraendert funktioniert.
import json

# Runtime-Basisverzeichnis
BASE_DIR = r"E:\01_PRODUCTIVE\webapp_SSP_Polska"
DATA_DIR = BASE_DIR + r"\data"
CREDENTIALS_PATH = DATA_DIR + r"\credentials.json"
META_DATA_PATH = DATA_DIR + r"\meta_data.csv"
# meta_data.csv der Poland-Klon-Kopie ist noch die HdlP-Datei (latin1). Sobald eine echte
# Polen-Version angelegt wird: UTF-8 verwenden (siehe meta.py).
META_DATA_ENCODING = 'latin1'  # -- HdlP Platzhalter, bis Polen-Daten da sind (dann 'utf-8') --


def get_credential(key):
    with open(CREDENTIALS_PATH) as json_file:
        return json.load(json_file)[key]


# SQL Settings (Passwort wird erst in db.get_engine() geladen)
# Gleicher zentraler DWH-Server wie HdlP -- Polen bekommt eigenen plant-Code (siehe PLANT_ID unten)
SQL_SETTINGS = {
    'server': 'S298A150x\\DWH',
    'database': 'DWH',
    'user': 'dwh_user'}

# TODO(PL): echten plant-Code fuer Polen von DWH-Team eintragen (dim.workplace.plant)
PLANT_ID = 'UjaP'  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Forcam API -- gleiche Instanz wie HdlP, keine Aenderung noetig
FORCAM_CLIENT_ID = "IT_TEST"
FORCAM_TOKEN_URL = "https://force:25443/ffauth/oauth2.0/accessToken"
FORCAM_BASE_URL = "https://force:24443/ffwebservices/customized/v3/ifareports/"
# War im Original als "Europe/Belgrade" hartkodiert (vermutlich ein Bug, zufaellig
# gleicher UTC-Offset wie Berlin). Fuer den Polen-Klon korrekt benannt: gleicher Offset wie Berlin.
FORCAM_TIMEZONE = "Europe/Warsaw"

# E-Mail
MAIL_HOST = "webmail.ifa-group.com"
MAIL_PORT = 587
MAIL_SENDER = "reporting_its.service@ifa-group.com"

# UI-Sprache: Default Polnisch, umschaltbar auf Englisch (siehe translations.py)
DEFAULT_LANGUAGE = "pl"
AVAILABLE_LANGUAGES = ["en", "pl"]

# Abteilungen mit voller Forcam-Integration (Mengen/Stoerungen pro Maschine).
# Alle anderen Abteilungen laufen im "Logistik"-Modus (manuelle Bereichs-Erfassung, siehe LOGISTICS_WORKPLACES).
# TODO(PL): pruefen, ob Polens Abteilungsnamen identisch sind oder angepasst werden muessen.
PRODUCTION_DEPARTMENTS = ['OMA']  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Bereiche fuer den Logistik-Modus (Abteilungen ausserhalb PRODUCTION_DEPARTMENTS)
# TODO(PL): Polens Bereichsliste eintragen, sobald verfuegbar. Leer lassen wuerde die
# Bereichs-Auswahl im Logistik-Modus leer machen.
LOGISTICS_WORKPLACES = ['NULL']  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# line_id in [DWH].[fact_production].[shopfloor_employees], unter dem die Logistik-Abteilung
# als Gesamtsumme (Anwesenheit/Urlaub/Krankheit) gefuehrt wird.
LOGISTICS_LINE_ID = 'LOG'  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# HdlP-Fabriklayout-Sonderregeln -- fuer Polen vermutlich leer/anders, siehe TABLES.md / Plan.
# TODO(PL): pruefen, ob und welche aequivalenten Sonderregeln Polen braucht.

# Sublinien, deren line_id-Bestandteile fuer die Mitarbeiterzaehlung zusammengefasst werden
# {subline_id: [line_id, ...]}
COMBINED_LINES = {}  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Workplace-IDs, deren Mengen aus SAP statt Forcam kommen (siehe TABLES.md: Job "02_3_OP_reported_quantities")
SAP_FED_WORKPLACES = []  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Sublinien, die komplett per SAP statt Forcam laufen
SAP_FED_SUBLINES = []  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Prozess-/Linien-Namen, die aus der Ausbringungsrelevanz-Berechnung ausgeschlossen werden
EXCLUDED_LINE_NAMES = []  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Manche Werke haben keine [DWH].[fact_production].[shopfloor_employees]-Daten.
# Wenn False: Mitarbeiterzahlen (Anwesend/Krank/Urlaub) werden nicht aus dem DWH geladen,
# sondern bleiben leer -- Schichtleiter traegt sie manuell im KPI-Editor ein (Feld ist editierbar).
SHOPFLOOR_EMPLOYEES_AVAILABLE = False  # -- HdlP Platzhalter, bis Polen-Daten da sind (Polen: False) --

# Fallback-Kontakt, falls meta_data.csv keinen Treffer fuer die gewaehlte Subline hat
FALLBACK_RESPONSIBLE = 'M. Tiszbierek'  # -- HdlP Platzhalter, bis Polen-Daten da sind --
FALLBACK_CONTACT_MAIL = 'Marco.Tiszbierek@ifa-group.com'  # -- HdlP Platzhalter, bis Polen-Daten da sind --

# Naechtlicher Health-Check (Testsuite + Mail, siehe health_check.py)
HEALTH_CHECK_REPORT_NAME = "SSP Polska"
HEALTH_CHECK_RECIPIENTS = ['frederic.schiller@ifa-group.com']  # TODO(PL): Empfaenger-Verteiler eintragen, bevor der Task Scheduler-Job aktiviert wird