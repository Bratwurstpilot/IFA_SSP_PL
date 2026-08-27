# Entrypoint fuer die SSP-Webapp — Start via: streamlit run main_v3_1.py
# Gesamte Logik liegt in den Modulen: config, db, forcam_api, meta,
# data_general, data_quantities, data_disturbances, email_report, ui
from ui import main

if __name__ == "__main__":
    main()