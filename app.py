import pdfplumber

# ... (το υπόλοιπο app παραμένει ως έχει) ...

# 2. Επεξεργασία Searchable PDF (Χωρίς OCR)
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

    # Αναζήτηση VIN (17 χαρακτήρες)
    vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', extracted_text.upper())
    vin = vin_match.group(0) if vin_match else "Δ/Α"

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
