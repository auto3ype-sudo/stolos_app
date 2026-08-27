# PAGE 2: VEHICLE CARD
elif menu == "Καρτέλα Οχήματος":
    st.title("📋 Καρτέλα Οχήματος & Ιστορικό")
    
    if st.session_state.vehicles.empty:
        st.warning("Παρακαλώ καταχωρήστε πρώτα οχήματα από την 'Εισαγωγή PDF & Excel'.")
    else:
        # Αναπτυσσόμενη λίστα επιλογής οχήματος
        selected_plate = st.selectbox(
            "🚗 Επιλέξτε Πινακίδα Οχήματος:", 
            st.session_state.vehicles["LicensePlate"].unique()
        )
        
        # Φιλτράρισμα δεδομένων για το επιλεγμένο όχημα
        veh_data = st.session_state.vehicles[st.session_state.vehicles["LicensePlate"] == selected_plate].iloc[0]
        
        st.markdown("---")
        
        # Βασικές Πληροφορίες σε Κάρτες (Metrics)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Πινακίδα", veh_data.get("LicensePlate", "-"))
        c2.metric("VIN (Πλαίσιο)", veh_data.get("VIN", "-"))
        c3.metric("Κατάσταση", veh_data.get("Status", "-"))
        c4.metric("Συνολικά ΧΛΜ", f"{veh_data.get('TotalKM', 0):,.0f} km")

        st.markdown("---")

        # Οργάνωση σε Καρτέλες (Tabs) για πλήρη εικόνα
        tab1, tab2, tab3 = st.tabs(["📌 Βασικά Στοιχεία", "🔧 Συντήρηση & Κατάσταση", "👤 Οδηγός & Χρήση"])

        with tab1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Μάρκα / Μοντέλο:** {veh_data.get('MakeModel', '-')}")
                st.write(f"**Έτος Κατασκευής:** {veh_data.get('Year', '-')}")
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
