import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="FleetCheck Pro", layout="wide")

HOURS_FILE = "hours.csv"
CHECKS_FILE = "data.csv"

# =========================
# SAFE LOAD / SAVE
# =========================
def load_csv(file, cols):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
        except:
            df = pd.DataFrame(columns=cols)
    else:
        df = pd.DataFrame(columns=cols)
    return df

def save_csv(df, file):
    df.to_csv(file, index=False)

hours = load_csv(HOURS_FILE, [
    "Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"
])

checks = load_csv(CHECKS_FILE, [
    "Date","Time","Driver","Vehicle","Latitude","Longitude","Defects","Status"
])

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
USERS = {"david":"1234","john":"1234"}

if not st.session_state.logged_in:
    st.title("FleetCheck Pro")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Login failed")

    st.stop()

# =========================
# NAV
# =========================
page = st.radio("", ["Driver","AI"], horizontal=True)

# =========================
# DRIVER PAGE
# =========================
if page == "Driver":

    st.header("Driver Panel")

    vehicle = st.selectbox("Vehicle", ["AB12 XYZ","BT23 FLEET"])

    # ================= GPS =================
    st.subheader("GPS")
    lat = st.text_input("Latitude")
    lon = st.text_input("Longitude")

    # ================= CHECKS =================
    st.subheader("Daily Vehicle Check")

    checks_list = [
        "Tyres","Brakes","Lights","Mirrors",
        "Horn","Seatbelt","Oil","Coolant",
        "Load Secure","Plates"
    ]

    results = {}
    notes = {}

    for item in checks_list:

        st.markdown(f"### {item}")

        status = st.radio(
            item,
            ["PASS","FAIL","NA"],
            key=f"{item}",
            horizontal=True
        )

        results[item] = status

        if status == "FAIL":
            notes[item] = st.text_area(f"{item} note", key=f"{item}_note")
            st.file_uploader(f"{item} photo", key=f"{item}_photo")

    overall_status = "PASS"
    if "FAIL" in results.values():
        overall_status = "FAIL"

    if overall_status == "FAIL":
        st.error("Vehicle FAILED")
    else:
        st.success("Vehicle PASSED")

    # SAVE CHECK
    if st.button("Save Check"):

        defect_text = " | ".join([f"{k}:{v}" for k, v in notes.items()])

        new = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Latitude": lat,
            "Longitude": lon,
            "Defects": defect_text,
            "Status": overall_status
        }])

        updated = pd.concat([checks, new], ignore_index=True)
        save_csv(updated, CHECKS_FILE)

        st.success("Check saved ✅")
        st.rerun()

    st.divider()

    # ================= HOURS =================
    st.subheader("Driver Hours")

    def get_user_hours():
        df = load_csv(HOURS_FILE, [
            "Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"
        ])
        df = df[df["Driver"] == st.session_state.user]
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
        return df

    def limits_ok():

        df = get_user_hours()
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        if not df.empty:
            today_df = df[df["Start"].dt.date == today]
            week_df = df[df["Start"].dt.date >= week_start]

            if today_df["Duration"].sum() >= 540:
                return False

            if week_df["Duration"].sum() >= 3360:
                return False

        if st.session_state.current:
            mins = int((datetime.now() - st.session_state.current["start"]).total_seconds() / 60)
            if mins >= 270:
                return False

        return True

    def start(type):

        if type == "DRIVING" and not limits_ok():
            st.error("Driving blocked (DVSA limit reached)")
            return

        st.session_state.current = {
            "type": type,
            "start": datetime.now()
        }

    def stop():

        if not st.session_state.current:
            return

        df = load_csv(HOURS_FILE, [
