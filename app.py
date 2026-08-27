import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(
    page_title="Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Αρχικοποίηση session state
if "vehicles" not in st.session_state:
    st.session_state.vehicles = pd.DataFrame(columns=[
        "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
        "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
        "TotalMaintenanceCost", "SustainabilityStatus"
    ])

# --- SIDEBAR ---
st.sidebar.title("🚛 Fleet Manager")
st.sidebar.success("📌 Έκδοση: **v3.1 - PDF & Excel Ready**")
st.sidebar.caption("Google Account: auto3ype@gmail.com")

menu = st.sidebar.radio(
    "Μενού Πλοήγησης",
    ["Dashboard Στόλου", "Καρτέλα Οχήματος", "Εισαγωγή PDF & Excel", "Google Drive Watcher", "Διαχείριση Οδηγών"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Κατάσταση Στόλου")
total_count = len(st.session_state.vehicles)
st.sidebar.write(f"Συνολικά Οχήματα: **{total_count}**")

if not st.session_state.vehicles.empty:
    csv = st.session_state.vehicles.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Λήψη Backup (CSV)",
        data=csv,
        file_name="fleet_backup.csv",
        mime="text/csv"
    )

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
        st.info("Δεν έχουν καταχωρηθεί ακόμα οχήματα. Χρησιμοποιήστε την ενότητα 'Εισαγωγή PDF & Excel'.")
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
        st.dataframe(veh_info, use_container_width=True)

# PAGE 3: IMPORT PDF & EXCEL
elif menu == "Εισαγωγή PDF & Excel":
    st.title("📂 Μαζική Εισαγωγή Στοιχείων Στόλου")
    st.markdown("👉 Ανεβάστε αρχεία **Excel (.xlsx)** ή **Searchable PDF**.")
    
    uploaded_files = st.file_uploader(
        "Επιλέξτε αρχεία Excel (.xlsx) ή PDF",
        type=["xlsx", "xls", "pdf"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("🔄 Επεξεργασία & Συγχρονισμός", type="primary"):
            parsed_vehicles = []
            
            with st.spinner("Γίνεται επεξεργασία αρχείων..."):
                for file in uploaded_files:
                    # 1. Επεξεργασία Excel
                    if file.name.endswith(('.xlsx', '.xls')):
                        try:
                            xl = pd.ExcelFile(file)
                            for sheet in xl.sheet_names:
                                df_sheet = xl.parse(sheet)
                                df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]
                                
                                for _, row in df_sheet.iterrows():
                                    plate = row.get("ΑΡΙΘΜ_ΚΥΚΛ") or row.get("ΠΙΝΑΚΙΔΑ") or row.get("LICENSEPLATE")
                                    if pd.isna(plate) or str(plate).strip() == "" or str(plate).strip() == "nan":
                                        continue
                                    
                                    clean_plate = str(plate).strip().upper().replace(" ", "").replace("-", "")
                                    vin = str(row.get("ΑΡΙΘΜ_ΠΛΑΙΣΙΟΥ", row.get("VIN", "Δ/Α"))).strip()
                                    make = str(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ", row.get("ΜΑΡΚΑ", ""))).strip()
                                    model = str(row.get("ΜΟΝΤΕΛΟ", "")).strip()
                                    fuel = str(row.get("ΚΑΥΣΙΜΟ", "Diesel")).strip()
                                    driver = str(row.get("ΦΟΡΕΑΣ_ΧΡΗΣΗΣ", row.get("ΟΔΗΓΟΣ", "Αναμονή"))).strip()
                                    km = row.get("ΧΛΜ_1_1_2022", row.get("TOTALKM", 0))
                                    
                                    try:
                                        km_val = float(km) if pd.notna(km) else 0.0
                                    except:
                                        km_val = 0.0

                                    parsed_vehicles.append({
                                        "VIN": vin if vin != "nan" else "Δ/Α",
                                        "LicensePlate": clean_plate,
                                        "MakeModel": f"{make} {model}".strip() if (make or model) else "Άγνωστο",
                                        "Year": 2020,
                                        "FuelType": fuel if fuel != "nan" else "Diesel",
                                        "Status": "Ενεργό",
                                        "Driver": driver if driver != "nan" else "Αναμονή",
                                        "TotalKM": km_val,
                                        "MonthlyKM": 0.0,
                                        "TireCondition": "Καλή",
                                        "TotalMaintenanceCost": 0.0,
                                        "SustainabilityStatus": "ΟΚ"
                                    })
                        except Exception as e:
                            st.error(f"Σφάλμα στο Excel `{file.name}`: {e}")

                    # 2. Επεξεργασία Searchable PDF
                    elif file.name.endswith('.pdf'):
                        extracted_text = ""
                        try:
                            with pdfplumber.open(file) as pdf:
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    if text:
                                        extracted_text += text + "\n"
                        except Exception as e:
                            st.warning(f"Αδυναμία ανάγνωσης κειμένου από το {file.name}: {e}")

                        # Αναζήτηση Πινακίδας
                        plate_match = re.search(r'([A-ZΆ-Ω]{3}\s*[-]?\s*\d{4})', extracted_text.upper())
                        if not plate_match:
                            plate_match = re.search(r'([A-ZΆ-Ω]{3}\s*[-]?\s*\d{4})', file.name.upper())
                        
                        plate = plate_match.group(1).replace(" ", "").replace("-", "") if plate_match else "ΑΓΝΩΣΤΗ"

                        # Αναζήτηση VIN
                        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', extracted_text.upper())
                        vin = vin_match.group(0) if vin_match else "Δ/Α (Από PDF)"

                        parsed_vehicles.append({
                            "VIN": vin,
                            "LicensePlate": plate,
                            "MakeModel": "Έγγραφο Άδειας (PDF)",
                            "Year": 2020,
                            "FuelType": "Diesel",
                            "Status": "Ενεργό",
                            "Driver": "Αναμονή",
                            "TotalKM": 0.0,
                            "MonthlyKM": 0.0,
                            "TireCondition": "Καλή",
                            "TotalMaintenanceCost": 0.0,
                            "SustainabilityStatus": "ΟΚ"
                        })

                if parsed_vehicles:
                    new_df = pd.DataFrame(parsed_vehicles)
                    st.session_state.vehicles = pd.concat([st.session_state.vehicles, new_df], ignore_index=True).drop_duplicates(subset=["LicensePlate"], keep="first").reset_index(drop=True)
                    st.success(f"Εισήχθησαν επιτυχώς {len(parsed_vehicles)} εγγραφές!")
                    st.info("💡 Μεταβείτε στο 'Dashboard Στόλου' για να δείτε τα αποτελέσματα.")

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
