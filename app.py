import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="FleetCheck Pro", layout="wide")

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
            return pd.read_csv(file)
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_csv(df, file):
    df.to_csv(file, index=False)

hours_cols = ["Driver","Vehicle","Type","Start","End","Duration","Latitude","Longitude"]
checks_cols = ["Date","Time","Driver","Vehicle","Latitude","Longitude","Defects","Status"]
jobs_cols = ["Date","Vehicle","Job","Status"]

hours = load_csv(HOURS_FILE, hours_cols)
checks = load_csv(CHECKS_FILE, checks_cols)
jobs = load_csv(JOBS_FILE, jobs_cols)

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
users = {"david":"1234","john":"1234"}

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
page = st.radio("", ["Driver","Jobs","AI"], horizontal=True)

# =========================
# DRIVER PAGE
# =========================
if page == "Driver":

    st.header("Driver Panel")

    vehicle = st.selectbox("Vehicle", ["AB12 XYZ","BT23 FLEET"])

    # -------- GPS --------
    st.subheader("GPS")
    lat = st.text_input("Latitude")
    lon = st.text_input("Longitude")

    # ================= CHECKS =================
    st.subheader("Vehicle Check")

    check_items = [
        "Tyres","Brakes","Lights","Mirrors",
        "Horn","Seatbelt","Oil","Coolant",
        "Load Secure","Plates"
    ]

    results = {}
    notes = {}
    photos_data = {}

    for item in check_items:

        st.markdown(f"### {item}")

        status = st.radio(
            item,
            ["PASS","FAIL","NA"],
            key=item,
            horizontal=True
        )

        results[item] = status

        if status == "FAIL":
            notes[item] = st.text_area(f"{item} note", key=f"{item}_note")

            photo = st.file_uploader(f"{item} photo", key=f"{item}_photo")
            if photo:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{item}.jpg"
                path = os.path.join(PHOTO_DIR, filename)

                with open(path, "wb") as f:
                    f.write(photo.getbuffer())

                photos_data[item] = filename

    overall = "PASS"
    if "FAIL" in results.values():
        overall = "FAIL"

    if overall == "FAIL":
        st.error("Vehicle FAILED")
    else:
        st.success("Vehicle PASSED")

    # SAVE CHECK
    if st.button("Save Check"):

        defects = []
        for k,v in notes.items():
            defects.append(f"{k}:{v}")

        defect_text = " | ".join(defects)

        new_check = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Latitude": lat,
            "Longitude": lon,
            "Defects": defect_text,
            "Status": overall
        }])

        checks = pd.concat([checks, new_check], ignore_index=True)
        save_csv(checks, CHECKS_FILE)

        # AUTO JOB CREATE IF FAIL
        if overall == "FAIL":
            for k,v in notes.items():
                new_job = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Vehicle": vehicle,
                    "Job": f"{k}: {v}",
                    "Status": "OPEN"
                }])

                jobs = pd.concat([jobs, new_job], ignore_index=True)

            save_csv(jobs, JOBS_FILE)

        st.success("Saved ✅")
        st.rerun()

    st.divider()

    # ================= HOURS =================
    st.subheader("Driver Hours")

    def get_hours():
        df = load_csv(HOURS_FILE, hours_cols)
        df = df[df["Driver"] == st.session_state.user]
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Start"])
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

        start_t = st.session_state.current["start"]
        end_t = datetime.now()

        mins = int((end_t - start_t).total_seconds()/60)

        new = pd.DataFrame([{
            "Driver": st.session_state.user,
            "Vehicle": vehicle,
            "Type": st.session_state.current["type"],
            "Start": start_t,
            "End": end_t,
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

    st.button("Stop Activity", on_click=stop)

    if st.session_state.current:
        mins = int((datetime.now() - st.session_state.current["start"]).total_seconds()/60)
        st.info(f"{st.session_state.current['type']} - {mins} mins")

    st.dataframe(get_hours())

# =========================
# JOBS PAGE
# =========================
if page == "Jobs":

    st.header("Jobs")

    jobs = load_csv(JOBS_FILE, jobs_cols)

    if jobs.empty:
        st.info("No jobs")
    else:
        for i,row in jobs.iterrows():
            c1,c2 = st.columns([3,1])
            c1.write(f"{row['Vehicle']} - {row['Job']}")

            if row["Status"] == "OPEN":
                if c2.button("Complete", key=i):
                    jobs.loc[i,"Status"] = "DONE"
                    save_csv(jobs, JOBS_FILE)
                    st.rerun()

    st.dataframe(jobs)

# =========================
# AI PAGE
# =========================
if page == "AI":

    st.header("AI Analysis")

    df = load_csv(HOURS_FILE, hours_cols)

    if df.empty:
        st.info("No data")
    else:
        for d in df["Driver"].unique():

            ddf = df[df["Driver"] == d]
            total = ddf[ddf["Type"]=="DRIVING"]["Duration"].sum()

            st.write("---")
            st.write(f"Driver: {d}")
            st.write(f"Driving total: {total}")

            if total > 3000:
                st.warning("High workload")

            violations = ddf[ddf["Duration"] > 270]
            if not violations.empty:
                st.error("Violations detected")
                st.dataframe(violations)
