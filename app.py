import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# FILES
# =========================
HOURS_FILE = "hours.csv"
CHECKS_FILE = "data.csv"
JOBS_FILE = "jobs.csv"
SETTINGS_FILE = "settings.csv"
USERS_FILE = "users.csv"
PHOTO_DIR = "photos"

os.makedirs(PHOTO_DIR, exist_ok=True)

# =========================
# LOAD / SAVE
# =========================
def load_csv(file, cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
        except:
            df = pd.DataFrame(columns=cols)
    else:
        df = pd.DataFrame(columns=cols)

    for c in cols:
        if c not in df.columns:
            df[c] = ""

    return df

def save_csv(df, file):
    df.to_csv(file, index=False)

# =========================
# INIT FILES
# =========================
hours_cols = ["Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"]
checks_cols = ["Date","Time","Driver","Vehicle","Latitude","Longitude","Defects","Status"]
jobs_cols = ["Date","Vehicle","Job","Status"]
users_cols = ["Username","Password","Role"]

if not os.path.exists(USERS_FILE):
    pd.DataFrame([
        {"Username":"office","Password":"admin","Role":"office"}
    ]).to_csv(USERS_FILE, index=False)

# =========================
# EMAIL FUNCTION
# =========================
def send_email_alert(subject, body):
    settings = load_csv(SETTINGS_FILE, ["Email","Password"])
    if settings.empty:
        return

    sender = settings.iloc[0]["Email"]
    password = settings.iloc[0]["Password"]

    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = sender

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
    except:
        pass

# =========================
# LOGIN
# =========================
users = load_csv(USERS_FILE, users_cols)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("FleetCheck Pro")

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

# =========================
# NAV
# =========================
menu = ["Driver Hours","Jobs","RHA Check","Manager","Settings"]

if st.session_state.role == "office":
    menu.append("Users")

app = st.sidebar.radio("App", menu)

vehicle = st.sidebar.selectbox("Vehicle", ["AB12 XYZ","BT23 FLEET"])
lat = st.sidebar.text_input("Latitude")
lon = st.sidebar.text_input("Longitude")

# =========================
# DRIVER HOURS
# =========================
if app == "Driver Hours":

    st.header("Driver Hours")

    current = st.session_state.get("current")

    def get_hours():
        df = load_csv(HOURS_FILE, hours_cols)
        return df[df["Driver"] == st.session_state.user]

    def start(t):
        st.session_state.current = {"type": t, "start": datetime.now()}

    def stop():
        if not st.session_state.current:
            return

        df = load_csv(HOURS_FILE, hours_cols)

        start = st.session_state.current["start"]
        end = datetime.now()
        mins = int((end-start).total_seconds()/60)

        new = pd.DataFrame([{
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Type": st.session_state.current["type"],
            "Start": start,
            "End": end,
            "Duration": mins,
            "Latitude": lat,
            "Longitude": lon
        }])

        df = pd.concat([df, new], ignore_index=True)
        save_csv(df, HOURS_FILE)

        st.session_state.current = None
        st.rerun()

    c1,c2,c3,c4 = st.columns(4)
    c1.button("Driving", on_click=start, args=("DRIVING",))
    c2.button("Rest", on_click=start, args=("REST",))
    c3.button("POA", on_click=start, args=("POA",))
    c4.button("Other", on_click=start, args=("OTHER",))

    st.button("Stop", on_click=stop)

    if current:
        mins = int((datetime.now() - current["start"]).total_seconds()/60)
        st.info(f"{current['type']} - {mins} mins")

    st.dataframe(get_hours().tail(10))

# =========================
# JOBS
# =========================
if app == "Jobs":

    st.header("Jobs")

    jobs = load_csv(JOBS_FILE, jobs_cols)

    job_text = st.text_input("New job")

    if st.button("Add Job"):
        new = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Vehicle": vehicle,
            "Job": job_text,
            "Status": "OPEN"
        }])
        jobs = pd.concat([jobs, new], ignore_index=True)
        save_csv(jobs, JOBS_FILE)
        st.rerun()

    for i,row in jobs.iterrows():
        c1,c2 = st.columns([3,1])
        c1.write(row["Job"])
        if row["Status"]=="OPEN":
            if c2.button("Done", key=i):
                jobs.loc[i,"Status"]="DONE"
                save_csv(jobs, JOBS_FILE)
                st.rerun()

# =========================
# RHA CHECK
# =========================
if app == "RHA Check":

    st.header("RHA Check")

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

    st.write("Status:", overall)

    if st.button("Submit Check"):

        defect_text = " | ".join([f"{k}:{v}" for k,v in notes.items()])

        checks = load_csv(CHECKS_FILE, checks_cols)

        new = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Latitude": lat,
            "Longitude": lon,
            "Defects": defect_text,
            "Status": overall
        }])

        checks = pd.concat([checks, new], ignore_index=True)
        save_csv(checks, CHECKS_FILE)

        if overall != "PASS":
            jobs = load_csv(JOBS_FILE, jobs_cols)

            for k,v in notes.items():
                j = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Vehicle": vehicle,
                    "Job": f"{k}:{v}",
                    "Status": "OPEN"
                }])
                jobs = pd.concat([jobs, j], ignore_index=True)

            save_csv(jobs, JOBS_FILE)

            send_email_alert("Vehicle Issue", defect_text)

        st.success("Check saved")
        st.rerun()

# =========================
# MANAGER
# =========================
if app == "Manager":

    st.header("Manager Dashboard")

    checks = load_csv(CHECKS_FILE, checks_cols)
    jobs = load_csv(JOBS_FILE, jobs_cols)

    st.write("Total checks:", len(checks))

    st.subheader("Open Jobs")
    st.dataframe(jobs[jobs["Status"]=="OPEN"])

# =========================
# SETTINGS
# =========================
if app == "Settings":

    st.header("Email Settings")

    email = st.text_input("Email")
    password = st.text_input("App Password", type="password")

    if st.button("Save"):
        df = pd.DataFrame([{"Email": email, "Password": password}])
        save_csv(df, SETTINGS_FILE)
        st.success("Saved")

# =========================
# USER MANAGEMENT
# =========================
if app == "Users":

    st.header("Driver Management")

    users = load_csv(USERS_FILE, users_cols)

    st.subheader("Add Driver")
    u = st.text_input("Username")
    p = st.text_input("Password")

    if st.button("Add Driver"):
        new = pd.DataFrame([{"Username":u,"Password":p,"Role":"driver"}])
        users = pd.concat([users, new], ignore_index=True)
