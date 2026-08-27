# Data Quantity Machine: Mengen pro Maschine aus Forcam/SAP laden und in ssp_webapp_quantities speichern
import datetime

import numpy as np
import pandas as pd
import requests
from sqlalchemy import MetaData, Table, update, insert, text

import config
import db
import forcam_api
import app_logging


def collect_data_quantity_machine(selection, progressbar, progressbar_text):
    app_logging.logger.info("Quantities: Collecting Machine Quantities")
    engine = db.get_engine()

    # Load Data
    if selection['subline'] in config.SAP_FED_SUBLINES:
        # Data comes from SAP and is transmitted in the SQL-Datawarehouse with the Job "02_3_OP_reported_quantities"
        pass
    else:
        df_quantity = load_data_quantity_machine_forcam(selection, progressbar, progressbar_text)

        sap_fed_in_selection = [wpl for wpl in selection['workplaces'] if wpl in config.SAP_FED_WORKPLACES]
        if sap_fed_in_selection:
            app_logging.logger.info("Insert SAP Data for Quantities of " + str(sap_fed_in_selection))
            # workplace_list needs to be a comma separated string for the SQL IN(...) clause
            workplace_list = ", ".join(f"'{wpl}'" for wpl in sap_fed_in_selection)
            df_quantity = insert_data_quantity_machine_sap(selection, workplace_list, df_quantity)

        save_data_quantity_machine(selection, df_quantity, save_style='update')

    # Read Data
    sql_select= f"""
        SELECT *
        FROM [DWH].[utility].[ssp_webapp_quantities]
        WHERE date_id = '{selection['date'].strftime("%Y-%m-%d")}'
        AND shift_id = '{selection['shift_id']}'
        AND workplace_id IN ({selection['workplaces_list']})"""
    df_raw = app_logging.log_and_read_sql(sql_select, engine, label="ssp_webapp_quantities(select)")

    # Add Meta Data
    df = pd.merge(df_raw, db.get_wpl_info(), on='workplace_id', how='inner')

    return df

def load_data_quantity_machine_forcam(selection, progressbar, progressbar_text):
    app_logging.logger.info("Quantities: Loading Machine Quantities from Forcam API")
    ifa_wpl_to_forcam_uuid = db.get_forcam_uuid_maps()[0]

    # Forcam API Request
    with requests.Session() as request:

        # Token + Request Header
        request_head = forcam_api.get_auth_header(request, ('Accept', 'application/json;charset=UTF-8'))
        base_url = config.FORCAM_BASE_URL
        report_url = f"ssp/?limit=100&formatted=true&timeZoneId={config.FORCAM_TIMEZONE}"

        # Workplace URL
        workplace_url = forcam_api.build_workplace_url(selection['workplaces'], ifa_wpl_to_forcam_uuid)

        # Time URL
        shift_start, shift_end = forcam_api.get_shift_window(selection, datetime.time(22,2,0))
        time_url = "&timeTimeType=HOUR&timeIncludeCurrent=true&timeStartDate="+shift_start.strftime("%Y-%m-%dT%H:%M:%S")+"&timeEndDate="+shift_end.strftime("%Y-%m-%dT%H:%M:%S")

        # Create Request
        request_url = base_url + report_url + workplace_url + time_url
        app_logging.log_api_request("Quantities", request_url)

        data_request = request.get(request_url, headers=request_head, verify=False).json()
        app_logging.log_api_response("Quantities", data_request)

        # Extract Data
        result_list = []
        for r in extract_api_data_quantity_machine(data_request, selection):
            result_list.append(r)

        # Check amount of total Results
        total = data_request['pagination']['total']
        if total > 0:
            app_logging.logger.info("Quantities: Amount of Events: " + str(total))
            offset = 100
            progressbar_step_ratio = int(40 / (total / offset)) / 100
            progressbar_step = 0.1
            while offset < total:
                request_url = base_url + report_url + workplace_url + time_url + "&offset=" + str(offset)
                app_logging.log_api_request("Quantities", request_url)
                data_request = request.get(request_url, headers=request_head, verify=False).json()
                app_logging.log_api_response("Quantities", data_request)

                # Extract Data
                for r in extract_api_data_quantity_machine(data_request, selection):
                    result_list.append(r)
                # Increase Offset
                offset += 100
                # Increase Progressbar
                progressbar_step += progressbar_step_ratio
                progressbar.progress(progressbar_step, text=progressbar_text)

        # Create Dataframe from Results
        df_results = pd.DataFrame(result_list)

        # Add missing Workplaces
        # Find missing workplace_ids, if df_result empty return empty list
        if len(df_results) > 0:
            existing_workplaces = df_results['workplace_id'].unique()
        else:
            existing_workplaces = []
        missing_workplaces = list(set(selection['workplaces']) - set(existing_workplaces))

        # Create rows for missing workplaces
        new_rows = pd.DataFrame({
            'date_id': [selection['date']] * len(missing_workplaces),
            'shift_id': [selection['shift_id']] * len(missing_workplaces),
            'workplace_id': missing_workplaces,
            'comment': [''] * len(missing_workplaces),
            'target': [0] * len(missing_workplaces),
            'OK': [0] * len(missing_workplaces),
            'NOK': [0] * len(missing_workplaces),
            'production_time': ['00:00'] * len(missing_workplaces),
            'halt_time': ['00:00'] * len(missing_workplaces),
            'setup_time': ['00:00'] * len(missing_workplaces),
            'pause_time': ['00:00'] * len(missing_workplaces),
        })

        # Add them to the original df_results
        df_results_updated = pd.concat([df_results, new_rows], ignore_index=True)

        if len(df_results_updated) > 0:
            # Transform Dataframe
            # Ensure time columns are in hh:mm:ss format
            time_columns = ['production_time', 'halt_time', 'setup_time', 'pause_time']
            for col in time_columns:
                df_results_updated[col] = pd.to_timedelta(df_results_updated[col] + ':00')

            # Group by workplace_id and sum the relevant columns
            agg_df = df_results_updated.groupby(['date_id', 'shift_id', 'workplace_id', 'comment']).agg({
                'target': 'sum',
                'OK': 'sum',
                'NOK': 'sum',
                'production_time': 'sum',
                'halt_time': 'sum',
                'setup_time': 'sum',
                'pause_time': 'sum'
            }).reset_index()

            # Convert the timedelta columns back to hh:mm format
            for col in time_columns:
                agg_df[col] = agg_df[col].apply(lambda x: f"{int(x.total_seconds() // 3600):02}:{int((x.total_seconds() % 3600) // 60):02}")

            agg_df['last_updated'] = datetime.datetime.now()
            agg_df['target_time_per_part_seconds'] = 0
            agg_df['actual_time_per_part_seconds'] = 0.0
            agg_df['parts_per_hour'] = 0.0
            agg_df['operation_id'] = ""
            agg_df['materialnumber'] = ""

        else:
            agg_df = pd.DataFrame()

    return agg_df

def insert_data_quantity_machine_sap(selection, workplace_list, original_df):
    # SQL Select
    sql_select = f"""
    SELECT * FROM [DWH].[fact_production].[reported_quantities_workplace]
    WHERE date_id = '{selection['date'].strftime("%Y-%m-%d")}'
        AND workplace_id IN ({workplace_list})"""

    df = app_logging.log_and_read_sql(sql_select, db.get_engine(), label="reported_quantities_workplace(sap)")

    # Selection of Shift
    if selection['shift_id'] == 'night_shift':
        ok_column = 'yield_night_shift'
        nok_column = 'scrap_night_shift'
    elif selection['shift_id'] == 'early_shift':
        ok_column = 'yield_early_shift'
        nok_column = 'scrap_early_shift'
    elif selection['shift_id'] == 'late_shift':
        ok_column = 'yield_late_shift'
        nok_column = 'scrap_late_shift'

    # Replace Data in orignal_df
    for index, row in original_df.iterrows():
        # Find the matching row in df based on workplace_id and date_id
        matching_row = df[(df['workplace_id'] == row['workplace_id'])]

        if not matching_row.empty:
            # Update the values in the original_df with the values from df
            original_df.at[index, 'OK'] = matching_row[ok_column].values[0]
            original_df.at[index, 'NOK'] = matching_row[nok_column].values[0]

    return original_df

def extract_api_data_quantity_machine(data_request, selection):
    forcam_uuid_to_ifa_wpl = db.get_forcam_uuid_maps()[1]

    result_list = []
    for i in range(len(data_request['_embedded']['ifareportsSsp'])):
        data = data_request['_embedded']['ifareportsSsp'][i]['properties']
        result = {
            'date_id': selection['date'].strftime("%Y-%m-%d"),
            'shift_id': selection['shift_id'],
            'operation_id': "", #data.get('operationId'),
            'workplace_id': forcam_uuid_to_ifa_wpl[data.get('workplaceId')],
            'materialnumber': "", #data.get('materialId'),
            'comment': '',
            'last_updated': '',
            'target': int(data.get('targetQuantity').replace('.00', '')),
            'OK': int(data.get('yieldQtyShift').replace('.00', '')),
            'NOK': int(data.get('scrapQtyShift').replace('.00', '')),
            'production_time': data.get('prodDuration'),
            'setup_time': data.get('setupDuration'),
            'halt_time': data.get('interuptDuration'),
            'pause_time': data.get('breakDuration'),
            'target_time_per_part_seconds': float(data.get('timePerUnitSec')),
            'actual_time_per_part_seconds': float(data.get('realTimePerUnitSec')),
            'parts_per_hour': float(data.get('pph'))
        }
        result_list.append(result)

    return result_list

def save_data_quantity_machine(selection, raw_df, save_style):
    app_logging.logger.info("Quantities: Saving Data in style: " + save_style)
    engine = db.get_engine()

    # Format the Dataframe like the SQL-Table
    sql_query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ssp_webapp_quantities'"
    selected_columns = app_logging.log_and_read_sql(sql_query, engine, label="ssp_webapp_quantities(columns)")['COLUMN_NAME'].tolist()
    df = pd.DataFrame(columns=selected_columns)

    # Iterate over each column and check if it exists in the original DataFrame
    for col in selected_columns:
        if col in raw_df.columns:
            # If the column exists, copy it to the subselected DataFrame
            df[col] = raw_df[col]
        else:
            # If the column doesn't exist, add it with NaN values
            df[col] = np.nan

    # Save Style Replace
    if save_style == 'replace':

        # Define the SQL delete query using f-string and text
        delete_sql = text(f"""
                DELETE FROM utility.ssp_webapp_quantities
                WHERE date_id = '{selection['date'].strftime('%Y-%m-%d')}'
                AND shift_id = '{selection['shift_id']}'
                AND workplace_id IN ({selection['workplaces_list']})""")

        # Execute the delete query
        app_logging.log_write("ssp_webapp_quantities", f"DELETE date={selection['date'].strftime('%Y-%m-%d')} shift={selection['shift_id']} workplaces=({selection['workplaces_list']})")
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(delete_sql)

        # Insert new DF
        df['last_updated'] = datetime.datetime.now()
        df.to_sql('ssp_webapp_quantities', engine, schema='utility', if_exists='append', index=False)

        app_logging.log_write("ssp_webapp_quantities", f"replaced, {len(df)} row(s) inserted")
        return

    # Save Style Update
    elif save_style == 'update':
        session = db.get_session()

        # Define metadata and table
        metadata = MetaData()
        ssp_webapp_quantities = Table('ssp_webapp_quantities', metadata, schema='utility', autoload_with=engine)


        for index, row in df.iterrows():
            # Define condition for the update
            update_condition = (
                (ssp_webapp_quantities.c.date_id == row['date_id']) &
                (ssp_webapp_quantities.c.shift_id == row['shift_id']) &
                (ssp_webapp_quantities.c.workplace_id == row['workplace_id'])
            )

            # Create update values
            update_values = {
                'last_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'target': row['target'],
                'OK': row['OK'],
                'NOK': row['NOK'],
                'production_time': row['production_time'],
                'setup_time': row['setup_time'],
                'halt_time': row['halt_time'],
                'pause_time': row['pause_time'],
                'target_time_per_part_seconds': row['target_time_per_part_seconds'],
                'actual_time_per_part_seconds': row['actual_time_per_part_seconds'],
                'parts_per_hour': row['parts_per_hour']
            }

            # Create update statement
            stmt = update(ssp_webapp_quantities).where(update_condition).values(update_values)

            # Execute update
            result = session.execute(stmt)

            # Check if any rows were updated
            if result.rowcount == 0:
                app_logging.log_write("ssp_webapp_quantities", f"no matching row for workplace_id={row['workplace_id']}, inserting new one")
                # Create insert statement
                stmt = insert(ssp_webapp_quantities).values(row.to_dict())

                # Execute insert
                session.execute(stmt)

            # Commit changes
            session.commit()

        app_logging.log_write("ssp_webapp_quantities", f"updated, {len(df)} row(s) processed")
        return