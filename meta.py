# Meta-Informationen: Schicht-Vorauswahl und meta_data.csv
import datetime

import pandas as pd

import config
from translations import t


def preselect_shift():
    now = datetime.datetime.today().time()

    # Determine the current shift based on the current time
    if now < datetime.time(6, 30, 0):
        preselected_shift = 0
    elif datetime.time(6, 30, 0) <= now < datetime.time(14, 30, 0):
        preselected_shift = 1
    elif datetime.time(14, 30, 0) <= now < datetime.time(22, 30, 0):
        preselected_shift = 2
    else:
        preselected_shift = 0

    return preselected_shift

def collect_data_meta_information(selection):
    data_meta = {}

    # Meta Data Table
    df_meta = pd.read_csv(config.META_DATA_PATH, delimiter=';', encoding=config.META_DATA_ENCODING)
    df_meta = df_meta[df_meta['subline_id'] == selection['subline']]
    if not df_meta.empty:
        data_meta['responsible'] = df_meta['responsible'].iloc[0]
        data_meta['mail'] = df_meta['email_verteiler'].iloc[0]
    else:
        data_meta['responsible'] = config.FALLBACK_RESPONSIBLE
        data_meta['mail'] = config.FALLBACK_CONTACT_MAIL

    # Calculate time till shift ends
    current_datetime = datetime.datetime.today()

    # Calculate Shiftend
    if selection['shift_id'] == 'night_shift':
        shift_end = datetime.datetime.combine(selection['date'], datetime.time(6,0,0))
    elif selection['shift_id'] == 'early_shift':
        shift_end = datetime.datetime.combine(selection['date'], datetime.time(14,0,0))
    elif selection['shift_id'] == 'late_shift':
        shift_end = datetime.datetime.combine(selection['date'], datetime.time(22,0,0))

    # Calculate delta between end of shift and current datetime
    timedelta = shift_end - current_datetime

    if timedelta.total_seconds() < 0:
        data_meta['time_till_shift_end'] = t("shift_ended")
    else:
        data_meta['time_till_shift_end'] = str(int(timedelta.total_seconds() / 60)) + t("minutes_remaining_suffix")

    return data_meta