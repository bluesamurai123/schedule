import streamlit as st
import json
import os
import datetime

st.set_page_config(page_title="Easy Schedule", page_icon="📅")
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
st.header("🚨 Alerts / Today Overview")

today = datetime.date.today()
today_tasks = []
future_tasks = []

for person in data["people"]:
    for t in data["people"][person]:
        d = get_task_date(t)
        if not d:
            continue

        if d == today:
            today_tasks.append((person,t))
        elif d > today:
            future_tasks.append((d,person,t))

if today_tasks:
    summary={}
    for p,t in today_tasks:
        if p not in summary:
            summary[p]={"total":0,"done":0}
        summary[p]["total"]+=1
        if t["status"]=="Complete":
            summary[p]["done"]+=1

    for p in summary:
        st.write(f"📌 {p}: {summary[p]['done']}/{summary[p]['total']} done")
else:
    st.success("✅ No tasks for today!")

if future_tasks:
    st.write("📅 Upcoming Tasks:")
    future_tasks.sort(key=lambda x:x[0])
    for d,p,t in future_tasks[:5]:
        st.write(f"➡ {p} - {t['task']} ({d} {t.get('time','')})")

st.divider()

# ---------------- QUICK ADD ----------------
st.subheader("➕ Quick Add")

if "show_more" not in st.session_state:
    st.session_state.show_more = False

colA, colB = st.columns(2)

with colA:
    if st.button("➕ More Options"):
        st.session_state.show_more = True

with colB:
    if st.session_state.show_more and st.button("❌ Close"):
        st.session_state.show_more = False

person_q = st.selectbox("Person", list(data["people"].keys()) if data["people"] else [])
task_q = st.text_input("Task")

if st.session_state.show_more:

    date_q = st.date_input("Date")
    time_q = st.time_input("Time")
    cat_q = st.selectbox("Category",
    ["Sports","Instruments","School","Homework","Exercise","Work","Other"])

    apply_all = st.checkbox("Apply to ALL people")

    if st.button("Add Task Quick"):

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
st.header("🏆 Leaderboard")

lb=[]
for p in data["people"]:
    pts=sum(
        t.get("points",0)
        for t in data["people"][p]
        if t.get("status")=="Complete"
    )
    lb.append((p,pts))

lb.sort(key=lambda x:x[1],reverse=True)

for i,(p,pts) in enumerate(lb,1):
    st.write(f"{i}. {p} - {pts} pts")

st.divider()

# ---------------- POINTS DASHBOARD (NEW 🔥) ----------------
if "show_points" not in st.session_state:
    st.session_state.show_points = True

col1, col2 = st.columns([4,1])

with col1:
    st.header("⭐ Points Dashboard")

with col2:
    if st.button("🔼" if st.session_state.show_points else "🔽"):
        st.session_state.show_points = not st.session_state.show_points

if st.session_state.show_points:

    grand_total = 0

    for person in data["people"]:

        pts = sum(t.get("points", 0) for t in data["people"][person])
        level = pts // 50
        progress = pts % 50

        grand_total += pts

        st.subheader(f"👤 {person}")
        st.write(f"Total Points: {pts}")
        st.write(f"Level: {level}")
        st.progress(progress / 50)

    st.divider()
    st.subheader(f"🔥 All Users Total Points: {grand_total}")

st.divider()

# ---------------- REVIEW DASHBOARD ----------------
st.header("📊 Review Dashboard")

if "show_review" not in st.session_state:
    st.session_state.show_review = False

if st.button("Toggle Review Board"):
    st.session_state.show_review = not st.session_state.show_review

if st.session_state.show_review:

    total_points = 0

    for person in data["people"]:
        st.subheader(f"👤 {person}")

        person_points = 0

        for t in data["people"][person]:

            if t.get("status") == "Complete":

                pts = t.get("points", 0)
                person_points += pts
                total_points += pts

                st.write(f"📌 {t['task']} | ⭐ {pts} pts")

        st.write(f"🏆 {person} Total: {person_points}")

    st.write(f"🔥 All-Time Total Points: {total_points}")

st.divider()

# ---------------- ADD PERSON ----------------
new_p = st.text_input("Add Person")

if st.button("Add Person"):
    if new_p and new_p not in data["people"]:
        data["people"][new_p]=[]
        save_data(data)
        st.rerun()

# ---------------- MAIN ----------------
for person in list(data["people"].keys()):

    if f"show_{person}" not in st.session_state:
        st.session_state[f"show_{person}"] = True

    col1,col2,col3 = st.columns([3,1,1])

    with col1:
        st.header(f"👤 {person}")

    with col2:
        if st.button("^", key=f"toggle_{person}"):
            st.session_state[f"show_{person}"] = not st.session_state[f"show_{person}"]

    with col3:
        if st.button("🗑️", key=f"del_{person}"):
            st.session_state[f"confirm_{person}"]=True

    if st.session_state.get(f"confirm_{person}",False):
        st.warning(f"Delete {person}?")

        c1,c2 = st.columns(2)
        with c1:
            if st.button("YES", key=f"yes_{person}"):
                del data["people"][person]
                save_data(data)
                st.rerun()
        with c2:
            if st.button("NO", key=f"no_{person}"):
                st.session_state[f"confirm_{person}"]=False

    if not st.session_state[f"show_{person}"]:
        st.divider()
        continue

    tasks = data["people"][person]

    pts=sum(t.get("points",0) for t in tasks)
    level=pts//50
    prog=pts%50

    st.write(f"Points: {pts} | Level: {level}")
    st.progress(prog/50)

    st.subheader("➕ Add Task")

    prev_tasks = sorted(set([t["task"] for t in tasks])) if tasks else []
    prev_tasks.insert(0,"None")

    selected_task = st.selectbox("Previous Task", prev_tasks, key=f"prev_{person}")
    new_task = st.text_input("New Task", key=f"task_{person}")

    task_name = selected_task if selected_task != "None" else new_task

    date_n = st.date_input("Date", key=f"date_{person}")
    time_n = st.time_input("Time", key=f"time_{person}")

    cat_n = st.selectbox(
        "Category",
        ["Sports","Instruments","School","Homework","Exercise","Work","Other"],
        key=f"cat_{person}"
    )

    if st.button("Add Task", key=f"btn_{person}"):
        if task_name:
            data["people"][person].append({
                "task":task_name,
                "date":str(date_n),
                "time":str(time_n),
                "category":cat_n,
                "status":"Incomplete",
                "review":"Pending",
                "points":0
            })
            save_data(data)
            st.rerun()

    st.write("### Tasks")

    for i,t in enumerate(tasks):

        col1,col2,col3 = st.columns([3,2,1])

        d=get_task_date(t)

        with col1:
            dot=STATUS_COLORS[t["status"]]
            st.write(f"{dot} {t['task']} - {d} {t.get('time','')}")

        with col2:
            ns = st.selectbox("Status", STATUSES,
            index=STATUSES.index(t["status"]),
            key=f"s_{person}_{i}")

            if ns!=t["status"]:
                t["status"]=ns
                save_data(data)
                st.rerun()

        with col3:
            if st.button("❌", key=f"x_{person}_{i}"):
                data["people"][person].pop(i)
                save_data(data)
                st.rerun()

        if t["status"]=="Complete":

            g=st.selectbox("Grade",
            ["Pending","Full (10)","Half (5)","None (0)"],
            key=f"g_{person}_{i}")

            if g=="Full (10)":
                t["points"]=10
            elif g=="Half (5)":
                t["points"]=5
            elif g=="None (0)":
                t["points"]=0

            save_data(data)

    st.divider()