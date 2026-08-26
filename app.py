import streamlit as st
import pandas as pd
import datetime
import json
import os

# SETUP & CONFIGURATION
st.set_page_config(
    page_title="Fleet Management System (Up to 100 Vehicles)",
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

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=[
        "ExpenseID", "LicensePlate", "InvoiceDate", "Category",
        "Description", "Amount", "Supplier", "SystemTimestamp"
    ])

if "drivers" not in st.session_state:
    st.session_state.drivers = pd.DataFrame(columns=[
        "DriverID", "FullName", "Phone", "Status", "AssignedVehicle"
    ])

# SIDEBAR NAVIGATION
st.sidebar.title("🚛 Fleet Manager v2.0")
st.sidebar.caption("Google Account: auto3ype@gmail.com")

menu = st.sidebar.radio(
    "Μενού Πλοήγησης",
    ["Dashboard Στόλου", "Καρτέλα Οχήματος", "Εισαγωγή PDF & Excel", "Google Drive Watcher", "Διαχείριση Οδηγών"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Όρια Στόλου")
active_count = len(st.session_state.vehicles)
st.sidebar.progress(min(active_count / 100, 1.0))
st.sidebar.write(f"Ενεργά Οχήματα: **{active_count} / 100**")

# PAGE 1: DASHBOARD
if menu == "Dashboard Στόλου":
    st.title("📊 Επισκόπηση Στόλου Οχημάτων")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Σύνολο Οχημάτων", f"{len(st.session_state.vehicles)} / 100")
    col2.metric("Ενεργά Οχήματα", len(st.session_state.vehicles[st.session_state.vehicles['Status'] == 'Ενεργό']) if not st.session_state.vehicles.empty else 0)
    
    total_cost = st.session_state.expenses['Amount'].sum() if not st.session_state.expenses.empty else 0.0
    col3.metric("Συνολικό Κόστος Συντήρησης", f"{total_cost:,.2f} €")
    col4.metric("Ασύμφορα Οχήματα (Alerts)", 0)

    st.markdown("---")
    st.subheader("Πίνακας Οχημάτων Στόλου")
    if st.session_state.vehicles.empty:
        st.info("Δεν έχουν καταχωρηθεί ακόμα οχήματα. Χρησιμοποιήστε την ενότητα 'Εισαγωγή PDF & Excel' για μαζική εισαγωγή.")
    else:
        st.dataframe(st.session_state.vehicles, use_container_width=True)

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
                    
                    # Παράδειγμα εξαγωγής εγγραφών από τα φύλλα
                    for sheet in xl.sheet_names:
                        df_sheet = xl.parse(sheet)
                        # Δημιουργία δοκιμαστικού οχήματος αν βρεθούν δεδομένα
                        parsed_vehicles.append({
                            "VIN": f"VIN-{sheet[:5]}",
                            "LicensePlate": f"KHK-{len(parsed_vehicles)+1000}",
                            "MakeModel": f"Όχημα ({sheet})",
                            "Year": 2022,
                            "FuelType": "Diesel",
                            "Status": "Ενεργό",
                            "Driver": "Αναμονή Ανάθεσης",
                            "TotalKM": 150000,
                            "MonthlyKM": 2500,
                            "TireCondition": "Καλή",
                            "TotalMaintenanceCost": 450.00,
                            "SustainabilityStatus": "ΟΚ"
                        })
                except Exception as e:
                    st.error(f"Σφάλμα ανάγνωσης Excel: {e}")

        st.markdown("---")
        if st.button("🔄 Συγχρονισμός & Ενημέρωση Στόλου στο Dashboard", type="primary"):
            if parsed_vehicles:
                new_df = pd.DataFrame(parsed_vehicles)
                st.session_state.vehicles = pd.concat([st.session_state.vehicles, new_df], ignore_index=True).drop_duplicates(subset=["LicensePlate"])
                st.success("Ο στόλος ενημερώθηκε επιτυχώς! Μεταβείτε στο 'Dashboard Στόλου' για να δείτε τα αποτελέσματα.")
                st.rerun()

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")
    if st.button("🔄 Χειροκίνητος Συγχρονισμός Drive Τώρα"):
        st.warning("Έλεγχος φακέλου Drive... Για αυτόματη ανάγνωση απαιτείται η εισαγωγή των API Secrets στο Streamlit Cloud.")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
