# Naechtlicher Health-Check: fuehrt Unit- und Integrationstests aus und verschickt eine
# Zusammenfassung per Mail. Gedacht fuer Windows Task Scheduler (siehe health_check.bat),
# taeglich 03:00 Uhr.
import datetime
import subprocess
import sys
import xml.etree.ElementTree as ET
import smtplib
from email.mime.text import MIMEText

import config

BASE_DIR = config.BASE_DIR
UNIT_JUNIT_PATH = BASE_DIR + r"\logs\unit_result.xml"
INTEGRATION_JUNIT_PATH = BASE_DIR + r"\logs\integration_result.xml"


def run_suite(path, junit_path):
    return subprocess.run(
        [sys.executable, "-m", "pytest", path, f"--junitxml={junit_path}", "-q"],
        capture_output=True, text=True, cwd=BASE_DIR,
    )


def _testcase_id(testcase):
    # JUnit-XML classname ist z.B. "tests.unit.test_db_lookups" -- zu einem
    # lesbaren pytest-Nodeid zusammensetzen: tests/unit/test_db_lookups.py::test_name
    classname = testcase.get("classname", "")
    name = testcase.get("name", "")
    path = classname.replace(".", "/") + ".py" if classname else "?"
    return f"{path}::{name}"


def parse_junit(junit_path):
    """Liefert Testergebnisse gruppiert nach Status (passed/failed/errored/xfailed)."""
    try:
        tree = ET.parse(junit_path)
    except (ET.ParseError, FileNotFoundError):
        # Testlauf konnte kein gueltiges JUnit-XML schreiben (z.B. Sammel-/Importfehler
        # vor dem ersten Test) -- als leeres Ergebnis werten, damit die Mail trotzdem
        # verschickt wird und der Fehlertext im subprocess-Output (siehe main()) sichtbar bleibt.
        return {"passed": [], "failed": [], "errored": [], "xfailed": []}

    root = tree.getroot()
    result = {"passed": [], "failed": [], "errored": [], "xfailed": []}
    for testcase in root.iter("testcase"):
        tid = _testcase_id(testcase)
        if testcase.find("failure") is not None:
            result["failed"].append(tid)
        elif testcase.find("error") is not None:
            result["errored"].append(tid)
        elif testcase.find("skipped") is not None:
            # xfail_strict=true (pytest.ini) sorgt dafuer, dass hier nur echte xfail-Tests
            # landen -- ein unerwarteter XPASS wuerde stattdessen als failure auftauchen.
            result["xfailed"].append(tid)
        else:
            result["passed"].append(tid)
    return result


def build_email_body(unit_result, integration_result, report_name):
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

    lines = [f"{report_name} Health-Check - {now_str}", ""]
    lines += _format_section("Unit-Tests", unit_result)
    lines.append("")
    lines += _format_section("Integrationstests (echte DB)", integration_result)

    return "\n".join(lines)


def _format_section(title, result):
    passed, failed, errored, xfailed = result["passed"], result["failed"], result["errored"], result["xfailed"]
    total = len(passed) + len(failed) + len(errored) + len(xfailed)
    n_passed = len(passed)

    lines = [f"== {title} ==", f"{title}: {n_passed}/{total} bestanden"]
    if xfailed:
        lines.append(f"davon {len(xfailed)} bekannte Fehler (xfail)")
    lines.append("")

    if failed or errored:
        lines.append("Fehlgeschlagen:")
        for tid in failed + errored:
            lines.append(f"  [FAIL] {tid}")
        lines.append("")

    if xfailed:
        lines.append("Bekannte Fehler (xfail, siehe Audit-Findings):")
        for tid in xfailed:
            lines.append(f"  [xfail] {tid}")
        lines.append("")

    if passed:
        lines.append("Bestanden:")
        for tid in passed:
            lines.append(f"  [ok] {tid}")

    return lines


def send_email(body, recipients, report_name):
    if not recipients:
        raise ValueError("HEALTH_CHECK_RECIPIENTS ist leer -- Mail wird nicht verschickt.")

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = config.MAIL_SENDER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"{report_name} Health-Check"

    with smtplib.SMTP(config.MAIL_HOST, config.MAIL_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(config.MAIL_SENDER, config.get_credential("mailuser"))
        server.sendmail(config.MAIL_SENDER, recipients, msg.as_string())


def main():
    unit_run = run_suite("tests/unit", UNIT_JUNIT_PATH)
    integration_run = run_suite("tests/integration", INTEGRATION_JUNIT_PATH)

    unit_result = parse_junit(UNIT_JUNIT_PATH)
    integration_result = parse_junit(INTEGRATION_JUNIT_PATH)

    body = build_email_body(unit_result, integration_result, config.HEALTH_CHECK_REPORT_NAME)

    print(body)

    def _total(result):
        return len(result["passed"]) + len(result["failed"]) + len(result["errored"]) + len(result["xfailed"])

    # Exitcode 1 bedeutet bei pytest normalerweise "Tests fehlgeschlagen" -- ABER
    # "python -m pytest" liefert ebenfalls Exitcode 1, wenn pytest selbst fehlt/nicht
    # startet (z.B. "No module named pytest"). 0 Tests insgesamt heisst: der Lauf ist gar nicht
    # bis zum JUnit-Report gekommen -- dann IMMER stdout/stderr zeigen, unabhaengig vom Exitcode.
    if unit_run.returncode not in (0, 1) or _total(unit_result) == 0:
        print("--- Unit-Test-Lauf: kein gueltiges Ergebnis ---", file=sys.stderr)
        print(unit_run.stdout, file=sys.stderr)
        print(unit_run.stderr, file=sys.stderr)
    if integration_run.returncode not in (0, 1) or _total(integration_result) == 0:
        print("--- Integrationstest-Lauf: kein gueltiges Ergebnis ---", file=sys.stderr)
        print(integration_run.stdout, file=sys.stderr)
        print(integration_run.stderr, file=sys.stderr)

    try:
        send_email(body, config.HEALTH_CHECK_RECIPIENTS, config.HEALTH_CHECK_REPORT_NAME)
    except Exception as e:
        # Health-Check darf nicht an Finding #10 (unguarded SMTP) selbst scheitern --
        # Fehler wird geloggt/ausgegeben, der Prozess beendet sich aber mit Exitcode != 0,
        # damit Task Scheduler den Lauf sichtbar als fehlgeschlagen protokolliert.
        print(f"Health-Check-Mail konnte nicht verschickt werden: {e}", file=sys.stderr)
        sys.exit(1)

    # pytest gibt Exitcode 1 zurueck, wenn mindestens ein Test fehlgeschlagen ist --
    # das soll den Health-Check-Lauf selbst ebenfalls als "nicht ok" markieren.
    if unit_run.returncode != 0 or integration_run.returncode != 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
