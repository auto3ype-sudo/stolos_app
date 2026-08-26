import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "vehicles" not in st.session_state:
    st.session_state.vehicles = pd.DataFrame(columns=[
        "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
        "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
        "TotalMaintenanceCost", "SustainabilityStatus"
    ])

st.sidebar.title("🚛 Fleet Manager v2.0")
st.sidebar.caption("Google Account: auto3ype@gmail.com")

menu = st.sidebar.radio(
    "Μενού Πλοήγησης",
    ["Dashboard Στόλου", "Καρτέλα Οχήματος", "Εισαγωγή PDF & Excel", "Google Drive Watcher", "Διαχείριση Οδηγών"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Κατάσταση Στόλου")
total_count = len(st.session_state.vehicles)
st.sidebar.write(f"Συνολικά Οχήματα: **{total_count}**")

# PAGE 1: DASHBOARD
if menu == "Dashboard Στόλου":
    st.title("📊 Επισκόπηση Στόλου Οχημάτων")
    
    active_count = len(st.session_state.vehicles[st.session_state.vehicles['Status'] == 'Ενεργό']) if not st.session_state.vehicles.empty else 0
    breakdown_count = len(st.session_state.vehicles[st.session_state.vehicles['Status'] == 'Σε Βλάβη']) if not st.session_state.vehicles.empty else 0
    pending_retire_count = len(st.session_state.vehicles[st.session_state.vehicles['Status'] == 'Σε Απόσυρση']) if not st.session_state.vehicles.empty else 0
    retired_count = len(st.session_state.vehicles[st.session_state.vehicles['Status'] == 'Αποσύρθηκε']) if not st.session_state.vehicles.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 Ενεργά", active_count)
    col2.metric("🟠 Σε Βλάβη", breakdown_count)
    col3.metric("🟡 Σε Απόσυρση", pending_retire_count)
    col4.metric("🔴 Αποσύρθηκαν", retired_count)

    st.markdown("---")
    st.subheader("Πίνακας Οχημάτων Στόλου")
    if st.session_state.vehicles.empty:
        st.info("Δεν έχουν καταχωρηθεί ακόμα οχήματα. Χρησιμοποιήστε την ενότητα 'Εισαγωγή PDF & Excel' για μαζική εισαγωγή.")
    else:
        # Φίλτρο με Checkboxes αντί για κόκκινα tags
        st.write("🔍 **Φιλτράρισμα Προβολής:**")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        show_active = f_col1.checkbox("🟢 Ενεργά", value=True)
        show_breakdown = f_col2.checkbox("🟠 Σε Βλάβη", value=True)
        show_pending = f_col3.checkbox("🟡 Σε Απόσυρση", value=True)
        show_retired = f_col4.checkbox("🔴 Αποσύρθηκαν", value=True)

        selected_statuses = []
        if show_active: selected_statuses.append("Ενεργό")
        if show_breakdown: selected_statuses.append("Σε Βλάβη")
        if show_pending: selected_statuses.append("Σε Απόσυρση")
        if show_retired: selected_statuses.append("Αποσύρθηκε")

        filtered_df = st.session_state.vehicles[st.session_state.vehicles['Status'].isin(selected_statuses)]
        st.dataframe(filtered_df, use_container_width=True)

        # Καθαρισμός/Διαγραφή Δεδομένων αν χρειάζεται
        st.markdown("---")
        if st.button("🗑️ Καθαρισμός Όλων των Δεδομένων Στόλου", type="secondary"):
            st.session_state.vehicles = st.session_state.vehicles.iloc[0:0]
            st.rerun()

# PAGE 2: VEHICLE CARD
elif menu == "Καρτέλα Οχήματος":
    st.title("📋 Καρτέλα Οχήματος & Ιστορικό")
    if st.session_state.vehicles.empty:
        st.warning("Παρακαλώ καταχωρήστε πρώτα οχήματα.")
    else:
        selected_plate = st.selectbox("Επιλέξτε Πινακίδα Οχήματος", st.session_state.vehicles["LicensePlate"].unique())
        veh_info = st.session_state.vehicles[st.session_state.vehicles["LicensePlate"] == selected_plate]
        st.dataframe(veh_info, use_container_width=True)

# PAGE 3: IMPORT PDF & EXCEL
elif menu == "Εισαγωγή PDF & Excel":
    st.title("📂 Αυτόματη Αναγνώριση Εγγράφων (PDF & Excel)")
    
    uploaded_files = st.file_uploader(
        "Επιλέξτε αρχεία PDF ή Excel",
        type=["pdf", "xlsx", "xls"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        parsed_vehicles = []
        
        for file in uploaded_files:
            st.write(f"📄 **Επεξεργασία αρχείου:** `{file.name}`")
            if file.name.endswith(('.xlsx', '.xls')):
                try:
                    xl = pd.ExcelFile(file)
                    st.success(f"Εντοπίστηκαν {len(xl.sheet_names)} φύλλα στο Excel: {', '.join(xl.sheet_names)}")
                    
                    for sheet in xl.sheet_names:
                        if "ΟΧΗΜΑΤΑ" in sheet.upper():
                            df_sheet = xl.parse(sheet)
                            
                            for _, row in df_sheet.iterrows():
                                plate = row.get("ΑΡΙΘΜ_ΚΥΚΛ")
                                if pd.isna(plate) or str(plate).strip() == "":
                                    continue
                                
                                clean_plate = str(plate).strip()

                                raw_year = row.get("ΕΤΟΣ_ΚΑΤΑΣΚΕΥΗΣ")
                                year_val = 2020
                                if pd.notna(raw_year):
                                    try:
                                        if isinstance(raw_year, (pd.Timestamp, datetime.datetime)):
                                            year_val = raw_year.year
                                        else:
                                            year_val = int(float(str(raw_year).split('-')[0]))
                                    except Exception:
                                        year_val = 2020

                                km_val = 0.0
                                for km_col in ["ΧΛΜ_1_1_2022", "ΧΛΜ_1_5_2021", "ΧΛΜ_1_1_2020", "km"]:
                                    if km_col in row and pd.notna(row[km_col]):
                                        try:
                                            km_val = float(row[km_col])
                                            if km_val > 0:
                                                break
                                        except Exception:
                                            pass

                                raw_status = (str(row.get("ΛΕΙΤΟΥΡΓΙΚΗ_ΚΑΤΑΣΤΑΣΗ", "")) + " " + str(row.get("ΚΑΤΑΣΤΑΣΗ 1/11/2024", ""))).upper()
                                if "ΠΑΡΟΠΛΙΣΜΕΝΟ" in raw_status or "ΑΠΟΣΥΡΣΗ" in raw_status or "ΕΠΙΣΤΡΑΦΕΙ" in raw_status:
                                    status = "Σε Απόσυρση"
                                elif "ΒΛΑΒΗ" in raw_status or "ΕΠΙΣΚΕΥΗ" in raw_status or "ΚΑΚΗ" in raw_status:
                                    status = "Σε Βλάβη"
                                else:
                                    status = "Ενεργό"

                                make = str(row.get("ΚΑΤΑΣΤΑΣΗ", "")) if not pd.isna(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ")) else ""
                                make = str(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ", "")) if not pd.isna(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ")) else ""
                                model = str(row.get("ΜΟΝΤΕΛΟ", "")) if not pd.isna(row.get("ΜΟΝΤΕΛΟ")) else ""
                                make_model = f"{make} {model}".strip() or "Άγνωστο"

                                parsed_vehicles.append({
                                    "VIN": str(row.get("ΑΡΙΘΜ_ΠΛΑΙΣΙΟΥ", "Δ/Α")),
                                    "LicensePlate": clean_plate,
                                    "MakeModel": make_model,
                                    "Year": year_val,
                                    "FuelType": str(row.get("ΚΑΥΣΙΜΟ", "Diesel")),
                                    "Status": status,
                                    "Driver": str(row.get("ΦΟΡΕΑΣ_ΧΡΗΣΗΣ", "Αναμονή Ανάθεσης")),
                                    "TotalKM": km_val,
                                    "MonthlyKM": float(row.get("ΚΜ/ΕΤΟΣ", 0))/12 if (pd.notna(row.get("ΚΜ/ΕΤΟΣ")) and str(row.get("ΚΜ/ΕΤΟΣ")).replace('.','',1).isdigit()) else 0.0,
                                    "TireCondition": "Καλή",
                                    "TotalMaintenanceCost": 0.0,
                                    "SustainabilityStatus": "ΟΚ"
                                })
                except Exception as e:
                    st.error(f"Σφάλμα ανάγνωσης Excel: {e}")

        st.markdown("---")
        if st.button("🔄 Συγχρονισμός & Ενημέρωση Στόλου στο Dashboard", type="primary"):
            if parsed_vehicles:
                new_df = pd.DataFrame(parsed_vehicles)
                st.session_state.vehicles = new_df.drop_duplicates(subset=["LicensePlate"], keep="first").reset_index(drop=True)
                st.success(f"Ενημερώθηκαν {len(st.session_state.vehicles)} μοναδικά οχήματα!")
                st.rerun()

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
