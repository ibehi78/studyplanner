import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from icalendar import Calendar, Event
import json
import os
import hashlib

# --- JSON backend ---
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,"w") as f:
            json.dump({"tasks":[],"timetable":[],"sessions":[],"users":[],"chat":[]}, f)
    with open(DATA_FILE,"r") as f:
        data = json.load(f)
    for key in ["tasks","timetable","sessions","users","chat"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
    return data

def save_data(data):
    with open(DATA_FILE,"w") as f:
        json.dump(data,f,default=str,indent=4)

# --- Password Hashing ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Sign Up & Login ---
def sign_up(username,password):
    data = load_data()
    if username in [u.get("username") for u in data["users"]]:
        return False, "Username already exists"
    if len(data["users"]) >= 10:
        return False, "User limit reached (10)"
    hashed_pw = hash_password(password)
    data["users"].append({"username":username,"password":hashed_pw})
    save_data(data)
    return True, "Sign Up successful!"

def login(username,password):
    data = load_data()
    hashed_pw = hash_password(password)
    for u in data["users"]:
        if u.get("username") == username and u.get("password") == hashed_pw:
            return True
    return False

# --- Page Config ---
st.set_page_config(page_title="Study Planner", layout="wide")

mode = st.sidebar.radio("Theme Mode", ["Light","Dark"])
color1 = st.sidebar.color_picker("Pick first color","#f8ffae")
color2 = st.sidebar.color_picker("Pick second color","#43c6ac")

st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(to right, {color1}, {color2});
    min-height: 100vh;
    color: {'white' if mode=='Dark' else 'black'};
}}
.stButton>button {{
    background-color: rgba(255, 255, 255, 0.3);
    border: 1px solid {'white' if mode=='Dark' else 'black'};
    color: {'white' if mode=='Dark' else 'black'};
    font-weight: bold;
    border-radius: 8px;
}}
.stButton>button:hover {{
    background-color: rgba(255, 255, 255, 0.5);
}}
textarea, input, select {{
    background-color: rgba(255, 255, 255, 0.3);
    border: 1px solid {'white' if mode=='Dark' else 'black'};
    color: {'white' if mode=='Dark' else 'black'};
    border-radius: 6px;
    padding: 5px;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(to bottom, {color1}, {color2});
    color: {'white' if mode=='Dark' else 'black'};
}}
</style>
""", unsafe_allow_html=True)

st.title("📚 Study Planner")

# --- Sidebar Account & Controls (hidden in one bar) ---
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

with st.sidebar.expander("🔒 Account & Controls", expanded=False):
    account_action = st.radio("Account Action", ["Login","Sign Up"], key="account_action_sidebar")

    if account_action == "Sign Up":
        new_user = st.text_input("Username", key="signup_username")
        new_pass = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up", key="signup_btn"):
            success, msg = sign_up(new_user, new_pass)
            if success:
                st.success(msg)
            else:
                st.error(msg)

    elif account_action == "Login":
        user = st.text_input("Username", key="login_username")
        pw = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_btn"):
            if login(user, pw):
                st.success(f"Logged in as {user}")
                st.session_state["logged_in_user"] = user
            else:
                st.error("Invalid username or password")

    if st.session_state.get("logged_in_user"):
        if st.button("Log out", key="logout_btn"):
            st.session_state["logged_in_user"] = None
            st.experimental_rerun()

    st.checkbox("Enable delete buttons", key="enable_delete")

if not st.session_state["logged_in_user"]:
    st.warning("Please log in or sign up to access the Study Planner.")
    st.stop()

# --- Core Functions ---
def add_task(subject,description,date):
    data = load_data()
    data["tasks"].append({"Subject":subject,"Description":description,"Date":str(date)})
    save_data(data)

def update_task(index,subject,description,date):
    data = load_data()
    data["tasks"][index] = {"Subject":subject,"Description":description,"Date":str(date)}
    save_data(data)

def delete_task(index):
    data = load_data()
    data["tasks"].pop(index)
    save_data(data)

def add_timetable(day,time,subject,notes):
    data = load_data()
    data["timetable"].append({"Day":day,"Time":str(time),"Subject":subject,"Notes":notes})
    save_data(data)

def update_timetable(index,day,time,subject,notes):
    data = load_data()
    data["timetable"][index] = {"Day":day,"Time":str(time),"Subject":subject,"Notes":notes}
    save_data(data)

def delete_timetable(index):
    data = load_data()
    data["timetable"].pop(index)
    save_data(data)

def add_session(name,date,notes):
    data = load_data()
    data["sessions"].append({"Session Name":name,"Date":str(date),"Notes":notes})
    save_data(data)

def update_session(index,name,date,notes):
    data = load_data()
    data["sessions"][index] = {"Session Name":name,"Date":str(date),"Notes":notes}
    save_data(data)

def delete_session(index):
    data = load_data()
    data["sessions"].pop(index)
    save_data(data)

def send_message(user,message):
    data = load_data()
    data["chat"].append({"User":user,"Message":message,"Time":str(datetime.datetime.now())})
    save_data(data)

def export_tasks_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    data_load = load_data()
    table_data = [["Subject","Description","Due Date"]] + [[t["Subject"],t["Description"],t["Date"]] for t in data_load["tasks"]]
    table = Table(table_data)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),
                               ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                               ('GRID',(0,0),(-1,-1),1,colors.black)]))
    doc.build([table])
    buffer.seek(0)
    return buffer

def export_timetable_ical():
    cal = Calendar()
    data_load = load_data()
    for t in data_load["timetable"]:
        try:
            dtstart = pd.to_datetime(t["Time"])
        except:
            dtstart = datetime.datetime.now()
        event = Event()
        event.add("summary",t["Subject"])
        event.add("description",t["Notes"])
        event.add("dtstart",dtstart)
        event.add("dtend",dtstart+pd.Timedelta(hours=1))
        cal.add_component(event)
    return cal.to_ical()

# --- Sidebar Menu ---
menu = st.sidebar.selectbox("Menu", ["Planner","Timetable","Sessions","Export","Users & Chat"])
data = load_data()

# --- Planner (Editable) ---
if menu == "Planner":
    st.subheader("📝 Tasks")
    subject = st.text_input("Subject", key="task_subject")
    description = st.text_area("Description", key="task_description")
    date = st.date_input("Due Date", key="task_date")
    if st.button("Add Task"):
        add_task(subject, description, date)
        st.success("Task added!")

    for i, t in enumerate(data["tasks"]):
        with st.expander(f"{t['Date']} - {t['Subject']}"):
            new_subject = st.text_input("Subject", value=t["Subject"], key=f"task_s_{i}")
            new_description = st.text_area("Description", value=t["Description"], key=f"task_d_{i}")
            new_date = st.date_input("Due Date", value=pd.to_datetime(t["Date"]), key=f"task_date_{i}")
            if st.button(f"Update Task {i}"):
                update_task(i, new_subject, new_description, new_date)
                st.success("Task updated!")
                st.experimental_rerun()
            if st.session_state.get("enable_delete") and st.button(f"Delete Task {i}"):
                delete_task(i)
                st.experimental_rerun()

# --- Timetable (Editable) ---
elif menu == "Timetable":
    st.subheader("📅 Timetable")
    day = st.text_input("Day", key="tt_day")
    time = st.text_input("Time", key="tt_time")
    subject = st.text_input("Subject (Timetable)", key="tt_subject")
    notes = st.text_area("Notes", key="tt_notes")
    if st.button("Add Timetable"):
        add_timetable(day, time, subject, notes)
        st.success("Timetable added!")

    for i, t in enumerate(data["timetable"]):
        with st.expander(f"{t['Day']} {t['Time']} - {t['Subject']}"):
            new_day = st.text_input("Day", value=t["Day"], key=f"tt_d_{i}")
            new_time = st.text_input("Time", value=t["Time"], key=f"tt_t_{i}")
            new_subject = st.text_input("Subject", value=t["Subject"], key=f"tt_s_{i}")
            new_notes = st.text_area("Notes", value=t["Notes"], key=f"tt_n_{i}")
            if st.button(f"Update Timetable {i}"):
                update_timetable(i, new_day, new_time, new_subject, new_notes)
                st.success("Timetable updated!")
                st.experimental_rerun()
            if st.session_state.get("enable_delete") and st.button(f"Delete Timetable {i}"):
                delete_timetable(i)
                st.rerun()

# --- Sessions (Editable) ---
elif menu == "Sessions":
    st.subheader("💻 Sessions")
    name = st.text_input("Session Name", key="session_name")
    date = st.date_input("Session Date", key="session_date")
    notes = st.text_area("Notes", key="session_notes")
    if st.button("Add Session"):
        add_session(name, date, notes)
        st.success("Session added!")

    for i, s in enumerate(data["sessions"]):
        with st.expander(f"{s['Date']} - {s['Session Name']}"):
            new_name = st.text_input("Session Name", value=s["Session Name"], key=f"ses_n_{i}")
            new_date = st.date_input("Session Date", value=pd.to_datetime(s["Date"]), key=f"ses_d_{i}")
            new_notes = st.text_area("Notes", value=s["Notes"], key=f"ses_notes_{i}")
            if st.button(f"Update Session {i}"):
                update_session(i, new_name, new_date, new_notes)
                st.success("Session updated!")
                st.experimental_rerun()
            if st.session_state.get("enable_delete") and st.button(f"Delete Session {i}"):
                delete_session(i)
                st.rerun()

# --- Export ---
elif menu == "Export":
    st.subheader("📤 Export")
    if st.button("Export Tasks as PDF"):
        pdf = export_tasks_pdf()
        st.download_button("Download PDF", pdf, file_name="tasks.pdf")
    if st.button("Export Timetable as iCal"):
        ical = export_timetable_ical()
        st.download_button("Download iCal", ical, file_name="timetable.ics")

# --- Users & Chat ---
elif menu == "Users & Chat":
    st.subheader("👥 Users & Chat")
    st.write(f"Total Users: {len(data['users'])}")
    message = st.text_input("Message")
    if st.button("Send"):
        send_message(st.session_state["logged_in_user"],message)
        st.rerun()
    st.write("--- Chat Messages ---")
    for c in data["chat"][-50:]:
        st.write(f"{c['Time']} - **{c['User']}**: {c['Message']}")
