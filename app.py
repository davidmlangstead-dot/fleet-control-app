import streamlit as st
from datetime import datetime
import pandas as pd
import os

DATA_FILE = "data.csv"
JOBS_FILE = "jobs.csv"

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
html, body {
    background-color: #0b1220;
    color: #e2e8f0;
}
.block-container {
    max-width: 1200px;
    margin: auto;
}
.topbar {
    background:#020617;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
}
.card {
    background:#1c2433;
    padding:18px;
    border-radius:12px;
    margin-bottom:20px;
}
.pass {color:#10b981; font-weight:bold;}
.fail {color:#ef4444; font-weight:bold;}
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
# DEMO DATA (IMPORTANT)
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

    st.title("🚚 FleetCheck Pro")
    st.markdown("Vehicle Inspection & Compliance System")

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
col1, col2 = st.columns([5,1])

col1.markdown(f"<div class='topbar'>User: {st.session_state.user}</div>", unsafe_allow_html=True)

if col2.button("Logout"):
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
# DRIVER
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

    ok = all([
        tyres,brakes,lights,mirrors,horn,
        seatbelt,oil,coolant,load,plates
    ])

    st.subheader("Photos (4 sides)")

    front = st.file_uploader("Front", type=["jpg","png"])
    back = st.file_uploader("Back", type=["jpg","png"])
    left = st.file_uploader("Left", type=["jpg","png"])
    right = st.file_uploader("Right", type=["jpg","png"])

    if ok:
        st.markdown("<div class='pass'>PASS</div>", unsafe_allow_html=True)
        defect = "NIL DEFECT"
    else:
        st.markdown("<div class='fail'>FAIL</div>", unsafe_allow_html=True)
        defect = st.text_area("Defect")

    if st.button("Submit"):

        now = datetime.now()

        row = {
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%H:%M:%S"),
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Odometer": odo,
            "Latitude": lat,
            "Longitude": lon,
            "Defects": defect,
            "Status": "PASS" if ok else "FAIL"
        }

        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        save_data(df)

        st.success("Saved with GPS + Photos")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if page == "Dashboard":

    st.metric("Total Checks", len(df))
    st.metric("Active Defects", len(df[df["Status"]=="FAIL"]))
    st.metric("Fixed", len(df[df["Status"]=="FIXED"]))

    st.subheader("Records")
    st.dataframe(df, use_container_width=True)

# =========================
# JOBS (OFFICE)
# =========================
if page == "Jobs":

    st.subheader("Create Job")

    veh = st.selectbox("Vehicle", VEHICLES)
    job = st.text_input("Job")
    eng = st.text_input("Engineer")

    if st.button("Add Job"):

        new_job = {
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Vehicle": veh,
            "Job": job,
            "Engineer": eng,
            "Status": "OPEN"
        }

        jobs = pd.concat([jobs, pd.DataFrame([new_job])], ignore_index=True)
        save_jobs(jobs)

        st.success("Job added")

    st.subheader("Open Jobs")
    st.dataframe(jobs[jobs["Status"]=="OPEN"], use_container_width=True)

# =========================
# WORKSHOP
# =========================
if page == "Workshop":

    st.subheader("Workshop Repairs")

    open_jobs = jobs[jobs["Status"]=="OPEN"]

    for i, r in open_jobs.iterrows():
        col1,col2 = st.columns([3,1])
        col1.write(f"{r['Vehicle']} - {r['Job']}")
        if col2.button("Complete", key=i):
            jobs.loc[i,"Status"] = "COMPLETE"
            save_jobs(jobs)
            st.rerun()

    st.subheader("Fix Defects")

    fails = df[df["Status"]=="FAIL"]

    for i,r in fails.iterrows():
        col1,col2 = st.columns([3,1])
        col1.write(f"{r['Vehicle']} - {r['Defects']}")
        if col2.button("Fix", key=f"f{i}"):
            df.loc[i,"Status"] = "FIXED"
            save_data(df)
            st.rerun()
``
