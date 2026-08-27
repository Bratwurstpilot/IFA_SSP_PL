# Finding #10: SMTP-Fehler (Auth, Connection) liessen create_and_send_email crashen.
# Fix: try/except um den SMTP-Block, Fehleranzeige statt Absturz.
import smtplib

import pandas as pd
import pytest
import streamlit as st

import config
import email_report


def _minimal_log_args():
    selection = {
        'subline': 'S1 - Sub 1',
        'date_str_de': '30.07.2026',
        'shift': 'Night shift',
        'department': 'LOG',  # nicht in config.PRODUCTION_DEPARTMENTS -> einfacherer LOG-Zweig
        'shift_id': 'night_shift',
    }
    data_meta = {
        'mail': 'team@ifa-group.com',
        'responsible': 'Team Lead',
        'time_till_shift_end': '120 minutes remaining',
    }
    data_general_input = {
        'name': 'Max Mustermann',
        'message': 'Alles ok',
        'kpi_employees_present': 5,
        'kpi_output_nok': 0,
        'kpi_output_ok': 0,
    }
    data_quantity_machine_input = pd.DataFrame()
    data_disturbance_input = pd.DataFrame(columns=[
        'workplace_id', 'source', 'problem', 'start', 'duration_minutes',
        'ssp_comment', 'solution', 'solved'])
    return selection, data_meta, data_general_input, data_quantity_machine_input, data_disturbance_input


class _FakeSMTPLoginFails:
    def __init__(self, host, port):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def ehlo(self):
        pass

    def starttls(self):
        pass

    def login(self, email, pw):
        raise smtplib.SMTPAuthenticationError(535, b"auth failed (simulated)")

    def sendmail(self, *args, **kwargs):
        pass


def test_smtp_failure_does_not_crash_and_shows_error(monkeypatch):
    monkeypatch.setattr(config, "get_credential", lambda key: "dummy-pw")
    monkeypatch.setattr(email_report.smtplib, "SMTP", _FakeSMTPLoginFails)

    errors = []
    monkeypatch.setattr(email_report.st, "error", lambda msg: errors.append(msg))
    monkeypatch.setattr(email_report.st, "success", lambda msg: (_ for _ in ()).throw(AssertionError("success should not be shown on failure")))

    selection, data_meta, data_general_input, data_quantity_machine_input, data_disturbance_input = _minimal_log_args()

    email_report.create_and_send_email(selection, data_meta, "", data_general_input, data_quantity_machine_input, data_disturbance_input)

    assert len(errors) == 1


def test_cc_addresses_outside_ifa_group_are_silently_dropped(monkeypatch):
    # known_issue (kein Crash): externe CC-Adressen werden ohne Hinweis fuer den Absender entfernt.
    monkeypatch.setattr(config, "get_credential", lambda key: "dummy-pw")

    sent = {}

    class _FakeSMTPOK:
        def __init__(self, host, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def ehlo(self):
            pass

        def starttls(self):
            pass

        def login(self, email, pw):
            pass

        def sendmail(self, from_addr, to_addrs, msg):
            sent["to_addrs"] = to_addrs

    monkeypatch.setattr(email_report.smtplib, "SMTP", _FakeSMTPOK)
    monkeypatch.setattr(email_report.st, "success", lambda msg: None)

    selection, data_meta, data_general_input, data_quantity_machine_input, data_disturbance_input = _minimal_log_args()
    email_cc = "ok@ifa-group.com, external@othercompany.com"

    email_report.create_and_send_email(selection, data_meta, email_cc, data_general_input, data_quantity_machine_input, data_disturbance_input)

    assert "ok@ifa-group.com" in sent["to_addrs"]
    assert "external@othercompany.com" not in sent["to_addrs"]
