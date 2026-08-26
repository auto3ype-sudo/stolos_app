import streamlit as st
import pandas as pd
import datetime
import json
import os

# SETUP & CONFIGURATION
st.set_page_config(
    page_title="Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State Database
if "vehicles" not in st.session_state:
    st.session_state.vehicles = pd.DataFrame(columns=[
        "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
        "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
        "TotalMaintenanceCost", "SustainabilityStatus"
    ])

# SIDEBAR NAVIGATION
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
    
    # Υπολογισμός οχημάτων ανά κατάσταση
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
        status_filter = st.multiselect(
            "Φιλτράρισμα ανά Κατάσταση:",
            options=["Ενεργό", "Σε Βλάβη", "Σε Απόσυρση", "Αποσύρθηκε"],
            default=["Ενεργό", "Σε Βλάβη", "Σε Απόσυρση", "Αποσύρθηκε"]
        )
        filtered_df = st.session_state.vehicles[st.session_state.vehicles['Status'].isin(status_filter)]
        st.dataframe(filtered_df, use_container_width=True)

# PAGE 2: VEHICLE CARD
elif menu == "Καρτέλα Οχήματος":
    st.title("📋 Καρτέλα Οχήματος & Ιστορικό")
    if st.session_state.vehicles.empty:
        st.warning("Παρακαλώ καταχωρήστε πρώτα οχήματα.")
    else:
        selected_plate = st.selectbox("Επιλέξτε Πινακίδα Οχήματος", st.session_state.vehicles["LicensePlate"].unique())
        veh_info = st.session_state.vehicles[st.session_state.vehicles["LicensePlate"] == selected_plate]
        st.write(veh_info)

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
                        # Διαβάζουμε μόνο τα φύλλα που περιέχουν λίστες οχημάτων
                        if "ΟΧΗΜΑΤΑ" in sheet.upper():
                            df_sheet = xl.parse(sheet)
                            
                            for _, row in df_sheet.iterrows():
                                plate = row.get("ΑΡΙΘΜ_ΚΥΚΛ")
                                if pd.isna(plate):
                                    continue
                                
                                # Χαρτογράφηση κατάστασης
                                raw_status = str(row.get("ΛΕΙΤΟΥΡΓΙΚΗ_ΚΑΤΑΣΤΑΣΗ", "")).upper()
                                if "ΚΑΛΗ" in raw_status or "ΣΕ ΚΥΚΛΟΦΟΡΙΑ" in raw_status:
                                    status = "Ενεργό"
                                elif "ΒΛΑΒΗ" in raw_status or "ΕΠΙΣΚΕΥΗ" in raw_status:
                                    status = "Σε Βλάβη"
                                elif "ΠΑΡΟΠΛΙΣΜΕΝΟ" in raw_status or "ΑΠΟΣΥΡΣΗ" in raw_status:
                                    status = "Σε Απόσυρση"
                                else:
                                    status = "Ενεργό"
                                
                                make = str(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ", "")) if not pd.isna(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ")) else ""
                                model = str(row.get("ΜΟΝΤΕΛΟ", "")) if not pd.isna(row.get("ΜΟΝΤΕΛΟ")) else ""
                                make_model = f"{make} {model}".strip() or "Άγνωστο"
                                
                                parsed_vehicles.append({
                                    "VIN": str(row.get("ΑΡΙΘΜ_ΠΛΑΙΣΙΟΥ", "Δ/Α")),
                                    "LicensePlate": str(plate).strip(),
                                    "MakeModel": make_model,
                                    "Year": int(row.get("ΕΤΟΣ_ΚΑΤΑΣΚΕΥΗΣ")) if pd.notna(row.get("ΕΤΟΣ_ΚΑΤΑΣΚΕΥΗΣ")) else 2020,
                                    "FuelType": str(row.get("ΚΑΥΣΙΜΟ", "Diesel")),
                                    "Status": status,
                                    "Driver": str(row.get("ΦΟΡΕΑΣ_ΧΡΗΣΗΣ", "Αναμονή Ανάθεσης")),
                                    "TotalKM": float(row.get("ΧΛΜ_1_1_2022", 0)) if pd.notna(row.get("ΧΛΜ_1_1_2022")) else 0,
                                    "MonthlyKM": float(row.get("ΚΜ/ΕΤΟΣ", 0))/12 if pd.notna(row.get("ΚΜ/ΕΤΟΣ")) else 0,
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
                st.session_state.vehicles = pd.concat([st.session_state.vehicles, new_df], ignore_index=True).drop_duplicates(subset=["LicensePlate"])
                st.success(f"Εισήχθησαν επιτυχώς {len(st.session_state.vehicles)} πραγματικά οχήματα! Μεταβείτε στο 'Dashboard Στόλου'.")
                st.rerun()

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
