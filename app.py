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
# INIT USERS (CRITICAL FIX)
# =========================
if not os.path.exists(USERS_FILE):
    pd.DataFrame([
        {"Username":"office","Password":"admin","Role":"office"},
        {"Username":"manager","Password":"admin","Role":"manager"},
        {"Username":"workshop","Password":"admin","Role":"workshop"}
    ]).to_csv(USERS_FILE, index=False)

# =========================
# LOAD SYSTEM DATA
# =========================
users = load_csv(USERS_FILE, ["Username","Password","Role"])
jobs = load_csv(JOBS_FILE, ["Date","Vehicle","Job","Status"])
checks = load_csv(CHECKS_FILE, ["Date","Driver","Vehicle","Status","Defects"])
vehicles_df = load_csv(VEHICLE_FILE, ["Vehicle"])

if vehicles_df.empty:
    vehicles_df = pd.DataFrame({"Vehicle":["AB12 XYZ"]})
    save_csv(vehicles_df, VEHICLE_FILE)

vehicles = vehicles_df["Vehicle"].tolist()

# =========================
# LOGIN
# =========================
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
# DRIVER
# =========================
if role == "driver":

    st.header("Driver")

    tab1, tab2 = st.tabs(["RHA Check","Jobs"])

    # CHECKS
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

            st.success("Check submitted ✅")


    # JOBS (READ ONLY)
    with tab2:
        st.subheader("Jobs")
        st.dataframe(jobs)


# =========================
# OFFICE
# =========================
if role == "office":

    st.header("Office")

    tab1, tab2, tab3 = st.tabs(["Jobs","Drivers","Users"])

    # JOBS
    with tab1:
        vehicle = st.selectbox("Vehicle", vehicles)
        job_text = st.text_input("Job")

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

    # DRIVERS
    with tab2:
        st.subheader("Add Driver")

        u = st.text_input("Username")
        p = st.text_input("Password")

        if st.button("Add Driver"):
            new = pd.DataFrame([{
                "Username": u,
                "Password": p,
                "Role": "driver"
            }])
            users = pd.concat([users, new], ignore_index=True)
            save_csv(users, USERS_FILE)
            st.rerun()

        st.subheader("Remove Driver")

        for i,row in users.iterrows():
            if row["Role"] == "driver":
                c1,c2 = st.columns([3,1])
                c1.write(row["Username"])

                if c2.button("Remove", key=i):
                    users = users.drop(i)
                    save_csv(users, USERS_FILE)
                    st.rerun()

    # ADD OTHER USERS (manager/workshop)
    with tab3:

        role_sel = st.selectbox("Role", ["manager","workshop"])
        u = st.text_input("Username_new")
        p = st.text_input("Password_new")

        if st.button("Add User"):
            new = pd.DataFrame([{
                "Username": u,
                "Password": p,
                "Role": role_sel
            }])
            users = pd.concat([users, new], ignore_index=True)
            save_csv(users, USERS_FILE)
            st.rerun()


# =========================
# MANAGER (TM)
# =========================
if role == "manager":

    st.header("Transport Manager")

    tab1, tab2 = st.tabs(["Checks","Jobs"])

    with tab1:
        st.subheader("Checks")
        st.dataframe(checks)

    with tab2:
        st.subheader("Jobs")
        st.dataframe(jobs)


# =========================
# WORKSHOP
# =========================
if role == "workshop":

    st.header("Workshop")

    for i,row in jobs.iterrows():

        c1,c2 = st.columns([3,1])

        c1.write(f"{row['Vehicle']} - {row['Job']}")

        if row["Status"] == "OPEN":
            if c2.button("Complete", key=i):
                jobs.loc[i,"Status"] = "DONE"
                save_csv(jobs, JOBS_FILE)
                st.rerun()
