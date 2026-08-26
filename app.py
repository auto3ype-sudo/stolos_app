import streamlit as st
import pandas as pd
import datetime
import json
import os

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Fleet Management System (Up to 100 Vehicles)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State Database for Mock/Demo usage
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

# ---------------------------------------------------------
# AI / DOCUMENT PARSER (MOCK & ENGINE INTEGRATION)
# ---------------------------------------------------------
def parse_license_pdf(file):
    """
    Διαβάζει PDF Αδείας Κυκλοφορίας και επιστρέφει βασικά στοιχεία.
    """
    # Εδώ γίνεται η σύνδεση με το Google Gemini API / Document AI
    return {
        "LicensePlate": "KXY-1234",
        "MakeModel": "Toyota Hilux",
        "VIN": "AHTKB3CD401234567",
        "Year": 2021,
        "FuelType": "Diesel"
    }

def parse_invoice_pdf(file):
    """
    Διαβάζει PDF Τιμολογίου/Προσφοράς διαφόρων προμηθευτών.
    Εξάγει τη ΜΙΑ ημερομηνία που αναγράφεται στο τιμολόγιο.
    """
    return {
        "LicensePlate": "KXY-1234",
        "InvoiceDate": datetime.date(2026, 5, 12),  # Η ημερομηνία που γράφει το τιμολόγιο
        "Supplier": "Service Hellas Α.Ε.",
        "Category": "Επισκευή/Ανταλλακτικά",
        "Amount": 450.00,
        "Description": "Αλλαγή σετ ιμάντα χρονισμού & τακάκια"
    }

def process_bulk_excel(file):
    """
    Διαβάζει πολύσελιδα αρχεία Excel (4-5 φύλλα) για αρχική εισαγωγή σταθερών στοιχείων.
    """
    xls = pd.ExcelFile(file)
    sheets_found = xls.sheet_names
    return sheets_found

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & GDRIVE SYNC
# ---------------------------------------------------------
st.sidebar.title("🚛 Fleet Manager v2.0")
st.sidebar.caption("Google Account: auto3ype@gmail.com")

menu = st.sidebar.radio(
    "Μενού Πλοήγησης",
    ["Dashboard Στόλου", "Καρτέλα Οχήματος", "Εισαγωγή PDF & Excel", "Google Drive Watcher", "Διαχείριση Οδηγών"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Όρια Στόλου")
current_fleet_size = len(st.session_state.vehicles)
st.sidebar.progress(current_fleet_size / 100)
st.sidebar.write(f"Ενεργά Οχήματα: **{current_fleet_size} / 100**")

# ---------------------------------------------------------
# 1. DASHBOARD ΣΤΟΛΟΥ
# ---------------------------------------------------------
if menu == "Dashboard Στόλου":
    st.title("📊 Επισκόπηση Στόλου Οχημάτων")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Σύνολο Οχημάτων", f"{current_fleet_size} / 100")
    col2.metric("Ενεργά Οχήματα", len(st.session_state.vehicles[st.session_state.vehicles["Status"] == "Ενεργό"]))
    
    total_cost = st.session_state.expenses["Amount"].sum() if not st.session_state.expenses.empty else 0.0
    col3.metric("Συνολικό Κόστος Συντήρησης", f"{total_cost:,.2f} €")
    col4.metric("Ασύμφορα Οχήματα (Alerts)", 0)

    st.markdown("---")
    st.subheader("Πίνακας Οχημάτων Στόλου")
    
    if st.session_state.vehicles.empty:
        st.info("Δεν έχουν καταχωρηθεί ακόμα οχήματα. Χρησιμοποιήστε την ενότητα 'Εισαγωγή PDF & Excel' για μαζική εισαγωγή.")
    else:
        st.dataframe(st.session_state.vehicles, use_container_width=True)

# ---------------------------------------------------------
# 2. ΚΑΡΤΕΛΑ ΟΧΗΜΑΤΟΣ (ΕΓΓΡΑΦΕΣ & ΔΙΟΡΘΩΣΕΙΣ)
# ---------------------------------------------------------
elif menu == "Καρτέλα Οχήματος":
    st.title("📋 Καρτέλα Οχήματος & Ιστορικό")
    
    if st.session_state.vehicles.empty:
        st.warning("Παρακαλώ καταχωρήστε πρώτα οχήματα.")
    else:
        selected_plate = st.selectbox("Επιλογή Πινακίδας (KY):", st.session_state.vehicles["LicensePlate"].unique())
        
        vehicle_data = st.session_state.vehicles[st.session_state.vehicles["LicensePlate"] == selected_plate].iloc[0]
        
        # Tabs για οργάνωση πληροφοριών
        tab1, tab2, tab3 = st.tabs(["Στοιχεία & Βιωσιμότητα", "Έξοδα & Τιμολόγια", "Διόρθωση / Νέα Εγγραφή"])
        
        with tab1:
            st.subheader(f"Οχημα: {vehicle_data['LicensePlate']} ({vehicle_data['MakeModel']})")
            c1, c2, c3 = st.columns(3)
            c1.write(f"**VIN:** {vehicle_data['VIN']}")
            c1.write(f"**Έτος:** {vehicle_data['Year']}")
            c2.write(f"**Χιλιομετρική Απόσταση:** {vehicle_data['TotalKM']} km")
            c2.write(f"**Χιλιόμετρα / Μήνα:** {vehicle_data['MonthlyKM']} km")
            c3.write(f"**Κατάσταση Ελαστικών:** {vehicle_data['TireCondition']}")
            c3.write(f"**Δείκτης Βιωσιμότητας:** {vehicle_data['SustainabilityStatus']}")

        with tab2:
            st.subheader("Ιστορικό Τιμολογίων & Επισκευών")
            plate_expenses = st.session_state.expenses[st.session_state.expenses["LicensePlate"] == selected_plate]
            if plate_expenses.empty:
                st.info("Δεν υπάρχουν καταγεγραμμένα έξοδα για το συγκεκριμένο όχημα.")
            else:
                st.dataframe(plate_expenses[["InvoiceDate", "Supplier", "Category", "Description", "Amount", "SystemTimestamp"]], use_container_width=True)

        with tab3:
            st.subheader("Χειροκίνητη Προσθήκη / Διόρθωση Στοιχείων")
            with st.form("edit_vehicle_form"):
                new_km = st.number_input("Ενημέρωση Χιλιομέτρων", value=int(vehicle_data['TotalKM']))
                new_monthly_km = st.number_input("Χιλιόμετρα / Μήνα", value=int(vehicle_data['MonthlyKM']))
                tire_status = st.selectbox("Κατάσταση Ελαστικών", ["Καλή", "Χρειάζεται Αλλαγή", "Πρόσφατα Αλλαγμένα"], index=0)
                
                submitted = st.form_submit_button("Αποθήκευση Αλλαγών")
                if submitted:
                    st.session_state.vehicles.loc[st.session_state.vehicles["LicensePlate"] == selected_plate, "TotalKM"] = new_km
                    st.session_state.vehicles.loc[st.session_state.vehicles["LicensePlate"] == selected_plate, "MonthlyKM"] = new_monthly_km
                    st.session_state.vehicles.loc[st.session_state.vehicles["LicensePlate"] == selected_plate, "TireCondition"] = tire_status
                    st.success("Η καρτέλα ενημερώθηκε επιτυχώς!")

# ---------------------------------------------------------
# 3. ΕΙΣΑΓΩΓΗ PDF & EXCEL (AI OCR & MULTI-SHEET PARSER)
# ---------------------------------------------------------
elif menu == "Εισαγωγή PDF & Excel":
    st.title("📂 Αυτόματη Αναγνώριση Εγγράφων (PDF & Excel)")
    
    st.markdown("""
    Ανεβάστε αρχεία για αυτόματη επεξεργασία:
    - **PDF Άδειας Κυκλοφορίας:** Δημιουργεί νέα καρτέλα οχήματος.
    - **PDF Τιμολογίου/Προσφοράς:** Διαβάζει τη **μία ημερομηνία έκδοσης** που αναγράφεται και συνδέει τα έξοδα με την πινακίδα.
    - **Excel (Πολύσελιδα):** Εισάγει μαζικά στατιστικά και ιστορικά στοιχεία.
    """)
    
    uploaded_files = st.file_uploader("Επιλέξτε αρχεία PDF ή Excel", type=["pdf", "xlsx", "xls"], accept_multiple_files=True)
    
    if uploaded_files:
        for file in uploaded_files:
            st.write(f"📄 **Επεξεργασία αρχείου:** `{file.name}`")
            
            if file.name.endswith(".pdf"):
                # Διαχωρισμός τύπου PDF (Demo λογική)
                if "adeia" in file.name.lower() or "license" in file.name.lower():
                    parsed_data = parse_license_pdf(file)
                    st.json(parsed_data)
                    if st.button(f"Προσθήκη Οχήματος από {file.name}"):
                        new_row = {
                            "VIN": parsed_data["VIN"],
                            "LicensePlate": parsed_data["LicensePlate"],
                            "MakeModel": parsed_data["MakeModel"],
                            "Year": parsed_data["Year"],
                            "FuelType": parsed_data["FuelType"],
                            "Status": "Ενεργό",
                            "Driver": "Αναμένεται",
                            "TotalKM": 0,
                            "MonthlyKM": 0,
                            "TireCondition": "Καλή",
                            "TotalMaintenanceCost": 0.0,
                            "SustainabilityStatus": "Βιώσιμο"
                        }
                        st.session_state.vehicles = pd.concat([st.session_state.vehicles, pd.DataFrame([new_row])], ignore_index=True)
                        st.success(f"Το όχημα {parsed_data['LicensePlate']} προστέθηκε στον στόλο!")
                else:
                    parsed_inv = parse_invoice_pdf(file)
                    st.write(f"**Ημερομηνία Τιμολογίου (Αναγραφόμενη):** {parsed_inv['InvoiceDate']}")
                    st.write(f"**Ποσό:** {parsed_inv['Amount']} € | **Προμηθευτής:** {parsed_inv['Supplier']}")
                    
                    if st.button(f"Καταχώρηση Εξόδου από {file.name}"):
                        new_expense = {
                            "ExpenseID": len(st.session_state.expenses) + 1,
                            "LicensePlate": parsed_inv["LicensePlate"],
                            "InvoiceDate": parsed_inv["InvoiceDate"], # ΜΙΑ ημερομηνία παραστατικού
                            "Category": parsed_inv["Category"],
                            "Description": parsed_inv["Description"],
                            "Amount": parsed_inv["Amount"],
                            "Supplier": parsed_inv["Supplier"],
                            "SystemTimestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.expenses = pd.concat([st.session_state.expenses, pd.DataFrame([new_expense])], ignore_index=True)
                        st.success("Το τιμολόγιο καταχωρήθηκε στην καρτέλα του οχήματος!")

            elif file.name.endswith((".xlsx", ".xls")):
                sheets = process_bulk_excel(file)
                st.success(f"Εντοπίστηκαν {len(sheets)} φύλλα στο Excel: {', '.join(sheets)}")
                st.info("Τα στοιχεία αναλύθηκαν και είναι έτοιμα για συγχρονισμό.")

# ---------------------------------------------------------
# 4. GOOGLE DRIVE WATCHER
# ---------------------------------------------------------
elif menu == "Google Drive Watcher":
    st.title("☁️ Google Drive Watcher & Sync")
    st.write("Σύνδεση με τον λογαριασμό **auto3ype@gmail.com**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Κατάσταση Φακέλου Drive")
        st.info("Φάκελος Παρακολούθησης: `/Fleet_Management_Drive/`")
        st.write("Αυτόματος έλεγχος για νέα PDF/Excel κάθε 15 λεπτά ή χειροκίνητα.")
    
    with col2:
        st.subheader("Ενέργειες")
        if st.button("🔄 Χειροκίνητος Συγχρονισμός Drive Τώρα"):
            st.warning("Έλεγχος φακέλου Drive... Εντοπίστηκαν 0 νέα αρχεία.")

# ---------------------------------------------------------
# 5. ΔΙΑΧΕΙΡΙΣΗ ΟΔΗΓΩΝ
# ---------------------------------------------------------
elif menu == "Διαχείριση Οδηγών":
    st.title("👨‍✈️ Στοιχεία Οδηγών & Υπευθύνων")
    
    with st.form("add_driver_form"):
        d_name = st.text_input("Ονοματεπώνυμο Οδηγού")
        d_phone = st.text_input("Τηλέφωνο Επικοινωνίας")
        d_status = st.selectbox("Κατάσταση", ["Ενεργός", "Ανενεργός"])
        
        submit_driver = st.form_submit_button("Προσθήκη Οδηγού")
        if submit_driver and d_name:
            new_driver = {
                "DriverID": len(st.session_state.drivers) + 1,
                "FullName": d_name,
                "Phone": d_phone,
                "Status": d_status,
                "AssignedVehicle": "-"
            }
            st.session_state.drivers = pd.concat([st.session_state.drivers, pd.DataFrame([new_driver])], ignore_index=True)
            st.success("Ο οδηγός καταχωρήθηκε!")

    st.subheader("Λίστα Οδηγών")
    st.dataframe(st.session_state.drivers, use_container_width=True)
