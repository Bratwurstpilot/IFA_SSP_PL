# DB-Engine und Stammdaten-Zugriff (ersetzt den alten __main__-Setup-Block)
# Cached: Engine einmal pro Prozess, Stammdaten mit 10 min TTL statt bei jedem Streamlit-Rerun.
import urllib.parse

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import app_logging


@st.cache_resource
def get_engine():
    # Benoetigt pyodbc + "ODBC Driver 17 for SQL Server" auf dem Host
    password = config.get_credential('dwh_user')
    settings = config.SQL_SETTINGS
    # quote_plus: Passwort kann Sonderzeichen (@ : / &) enthalten, die die Connection-URL sonst falsch parsen
    user = urllib.parse.quote_plus(settings['user'])
    password = urllib.parse.quote_plus(password)
    return create_engine(
        "mssql+pyodbc://" + user + ":" + password + "@" + settings['server'] + "/" + settings['database'] + "?driver=ODBC Driver 17 for SQL Server")


@st.cache_resource
def _get_session_factory():
    return sessionmaker(bind=get_engine())


def get_session():
    # Frische Session pro Aufruf; jede Save-Funktion committet selbst
    return _get_session_factory()()


@st.cache_data(ttl=600)
def get_hierarchy():
    engine = get_engine()

    # Get Dictionary of department - line - subline
    try:
        df_hierarchy = app_logging.log_and_read_sql(f"SELECT DISTINCT department, line_id + ' - ' + line_name AS line_id, subline_id + ' - ' + subline_name AS subline_id FROM [DWH].[dim].[workplace] WHERE department IS NOT NULL AND plant = '{config.PLANT_ID}'", engine, label="hierarchy")
        df_wpl = app_logging.log_and_read_sql(f"SELECT DISTINCT workplace_id, line_id + ' - ' + line_name AS line_id, subline_id + ' - ' + subline_name AS subline_id FROM [DWH].[dim].[workplace] WHERE department IS NOT NULL AND plant = '{config.PLANT_ID}'", engine, label="workplace_mapping")
    except Exception as e:
        app_logging.logger.error(f"get_hierarchy: DB query failed, returning empty hierarchy: {e}")
        return {}

    # Precompute workplace lists once instead of re-filtering df_wpl per hierarchy row
    workplaces_by_line = df_wpl.groupby('line_id')['workplace_id'].apply(list).to_dict()
    workplaces_by_subline = df_wpl.groupby('subline_id')['workplace_id'].apply(list).to_dict()

    # Create hierarchy
    hierarchy = {}
    for row in df_hierarchy.itertuples(index=False):
        department, line_id, subline_id = row.department, row.line_id, row.subline_id

        line_dict = hierarchy.setdefault(department, {}).setdefault(line_id, {})

        # No Subline
        if subline_id is None:
            line_dict[line_id] = workplaces_by_line.get(line_id, [])
        # Subline
        else:
            line_dict[subline_id] = workplaces_by_subline.get(subline_id, [])

    return hierarchy


@st.cache_data(ttl=600)
def get_forcam_uuid_maps():
    engine = get_engine()

    # Forcam Workplace UUIDS
    try:
        df_forcam_uuid = app_logging.log_and_read_sql("SELECT DISTINCT workplace_ifa_id, workplace_forcam_uuid FROM [DWH].[dim].[forcam_hierarchy]", engine, label="forcam_uuid_map")
    except Exception as e:
        app_logging.logger.error(f"get_forcam_uuid_maps: DB query failed, returning empty maps: {e}")
        return {}, {}

    ifa_wpl_to_forcam_uuid = dict(zip(df_forcam_uuid['workplace_ifa_id'], df_forcam_uuid['workplace_forcam_uuid']))

    duplicate_uuids = df_forcam_uuid.loc[df_forcam_uuid['workplace_forcam_uuid'].duplicated(), 'workplace_forcam_uuid'].tolist()
    if duplicate_uuids:
        app_logging.logger.warning(f"Duplicate Forcam UUIDs in forcam_hierarchy, reverse mapping drops entries: {duplicate_uuids}")
    forcam_uuid_to_ifa_wpl = dict(zip(df_forcam_uuid['workplace_forcam_uuid'], df_forcam_uuid['workplace_ifa_id']))

    return ifa_wpl_to_forcam_uuid, forcam_uuid_to_ifa_wpl


# Spaltenname ist Teil der SQL-Identifier-Position (kein Query-Parameter moeglich) --
# deshalb ueber Whitelist validieren statt Sprachwert direkt in die Query zu interpolieren.
_TITLE_COLUMN_BY_LANGUAGE = {"en": "title_en", "pl": "title_pl", "de": "title_de"}


@st.cache_data(ttl=600)
def get_operating_state_codes(language):
    # Forcam Operating state codes -- Titel-Spalte je nach UI-Sprache (Tabelle hat title_de/title_en/title_pl)
    title_column = _TITLE_COLUMN_BY_LANGUAGE.get(language, "title_en")
    try:
        return app_logging.log_and_read_sql(f"SELECT DISTINCT code, {title_column} AS title, color FROM [DWH].[dim].[forcam_operating_state_codes_polska]", get_engine(), label="operating_state_codes")
    except Exception as e:
        app_logging.logger.error(f"get_operating_state_codes: DB query failed, returning empty result: {e}")
        return pd.DataFrame(columns=['code', 'title', 'color'])


@st.cache_data(ttl=600)
def get_wpl_info():
    # Workplace Infos
    excluded_lines = ", ".join(f"'{name}'" for name in config.EXCLUDED_LINE_NAMES) or "''"
    try:
        return app_logging.log_and_read_sql(f"""
                SELECT workplace_id, process, machine_name, output_relevant, line_name
                FROM [DWH].[dim].[workplace]
                WHERE plant = '{config.PLANT_ID}' AND (process != 'mes-logout' OR process IS NULL) AND line_name NOT IN ({excluded_lines})
                """, get_engine(), label="wpl_info")
    except Exception as e:
        app_logging.logger.error(f"get_wpl_info: DB query failed, returning empty result: {e}")
        return pd.DataFrame(columns=['workplace_id', 'process', 'machine_name', 'output_relevant', 'line_name'])