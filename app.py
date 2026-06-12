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
# MAIN NAV (3 APPS)
# =========================
app = st.sidebar.radio("Select App", ["Driver Hours","Jobs","RHA Check"])

vehicle = st.sidebar.selectbox("Vehicle", ["AB12 XYZ","BT23 FLEET"])

lat = st.sidebar.text_input("Latitude")
lon = st.sidebar.text_input("Longitude")

# =========================
# APP 1 - DRIVER HOURS
# =========================
if app == "Driver Hours":

    st.header("Driver Hours")

    def get_hours():
        df = load_csv(HOURS_FILE, hours_cols)
        df = df[df.get("Driver","") == st.session_state.user]
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

    def start(activity):
        if activity == "DRIVING" and not can_drive():
            st.error("Driving blocked (DVSA)")
            return
        st.session_state.current = {"type": activity, "start": datetime.now()}

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

    st.button("Stop", on_click=stop)

    if st.session_state.current:
        mins = int((datetime.now() - st.session_state.current["start"]).total_seconds()/60)
        st.info(f"{st.session_state.current['type']} - {mins} mins")

    st.dataframe(get_hours().tail(10))

# =========================
# APP 2 - JOBS
# =========================
if app == "Jobs":

    st.header("Jobs")

    jobs = load_csv(JOBS_FILE, jobs_cols)

    job_text = st.text_input("Add Job")
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

    if jobs.empty:
        st.info("No jobs")
    else:
        for i,row in jobs.iterrows():
            c1,c2 = st.columns([3,1])
            c1.write(f"{row['Vehicle']} - {row['Job']}")

            if row["Status"] == "OPEN":
                if c2.button("Done", key=i):
                    jobs.loc[i,"Status"] = "DONE"
                    save_csv(jobs, JOBS_FILE)
                    st.rerun()

# =========================
# APP 3 - RHA CHECK SHEET
# =========================
if app == "RHA Check":

    st.header("RHA Daily Check")

    checks = load_csv(CHECKS_FILE, checks_cols)

    items = [
        "Tyres","Brakes","Lights","Mirrors",
        "Horn","Seatbelt","Oil","Coolant",
        "Load Secure","Plates"
    ]

    results = {}
    notes = {}

    for item in items:
        with st.expander(item):

            status = st.radio(item, ["PASS","FAIL","NA"], key=item)
            results[item] = status

            if status == "FAIL":
                notes[item] = st.text_area(f"{item} note", key=f"{item}_note")

                photo = st.file_uploader(f"{item} photo", key=f"{item}_photo")

                if photo:
                    path = os.path.join(PHOTO_DIR, f"{datetime.now().timestamp()}_{item}.jpg")
                    with open(path, "wb") as f:
                        f.write(photo.getbuffer())

    overall = "FAIL" if "FAIL" in results.values() else "PASS"

    if st.button("Submit RHA Check"):

        defect_text = " | ".join([f"{k}:{v}" for k,v in notes.items()])

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

        # AUTO JOBS
        if overall == "FAIL":
            jobs = load_csv(JOBS_FILE, jobs_cols)

            for k,v in notes.items():
                job = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Vehicle": vehicle,
                    "Job": f"{k}: {v}",
                    "Status": "OPEN"
                }])
                jobs = pd.concat([jobs, job], ignore_index=True)

            save_csv(jobs, JOBS_FILE)

        st.success("Check submitted ✅")
        st.rerun()
``
