import streamlit as st
from datetime import datetime
import pandas as pd
import os

DATA_FILE = "data.csv"
JOBS_FILE = "jobs.csv"

st.set_page_config(layout="wide", page_title="Fleet Control Pro")

# =========================
# LOAD / SAVE
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

    st.title("Fleet Control Pro")

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
col1, col2 = st.columns([6,1])

col1.write(f"Logged in as: {st.session_state.user}")

if col2.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# =========================
# NAV (ROLE BASED)
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

    vehicle = st.selectbox("Vehicle", VEHICLES)
    odo = st.number_input("Odometer", 0)

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

    if ok:
        st.success("PASS")
        defect = "NIL DEFECT"
    else:
        st.error("FAIL")
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

        st.success("Saved")

# =========================
# DASHBOARD
# =========================
if page == "Dashboard":

    st.subheader("Fleet Overview")

    st.metric("Total Checks", len(df))
    st.metric("Fails", len(df[df["Status"]=="FAIL"]))

    st.subheader("Records")

    if df.empty:
        st.info("No data yet")
    else:
        st.dataframe(df, use_container_width=True)

# =========================
# JOBS (OFFICE)
# =========================
if page == "Jobs":

    st.subheader("Create Job")

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

        st.success("Job created")

    st.markdown("---")

    st.subheader("Open Jobs")

    open_jobs = jobs[jobs["Status"]=="OPEN"]

    if open_jobs.empty:
        st.info("No open jobs")
    else:
        st.dataframe(open_jobs, use_container_width=True)

# =========================
# WORKSHOP (REPAIRS)
# =========================
if page == "Workshop":

    st.subheader("Workshop Repairs")

    open_jobs = jobs[jobs["Status"]=="OPEN"]

    if open_jobs.empty:
        st.info("No jobs to complete")
    else:
        for i, r in open_jobs.iterrows():

            col1, col2 = st.columns([3,1])

            col1.write(f"{r['Vehicle']} - {r['Job']} ({r['Engineer']})")

            if col2.button("Complete", key=i):
                jobs.loc[i,"Status"] = "COMPLETE"
                save_jobs(jobs)
                st.rerun()

    st.markdown("---")

    st.subheader("Fix Defects")

    fails = df[df["Status"]=="FAIL"]

    if fails.empty:
        st.info("No defects")
    else:
        for i, r in fails.iterrows():

            col1, col2 = st.columns([3,1])

            col1.write(r["Vehicle"] + " - " + r["Defects"])

            if col2.button("Fix", key=f"fix{i}"):
                df.loc[i,"Status"] = "FIXED"
                save_data(df)
                st.rerun()
