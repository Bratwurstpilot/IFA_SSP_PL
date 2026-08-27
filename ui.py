# Streamlit UI: Seitenaufbau, Datenladen, Formular, Speichern, E-Mail-Versand
import datetime
import time

import pandas as pd
import streamlit as st

import config
import db
import meta
import data_general
import data_quantities
import data_disturbances
import email_report
import translations
import app_logging
from translations import t


# Streamlit app
def main():
    # Config
    st.set_page_config(layout="wide", page_title="IFA - SSP")

    # Initialize Session States
    if "disable_email" not in st.session_state:
        st.session_state.disable_email = True

    if "language" not in st.session_state:
        st.session_state.language = config.DEFAULT_LANGUAGE

    if "selection" in st.session_state:
        selection = st.session_state.selection

    # Stammdaten (gecacht)
    hierarchy = db.get_hierarchy()

    if not hierarchy:
        st.warning(t("no_data_for_plant"))
        st.stop()

    # Language switch
    translations.set_language(st.selectbox("Language / Język", config.AVAILABLE_LANGUAGES, format_func=lambda l: translations.LANGUAGE_LABELS[l], index=config.AVAILABLE_LANGUAGES.index(translations.get_language())))

    # Title
    st.title(t("app_title"))

    # Select date
    selected_date = st.date_input(t("label_date"), format='DD.MM.YYYY', max_value=datetime.date.today(), min_value=datetime.date.today()-datetime.timedelta(days=180))
    selected_date_str_de = selected_date.strftime('%d.%m.%Y')

    # Select Shift (Anzeige uebersetzt, interne shift_id bleibt stabil ueber Index statt Text-Vergleich)
    shift_ids = ['night_shift', 'early_shift', 'late_shift']
    shift_labels = [t("shift_night"), t("shift_early"), t("shift_late")]
    selected_shift = st.selectbox(t("label_shift"), shift_labels, index=meta.preselect_shift())
    selected_shift_id = shift_ids[shift_labels.index(selected_shift)]

    # Select Department
    selected_department = st.selectbox(t("label_department"), list(hierarchy.keys()))

    # Select Line
    selected_line = st.selectbox(t("label_line"), list(hierarchy[selected_department].keys()))

    # Select Subline
    selected_subline = st.selectbox(t("label_subline"), list(hierarchy[selected_department][selected_line].keys()))

    # Load Data
    if "data" in st.session_state:
        st.info(t("info_reload_warning"))

    if st.button(t("button_load_data") + selected_shift + ' - ' + selected_subline):

        # Set workplace_list for selected subline
        if selected_department in config.PRODUCTION_DEPARTMENTS:
            selected_workplaces = list(hierarchy[selected_department][selected_line][selected_subline])
        else:
            selected_workplaces = config.LOGISTICS_WORKPLACES

        # Preselect Workplaces OP
        selected_workplaces_list = ""
        for wpl in selected_workplaces:
            selected_workplaces_list += "'" + wpl + "',"
        selected_workplaces_list = selected_workplaces_list[:-1]

        # Collect Selection
        selection = {
            'date': selected_date,
            'date_str_de': selected_date_str_de,
            'shift': selected_shift,
            'shift_id': selected_shift_id,
            'department': selected_department,
            'line': selected_line,
            'subline': selected_subline,
            'workplaces': selected_workplaces,
            'workplaces_list': selected_workplaces_list}

        st.session_state.selection = selection

        # Load Data for OP
        if selected_department in config.PRODUCTION_DEPARTMENTS:
            # Running Data Requests
            app_logging.logger.info("########## LOADING DATA ###################")
            app_logging.logger.info("Selection: " + str(selection))

            progressbar_text = t("progress_loading")
            progress_completion = 0
            progressbar = st.progress(progress_completion, text=progressbar_text)

            # Meta Data
            progressbar_text = t("progress_meta")
            progressbar.progress(progress_completion, text=progressbar_text)
            data_meta = meta.collect_data_meta_information(selection)
            progress_completion = 0.1

            # Quantitiy
            progressbar_text = t("progress_quantity")
            progressbar.progress(progress_completion, text=progressbar_text)
            data_quantity_machine = data_quantities.collect_data_quantity_machine(selection, progressbar, progressbar_text)
            progress_completion = 0.5

            # Disturbance
            progressbar_text = t("progress_disturbance")
            progressbar.progress(progress_completion, text=progressbar_text)
            data_disturbance = data_disturbances.collect_data_disturbance(selection, progressbar, progressbar_text)
            progress_completion = 0.9

            # General Data
            progressbar_text = t("progress_kpi")
            progressbar.progress(progress_completion, text=progressbar_text)
            data_general_data = data_general.collect_data_general(selection, data_quantity_machine)
            data_general_input = data_general_data
            progress_completion = 100

            # Close Progress Bar
            progressbar.progress(progress_completion, text=progressbar_text)
            time.sleep(1)
            progressbar.empty()

            st.session_state.data = {
                'data_meta': data_meta,
                'data_quantity_machine': data_quantity_machine,
                'data_disturbance': data_disturbance,
                'data_general': data_general_data,
                'data_general_input': data_general_input
            }

        # Load Data for LOG
        else:
            # Dummy DF
            data_quantity_machine = pd.DataFrame([{
                "workplace_id": '1',
                "output_relevant": False,
                "OK": 0,
                "NOK": 0}])

            data_disturbance = pd.DataFrame({
                'workplace_machine': [],
                'source': [],
                'problem': [],
                'start': [],
                'duration_minutes': [],
                'ssp_comment': [],
                'solution': [],
                'solved': []})

            data_disturbance['start'] = pd.to_datetime(data_disturbance['start'])
            data_disturbance['start'] = data_disturbance['start'].dt.time
            data_disturbance['solved'] = data_disturbance['solved'].astype(bool)
            data_disturbance['ssp_comment'] = data_disturbance['ssp_comment'].astype(str)
            data_disturbance['solution'] = data_disturbance['solution'].astype(str)

            # Load Data
            data_meta = meta.collect_data_meta_information(selection)
            data_general_data = data_general.collect_data_general(selection, data_quantity_machine)
            data_general_input = data_general_data
            data_disturbance = data_disturbances.collect_data_disturbance_log(selection)

            st.session_state.data = {
                'data_meta': data_meta,
                'data_quantity_machine': data_quantity_machine,
                'data_disturbance': data_disturbance,
                'data_general': data_general_data,
                'data_general_input': data_general_input}

            app_logging.logger.info(str(st.session_state))


    # Show Form for Data Input
    if "data" in st.session_state:
        with st.form("ssp_form", clear_on_submit=False):
            # Get Data from session state
            data_meta = st.session_state.data['data_meta']
            data_quantity_machine = st.session_state.data['data_quantity_machine']
            data_disturbance = st.session_state.data['data_disturbance']
            data_general_data = st.session_state.data['data_general']
            data_general_input = st.session_state.data['data_general_input']

            # Header
            st.header('SSP: ' + selection['subline'] + ' - ' + selection['date'].strftime('%d.%m.%Y') + ' - ' + selection['shift'])
            st.divider()

            # Meta Data
            st.subheader(t("subheader_general_info"))
            data_schiko_name_input = st.text_input(label=t("label_shift_leader"), placeholder=t("placeholder_enter_name"), value=data_general_data['name'], max_chars=50)
            st.text(t("text_team_leader") + data_meta['responsible'])
            st.text(t("text_time_remaining") + data_meta['time_till_shift_end'])
            st.divider()

            # Display for OP
            if st.session_state.selection['department'] in config.PRODUCTION_DEPARTMENTS:
                # KPI's
                st.subheader(t("subheader_kpis"))
                if not config.SHOPFLOOR_EMPLOYEES_AVAILABLE:
                    st.info(t("info_manual_employee_entry"))
                kpi = {t("col_metric"): [t("kpi_output"), t("kpi_scrap"), t("kpi_employees_present"), t("kpi_output_per_employee")],
                        t("col_value"): [data_general_data['kpi_output_ok'], data_general_data['kpi_output_nok'], data_general_data['kpi_employees_present'], round(data_general_data['kpi_output_per_employee'], 1)]}
                data_df_kpi = pd.DataFrame(kpi)
                data_kpi_input = st.data_editor(data_df_kpi, hide_index=True, disabled=[t("col_metric")])

                st.divider()

                # Machine and Materialnumber
                st.subheader(t("subheader_quantity_per_machine"))
                data_quantity_machine.sort_values(by=['output_relevant', 'workplace_id', 'OK'], ascending=[False, True, False], inplace=True)
                data_quantity_machine_input = st.data_editor(data_quantity_machine, hide_index=True,
                                                    column_order=["workplace_id", "machine_name", "output_relevant", "OK", "NOK", "production_time", "halt_time", "setup_time", "comment"],
                                                    column_config=
                                                    {"workplace_id": st.column_config.Column(t("col_workplace")),
                                                        "machine_name": st.column_config.Column(t("col_machine")),
                                                    "output_relevant": st.column_config.CheckboxColumn(t("col_output_relevant")),
                                                    "OK": st.column_config.NumberColumn(t("col_ok")),
                                                    "NOK": st.column_config.NumberColumn(t("col_nok")),
                                                    "production_time": st.column_config.Column(t("col_production_time")),
                                                    "halt_time": st.column_config.Column(t("col_halt_time")),
                                                    "setup_time": st.column_config.Column(t("col_setup_time")),
                                                    "comment": st.column_config.TextColumn(t("col_comment"))},
                                                        disabled=['workplace_id', 'machine_name', 'output_relevant', 'OK', 'NOK', 'production_time', 'halt_time', 'setup_time'])
                st.divider()

                # Disturbances
                st.subheader(t("subheader_machine_disturbances"))

                # Create Selection for workplace_id + machine names
                df_wpl_info = db.get_wpl_info()
                selected_workplaces_machine_names = df_wpl_info[df_wpl_info['workplace_id'].isin(selection['workplaces'])]
                selected_workplaces_machine_names.loc[:, 'machine_name'] = selected_workplaces_machine_names['machine_name'].fillna('')
                selected_workplaces_machine_names = (selected_workplaces_machine_names['workplace_id'] + ' - ' + selected_workplaces_machine_names['machine_name']).tolist()

                # Create Data Editor
                data_disturbance['workplace_machine'] = data_disturbance['workplace_id'] + ' - ' + data_disturbance['machine_name']
                data_disturbance.sort_values(by=['workplace_machine', 'start'], ascending=True, inplace=True)
                data_disturbance.reset_index(drop=True, inplace=True)
                data_disturbance_input = st.data_editor(data_disturbance, num_rows="dynamic", hide_index=True,
                                                    column_order=["workplace_machine", "source", "problem", "start", "duration_minutes", "sf_comment", "ssp_comment", "solution", "solved"],
                                                    column_config=
                                                    {"workplace_machine": st.column_config.SelectboxColumn(t("col_workplace"), options=selected_workplaces_machine_names, required=True),
                                                    "source": st.column_config.TextColumn(t("col_source"), default="SSP"),
                                                    "problem": st.column_config.Column(t("col_problem_description")),
                                                    "start":  st.column_config.TimeColumn(t("col_disturbance_start")),
                                                    "duration_minutes": st.column_config.NumberColumn(t("col_duration_minutes"), format="%d min", min_value=0, max_value=480),
                                                    "sf_comment": st.column_config.Column(t("col_forcam_comment")),
                                                    "ssp_comment": st.column_config.Column(t("col_ssp_comment")),
                                                    "solution": st.column_config.Column(t("col_action_taken")),
                                                        "solved": st.column_config.CheckboxColumn(t("col_done"), default=False)},
                                                        disabled=["source", "sf_comment"])

                # Clean Input Dataframe
                data_disturbance_input.dropna(subset=['workplace_machine'], inplace=True)
                if len(data_disturbance_input) != 0:
                    data_disturbance_input[['workplace_id', 'machine_name']] = data_disturbance_input['workplace_machine'].str.split(' - ', n=1, expand=True)
                data_disturbance_input = data_disturbance_input.drop('workplace_machine', axis=1)
                data_disturbance_input['date_id'] = selection['date'].strftime('%Y-%m-%d')
                data_disturbance_input['shift_id'] = selection['shift_id']
                st.divider()

            # Display for LOG
            else:

                # KPI's
                st.subheader(t("subheader_personnel_info"))
                if not config.SHOPFLOOR_EMPLOYEES_AVAILABLE:
                    st.info(t("info_manual_employee_entry"))
                kpi = {t("col_metric"): [t("kpi_employees_present_shift"), t("kpi_sick"), t("kpi_vacation")],
                        t("col_value"): [data_general_data['kpi_employees_present'], data_general_data['kpi_output_nok'], data_general_data['kpi_output_ok']]}
                data_df_kpi = pd.DataFrame(kpi)
                data_kpi_input = st.data_editor(data_df_kpi, hide_index=True, disabled=[t("col_metric")])


                # Dummy DF quantity machine
                data_quantity_machine_input = pd.DataFrame()

                # LOG Table
                st.subheader(t("subheader_overview"))

                data_disturbance_input = st.data_editor(data_disturbance, num_rows="dynamic", hide_index=True,
                                                    column_order=["workplace_id", "source", "problem", "start", "duration_minutes", "ssp_comment", "solution", "solved"],
                                                    column_config=
                                                    {"workplace_id": st.column_config.SelectboxColumn(t("col_area"), options=config.LOGISTICS_WORKPLACES, required=True),
                                                    "source": st.column_config.TextColumn(t("col_source"), default="SSP"),
                                                    "problem": st.column_config.TextColumn(t("col_problem"), default=""),
                                                    "start":  st.column_config.TimeColumn(t("col_disturbance_start")),
                                                    "duration_minutes": st.column_config.NumberColumn(t("col_duration_minutes"), format="%d min", min_value=0, max_value=480),
                                                    "ssp_comment": st.column_config.TextColumn(t("col_ssp_comment"), default=""),
                                                    "solution": st.column_config.TextColumn(t("col_action_taken"), default=""),
                                                        "solved": st.column_config.CheckboxColumn(t("col_done"), default=False)},
                                                        disabled=["source", "sf_comment"])
                # Clean DF
                data_disturbance_input['date_id'] = selection['date'].strftime('%Y-%m-%d')
                data_disturbance_input['shift_id'] = selection['shift_id']

                st.divider()


            # Nachricht für die Schichtübergabe
            st.subheader(t("subheader_handover_message"))
            data_schichtubergabe_input = st.text_area(label=t("label_handover_message"), value=data_general_data['message'], label_visibility="collapsed", placeholder=t("placeholder_handover_message"), max_chars=999)
            st.divider()

            # Save Data
            st.subheader(t("subheader_save"))
            submitted = st.form_submit_button(t("button_save_data"))
            if submitted:
                if len(data_schiko_name_input) == 0:
                    st.error(t("error_name_required"))
                else:
                    app_logging.logger.info("SAVE submitted")
                    with st.spinner(t("spinner_saving")):
                        # Save for OP
                        if st.session_state.selection['department'] in config.PRODUCTION_DEPARTMENTS:
                            # Create General Input Data and save all
                            data_general_input['name'] = data_schiko_name_input
                            data_general_input['message'] = data_schichtubergabe_input
                            data_general_input['kpi_output_ok'] = data_kpi_input.iloc[0, 1]
                            data_general_input['kpi_output_nok'] = data_kpi_input.iloc[1, 1]
                            data_general_input['kpi_employees_present'] = data_kpi_input.iloc[2, 1]
                            if data_general_input['kpi_employees_present'] > 0:
                                data_general_input['kpi_output_per_employee'] = data_general_input['kpi_output_ok'] / data_general_input['kpi_employees_present']
                            else: data_general_input['kpi_output_per_employee'] = 0


                        # Save for LOG
                        else:
                            # Create General Input Data and save all
                            data_general_input['name'] = data_schiko_name_input
                            data_general_input['message'] = data_schichtubergabe_input
                            data_general_input['kpi_employees_present'] = data_kpi_input.iloc[0, 1]
                            data_general_input['kpi_output_nok'] = data_kpi_input.iloc[1, 1]
                            data_general_input['kpi_output_ok'] = data_kpi_input.iloc[2, 1]
                            if data_general_input['kpi_employees_present'] > 0:
                                data_general_input['kpi_output_per_employee'] = 0
                            else: data_general_input['kpi_output_per_employee'] = 0

                        save_all_data(selection, data_general_input, data_quantity_machine_input, data_disturbance_input)

                        # Return Message
                        time.sleep(1)
                        st.success(t("success_saved"))

                        # Enable E-Mail
                        st.session_state.disable_email = False


        if "data" in st.session_state:
            # Send E-Mail and save_data
            st.subheader(t("subheader_send_email"))
            st.text(t("text_mail_distribution") + data_meta['mail'])

            email_cc = st.text_input(label=t("label_cc_email"), placeholder=t("placeholder_cc_email"), max_chars=500)

            if st.session_state.disable_email:
                st.info(t("info_email_disabled"))


            if st.button(t("button_send_email"), disabled=st.session_state.disable_email):
                if len(data_schiko_name_input) == 0:
                    st.error(t("error_name_required"))
                else:
                    # Send E-Mail
                    email_report.create_and_send_email(selection, data_meta, email_cc, data_general_input, data_quantity_machine_input, data_disturbance_input)
                    app_logging.logger.info("EMAIL submitted")


def save_all_data(selection, data_general_input, data_quantity_machine_input, data_disturbance_input):
    app_logging.logger.info("Saving all Data")

    data_general.save_data_general(selection, data_general_input)
    if len(data_quantity_machine_input) > 0:
        data_quantities.save_data_quantity_machine(selection, raw_df=data_quantity_machine_input, save_style='replace')
    if len(data_disturbance_input) > 0:
        data_disturbances.save_data_disturbance(selection, raw_df=data_disturbance_input, save_style='replace')

    return