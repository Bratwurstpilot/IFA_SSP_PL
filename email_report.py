# E-Mail-Versand des SSP-Berichts als HTML-Mail
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
import streamlit as st

import config
import app_logging
from translations import t


def create_and_send_email(selection, data_meta, email_cc, data_general_input, data_quantity_machine_input, data_disturbance_input):
    # Disable Button
    st.session_state.disable_email = True

    # Settings
    host = config.MAIL_HOST
    port = config.MAIL_PORT
    email = config.MAIL_SENDER
    pw = config.get_credential('mailuser')
    mail_to = [data_meta['mail']]

    # CC Adress
    # Step 1: Split the string at commas to create a list of email addresses
    email_list = email_cc.split(',')
    # Step 2: Trim any whitespace around email addresses
    email_list = [email.strip() for email in email_list]
    # Step 3: Define the pattern to match email addresses in the form xxx.xxx@ifa-group.com
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    # Step 4: Filter the list to include only addresses that match the desired pattern
    mail_cc = [email for email in email_list if pattern.match(email) and email.endswith('@ifa-group.com')]


    # HTML Message
    message = MIMEMultipart("related")
    message["From"] = email
    message["To"] = ", ".join(mail_to)
    message["Subject"] = 'SSP: ' + selection['subline'] + ' - ' + selection['date_str_de'] + ' - ' + selection['shift']
    message["Cc"] = ", ".join(mail_cc)

    #mail_bcc = ['benedikt.wehrmeister@ifa-group.com']

    html = f"""<html>
            <meta http-equiv="content-type" content="text/html; charset=utf-8">
            <head></head>
            <body>
                <basefont face = "arial, verdana, sans-serif" size ="4">
                <h2 style='font-size: 20px'><br><u><strong>SSP: {selection['subline']} - {selection['date_str_de']} - {selection['shift']}</strong></u></br></h2>"""

    # Overview
    html += f"""<strong>{t("subheader_overview")}</strong>"""

    html += """<table border='1' style="width:40%;border-collapse:collapse;font-family:arial;font-size:80%">"""
    html += f"""<tr>
    <td style="text-align:left">{t("email_row_shift_leader")}</td>
    <td style="text-align:center">{data_general_input['name']}</td>
    </tr>"""
    html += f"""<tr>
    <td style="text-align:left">{t("email_row_team_leader")}</td>
    <td style="text-align:center">{data_meta['responsible']}</td>
    </tr>"""
    html += f"""<tr>
    <td style="text-align:left">{t("email_row_time_remaining")}</td>
    <td style="text-align:center">{data_meta['time_till_shift_end']}</td>
    </tr>"""
    html += """</table>"""
    html += """<br></br>"""

    # Schiko Message
    html += f"""<strong>{t("label_handover_message")}</strong>"""
    html += """<table border='1' style="width:40%;border-collapse:collapse;font-family:arial;font-size:80%">"""
    html += f"""<tr>
    <td style="text-align:left">{data_general_input['message']}</td></tr>"""
    html += """</table>"""
    html += """<br></br>"""

    # OP-Email
    if selection['department'] in config.PRODUCTION_DEPARTMENTS:
        # KPI
        html += f"""<strong>{t("subheader_kpis")}</strong>"""
        kpi = {t("col_metric"): [t("kpi_output"), t("kpi_scrap"), t("kpi_employees_present"), t("kpi_output_per_employee")],
                t("col_value"): [int(data_general_input['kpi_output_ok']), int(data_general_input['kpi_output_nok']), int(data_general_input['kpi_employees_present']), round(data_general_input['kpi_output_per_employee'],1)]}
        html += dataframe_to_html(pd.DataFrame(kpi), width='40%', style_first_col='left')
        html += """<br></br>"""

        # Quantities by Machine
        html += f"""<strong>{t("subheader_quantity_per_machine")}</strong>"""
        column_select = ['workplace_id', 'machine_name', 'output_relevant', 'OK', 'NOK', 'production_time', 'halt_time', 'setup_time', 'comment']
        column_names = [t("col_workplace"), t("col_machine"), t("col_output_relevant"), t("col_ok"), t("col_nok"), t("col_production_time"), t("col_halt_time"), t("col_setup_time"), t("col_comment")]
        html += dataframe_to_html(data_quantity_machine_input, column_select=column_select, header_names=column_names, width='80%')
        html += """<br></br>"""

        # Issues by Machine
        html += f"""<strong>{t("subheader_machine_disturbances")}</strong>"""
        column_select = ['workplace_id', 'machine_name', 'source', 'problem','start', 'duration_minutes', 'sf_comment', 'ssp_comment', 'solution', 'solved']
        column_names = [t("col_workplace"), t("col_machine"), t("col_source"), t("col_problem_description"), t("col_disturbance_start"), t("col_duration_min_short"), t("col_forcam_comment"), t("col_ssp_comment"), t("col_action_taken"), t("col_done")]
        html += dataframe_to_html(data_disturbance_input, column_select=column_select, header_names=column_names, width='80%')
        html += """<br></br>"""

        html += f"""
        <br>{t("email_short_disturbance_note")}</br>"""

    # LOG E-Mail
    else:
        # KPI
        html += f"""<strong>{t("subheader_personnel_info")}</strong>"""
        kpi = {t("col_metric"): [t("kpi_employees_present_shift"), t("kpi_sick"), t("kpi_vacation")],
                        t("col_value"): [data_general_input['kpi_employees_present'], data_general_input['kpi_output_nok'], data_general_input['kpi_output_ok']]}
        html += dataframe_to_html(pd.DataFrame(kpi), width='40%', style_first_col='left')
        html += """<br></br>"""

        # Issues by Machine
        html += f"""<strong>{t("email_problem_reports_header")}</strong>"""
        column_select = ['workplace_id', 'source', 'problem','start', 'duration_minutes', 'ssp_comment', 'solution', 'solved']
        column_names = [t("col_area"), t("col_source"), t("col_problem_description"), t("col_disturbance_start"), t("col_duration_min_short"), t("col_ssp_comment"), t("col_action_taken"), t("col_done")]
        html += dataframe_to_html(data_disturbance_input, column_select=column_select, header_names=column_names, width='80%')
        html += """<br></br>"""

    # E-Mail End
    html += f"""
    <br>{t("email_footer_auto_generated")}</br>
    <br>{t("email_footer_contact")}</br>
    </body>
    </html>"""

    # Turn these into plain/html MIMEText objects
    mail_object = MIMEText(html, "html")
    message.attach(mail_object)

    # Create secure connection with server and send email
    receiver_email = mail_to + mail_cc #+ mail_bcc
    try:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email, pw)
            server.sendmail(email, receiver_email, message.as_string())
    except Exception as e:
        app_logging.logger.error(f"E-Mail send failed: {e}")
        st.error(t("error_email_failed"))
        return

    app_logging.logger.info("E-Mail was send")
    st.success(t("success_email_sent"))
    return

def dataframe_to_html(df, column_select=[], header_names=[], percentage_columns=[], width='100%', font='arial', font_size='80%', style='center', style_first_col='center'):
    # Column Selection
    if len(column_select) != 0:
        df = df[column_select]

    # Rename Header
    if len(header_names) != 0:
        df = df.rename(columns=dict(zip(df.columns, header_names)))

    header = df.columns.to_list()

    # Indicate Table & set headers
    html = f"""<table border='1' style="width:{width};border-collapse:collapse;font-family:{font};font-size:{font_size}">"""
    html += """<tr>"""
    for head in header:
        html += f"""<th>&nbsp{head}&nbsp</th>"""
    html += """</tr>"""
    # Write Values
    for index, row in df.iterrows():
        html += """<tr>"""
        col_index = 0
        for col in header:
            value = row[col]
            # Translate True / False
            if value is True:
                value = t("bool_yes")
            elif value is False:
                value = t("bool_no")
            # Check Valuetypes
            if value is None or pd.isna(value) or value == 'nan':
                value = ""
            elif isinstance(value, float):
                # Check if the float is actually a whole number
                if value.is_integer():
                    value = str(int(value))
                else:
                    value = str(round(value, 1)).replace(".", ",")

            # Check percentage
            if col in percentage_columns:
                value = str("%.1f%%" % (row[col])).replace(".",",")
            # Write Value und adjust Style
            if col_index != 0:
                html += f"""<td style="text-align:{style}">{value}</td>"""
            else:
                html += f"""<td style="text-align:{style_first_col}">{value}</td>"""
            col_index +=1
        html += """</tr>"""
    # End Table
    html += """</table>"""
    return html