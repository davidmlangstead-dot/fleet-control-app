import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os

DATA_FILE = "data.csv"
JOBS_FILE = "jobs.csv"
HOURS_FILE = "hours.csv"

st.set_page_config(layout="wide", page_title="FleetCheck Pro")

# =========================
# LOAD / SAVE
# =========================

def load_csv(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save_csv(df, file):
    df.to_csv(file, index=False)

checks = load_csv(DATA_FILE, ["Date","Time","Driver","Vehicle","Odometer","Latitude","Longitude","Defects","Status"])
jobs = load_csv(JOBS_FILE, ["Date","Vehicle","Job","Engineer","Status"])
hours = load_csv(HOURS_FILE, ["Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"])

# =========================
# SESSION
# =========================

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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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


    st.markdown("## Driver Panel")


    vehicle = st.selectbox("Vehicle", VEHICLES)


    # =========================
    # REAL GPS BUTTON
    # =========================


    st.subheader("GPS Auto Capture")


    st.components.v1.html("""
        <button onclick=\"navigator.geolocation.getCurrentPosition(function(pos){
        const lat=pos.coords.latitude;
        const lon=pos.coords.longitude;
        window.parent.location.search=`?lat=${lat}&lon=${lon}`;
        })\">Get GPS</button>
    """, height=60)


    params = st.experimental_get_query_params()
    lat = params.get("lat", [""])[0]
    lon = params.get("lon", [""])[0]


    col1, col2 = st.columns(2)
    lat = col1.text_input("Latitude", lat)
    lon = col2.text_input("Longitude", lon)


    # =========================
    # DRIVER HOURS
    # =========================


    st.subheader("Driver Hours")


    def start_hours(activity):
        now = datetime.now()
        if st.session_state.current_hours:
            stop_hours()
        st.session_state.current_hours = {"type": activity, "start": now}


    def stop_hours():
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


        global hours
        hours = pd.concat([hours, pd.DataFrame([new])], ignore_index=True)
        save_csv(hours, HOURS_FILE)


        st.session_state.current_hours = None


    c1, c2, c3, c4 = st.columns(4)
    c1.button("Driving", on_click=start_hours, args=("DRIVING",))
    c2.button("Rest", on_click=start_hours, args=("REST",))
    c3.button("POA", on_click=start_hours, args=("POA",))
    c4.button("Other", on_click=start_hours, args=("OTHER",))


    st.button("Stop", on_click=stop_hours)


    # =========================
    # LIVE + DVSA LIMITS
    # =========================


    if st.session_state.current_hours:
        elapsed = int((datetime.now() - st.session_state.current_hours["start"]).total_seconds() / 60)
        st.info(f"Current: {st.session_state.current_hours['type']} ({elapsed} mins)")


        if st.session_state.current_hours["type"] == "DRIVING":
            if elapsed >= 270:
                st.error("🚫 OVER 4.5 HOURS - STOP NOW")
            elif elapsed >= 240:
                st.warning("⚠️ Approaching 4.5 hour limit")


    st.write("---")


    # =========================
    # DAILY + WEEKLY CHECKS
    # =========================


    if not hours.empty:
        df_user = hours[hours["Driver"] == st.session_state.user].copy()
        df_user["Start"] = pd.to_datetime(df_user["Start"])


        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())


        today_df = df_user[df_user["Start"].dt.date == today]
        week_df = df_user[df_user["Start"].dt.date >= week_start]


        drive_today = today_df[today_df["Type"] == "DRIVING"]["Duration"].sum()
        drive_week = week_df[week_df["Type"] == "DRIVING"]["Duration"].sum()


        st.subheader("Summary")
        st.write(f"Today Driving: {drive_today} mins")
        st.write(f"Week Driving: {drive_week} mins")


        if drive_today >= 540:
            st.error("🚫 DAILY LIMIT HIT (9h)")
        elif drive_today >= 480:
            st.warning("⚠️ Near daily limit")


    st.subheader("Hours Log")
    st.dataframe(df_user, use_container_width=True)
# =========================
# AI ANALYSIS (SMART FREE)
# =========================

if page == "AI":

    st.markdown("## AI Driver Analysis")

    if hours.empty:
        st.info("No data yet")
    else:
        df = hours.copy()
        df["Start"] = pd.to_datetime(df["Start"])
        drivers = df["Driver"].unique()


        for d in drivers:
            ddf = df[df["Driver"] == d]
            total_drive = ddf[ddf["Type"] == "DRIVING"]["Duration"].sum()


            st.write("---")
            st.write(f"Driver: {d}")
            st.write(f"Total Driving: {total_drive} mins")

            if total_drive > 3000:
                st.warning("⚠️ High workload driver")

            over_limit = ddf[ddf["Duration"] > 270]
            if not over_limit.empty:
                st.error("🚫 Driving violations detected")
                st.write(over_limit[["Start","Duration"]])

    st.caption("AI is rule-based and free. Upgrade later if needed.")
