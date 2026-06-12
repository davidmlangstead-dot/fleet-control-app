import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# FILES / FOLDERS
# =========================
HOURS_FILE = "hours.csv"
CHECKS_FILE = "data.csv"
JOBS_FILE = "jobs.csv"
PHOTO_DIR = "photos"

os.makedirs(PHOTO_DIR, exist_ok=True)

# =========================
# LOAD / SAVE FUNCTIONS
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

hours_cols = ["Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"]
checks_cols = ["Date","Time","Driver","Vehicle","Latitude","Longitude","Defects","Status"]
jobs_cols = ["Date","Vehicle","Job","Status"]

# =========================
# SESSION
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current" not in st.session_state:
    st.session_state.current = None

# =========================
# LOGIN SYSTEM
# =========================
users = {"david":"1234","john":"1234"}

if not st.session_state.logged_in:
    st.title("FleetCheck Pro")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Login failed")

    st.stop()

# =========================
# MAIN NAV (3 APPS)
# =========================
app = st.sidebar.radio("Select App", ["Driver Hours","Jobs","RHA Check"])

vehicle = st.sidebar.selectbox("Vehicle", ["AB12 XYZ","BT23 FLEET"])

lat = st.sidebar.text_input("Latitude")
lon = st.sidebar.text_input("Longitude")

# =========================
# DRIVER HOURS
# =========================
if app == "Driver Hours":

    st.header("Driver Hours")

    def get_hours():
        df = load_csv(HOURS_FILE, hours_cols)
        df = df[df.get("Driver") == st.session_state.user]
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
        return df

    def can_drive():
        df = get_hours()

        if not df.empty:
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())

            today_drive = df[df["Start"].dt.date == today]["Duration"].sum()
            week_drive = df[df["Start"].dt.date >= week_start]["Duration"].sum()

            if today_drive >= 540:
                return False
            if week_drive >= 3360:
                return False

        if st.session_state.current:
            mins = int((datetime.now() - st.session_state.current["start"]).total_seconds()/60)
            if mins >= 270:
                return False

        return True

    def start(act):
        if act == "DRIVING" and not can_drive():
            st.error("Driving blocked (DVSA)")
            return
        st.session_state.current = {"type": act, "start": datetime.now()}

    def stop():
        if not st.session_state.current:
            return

        df = load_csv(HOURS_FILE, hours_cols)

        start_time = st.session_state.current["start"]
        end_time = datetime.now()

        minutes = int((end_time - start_time).total_seconds()/60)

        new = pd.DataFrame([{
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Type": st.session_state.current["type"],
            "Start": start_time,
            "End": end_time,
            "Duration": minutes,
            "Latitude": lat,
