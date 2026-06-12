import streamlit as st
from datetime import datetime
import pandas as pd
import os

DATA_FILE = "data.csv"
JOBS_FILE = "jobs.csv"

st.set_page_config(layout="wide", page_title="Fleet Control Pro")

# =========================
# STYLE (PRO UI)
# =========================
st.markdown("""
<style>
html, body {
    background-color: #0b1220;
    color: #e2e8f0;
}
.block-container {max-width:1200px; margin:auto;}

.topbar {
    background:#020617;
    padding:18px;
    border-radius:10px;
    margin-bottom:20px;
    display:flex;
    justify-content:space-between;
}

.card {
    background:#1c2433;
    padding:20px;
    border-radius:12px;
    margin-bottom:20px;
}

.pass {color:#10b981; font-weight:bold;}
.fail {color:#ef4444; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# =========================
# DATA
# =========================
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=[
        "Date","Time","Driver","Vehicle","Odometer","Defects","Status"
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

    st.markdown("<h2>Fleet Control Pro</h2>", unsafe_allow_html=True)

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
# HEADER
# =========================
st.markdown(f"""
<div class="topbar">
<div>Fleet Control Pro</div>
<div>User: {st.session_state.user}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# NAV
# =========================
page = st.radio("", ["Driver","Dashboard","Workshop","Jobs"], horizontal=True)

# =========================
# DRIVER
# =========================
if page == "Driver":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    vehicle = st.selectbox("Vehicle", VEHICLES)
    odo = st.number_input("Odometer", 0)

    st.markdown("### Checks")

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

    if ok:
        st.markdown("<div class='pass'>PASS</div>", unsafe_allow_html=True)
        defect = "NIL DEFECT"
    else:
        st.markdown("<div class='fail'>FAIL</div>", unsafe_allow_html=True)
        defect = st.text_area("Defect")

    if st.button("Submit"):

        now = datetime.now()

        new_row = {
            "Date": now.strftime("%Y-%m-%d"),
            "Time": now.strftime("%H:%M:%S"),
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Odometer": odo,
            "Defects": defect,
            "Status": "PASS" if ok else "FAIL"
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)

        st.success("Check saved")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DASHBOARD (ALWAYS SHOW)
# =========================
if page == "Dashboard":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    total = len(df)
    fails = len(df[df["Status"]=="FAIL"])
    fixed = len(df[df["Status"]=="FIXED"])

    col1,col2,col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("Active Defects", fails)
    col3.metric("Fixed", fixed)

    st.markdown("</div>", unsafe_allow_html=True)

    # ALWAYS SHOW TABLE
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("All Activity")

    if df.empty:
        st.info("No data yet")
    else:
        st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# WORKSHOP (FIX DEFECTS)
# =========================
if page == "Workshop":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    fails = df[df["Status"]=="FAIL"]

    if fails.empty:
        st.info("No defects")
    else:
        for i, r in fails.iterrows():
            col1,col2 = st.columns([3,1])

            col1.write(f"{r['Vehicle']} - {r['Defects']}")

            if col2.button("Fix", key=i):
                df.loc[i,"Status"] = "FIXED"
                save_data(df)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# JOB REPORTING (NEW)
# =========================
if page == "Jobs":

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Log Job")

    veh = st.selectbox("Vehicle", VEHICLES)
    job = st.text_input("Job Description")
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

    st.markdown("</div>", unsafe_allow_html=True)

    # JOB LIST
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Active Jobs")

    if jobs.empty:
        st.info("No jobs logged")
    else:
        for i, r in jobs.iterrows():
            col1, col2 = st.columns([3,1])

            col1.write(f"{r['Vehicle']} - {r['Job']} ({r['Engineer']})")

            if col2.button("Complete", key=f"job{i}"):
                jobs.loc[i,"Status"] = "COMPLETE"
                save_jobs(jobs)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
