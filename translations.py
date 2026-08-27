# i18n-Schicht: Englisch (Standard) + Polnisch. Aktive Sprache liegt in st.session_state.
# Polnische Texte sind ein erster Entwurf -- muessen von einem Muttersprachler geprueft werden (siehe Plan).
import streamlit as st

import config

TRANSLATIONS = {
    "app_title": {"en": "IFA Operation Shift Report",  "pl": "IFA Raport zmianowy"},
    "label_date": {"en": "Date:", "pl": "Data:"},
    "label_shift": {"en": "Shift:", "pl": "Zmiana:"},
    "shift_night": {"en": "Night shift", "pl": "Zmiana 3"},
    "shift_early": {"en": "Morning shift", "pl": "Zmiana 1"},
    "shift_late": {"en": "Afternoon shift", "pl": "Zmiana 2"},
    "label_department": {"en": "Department:", "pl": "Obszar:"},
    "label_line": {"en": "Line:", "pl": "Dzial:"},
    "label_subline": {"en": "Subline:", "pl": "Linia:"},
    "info_reload_warning": {"en": "Reloading the data will discard any unsaved changes.", "pl": "Ponowne wczytanie danych spowoduje utratę niezapisanych zmian."},
    "button_load_data": {"en": "Load data for: ", "pl": "Wczytaj dane dla: "},
    "progress_loading": {"en": "Loading data for the shift report...", "pl": "Wczytywanie danych raportu zmianowego..."},
    "progress_meta": {"en": "Collecting meta data...", "pl": "Zbieranie danych meta..."},
    "progress_quantity": {"en": "Calculating reported quantities per machine...", "pl": "Obliczanie zgłoszonych ilości na maszynę..."},
    "progress_disturbance": {"en": "Searching for machine disturbances...", "pl": "Wyszukiwanie zakłóceń maszyn..."},
    "progress_kpi": {"en": "Calculating KPIs...", "pl": "Obliczanie wskaźników KPI..."},
    "subheader_general_info": {"en": "General Information", "pl": "Informacje ogólne"},
    "label_shift_leader": {"en": "Shift leader:", "pl": "Kierownik zmiany:"},
    "placeholder_enter_name": {"en": "Please enter name...", "pl": "Proszę wpisać imię i nazwisko..."},
    "text_team_leader": {"en": "Team leader: ", "pl": "Lider zespołu: "},
    "text_time_remaining": {"en": "Time until end of shift: ", "pl": "Czas do końca zmiany: "},
    "subheader_kpis": {"en": "KPIs", "pl": "KPI"},
    "kpi_output": {"en": "Output", "pl": "Sztuki OK"},
    "kpi_scrap": {"en": "Scrap", "pl": "Sztuki NOK"},
    "kpi_employees_present": {"en": "Employees present", "pl": "Obecni pracownicy"},
    "kpi_output_per_employee": {"en": "Output per employee", "pl":"Wydajność na pracownika"},
    "col_metric": {"en": "Metric", "pl": "Wskaźnik"},
    "col_value": {"en": "Value", "pl": "Wartość"},
    "subheader_quantity_per_machine": {"en": "Output per machine", "pl": "Produkcja na maszynę"},
    "col_workplace": {"en": "Workplace", "pl": "Miejsce pracy"},
    "col_machine": {"en": "Machine", "pl": "Maszyna"},
    "col_output_relevant": {"en": "Output relevant", "pl": "Istotne dla produkcji"},
    "col_ok": {"en": "OK", "pl": "OK"},
    "col_nok": {"en": "NOK", "pl": "NOK"},
    "col_production_time": {"en": "Production time", "pl": "Czas produkcji"},
    "col_halt_time": {"en": "Loss time", "pl": "Czas strat"},
    "col_setup_time": {"en": "Setup time", "pl": "Czas przezbrojenia"},
    "col_comment": {"en": "Comment", "pl": "Komentarz"},
    "subheader_machine_disturbances": {"en": "Machine disturbances", "pl": "Postoje maszyn"},
    "col_source": {"en": "Source", "pl": "Źródło"},
    "col_problem_description": {"en": "Problem description", "pl": "Opis problemu"},
    "col_disturbance_start": {"en": "Disturbance start", "pl": "Początek zakłócenia"},
    "col_duration_minutes": {"en": "Duration in minutes", "pl": "Czas trwania w minutach"},
    "col_duration_min_short": {"en": "Duration [min]", "pl": "Czas [min]"},
    "col_forcam_comment": {"en": "Forcam comment", "pl": "Komentarz Forcam"},
    "col_ssp_comment": {"en": "SSP comment", "pl": "Komentarz SSP"},
    "col_action_taken": {"en": "Action taken", "pl": "Podjęte działanie"},
    "col_done": {"en": "Done", "pl": "Zrobione"},
    "subheader_personnel_info": {"en": "Personnel info", "pl": "Informacje o personelu"},
    "kpi_employees_present_shift": {"en": "Employees present (shift)", "pl": "Obecni pracownicy (zmiana)"},
    "kpi_sick": {"en": "Sick (day)", "pl": "Chorobowe (dzień)"},
    "kpi_vacation": {"en": "Vacation (day)", "pl": "Urlop (dzień)"},
    "subheader_overview": {"en": "Overview", "pl": "Przegląd"},
    "col_area": {"en": "Area", "pl": "Obszar"},
    "col_problem": {"en": "Problem", "pl": "Problem"},
    "subheader_handover_message": {"en": "Add message for shift handover", "pl": "Dodatkowe informacje do przekazania zmiany"},
    "label_handover_message": {"en": "Shift handover message", "pl": "Wiadomość przekazania zmiany"},
    "placeholder_handover_message": {"en": "If needed, enter a message for the shift handover here", "pl": "Jeśli potrzeba, wpisz tutaj wiadomość do przekazania zmiany"},
    "subheader_save": {"en": "Save", "pl": "Zapisz"},
    "button_save_data": {"en": "Save data", "pl": "Zapisz dane"},
    "error_name_required": {"en": "Please enter a name! The shift report was not saved.", "pl": "Proszę wpisać imię i nazwisko! Raport zmianowy nie został zapisany."},
    "spinner_saving": {"en": "Saving data...", "pl": "Zapisywanie danych..."},
    "success_saved": {"en": "Data was saved successfully.", "pl": "Dane zostały pomyślnie zapisane."},
    "subheader_send_email": {"en": "Send Email", "pl": "Wyślij e-mail"},
    "text_mail_distribution": {"en": "Email distribution list used: ", "pl": "Użyta lista dystrybucyjna e-mail: "},
    "label_cc_email": {"en": "CC email address:", "pl": "Adres e-mail CC:"},
    "placeholder_cc_email": {"en": "For multiple recipients, separate addresses with a comma. e.g.: max.mustermann@ifa-group.com", "pl": "W przypadku wielu odbiorców rozdziel adresy przecinkiem. np.: max.mustermann@ifa-group.com, jane.doe@ifa-group.com"},
    "info_email_disabled": {"en": 'To send the shift report, the data must first be saved using the "Save data" button.', "pl": 'Aby wysłać raport zmianowy, dane muszą najpierw zostać zapisane za pomocą przycisku "Zapisz dane".'},
    "button_send_email": {"en": "Send email", "pl": "Wyślij e-mail"},

    # E-Mail-Report (email_report.py)
    "email_row_shift_leader": {"en": "Shift leader", "pl": "Kierownik zmiany"},
    "email_row_team_leader": {"en": "Team leader", "pl": "Lider zespołu"},
    "email_row_time_remaining": {"en": "Time until end of shift", "pl": "Czas do końca zmiany"},
    "email_short_disturbance_note": {"en": "Machine disturbances lasting less than 10 minutes are not shown.", "pl": "Zakłócenia maszyn trwające krócej niż 10 minut nie są wyświetlane."},
    "email_problem_reports_header": {"en": "Problem reports", "pl": "Zgłoszenia problemów"},
    "email_footer_auto_generated": {"en": "This is an automatically generated email.", "pl": "To jest automatycznie wygenerowany e-mail."},
    "email_footer_contact": {"en": "If you have questions or notice errors, please contact the ITS team.", "pl": "W przypadku pytań lub błędów prosimy o kontakt z zespołem ITS."},
    "success_email_sent": {"en": "Email sent successfully!", "pl": "E-mail wysłany pomyślnie!"},
    "bool_yes": {"en": "Yes", "pl": "Tak"},
    "bool_no": {"en": "No", "pl": "Nie"},
    "info_manual_employee_entry": {"en": "No automatic employee data available for this plant. Please enter the numbers manually.", "pl": "Brak automatycznych danych o pracownikach dla tego zakładu. Proszę wpisać liczby ręcznie."},
    "shift_ended": {"en": "Shift ended", "pl": "Zmiana zakończona"},
    "minutes_remaining_suffix": {"en": " minutes remaining", "pl": " minut pozostało"},
    "no_data_for_plant": {"en": "No master data found for this plant. Please contact IT support.", "pl": "Nie znaleziono danych podstawowych dla tego zakładu. Skontaktuj się z działem IT."},
    "error_email_failed": {"en": "Sending the email failed. Please try again or contact IT support.", "pl": "Wysłanie e-maila nie powiodło się. Spróbuj ponownie lub skontaktuj się z działem IT."},
}

LANGUAGE_LABELS = {"en": "English", "pl": "Polski"}


def get_language():
    return st.session_state.get("language", config.DEFAULT_LANGUAGE)


def set_language(language):
    st.session_state.language = language


def t(key):
    language = get_language()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(language, entry.get(config.DEFAULT_LANGUAGE, key))
