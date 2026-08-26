import streamlit as st
import pandas as pd
import re
import numpy as np
import pdfplumber
from pdf2image import convert_from_bytes
from PIL import Image

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

# Φόρτωση του EasyOCR Engine
@st.cache_resource
def load_ocr_reader():
    import easyocr
    return easyocr.Reader(['el', 'en'], gpu=False)

def extract_text_from_pdf(pdf_file):
    """Εξαγωγή κειμένου είτε απευθείας είτε μέσω OCR αν είναι εικόνα/scan"""
    full_text = ""
    pdf_bytes = pdf_file.read()
    pdf_file.seek(0)
    
    # 1. Προσπάθεια με pdfplumber
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
    except Exception:
        pass

    # 2. Αν δεν βρέθηκε αρκετό κείμενο, εκτέλεση EasyOCR
    if len(full_text.strip()) < 30:
        try:
            images = convert_from_bytes(pdf_bytes, dpi=200)
            reader = load_ocr_reader()
            for img in images:
                img_np = np.array(img)
                results = reader.readtext(img_np, detail=0)
                full_text += " ".join(results) + "\n"
        except Exception as e:
            st.error(f"Σφάλμα OCR στο αρχείο {pdf_file.name}: {e}")

    return full_text

def parse_pdf_registration(pdf_file):
    """Parsing κειμένου με Regex"""
    full_text = extract_text_from_pdf(pdf_file)
    text_upper = full_text.upper()

    plate, vin, make_model, fuel = None, "Δ/Α", "Άγνωστο Μοντέλο", "Δ/Α"

    # 1. Πινακίδα (ΑΡΙΘΜΟΣ ΚΥΚΛΟΦΟΡΙΑΣ)
    plate_match = re.search(r'([A-ZΆ-Ω]{3}\s*[-]?\s*\d{4})', text_upper)
    if plate_match:
        plate = plate_match.group(1).replace(" ", "").replace("-", "")
    else:
        file_match = re.search(r'([A-ZΆ-Ω]{3}\s*\d{4})', pdf_file.name.upper())
        plate = file_match.group(1) if file_match else pdf_file.name.replace('.pdf', '')

    # 2. VIN / Αριθμός Πλαισίου (17 αλφαριθμητικοί χαρακτήρες)
    vin_match = re.search(r'\b([A-HJ-NPR-Z0-9]{17})\b', text_upper)
    if vin_match:
        vin = vin_match.group(1)

    # 3. Καύσιμο
    if any(k in text_upper for k in ["PETROL", "BENZIN", "ΒΕΝΖΙΝΗ", "BENZINE"]):
        fuel = "Βενζίνη"
    elif any(k in text_upper for k in ["DIESEL", "ΠΕΤΡΕΛΑΙΟ"]):
        fuel = "Diesel"

    # 4. Μάρκα & Μοντέλο
    makes = ["TOYOTA", "MERCEDES", "FORD", "NISSAN", "VOLKSWAGEN", "FIAT", "PEUGEOT", "RENAULT", "SKODA", "CITROEN", "OPEL", "HYUNDAI"]
    found_make = ""
    for m in makes:
        if m in text_upper:
            found_make = m
            break
    
    if found_make:
        make_model = found_make
        if "YARIS" in text_upper: make_model += " Yaris"
        elif "SPRINTER" in text_upper: make_model += " Sprinter"
        elif "TRANSIT" in text_upper: make_model += " Transit"
        elif "COROLLA" in text_upper: make_model += " Corolla"
        elif "CLIO" in text_upper: make_model += " Clio"
    else:
        make_model = "Άδεια Κυκλοφορίας"

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

# --- SIDEBAR ---
st.sidebar.title("🚛 Fleet Manager")
st.sidebar.success("📌 Εκδοση: **v2.4 - Full OCR Engine**")
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
        if st.button("🔄 Επεξεργασία & Συγχρονισμός στο Dashboard", type="primary"):
            parsed_vehicles = []
            
            with st.spinner("Γίνεται ανάγνωση των αδειών κυκλοφορίας μέσω OCR..."):
                for file in uploaded_files:
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
                            st.error(f"Σφάλμα Excel `{file.name}`: {e}")

                    elif file.name.endswith('.pdf'):
                        try:
                            parsed_item = parse_pdf_registration(file)
                            parsed_vehicles.append(parsed_item)
                        except Exception as e:
                            st.error(f"Σφάλμα PDF `{file.name}`: {e}")

                if parsed_vehicles:
                    new_df = pd.DataFrame(parsed_vehicles)
                    st.session_state.vehicles = new_df.drop_duplicates(subset=["LicensePlate"], keep="first").reset_index(drop=True)
                    st.success(f"Ενημερώθηκαν επιτυχώς {len(parsed_vehicles)} οχήματα!")
                    st.info("💡 Μεταβείτε στο 'Dashboard Στόλου' από τη στήλη αριστερά.")

# PAGE 4: GOOGLE DRIVE WATCHER
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")

# PAGE 5: DRIVER MANAGEMENT
elif menu == "Διαχείριση Οδηγών":
    st.title("🧑‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    st.write("Διαχείριση οδηγών στόλου.")
