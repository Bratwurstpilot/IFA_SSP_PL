# Gemeinsame Forcam-API-Helfer (Token, Workplace-URL, Schichtfenster)
import datetime
import urllib.parse

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import config
import app_logging


def get_auth_header(request, accept_header):
    # Get Token
    # quote_plus: Client-Secret kann Sonderzeichen (& = etc.) enthalten, die den Query-String sonst zerstueckeln
    password = urllib.parse.quote_plus(config.get_credential('forcam_api_user'))
    urlToken = config.FORCAM_TOKEN_URL + "?client_id=" + config.FORCAM_CLIENT_ID + "&client_secret=" + password + "&grant_type=client_credentials&scope=read"

    app_logging.log_api_request("Forcam-Token", urlToken)
    token = request.get(urlToken, verify=False).json()
    accessToken = token['access_token']

    # Request Header — accept_header als (key, value)-Tupel, da Mengen-Report
    # 'Accept': 'application/json...' und Stoerungs-Report 'accept': 'application/hal+json...' erwartet
    request_head = {'Accept-Language': 'en-EN',
        accept_header[0]: accept_header[1],
        'Authorization': 'Bearer {}'.format(accessToken)}

    return request_head


def build_workplace_url(workplaces, ifa_wpl_to_forcam_uuid):
    # Workplace URL
    workplace_url = """"""
    for wpl in workplaces:
        try:
            workplace_url += "&workplace=" + ifa_wpl_to_forcam_uuid[wpl]
        except:
            continue
    return workplace_url


def get_shift_window(selection, night_start):
    # Time URL — night_start unterscheidet sich: 22:02 (Mengen) vs 22:00 (Stoerungen)
    if selection['shift_id'] == 'night_shift':
        shift_start = datetime.datetime.combine(selection['date'] - datetime.timedelta(days=1), night_start)
        shift_end = datetime.datetime.combine(selection['date'], datetime.time(6,0,0))
    elif selection['shift_id'] == 'early_shift':
        shift_start = datetime.datetime.combine(selection['date'], datetime.time(6,0,0))
        shift_end = datetime.datetime.combine(selection['date'], datetime.time(14,0,0))
    elif selection['shift_id'] == 'late_shift':
        shift_start = datetime.datetime.combine(selection['date'], datetime.time(14,0,0))
        shift_end = datetime.datetime.combine(selection['date'], datetime.time(22,0,0))

    return shift_start, shift_end