import streamlit as st
from datetime import datetime
import pandas as pd
import os

DATA_FILE = "data.csv"

st.set_page_config(layout="wide")

# =========================
# PROFESSIONAL UI STYLE
# =========================
st.markdown("""
<style>
html, body {
    background-color: #0b1220;
    color: #e2e8f0;
}

.block-container {
    max-width: 1100px;
    margin: auto;
    padding-top: 1rem;
}

.topbar {
    background: #020617;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
}

.card {
    background: #1c2433;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.pass {
    color: #10b981;
    font-weight: bold;
    font-size: 18px;
}

.fail {
    color: #ef4444;
    font-weight: bold;
    font-size: 18px;
}

button[kind="primary"] {
    background-color: #3b82f6 !important;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "Date","Time","Driver","Vehicle","Odometer",
        "Tyres","Brakes","Lights","Defects","Status"
    ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# =========================
# USERS
# =========================
users = {
    "david": {"password": "1234", "role": "driver"},
    "john": {"password": "1234", "role": "driver"},
    "office": {"password": "admin", "role": "office"}
}

# =========================
# LOGIN
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown("<div class='topbar'><h2>Fleet Control Pro</h2></div>", unsafe_allow_html=True)

    username = st.text_input("Username").lower()
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if username in users and password == users[username]["password"]:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================
# HEADER BAR
# =========================
st.markdown(f"""
<div class='topbar'>
    Logged in as: {st.session_state.user}
</div>
""", unsafe_allow_html=True)

# =========================
# NAV
# =========================
page = st.radio("", ["Driver", "Dashboard"], horizontal=True)

# =========================
# DRIVER PAGE
# =========================
if page == "Driver" and st.session_state.role == "driver":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Driver Inspection")

    col1, col2 = st.columns(2)
    with col1:
        vehicle = st.text_input("Vehicle Registration")
    with col2:
        odo = st.number_input("Odometer", min_value=0)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Full Vehicle Check (10 Points)")

    c1, c2, c3 = st.columns(3)

    tyres = c1.checkbox("Tyres")
    brakes = c1.checkbox("Brakes")
    lights = c1.checkbox("Lights")

    mirrors = c2.checkbox("Mirrors")
    horn = c2.checkbox("Horn")
    seatbelt = c2.checkbox("Seatbelt")

    oil = c3.checkbox("Oil")
    coolant = c3.checkbox("Coolant")
    load_secure = c3.checkbox("Load Secure")
    plates = c3.checkbox("Number Plates")

    all_ok = all([
        tyres, brakes, lights,
        mirrors, horn, seatbelt,
        oil, coolant, load_secure, plates
    ])

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if all_ok:
        st.markdown("<div class='pass'>✅ PASS - Vehicle Roadworthy</div>", unsafe_allow_html=True)
        defect = "NIL DEFECT"
    else:
        st.markdown("<div class='fail'>❌ FAIL - Add Defect</div>", unsafe_allow_html=True)
        defect = st.text_area("Defect Details")

    if st.button("Submit Check", use_container_width=True):

        if not vehicle:
            st.error("Enter vehicle")
        elif not all_ok and not defect:
            st.error("Enter defect")
        else:
            now = datetime.now()

            new_row = {
                "Date": now.strftime("%Y-%m-%d"),
                "Time": now.strftime("%H:%M:%S"),
                "Driver": st.session_state.user,
                "Vehicle": vehicle,
                "Odometer": odo,
                "Tyres": tyres,
                "Brakes": brakes,
                "Lights": lights,
                "Defects": defect,
                "Status": "PASS" if all_ok else "FAIL"
            }

            df2 = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df2)

            st.success("Check saved")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DASHBOARD PAGE
# =========================
if page == "Dashboard" and st.session_state.role == "office":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    total = len(df)
    passes = len(df[df["Status"] == "PASS"])
    fails = len(df[df["Status"] == "FAIL"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Checks", total)
    col2.metric("Pass", passes)
    col3.metric("Fail", fails)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Active Defects")

    defects = df[df["Status"] == "FAIL"]

    if defects.empty:
        st.success("No issues")
    else:
        for _, r in defects.iterrows():
            st.error(f"{r['Vehicle']} - {r['Defects']}")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Records")
    st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)