import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# FILES
# =========================
HOURS_FILE = "hours.csv"
CHECKS_FILE = "data.csv"
JOBS_FILE = "jobs.csv"
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

    # ensure columns always exist
    for col in cols:
        if col not in df.columns:
            df[col] = ""

    return df


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
# LOGIN
# =========================
users = {"david": "1234", "john": "1234"}

if not st.session_state.logged_in:
    st.title("FleetCheck Pro")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Login failed")

    st.stop()

# =========================
# NAV
# =========================
app = st.sidebar.radio("Select App", ["Driver Hours", "Jobs", "RHA Check"])

vehicle = st.sidebar.selectbox("Vehicle", ["AB12 XYZ", "BT23 FLEET"])
lat = st.sidebar.text_input("Latitude")
lon = st.sidebar.text_input("Longitude")

# =========================
# DRIVER HOURS
# =========================
if app == "Driver Hours":

    st.header("Driver Hours")

    def get_hours():
        df = load_csv(HOURS_FILE, hours_cols)

        if not df.empty:
            df = df[df["Driver"] == st.session_state.user]
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
            mins = int((datetime.now() - st.session_state.current["start"]).total_seconds() / 60)
            if mins >= 270:
                return False

        return True

    def start(activity):
        if activity == "DRIVING" and not can_drive():
            st.error("Driving blocked (DVSA)")
            return

        st.session_state.current = {
            "type": activity,
            "start": datetime.now()
        }

    def stop():
        if not st.session_state.current:
            return

        df = load_csv(HOURS_FILE, hours_cols)

