# Data Disturbances: Maschinenstoerungen aus Forcam laden und in ssp_webapp_disturbances speichern
import datetime

import pandas as pd
import requests
from sqlalchemy import MetaData, Table, update, insert, text

import config
import db
import forcam_api
import app_logging
from translations import get_language


def collect_data_disturbance(selection, progressbar, progressbar_text):
    app_logging.logger.info("Disturbance: Collecting Machine Disturbance Data")
    engine = db.get_engine()

    # Load Data from Forcam
    df = load_data_disturbance(selection, progressbar, progressbar_text)

    # Translate code to text (Spalte je nach aktiver UI-Sprache, siehe db.get_operating_state_codes)
    df = pd.merge(df, db.get_operating_state_codes(get_language()), on='code', how='left')
    df = df.rename(columns={'title': 'problem'})

    # Update Database with Forcam Data
    save_data_disturbance(selection, df, save_style='update')

    # Read DWH Table
    sql_select = """SELECT * FROM [utility].[ssp_webapp_disturbances] WHERE date_id = '""" + selection['date'].strftime("%Y-%m-%d") + "' AND shift_id = '" + selection['shift_id'] + "' AND workplace_id IN (" + selection['workplaces_list'] + ")"
    df = app_logging.log_and_read_sql(sql_select, engine, label="ssp_webapp_disturbances(select)")

    # Add Meta Data
    df = pd.merge(df, db.get_wpl_info(), on='workplace_id', how='inner')
    df['machine_name'] = df['machine_name'].fillna('')

    return df


def collect_data_disturbance_log(selection):
    app_logging.logger.info("Disturbance: Collecting Disturbance for log")

    # Read DWH Table
    sql_select = """SELECT * FROM [utility].[ssp_webapp_disturbances] WHERE date_id = '""" + selection['date'].strftime("%Y-%m-%d") + "' AND shift_id = '" + selection['shift_id'] + "' AND workplace_id IN (" + selection['workplaces_list'] + ")"
    df = app_logging.log_and_read_sql(sql_select, db.get_engine(), label="ssp_webapp_disturbances(log)")

    return df

def load_data_disturbance(selection, progressbar, progressbar_text):
    app_logging.logger.info("Disturbance: Loading Machine Disturbance Data from Forcam API")
    ifa_wpl_to_forcam_uuid = db.get_forcam_uuid_maps()[0]

    # Forcam API Request
    with requests.Session() as request:

        # Token + Request Header
        request_head = forcam_api.get_auth_header(request, ('accept', 'application/hal+json;charset=UTF-8'))
        base_url = config.FORCAM_BASE_URL
        report_url = f"operating_state_log/?limit=100&formatted=true&timeZoneId={config.FORCAM_TIMEZONE}"

        # Workplace URL
        workplace_url = forcam_api.build_workplace_url(selection['workplaces'], ifa_wpl_to_forcam_uuid)

        # Time URL
        shift_start, shift_end = forcam_api.get_shift_window(selection, datetime.time(22,0,0))
        time_url = "&timeType=HOUR&includeCurrent=true&startDate="+shift_start.strftime("%Y-%m-%dT%H:%M:%S")+"&endDate="+shift_end.strftime("%Y-%m-%dT%H:%M:%S")

        # Create Request URL
        request_url = base_url + report_url + workplace_url + time_url

        # Add Filter for operating states (Rüsten, Störungen, Org. Stillstand, Musterproduktion, Material Logistik, Qualität)

        # Rüsten, Störungen, Org. Stillstand, Musterproduktion, Material Logistik, Qualität
        # operating_states_url = "&operationOperatingStatus=8098001&operationOperatingStatus=178652&operationOperatingStatus=867932451&operationOperatingStatus=2453935351&operationOperatingStatus=8098003&operationOperatingStatus=2236553651&operationOperatingStatus=8098002&operationOperatingStatus=178953&operationOperatingStatus=8098005&operationOperatingStatus=8098004&operationOperatingStatus=8098007&operationOperatingStatus=8098006&operationOperatingStatus=8098008&operationOperatingStatus=8098023&operationOperatingStatus=179357&operationOperatingStatus=766925901&operationOperatingStatus=8098012&operationOperatingStatus=164353801&operationOperatingStatus=8098011&operationOperatingStatus=179366&operationOperatingStatus=8098013&operationOperatingStatus=8098010&operationOperatingStatus=8098015&operationOperatingStatus=8098014&operationOperatingStatus=8098016&operationOperatingStatus=8098009&operationOperatingStatus=766925902&operationOperatingStatus=164353802&operationOperatingStatus=766925904&operationOperatingStatus=766925903&operationOperatingStatus=8098018&operationOperatingStatus=8098026&operationOperatingStatus=8098019&operationOperatingStatus=8098021&operationOperatingStatus=8098020"
        # Störungen, Org. Stillstand, Musterproduktion, Material Logistik, Qualität
        operating_states_url = "&operationOperatingStatus=8098005&operationOperatingStatus=8098004&operationOperatingStatus=8098007&operationOperatingStatus=8098006&operationOperatingStatus=8098008&operationOperatingStatus=8098023&operationOperatingStatus=179357&operationOperatingStatus=766925901&operationOperatingStatus=8098012&operationOperatingStatus=164353801&operationOperatingStatus=8098011&operationOperatingStatus=179366&operationOperatingStatus=8098013&operationOperatingStatus=8098010&operationOperatingStatus=8098015&operationOperatingStatus=8098014&operationOperatingStatus=8098016&operationOperatingStatus=8098009&operationOperatingStatus=766925902&operationOperatingStatus=164353802&operationOperatingStatus=766925904&operationOperatingStatus=766925903&operationOperatingStatus=8098018&operationOperatingStatus=8098026&operationOperatingStatus=8098019&operationOperatingStatus=8098021&operationOperatingStatus=8098020"

        request_url += operating_states_url
        app_logging.log_api_request("Disturbance", request_url)

        # Send Request to API
        data_request = request.get(request_url, headers=request_head, verify=False).json()
        app_logging.log_api_response("Disturbance", data_request)

        # Extract Data
        result_list = []
        for r in extract_api_data_disturbances(data_request, selection):
            result_list.append(r)

        # Check amount of total Results
        total = data_request['pagination']['total']
        if total > 0:
            app_logging.logger.info("Disturbance: Amount of Events: " + str(total))
            offset = 100
            progressbar_step_ratio = int(40 / (total / offset)) / 100
            progressbar_step = 0.5
            while offset < total:
                request_url = base_url + report_url + workplace_url + time_url
                request_url += operating_states_url + "&offset=" + str(offset)
                app_logging.log_api_request("Disturbance", request_url)

                data_request = request.get(request_url, headers=request_head, verify=False).json()
                app_logging.log_api_response("Disturbance", data_request)

                # Extract Data
                for r in extract_api_data_disturbances(data_request, selection):
                    result_list.append(r)
                # Increase Offset
                offset += 100
                # Increase Progressbar
                progressbar_step += progressbar_step_ratio
                progressbar.progress(progressbar_step, text=progressbar_text)

        # Create Dataframe from Results
        df_results = pd.DataFrame(result_list)

        # Filter Dataframes for states with 10 Minutes or longer
        try:
            df = df_results[df_results['duration_minutes'] >= 10]
            df = df.sort_values(['workplace_id', 'start'])

            df['start'] = df['start'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df['end'] = df['end'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df['source'] = 'Forcam'
            df['last_updated'] = datetime.datetime.now()

        except Exception as e:
            app_logging.logger.warning(f"Disturbance: No Data found or Error happened, creating empty DF: {e}")
            df = pd.DataFrame(columns=['date_id', 'shift_id', 'workplace_id', 'start', 'end', 'code', 'status',
            'sf_comment', 'duration_minutes', 'source', 'last_updated'])

    return df

def extract_api_data_disturbances(data_request, selection):
    result_list = []
    for i in range(len(data_request['_embedded']['ifareportsOperating_state_log'])):
        data = data_request['_embedded']['ifareportsOperating_state_log'][i]['properties']
        result = {'date_id': selection['date'].strftime("%Y-%m-%d"),
                'shift_id': selection['shift_id'],
                'workplace_id': data.get('workplaceId').split(" ")[0],
                'start': datetime.datetime.strptime(data.get('startTs'), "%d/%m/%Y, %H:%M"),
                'end': datetime.datetime.strptime(data.get('endTs'), "%d/%m/%Y, %H:%M"),
                'code': data.get('operatingStatusMnemonic'),
                'status': data.get('operatingStatusText'),
                'sf_comment': data.get('ticketTitle')}
        result['duration_minutes'] = (result['end'] - result['start']).total_seconds()/60

        result_list.append(result)

    return result_list

def save_data_disturbance(selection, raw_df, save_style):
    app_logging.logger.info("Disturbance: Saving Data in style: " + save_style)
    engine = db.get_engine()

    # Format the Dataframe like the SQL-Table
    sql_query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ssp_webapp_disturbances'"
    selected_columns = app_logging.log_and_read_sql(sql_query, engine, label="ssp_webapp_disturbances(columns)")['COLUMN_NAME'].tolist()

    # Create an empty DataFrame with the selected columns
    df = pd.DataFrame(columns=selected_columns)

    # Iterate over each column and check if it exists in the original DataFrame
    for col in selected_columns:
        if col in raw_df.columns:
            # If the column exists, copy it to the subselected DataFrame
            df[col] = raw_df[col]
        else:
            if col == 'solved':
                df[col] = False
            else:
                df[col] = ''

    # Save Style Replace
    if save_style == 'replace':

        # Delete old Entries
        delete_sql = text(f"""
        DELETE FROM utility.ssp_webapp_disturbances
        WHERE date_id = '{selection['date'].strftime("%Y-%m-%d")}' AND
            shift_id = '{selection['shift_id']}' AND
            workplace_id IN ({selection['workplaces_list']})
        """)

        # Execute the delete query
        app_logging.log_write("ssp_webapp_disturbances", f"DELETE date={selection['date'].strftime('%Y-%m-%d')} shift={selection['shift_id']} workplaces=({selection['workplaces_list']})")
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(delete_sql)

        # Insert new DF
        df['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_sql('ssp_webapp_disturbances', engine, schema='utility', if_exists='append', index=False)

        app_logging.log_write("ssp_webapp_disturbances", f"replaced, {len(df)} row(s) inserted")
        return

    # Save Style Update
    elif save_style == 'update':
        session = db.get_session()

        # Define metadata and table
        metadata = MetaData()
        ssp_webapp_disturbances = Table('ssp_webapp_disturbances', metadata, schema='utility', autoload_with=engine)

        for index, row in df.iterrows():
            # Define condition for the update
            update_condition = (
                (ssp_webapp_disturbances.c.date_id == row['date_id']) &
                (ssp_webapp_disturbances.c.shift_id == row['shift_id']) &
                (ssp_webapp_disturbances.c.workplace_id == row['workplace_id']) &
                (ssp_webapp_disturbances.c.source == 'Forcam') &
                (ssp_webapp_disturbances.c.start == row['start']))

            # Create update values
            update_values = {
                'last_updated': datetime.datetime.now(),
                'end': row['end'],
                'code': row['code'],
                'duration_minutes': row['duration_minutes'],
                'sf_comment': row['sf_comment']}

            # Create update statement
            stmt = update(ssp_webapp_disturbances).where(update_condition).values(update_values)

            # Execute update
            result = session.execute(stmt)

            # Insert Row if nothing was updated
            if result.rowcount == 0:
                app_logging.log_write("ssp_webapp_disturbances", f"no matching row for workplace_id={row['workplace_id']}, inserting new one")
                # Create insert statement
                stmt = insert(ssp_webapp_disturbances).values(row.to_dict())

                # Execute insert
                session.execute(stmt)


        # Commit changes
        session.commit()

        app_logging.log_write("ssp_webapp_disturbances", f"updated, {len(df)} row(s) processed")
        return