import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="FleetCheck Pro", layout="wide")

# =========================
# FILES
# =========================
HOURS_FILE = "hours.csv"

# =========================
# LOAD SAFE
# =========================
def load_hours():
    if os.path.exists(HOURS_FILE):
        try:
            df = pd.read_csv(HOURS_FILE)
        except:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=[
            "Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"
        ])

    return df

def save_hours(df):
    df.to_csv(HOURS_FILE, index=False)

hours = load_hours()

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current" not in st.session_state:
    st.session_state.current = None

# =========================
# LOGIN
# =========================
USERS = {
    "david":"1234",
    "john":"1234"
}

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

    # ----- GPS (SAFE) -----
    st.subheader("GPS (safe input)")
    lat = st.text_input("Latitude")
    lon = st.text_input("Longitude")

    # ----- HOURS -----
    st.subheader("Driver Hours")

    def get_user_hours():
        df = hours[hours["Driver"] == st.session_state.user].copy()
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
        return df

    def check_limits():

        df = get_user_hours()

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        if not df.empty:

            today_df = df[df["Start"].dt.date == today]
            week_df = df[df["Start"].dt.date >= week_start]

            drive_today = today_df[today_df["Type"] == "DRIVING"]["Duration"].sum()
            drive_week = week_df[week_df["Type"] == "DRIVING"]["Duration"].sum()

            if drive_today >= 540:
                return False, "Daily limit reached (9h)"

            if drive_week >= 3360:
                return False, "Weekly limit reached (56h)"

        if st.session_state.current:
            elapsed = int((datetime.now() - st.session_state.current["start"]).total_seconds()/60)
            if st.session_state.current["type"] == "DRIVING" and elapsed >= 270:
                return False, "Must take break (4.5h reached)"

        return True, ""

    def start(type):

        if type == "DRIVING":
            allowed, msg = check_limits()
            if not allowed:
                st.error(msg)
                return

        st.session_state.current = {
            "type": type,
            "start": datetime.now()
        }

    def stop():

        if not st.session_state.current:
            return

        start_time = st.session_state.current["start"]
        end_time = datetime.now()

        duration = int((end_time - start_time).total_seconds()/60)

        new = pd.DataFrame([{
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Type": st.session_state.current["type"],
            "Start": start_time,
            "End": end_time,
            "Duration": duration,
            "Latitude": lat,
            "Longitude": lon
        }])

        global hours
        hours = pd.concat([hours, new], ignore_index=True)
        save_hours(hours)

        st.session_state.current = None

    c1,c2,c3,c4 = st.columns(4)

    c1.button("Driving", on_click=start, args=("DRIVING",))
    c2.button("Rest", on_click=start, args=("REST",))
    c3.button("POA", on_click=start, args=("POA",))
    c4.button("Other", on_click=start, args=("OTHER",))

    st.button("Stop", on_click=stop)

    # ----- LIVE -----
    if st.session_state.current:
        mins = int((datetime.now() - st.session_state.current["start"]).total_seconds()/60)
        st.info(f"{st.session_state.current['type']} - {mins} mins")

        if st.session_state.current["type"] == "DRIVING":
            if mins >= 270:
                st.error("STOP NOW - 4.5h reached")
            elif mins >= 240:
                st.warning("Approaching 4.5h")

    # ----- SUMMARY -----
    df_user = get_user_hours()

    if not df_user.empty:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        today_df = df_user[df_user["Start"].dt.date == today]
        week_df = df_user[df_user["Start"].dt.date >= week_start]

        st.subheader("Summary")
        st.write("Today:", today_df[today_df["Type"]=="DRIVING"]["Duration"].sum(), "mins")
        st.write("Week:", week_df[week_df["Type"]=="DRIVING"]["Duration"].sum(), "mins")

    st.subheader("Logs")
    st.dataframe(df_user)

# =========================
# AI PAGE
# =========================
if page == "AI":

    st.header("AI Analysis")

