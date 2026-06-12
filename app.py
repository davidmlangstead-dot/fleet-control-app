import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# FILES
# =========================
USERS_FILE = "users.csv"
JOBS_FILE = "jobs.csv"
CHECKS_FILE = "checks.csv"
VEHICLE_FILE = "vehicles.csv"

# =========================
# LOAD / SAVE
# =========================
def load_csv(file, cols):
    if os.path.exists(file):
        try:
            return pd.read_csv(file)
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_csv(df, file):
    df.to_csv(file, index=False)

# =========================
# INIT FILES
# =========================
if not os.path.exists(USERS_FILE):
    pd.DataFrame([
        {"Username":"office","Password":"admin","Role":"office"},
        {"Username":"manager","Password":"manager","Role":"manager"}
    ]).to_csv(USERS_FILE, index=False)

if not os.path.exists(VEHICLE_FILE):
    pd.DataFrame({"Vehicle":["AB12 XYZ"]}).to_csv(VEHICLE_FILE, index=False)

# =========================
# LOGIN
# =========================
users = load_csv(USERS_FILE, ["Username","Password","Role"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("FleetCheck Pro Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):

        match = users[(users["Username"] == u) & (users["Password"] == p)]

        if not match.empty:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.session_state.role = match.iloc[0]["Role"]
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

role = st.session_state.role

# =========================
# LOAD DATA
# =========================
jobs = load_csv(JOBS_FILE, ["Date","Vehicle","Job","Status"])
checks = load_csv(CHECKS_FILE, ["Date","Driver","Vehicle","Status","Defects"])
vehicles_df = load_csv(VEHICLE_FILE, ["Vehicle"])
vehicles = vehicles_df["Vehicle"].tolist()

# =========================
# DRIVER VIEW
# =========================
if role == "driver":

    st.header("Driver Panel")

    tab1, tab2 = st.tabs(["RHA Check","Jobs"])

    # -------------------
    # CHECKS
    # -------------------
    with tab1:

        vehicle = st.selectbox("Vehicle", vehicles)

        items = ["Tyres","Brakes","Lights","Mirrors"]

        results = {}
        notes = {}

        for i in items:
            st.subheader(i)
            status = st.radio(i, ["PASS","DEFECT","FAIL"], key=i)
            results[i] = status

            if status != "PASS":
                notes[i] = st.text_area(f"{i} note")

        if "FAIL" in results.values():
            overall = "FAIL"
        elif "DEFECT" in results.values():
            overall = "PASS_WITH_DEFECT"
        else:
            overall = "PASS"

        st.write("Result:", overall)

        if st.button("Submit Check"):

            new = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Driver": st.session_state.user,
                "Vehicle": vehicle,
                "Status": overall,
                "Defects": str(notes)
            }])

            checks = pd.concat([checks, new], ignore_index=True)
            save_csv(checks, CHECKS_FILE)

            st.success("Check submitted")

    # -------------------
    # JOBS VIEW (READ ONLY)
    # -------------------
    with tab2:

        st.subheader("Assigned Jobs")

        st.dataframe(jobs)

# =========================
# OFFICE VIEW (ADMIN)
# =========================
if role == "office":

    st.header("Office Dashboard")

    tab1, tab2 = st.tabs(["Jobs","Drivers"])

    # -------------------
    # JOB CREATION
    # -------------------
    with tab1:

        vehicle = st.selectbox("Vehicle", vehicles)
        job_text = st.text_input("Job Description")

        if st.button("Create Job"):

            new = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Vehicle": vehicle,
                "Job": job_text,
                "Status": "OPEN"
            }])

            jobs = pd.concat([jobs, new], ignore_index=True)
            save_csv(jobs, JOBS_FILE)
            st.rerun()

        st.dataframe(jobs)

    # -------------------
    # DRIVER MANAGEMENT
    # -------------------
    with tab2:

        st.subheader("Add Driver")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password")

        if st.button("Add Driver"):
            new = pd.DataFrame([{
                "Username": new_user,
                "Password": new_pass,
                "Role": "driver"
            }])

            users = pd.concat([users, new], ignore_index=True)
            save_csv(users, USERS_FILE)
            st.rerun()

        st.subheader("Remove Driver")

        for i,row in users.iterrows():
            if row["Role"] == "driver":
                col1,col2 = st.columns([3,1])
                col1.write(row["Username"])

                if col2.button("Remove", key=i):
                    users = users.drop(i)
                    save_csv(users, USERS_FILE)
                    st.rerun()

# =========================
# MANAGER VIEW (TM)
# =========================
if role == "manager":

    st.header("Manager Dashboard")

    tab1, tab2, tab3 = st.tabs(["Checks","Jobs","Fleet"])

    # -------------------
    # CHECK MONITORING
    # -------------------
    with tab1:

        st.subheader("Vehicle Checks")

        if checks.empty:
            st.info("No data")
        else:
            st.dataframe(checks)

    # -------------------
    # JOB MONITORING
    # -------------------
    with tab2:

        st.subheader("Jobs")

        for i,row in jobs.iterrows():
            c1,c2 = st.columns([3,1])
            c1.write(row["Job"])

            if row["Status"] == "OPEN":
                if c2.button("Complete", key=f"job{i}"):
                    jobs.loc[i,"Status"] = "DONE"
                    save_csv(jobs, JOBS_FILE)
                    st.rerun()

    # -------------------
    # VEHICLE MANAGEMENT
    # -------------------
    with tab3:

        st.subheader("Add Vehicle")
        new_vehicle = st.text_input("Vehicle name")

        if st.button("Add Vehicle"):
            vehicles_df = pd.concat(
                [vehicles_df, pd.DataFrame({"Vehicle":[new_vehicle]})],
                ignore_index=True
            )
            save_csv(vehicles_df, VEHICLE_FILE)
            st.rerun()

        st.subheader("Remove Vehicle")

        for i,row in vehicles_df.iterrows():
            col1,col2 = st.columns([3,1])
            col1.write(row["Vehicle"])

            if col2.button("Remove", key=f"veh{i}"):
                vehicles_df = vehicles_df.drop(i)
                save_csv(vehicles_df, VEHICLE_FILE)
                st.rerun()
