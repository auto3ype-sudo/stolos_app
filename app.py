import streamlit as st
import pandas as pd
import re
import pdfplumber  # pip install pdfplumber

st.set_page_config(page_title="Fleet Management System", layout="wide")

if "vehicles" not in st.session_state:
    st.session_state.vehicles = pd.DataFrame(columns=[
        "VIN", "LicensePlate", "MakeModel", "Year", "FuelType",
        "Status", "Driver", "TotalKM", "MonthlyKM", "TireCondition",
        "TotalMaintenanceCost", "SustainabilityStatus"
    ])

def parse_greek_registration_pdf(pdf_file):
    """Εξάγει πραγματικά στοιχεία από PDF άδειας κυκλοφορίας"""
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    
    # 1. Αριθμός Κυκλοφορίας (Πινακίδα)
    plate_match = re.search(r'(?:ΑΡΙΘΜΟΣ ΚΥΚΛΟΦΟΡΙΑΣ|ΑΡΙΘ\. ΚΥΚΛΟΦΟΡΙΑΣ)\s*[:\.]?\s*([A-ZΆ-Ω]{3}\s*[-]?\s*\d{4})', text, re.IGNORECASE)
    plate = plate_match.group(1).replace(" ", "") if plate_match else None
    if not plate:
        fallback_match = re.search(r'([A-ZΆ-Ω]{3}\s*\d{4})', pdf_file.name.upper())
        plate = fallback_match.group(1) if fallback_match else pdf_file.name.replace('.pdf', '')

    # 2. Αριθμός Πλαισίου (VIN - Πεδίο E)
    vin_match = re.search(r'\((?:E|Ε)\)\s*([A-HJ-NPR-Z0-9]{17})', text)
    vin = vin_match.group(1) if vin_match else "Δ/Α"

    # 3. Μάρκα & Μοντέλο (Πεδία D.1 / D.3)
    make_match = re.search(r'\(D\.1\)\s*([^\n]+)', text)
    model_match = re.search(r'\(D\.3\)\s*([^\n]+)', text)
    make = make_match.group(1).strip() if make_match else ""
    model = model_match.group(1).strip() if model_match else ""
    make_model = f"{make} {model}".strip() or "Έγγραφο Άδειας (PDF)"

    # 4. Καύσιμο (Πεδίο P.3)
    fuel_match = re.search(r'\(P\.3\)\s*([^\n]+)', text)
    fuel = fuel_match.group(1).strip() if fuel_match else "Δ/Α"

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

# --- ΕΝΟΣΩΜΑΤΩΣΗ ΣΤΟ STREAMLIT (Στο "Εισαγωγή PDF & Excel") ---
# Αντικαταστήστε το block "ΕΠΕΞΕΡΓΑΣΙΑ PDF" με το παρακάτω:
"""
elif file.name.endswith('.pdf'):
    try:
        parsed_data = parse_greek_registration_pdf(file)
        parsed_vehicles.append(parsed_data)
        st.success(f"Επιτυχής ανάγνωση PDF: {parsed_data['LicensePlate']} ({parsed_data['MakeModel']})")
    except Exception as e:
        st.error(f"Σφάλμα ανάγνωσης PDF `{file.name}`: {e}")
"""
