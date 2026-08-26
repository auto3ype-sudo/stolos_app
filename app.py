import streamlit as st
import pandas as pd
import re
import numpy as np
from PIL import Image
import pdfplumber

st.set_page_config(
    page_title="Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Φόρτωση του EasyOCR Engine (Lazy Load για ταχύτητα)
@st.cache_resource
def load_ocr_reader():
    import easyocr
    return easyocr.Reader(['el', 'en'], gpu=False)

if "vehicles" not in st.session_state:
    st.session_state.vehicles = pd.DataFrame(columns=[
        "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
        "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
        "TotalMaintenanceCost", "SustainabilityStatus"
    ])

def parse_pdf_registration(pdf_file):
    """Εξαγωγή στοιχείων από PDF άδειας κυκλοφορίας με χρήση OCR"""
    plate, vin, make_model, fuel = None, "Δ/Α", "Έγγραφο Άδειας (PDF)", "Δ/Α"
    
    # 1. Προσπάθεια ανάγνωσης με pdfplumber (Text PDF)
    try:
        with pdfplumber.open(pdf_file) as pdf:
            full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    except Exception:
        full_text = ""

    # Αν το PDF είναι σκαναρισμένο (εικόνα), χρησιμοποιούμε EasyOCR
    if len(full_text.strip()) < 20:
        try:
            reader = load_ocr_reader()
            with pdfplumber.open(pdf_file) as pdf:
                full_text = ""
                for page in pdf.pages:
                    pix = page.to_image(resolution=150)
                    img = pix.original
                    results = reader.readtext(np.array(img), detail=0)
                    full_text += "\n" + "\n".join(results)
        except Exception:
            pass

    # --- REGEX PARSING ---
    # Πινακίδα (ΑΡΙΘΜΟΣ ΚΥΚΛΟΦΟΡΙΑΣ)
    plate_match = re.search(r'([A-ZΆ-Ω]{3}\s*[-]?\s*\d{4})', full_text.upper())
    if plate_match:
        plate = plate_match.group(1).replace(" ", "").replace("-", "")
    else:
        file_match = re.search(r'([A-ZΆ-Ω]{3}\s*\d{4})', pdf_file.name.upper())
        plate = file_match.group(1) if file_match else pdf_file.name.replace('.pdf', '')

    # VIN / Αριθμός Πλαισίου (Πεδίο E - 17 χαρακτήρες)
    vin_match = re.search(r'\b([A-HJ-NPR-Z0-9]{17})\b', full_text.upper())
    if vin_match:
        vin = vin_match.group(1)

    # Καύσιμο (Πεδίο P.3)
    if "PETROL" in full_text.upper() or "BENZIN" in full_text.upper() or "ΒΕΝΖΙΝΗ" in full_text.upper():
        fuel = "Βενζίνη"
    elif "DIESEL" in full_text.upper() or "ΠΕΤΡΕΛΑΙΟ" in full_text.upper():
        fuel = "Diesel"

    # Μάρκα / Μοντέλο
    makes = ["TOYOTA", "MERCEDES", "FORD", "NISSAN", "VOLKSWAGEN", "FIAT", "PEUGEOT", "RENAULT", "SKODA", "CITROEN"]
    found_make = ""
    for m in makes:
        if m in full_text.upper():
            found_make = m
            break
    
    if found_make:
        make_model = found_make
        if "YARIS" in full_text.upper(): make_model += " Yaris"
        elif "SPRINTER" in full_text.upper(): make_model += " Sprinter"
        elif "TRANSIT" in full_text.upper(): make_model += " Transit"

    return {
        "VIN": vin,
        "LicensePlate": plate,
        "MakeModel": make_model,
        "Year": 2020,
        "FuelType": fuel,
        "Status": "Ενεργό",
        "Driver": "Αναμονή",
        "TotalKM": 0.0,
        "MonthlyKM": 0.0,
        "TireCondition": "Καλή",
        "TotalMaintenanceCost": 0.0,
        "SustainabilityStatus": "ΟΚ"
    }

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
                    for sheet in xl.sheet_names:
                        if "ΟΧΗΜΑΤΑ" in sheet.upper():
                            df_sheet = xl.parse(sheet)
                            for _, row in df_sheet.iterrows():
                                plate = row.get("ΑΡΙΘΜ_ΚΥΚΛ")
                                if pd.isna(plate) or str(plate).strip() == "":
                                    continue
                                
                                clean_plate = str(plate).strip()
                                make = str(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ", "")) if pd.notna(row.get("ΚΑΤΑΣΚΕΥΑΣΤΗΣ")) else ""
                                model = str(row.get("ΜΟΝΤΕΛΟ", "")) if pd.notna(row.get("ΜΟΝΤΕΛΟ")) else ""
                                
                                parsed_vehicles.append({
                                    "VIN": str(row.get("ΑΡΙΘΜ_ΠΛΑΙΣΙΟΥ", "Δ/Α")),
                                    "LicensePlate": clean_plate,
                                    "MakeModel": f"{make} {model}".strip() or "Άγνωστο",
                                    "Year": 2020,
                                    "FuelType": str(row.get("ΚΑΥΣΙΜΟ", "Diesel")),
                                    "Status": "Ενεργό",
                                    "Driver": str(row.get("ΦΟΡΕΑΣ_ΧΡΗΣΗΣ", "Αναμονή")),
                                    "TotalKM": float(row.get("ΧΛΜ_1_1_2022", 0)) if pd.notna(row.get("ΧΛΜ_1_1_2022")) else 0.0,
                                    "MonthlyKM": 0.0,
                                    "TireCondition": "Καλή",
                                    "TotalMaintenanceCost": 0.0,
                                    "SustainabilityStatus": "ΟΚ"
                                })
                except Exception as e:
                    st.error(f"Σφάλμα ανάγνωσης Excel `{file.name}`: {e}")

            elif file.name.endswith('.pdf'):
                try:
                    parsed_item = parse_pdf_registration(file)
                    parsed_vehicles.append(parsed_item)
                except Exception as e:
                    st.error(f"Σφάλμα ανάγνωσης PDF `{file.name}`: {e}")

        st.markdown("---")
        if st.button("🔄 Συγχρονισμός & Ενημέρωση Στόλου στο Dashboard", type="primary"):
            if parsed_vehicles:
                new_df = pd.DataFrame(parsed_vehicles)
                st.session_state.vehicles = pd.concat([st.session_state.vehicles, new_df], ignore_index=True).drop_duplicates(subset=["LicensePlate"], keep="first").reset_index(drop=True)
                st.success(f"Ενημερώθηκαν {len(st.session_state.vehicles)} οχήματα από τα αρχεία σας!")
                st.rerun()

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
