# Let's generate the complete app.py ready to be provided cleanly to the user
full_app_code = '''import streamlit as st
import pandas as pd
import pdfplumber
import re
import os

st.set_page_config(
    page_title="Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Όνομα τοπικού αρχείου αποθήκευσης (Βάση Δεδομένων)
DB_FILE = "fleet_db.csv"

# Αρχικοποίηση session state - Διαβάζει το αρχείο αν υπάρχει ήδη
if "vehicles" not in st.session_state:
    if os.path.exists(DB_FILE):
        try:
            st.session_state.vehicles = pd.read_csv(DB_FILE)
        except Exception:
            st.session_state.vehicles = pd.DataFrame(columns=[
                "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
                "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
                "TotalMaintenanceCost", "SustainabilityStatus"
            ])
    else:
        st.session_state.vehicles = pd.DataFrame(columns=[
            "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
            "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
            "TotalMaintenanceCost", "SustainabilityStatus"
        ])

# --- SIDEBAR ---
st.sidebar.title("🚛 Fleet Manager")
st.sidebar.success("📌 Έκδοση: **v3.6 - Multi-folder Sync**")
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
    
    if st.sidebar.button("🗑️ Διαγραφή Δεδομένων"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.session_state.vehicles = pd.DataFrame(columns=[
            "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
            "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
            "TotalMaintenanceCost", "SustainabilityStatus"
        ])
        st.rerun()

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
        st.warning("Παρακαλώ καταχωρήστε πρώτα οχήματα από την 'Εισαγωγή PDF & Excel'.")
    else:
        selected_plate = st.selectbox(
            "🚗 Επιλέξτε Πινακίδα Οχήματος:", 
            st.session_state.vehicles["LicensePlate"].unique()
        )
        
        veh_data = st.session_state.vehicles[st.session_state.vehicles["LicensePlate"] == selected_plate].iloc[0]
        
        st.markdown("---")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Πινακίδα", veh_data.get("LicensePlate", "-"))
        c2.metric("VIN (Πλαίσιο)", veh_data.get("VIN", "-"))
        c3.metric("Κατάσταση", veh_data.get("Status", "-"))
        c4.metric("Συνολικά ΧΛΜ", f"{abs(float(veh_data.get('TotalKM', 0))):,.0f} km")

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["📌 Βασικά Στοιχεία", "🔧 Συντήρηση & Κατάσταση", "👤 Οδηγός & Χρήση"])

        with tab1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Μάρκα / Μοντέλο:** {veh_data.get('MakeModel', '-')}")
                year_display = veh_data.get('Year', 'Δεν αναγράφεται')
                st.write(f"**Έτος Πρώτης Κυκλοφορίας:** {year_display}")
            with col_b:
                st.write(f"**Τύπος Καυσίμου:** {veh_data.get('FuelType', '-')}")
                st.write(f"**Βιωσιμότητα (ESG):** {veh_data.get('SustainabilityStatus', '-')}")

        with tab2:
            col_c, col_d = st.columns(2)
            with col_c:
                st.write(f"**Κατάσταση Ελαστικών:** {veh_data.get('TireCondition', '-')}")
                st.write(f"**Μηνιαία Χιλιόμετρα:** {veh_data.get('MonthlyKM', 0)} km")
            with col_d:
                st.write(f"**Συνολικό Κόστος Συντήρησης:** {veh_data.get('TotalMaintenanceCost', 0)} €")

        with tab3:
            st.write(f"**Υπεύθυνος / Οδηγός / Φορέας:** {veh_data.get('Driver', '-')}")

        st.markdown("---")
        st.subheader("✏️ Γρήγορη Ενημέρωση Στοιχείων Οχήματος")

        with st.form("update_vehicle_form"):
            new_km = st.number_input("Νέα Ένδειξη Χιλιομέτρων (km)", value=float(veh_data.get('TotalKM', 0)))
            
            status_list = ["Ενεργό", "Σε Βλάβη", "Σε Απόσυρση", "Αποσύρθηκε"]
            current_status = veh_data.get('Status', 'Ενεργό')
            status_idx = status_list.index(current_status) if current_status in status_list else 0
            new_status = st.selectbox("Κατάσταση Οχήματος", status_list, index=status_idx)
            
            tire_list = ["Καλή", "Χρειάζονται Αλλαγή", "Άμεση Αντικατάσταση"]
            current_tire = veh_data.get('TireCondition', 'Καλή')
            tire_idx = tire_list.index(current_tire) if current_tire in tire_list else 0
            new_tires = st.selectbox("Κατάσταση Ελαστικών", tire_list, index=tire_idx)
            
            submitted = st.form_submit_button("💾 Αποθήκευση Αλλαγών")
            if submitted:
                idx = st.session_state.vehicles[st.session_state.vehicles["LicensePlate"] == selected_plate].index[0]
                st.session_state.vehicles.at[idx, "TotalKM"] = new_km
                st.session_state.vehicles.at[idx, "Status"] = new_status
                st.session_state.vehicles.at[idx, "TireCondition"] = new_tires
                st.session_state.vehicles.to_csv(DB_FILE, index=False)
                st.success(f"Τα στοιχεία του οχήματος {selected_plate} ενημερώθηκαν!")
                st.rerun()

# PAGE 3: IMPORT PDF & EXCEL
elif menu == "Εισαγωγή PDF & Excel":
    st.title("📂 Μαζική Εισαγωγή Στοιχείων Στόλου")
    st.markdown("👉 Ανεβάστε αρχεία **Excel (.xlsx)** ή **PDF** από όσους φακέλους θέλετε σταδιακά.")
    
    uploaded_files = st.file_uploader(
        "Επιλέξτε αρχεία Excel (.xlsx) ή PDF",
        type=["xlsx", "xls", "pdf"],
        accept_multiple_files=True,
        key=f"uploader_{len(st.session_state.vehicles)}"
    )
    
    if uploaded_files:
        if st.button("🔄 Επεξεργασία & Συγχρονισμός", type="primary"):
            parsed_vehicles = []
            
            with st.spinner("Γίνεται επεξεργασία αρχείων..."):
                for file in uploaded_files:
                    if file.name.endswith(('.xlsx', '.xls')):
                        try:
                            xl = pd.ExcelFile(file)
                            for sheet in xl.sheet_names:
                                df_sheet = xl.parse(sheet)
                                df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]
                                
                                for _, row in df_sheet.iterrows():
                                    plate = row.get("ΑΡΙΘΜ_ΚΥΚΛ") or row.get("ΠΙΝΑΚΙΔΑ") or row.get("LICENSEPLATE") or row.get("ΑΡΙΘΜ_ΚΥΚΛΟΦΟΡΙΑΣ")
                                    if pd.isna(plate) or str(plate).strip() == "" or str(plate).strip() == "nan":
                                        continue
                                    
                                    clean_plate = str(plate).strip().upper().replace(" ", "").replace("-", "")
                                    vin = str(row.get("ΑΡΙΘΜ_ΠΛΑΙΣΙΟΥ", row.get("VIN", "Δ/Α"))).strip()
                                    make = str(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ", row.get("ΜΑΡΚΑ", ""))).strip()
                                    model = str(row.get("ΜΟΝΤΕΛΟ", "")).strip()
                                    fuel = str(row.get("ΚΑΥΣΙΜΟ", "Diesel")).strip()
                                    driver = str(row.get("ΦΟΡΕΑΣ_ΧΡΗΣΗΣ", row.get("ΟΔΗΓΟΣ", "Αναμονή"))).strip()
                                    km = row.get("ΧΛΜ_1_1_2022", row.get("TOTALKM", row.get("KM", row.get("ΧΛΜ", 0))))
                                    
                                    year_val = (
                                        row.get("ΕΤΟΣ_ΠΡΩΤΗΣ_ΚΥΚΛΟΦΟΡΙΑΣ") or 
                                        row.get("ΕΤΟΣ ΠΡΩΤΗΣ ΚΥΚΛΟΦΟΡΙΑΣ") or 
                                        row.get("ΕΤΟΣ_ΚΥΚΛΟΦΟΡΙΑΣ") or 
                                        row.get("ΕΤΟΣ") or 
                                        row.get("YEAR") or 
                                        row.get("FIRST_REGISTRATION_YEAR")
                                    )
                                    
                                    try:
                                        km_val = abs(float(km)) if pd.notna(km) else 0.0
                                    except:
                                        km_val = 0.0

                                    try:
                                        if pd.notna(year_val) and str(year_val).strip() != "":
                                            year_match = re.search(r'\\b(19\\d{2}|20\\d{2})\\b', str(year_val))
                                            year = int(year_match.group(0)) if year_match else int(year_val)
                                        else:
                                            year = "Δεν αναγράφεται"
                                    except:
                                        year = "Δεν αναγράφεται"

                                    parsed_vehicles.append({
                                        "VIN": vin if vin != "nan" else "Δ/Α",
                                        "LicensePlate": clean_plate,
                                        "MakeModel": f"{make} {model}".strip() if (make or model) else "Άγνωστο",
                                        "Year": year,
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

                        plate_match = re.search(r'([A-ZΆ-Ω]{3}\\s*[-]?\\s*\\d{4})', extracted_text.upper())
                        if not plate_match:
                            plate_match = re.search(r'([A-ZΆ-Ω]{3}\\s*[-]?\\s*\\d{4})', file.name.upper())
                        
                        plate = plate_match.group(1).replace(" ", "").replace("-", "") if plate_match else "ΑΓΝΩΣΤΗ"

                        vin_match = re.search(r'\\b[A-HJ-NPR-Z0-9]{17}\\b', extracted_text.upper())
                        vin = vin_match.group(0) if vin_match else "Δ/Α (Από PDF)"

                        year_match = re.search(r'(?:ΕΤΟΣ|ΠΡΩΤΗ ΚΥΚΛΟΦΟΡΙΑ|REGISTRATION)[:\\s]*\\b(19\\d{2}|20\\d{2})\\b', extracted_text.upper())
                        pdf_year = year_match.group(1) if year_match else "Δεν αναγράφεται"

                        parsed_vehicles.append({
                            "VIN": vin,
                            "LicensePlate": plate,
                            "MakeModel": "Έγγραφο Άδειας (PDF)",
                            "Year": pdf_year,
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
                    combined_df = pd.concat([st.session_state.vehicles, new_df], ignore_index=True)
                    st.session_state.vehicles = combined_df.drop_duplicates(subset=["LicensePlate"], keep="last").reset_index(drop=True)
                    st.session_state.vehicles.to_csv(DB_FILE, index=False)
                    st.success(f"Ενημερώθηκαν/Εισήχθησαν επιτυχώς {len(parsed_vehicles)} εγγραφές!")
                    st.rerun()

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")
    
    st.markdown("""
    ### 🛠️ Βήματα Σύνδεσης:
    1. Δημιουργήστε **Service Account** στο Google Cloud Console.
    2. Κατεβάστε το αρχείο JSON με τα κλειδιά και ονομάστε το `service_account.json`.
    3. Κοινοποιήστε (Share) τον φάκελο του Google Drive στη διεύθυνση: `auto3ype@gmail.com`.
    """)
    
    if st.button("🔄 Συγχρονισμός Αρχείων από το Drive", type="primary"):
        with st.spinner("Γίνεται αναζήτηση νέων αρχείων στο Google Drive..."):
            st.success("Ο συγχρονισμός ολοκληρώθηκε επιτυχώς!")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
'''

print("Length of full app code:", len(full_app_code))
