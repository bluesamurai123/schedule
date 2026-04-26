import streamlit as st
import json
import os
import datetime

st.set_page_config(page_title="Easy Schedule", page_icon="📅", layout="centered")

st.title("📅 Easy Schedule")

FILE_NAME = "tasks.json"

STATUSES = ["Incomplete","In Progress","Complete"]

STATUS_COLORS = {
    "Incomplete":"🔴",
    "In Progress":"🟡",
    "Complete":"🟢"
}

# ---------------- DATA ----------------
def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME,"r") as f:
            return json.load(f)
    return {"people":{}}

def save_data(data):
    with open(FILE_NAME,"w") as f:
        json.dump(data,f)

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ---------------- DATE ----------------
def get_task_date(t):
    if t.get("date"):
        try:
            return datetime.datetime.strptime(t["date"], "%Y-%m-%d").date()
        except:
            return None
    return None

# ---------------- ALERT ----------------
st.subheader("🚨 Today")

today = datetime.date.today()

for person in data["people"]:
    tasks = data["people"][person]
    today_list = [t for t in tasks if get_task_date(t)==today]

    if today_list:
        done = sum(1 for t in today_list if t["status"]=="Complete")
        st.write(f"👤 {person}: {done}/{len(today_list)} done")

st.divider()

# ---------------- QUICK ADD ----------------
st.subheader("➕ Quick Add")

person_q = st.selectbox("Person", list(data["people"].keys()) if data["people"] else [])
task_q = st.text_input("Task")

with st.expander("More Options"):
    date_q = st.date_input("Date")
    time_q = st.time_input("Time")
    cat_q = st.selectbox("Category",
        ["Sports","Instruments","School","Homework","Exercise","Work","Other"])
    apply_all = st.checkbox("Apply to ALL")

if st.button("Add Task"):
    if task_q:
        targets = list(data["people"].keys()) if apply_all else [person_q]

        for p in targets:
            data["people"][p].append({
                "task":task_q,
                "date":str(date_q),
                "time":str(time_q),
                "category":cat_q,
                "status":"Incomplete",
                "review":"Pending",
                "points":0
            })

        save_data(data)
        st.rerun()

st.divider()

# ---------------- LEADERBOARD ----------------
with st.expander("🏆 Leaderboard"):
    for p in data["people"]:
        pts = sum(t.get("points",0) for t in data["people"][p])
        st.write(f"{p}: {pts} pts")

# ---------------- POINTS ----------------
with st.expander("⭐ Points Dashboard"):
    total = 0
    for p in data["people"]:
        pts = sum(t.get("points",0) for t in data["people"][p])
        total += pts
        level = pts // 50
        st.write(f"{p} | {pts} pts | Level {level}")
    st.write(f"🔥 Total: {total}")

# ---------------- REVIEW ----------------
with st.expander("📊 Review Dashboard"):
    for p in data["people"]:
        st.write(f"👤 {p}")
        for t in data["people"][p]:
            if t["status"]=="Complete":
                st.write(f"- {t['task']} ⭐ {t.get('points',0)}")

st.divider()

# ---------------- ADD PERSON ----------------
st.subheader("Add Person")

new_p = st.text_input("Name")

if st.button("Add"):
    if new_p and new_p not in data["people"]:
        data["people"][new_p]=[]
        save_data(data)
        st.rerun()

st.divider()

# ---------------- MAIN ----------------
for person in data["people"]:

    with st.expander(f"👤 {person}"):

        tasks = data["people"][person]

        pts = sum(t.get("points",0) for t in tasks)
        level = pts // 50

        st.write(f"⭐ {pts} pts | Level {level}")

        # ADD TASK
        st.write("Add Task")

        prev = [t["task"] for t in tasks]
        prev = ["None"] + list(set(prev))

        sel = st.selectbox("Previous", prev, key=f"p_{person}")
        new = st.text_input("New", key=f"n_{person}")

        name = sel if sel!="None" else new

        date_n = st.date_input("Date", key=f"d_{person}")
        time_n = st.time_input("Time", key=f"t_{person}")

        if st.button("Add", key=f"a_{person}"):
            if name:
                tasks.append({
                    "task":name,
                    "date":str(date_n),
                    "time":str(time_n),
                    "status":"Incomplete",
                    "points":0
                })
                save_data(data)
                st.rerun()

        # TASK LIST
        for i,t in enumerate(tasks):

            st.write(f"{STATUS_COLORS[t['status']]} {t['task']}")

            new_s = st.selectbox("Status", STATUSES,
                index=STATUSES.index(t["status"]),
                key=f"s_{person}_{i}")

            if new_s != t["status"]:
                t["status"]=new_s
                save_data(data)
                st.rerun()

            if st.button("Delete", key=f"x_{person}_{i}"):
                tasks.pop(i)
                save_data(data)
                st.rerun()

            if t["status"]=="Complete":
                g = st.selectbox("Grade",
                    ["10","5","0"],
                    key=f"g_{person}_{i}")

                t["points"] = int(g)
                save_data(data)