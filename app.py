import streamlit as st
from datetime import datetime
import pandas as pd
import os

DATA_FILE = "data.csv"
JOBS_FILE = "jobs.csv"

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# FULL PRO UI STYLE
# =========================
st.markdown("""
<style>

/* Base */
html, body {
    background-color: #0b1220;
    color: #e2e8f0;
}

/* Layout */
.block-container {
    max-width: 1200px;
    margin: auto;
}

/* Top Bar */
.topbar {
    background: linear-gradient(90deg, #020617, #0f172a);
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand {
    font-size: 26px;
    font-weight: 600;
}

/* Cards */
.card {
    background: #1e293b;
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

/* Buttons */
button[kind="primary"] {
    background-color: #3b82f6 !important;
    border-radius: 10px !important;
}

/* Status */
.pass {
    color: #22c55e;
    font-weight: bold;
}

.fail {
    color: #ef4444;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# =========================
# LOAD / SAVE
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "Date","Time","Driver","Vehicle","Odometer",
        "Latitude","Longitude","Defects","Status"
    ])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_jobs():
    if os.path.exists(JOBS_FILE):
        return pd.read_csv(JOBS_FILE)
    return pd.DataFrame(columns=[
        "Date","Vehicle","Job","Engineer","Status"
    ])

def save_jobs(df):
    df.to_csv(JOBS_FILE, index=False)

df = load_data()
jobs = load_jobs()

# =========================
# DEMO DATA (SO APP NEVER EMPTY)
# =========================
if df.empty:
    df = pd.DataFrame([{
        "Date":"2026-06-01",
        "Time":"08:00:00",
        "Driver":"david",
        "Vehicle":"AB12 XYZ",
        "Odometer":100000,
        "Latitude":"51.5",
        "Longitude":"0.1",
        "Defects":"Brake issue",
        "Status":"FAIL"
    }])
    save_data(df)

# =========================
# USERS
# =========================
users = {
    "david": {"password":"1234","role":"driver"},
    "john": {"password":"1234","role":"driver"},
    "office": {"password":"admin","role":"office"}
}

VEHICLES = ["AB12 XYZ","BT23 FLEET","CV34 VAN","DV45 TRUCK"]

# =========================
# LOGIN
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown("<h1>🚚 FleetCheck Pro</h1>", unsafe_allow_html=True)
    st.write("Vehicle Inspection & Compliance System")

    u = st.text_input("Username").lower()
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================
# HEADER + LOGOUT
# =========================
st.markdown(f"""
<div class="topbar">
    <div class="brand">FleetCheck Pro</div>
    <div>User: {st.session_state.user}</div>
</div>
""", unsafe_allow_html=True)

if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# =========================
# NAV
# =========================
if st.session_state.role == "driver":
    pages = ["Driver"]
else:
    pages = ["Dashboard","Jobs","Workshop"]

page = st.radio("", pages, horizontal=True)

# =========================
# DRIVER PAGE
# =========================
if page == "Driver":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    vehicle = col1.selectbox("Vehicle", VEHICLES)
    odo = col2.number_input("Odometer", 0)

    st.subheader("GPS")
    col1, col2 = st.columns(2)
    lat = col1.text_input("Latitude")
    lon = col2.text_input("Longitude")

    st.subheader("Checks")

    tyres = st.checkbox("Tyres")
    brakes = st.checkbox("Brakes")
    lights = st.checkbox("Lights")
    mirrors = st.checkbox("Mirrors")
    horn = st.checkbox("Horn")
    seatbelt = st.checkbox("Seatbelt")
    oil = st.checkbox("Oil")
    coolant = st.checkbox("Coolant")
    load = st.checkbox("Load Secure")
    plates = st.checkbox("Plates")

    ok = all([tyres,brakes,lights,mirrors,horn,seatbelt,oil,coolant,load,plates])

    st.subheader("📸 Photos")

    front = st.file_uploader("Front")
    back = st.file_uploader("Back")
    left = st.file_uploader("Left")
    right = st.file_uploader("Right")

    if ok:
        st.markdown("<div class='pass'>✅ PASS</div>", unsafe_allow_html=True)
        defect = "NIL DEFECT"
    else:
        st.markdown("<div class='fail'>❌ FAIL</div>", unsafe_allow_html=True)
        defect = st.text_area("Defect")

    if st.button("Submit Check"):

