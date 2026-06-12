import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os

# FILES
DATA_FILE = "data.csv"
JOBS_FILE = "jobs.csv"
HOURS_FILE = "hours.csv"

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

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

checks = load_csv(DATA_FILE, ["Date","Time","Driver","Vehicle","Odometer","Latitude","Longitude","Defects","Status"])
jobs = load_csv(JOBS_FILE, ["Date","Vehicle","Job","Engineer","Status"])
hours = load_csv(HOURS_FILE, ["Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"])

# =========================
# SESSION
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_hours" not in st.session_state:
    st.session_state.current_hours = None

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
if not st.session_state.logged_in:

    st.title("FleetCheck Pro")

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
# NAV
# =========================
if st.session_state.role == "driver":
    pages = ["Driver"]
else:
    pages = ["Dashboard","Jobs","Workshop","AI"]

page = st.radio("", pages, horizontal=True)

# =========================
# DRIVER PAGE
# =========================
if page == "Driver":

    st.header("Driver Panel")

    vehicle = st.selectbox("Vehicle", VEHICLES)

    # ================= GPS =================
    st.subheader("GPS")

    st.components.v1.html("""
    <button onclick="
    navigator.geolocation.getCurrentPosition(function(pos){
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        window.parent.location.search = `?lat=${lat}&lon=${lon}`;
    });
    ">Get GPS</button>
    """, height=50)

    params = st.query_params
    lat = params.get("lat", "")
    lon = params.get("lon", "")

    c1, c2 = st.columns(2)
    lat = c1.text_input("Latitude", lat)
    lon = c2.text_input("Longitude", lon)

    # ================= HOURS =================
    st.subheader("Driver Hours")

    def get_driver_data():
        df = hours[hours["Driver"] == st.session_state.user].copy()
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
        return df

    def can_drive():
        df = get_driver_data()

        if df.empty:
            return True

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        today_df = df[df["Start"].dt.date == today]
        week_df = df[df["Start"].dt.date >= week_start]

        drive_today = today_df[today_df["Type"] == "DRIVING"]["Duration"].sum()
        drive_week = week_df[week_df["Type"] == "DRIVING"]["Duration"].sum()

        if drive_today >= 540:
            return False, "Daily limit reached (9h)"
        if drive_week >= 3360:
            return False, "Weekly limit reached (56h)"

        if st.session_state.current_hours:
            elapsed = int((datetime.now() - st.session_state.current_hours["start"]).total_seconds() / 60)
            if elapsed >= 270:
                return False, "4.5 hour limit reached - must rest"

        return True, ""

    def start_hours(activity):

        if activity == "DRIVING":
            allowed, msg = can_drive()
            if allowed is False:
                st.error(msg)
                return

        if st.session_state.current_hours:
            stop_hours()

        st.session_state.current_hours = {
            "type": activity,
            "start": datetime.now()
        }

    def stop_hours():
        global hours

        if not st.session_state.current_hours:
            return

        end = datetime.now()
        start = st.session_state.current_hours["start"]

        duration = int((end - start).total_seconds() / 60)

        new = {
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Type": st.session_state.current_hours["type"],
            "Start": start,
            "End": end,
            "Duration": duration,
            "Latitude": lat,
            "Longitude": lon
        }

        hours = pd.concat([hours, pd.DataFrame([new])], ignore_index=True)
        save_csv(hours, HOURS_FILE)

        st.session_state.current_hours = None

    b1, b2, b3, b4 = st.columns(4)

    b1.button("Driving", on_click=start_hours, args=("DRIVING",))
    b2.button("Rest", on_click=start_hours, args=("REST",))
    b3.button("POA", on_click=start_hours, args=("POA",))
    b4.button("Other", on_click=start_hours, args=("OTHER",))

    st.button("Stop", on_click=stop_hours)

    # ================= LIVE =================
    if st.session_state.current_hours:
        elapsed = int((datetime.now() - st.session_state.current_hours["start"]).total_seconds() / 60)

        st.info(f"{st.session_state.current_hours['type']} - {elapsed} mins")

        if st.session_state.current_hours["type"] == "DRIVING":
            if elapsed >= 270:
                st.error("LOCKED - Must rest now")
            elif elapsed >= 240:
                st.warning("Approaching 4.5 hours")

    st.divider()

    # ================= SUMMARY =================
    df_user = get_driver_data()

    if not df_user.empty:

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        today_df = df_user[df_user["Start"].dt.date == today]
        week_df = df_user[df_user["Start"].dt.date >= week_start]

        drive_today = today_df[today_df["Type"] == "DRIVING"]["Duration"].sum()
        drive_week = week_df[week_df["Type"] == "DRIVING"]["Duration"].sum()

        st.subheader("Summary")
        st.write(f"Today: {drive_today} mins")
        st.write(f"Week: {drive_week} mins")

        if drive_today >= 540:
            st.error("Daily limit hit")
        if drive_week >= 3360:
            st.error("Weekly limit hit")

    st.subheader("Logs")
    st.dataframe(df_user, use_container_width=True)

# =========================
# AI PAGE
# =========================
if page == "AI":

    st.header("AI Driver Analysis")

    if hours.empty:
        st.info("No data")
    else:
        df = hours.copy()
        df["Start"] = pd.to_datetime(df["Start"], errors="coerce")

        for driver in df["Driver"].unique():
            ddf = df[df["Driver"] == driver]

            total = ddf[ddf["Type"] == "DRIVING"]["Duration"].sum()

            st.write("---")
            st.write(f"Driver: {driver}")
            st.write(f"Driving total: {total} mins")

            if total > 3000:
                st.warning("High workload")

            violations = ddf[ddf["Duration"] > 270]

            if not violations.empty:
                st.error("Violations detected")
                st.dataframe(violations[["Start","Duration"]])
