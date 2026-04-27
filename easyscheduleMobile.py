import streamlit as st
import json, os, hashlib, calendar
from datetime import date, datetime

st.set_page_config(page_title="Easy Schedule", page_icon="📅", layout="centered")

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

USERS_FILE = "users.json"

def load_users():
    return json.load(open(USERS_FILE)) if os.path.exists(USERS_FILE) else {}

def save_users(u):
    json.dump(u, open(USERS_FILE, "w"), indent=2)

def load_data(user):
    f = f"tasks_{user}.json"
    return json.load(open(f)) if os.path.exists(f) else {
        "people": {},
        "task_history": [],
        "archived_points": {},
        "all_time_points": {},
        "last_reset": ""
    }

def save_data(user, d):
    json.dump(d, open(f"tasks_{user}.json", "w"), indent=2)

STATUSES = ["Incomplete", "In Progress", "Complete"]
CATEGORIES = ["Sports", "Instruments", "School", "Classes", "Homework", "Exercise", "Work", "Other"]

CATEGORY_COLORS = {
    "Sports":      "#222222",
    "Other":       "#ffffff",
    "School":      "#f0c040",
    "Classes":     "#e03030",
    "Exercise":    "#f07820",
    "Instruments": "#3080e0",
    "Homework":    "#40a840",
    "Work":        "#e060a0",
}

CATEGORY_TEXT = {
    "Sports":      "white",
    "Other":       "#333333",
    "School":      "#333333",
    "Classes":     "white",
    "Exercise":    "white",
    "Instruments": "white",
    "Homework":    "white",
    "Work":        "white",
}

STATUS_ICON = {"Incomplete": "🔴", "In Progress": "🟡", "Complete": "🟢"}

def cat_badge(cat):
    bg = CATEGORY_COLORS.get(cat, "#cccccc")
    fg = CATEGORY_TEXT.get(cat, "white")
    return f"<span style='background:{bg};color:{fg};padding:2px 8px;border-radius:10px;font-size:12px;font-weight:bold'>{cat}</span>"

# ─────────────────────────────────────────
# SESSION INIT
# ─────────────────────────────────────────
for key, val in [
    ("user", None),
    ("data", None),
    ("cal_month", date.today().month),
    ("cal_year", date.today().year),
    ("selected_date", None)
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────
if not st.session_state.user:
    st.title("📅 Easy Schedule")
    st.markdown("### Welcome! Please log in or sign up.")

    users = load_users()
    mode = st.selectbox("", ["Login", "Sign Up"], label_visibility="collapsed")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if mode == "Sign Up":
        if st.button("Create Account", use_container_width=True):
            if not u or not p:
                st.error("Fill in both fields")
            elif u in users:
                st.error("Username already exists")
            else:
                users[u] = hash_pw(p)
                save_users(users)
                st.success("Account created! Please log in.")

    if mode == "Login":
        if st.button("Login", use_container_width=True):
            if u in users and users[u] == hash_pw(p):
                st.session_state.user = u
                st.session_state.data = load_data(u)
                st.rerun()
            else:
                st.error("Wrong username or password")

    st.stop()

# ─────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────
user = st.session_state.user
data = st.session_state.data

for key, default in [
    ("task_history", []),
    ("archived_points", {}),
    ("all_time_points", {}),
    ("last_reset", "")
]:
    if key not in data:
        data[key] = default

def save():
    save_data(user, data)

today = date.today()
today_str = str(today)

# ── DAILY RESET ──
if data["last_reset"] != today_str:
    for p in data["people"]:
        for t in data["people"][p]:
            t["points"] = 0
    data["last_reset"] = today_str
    save()

# ── TOP BAR ──
col_title, col_user, col_logout = st.columns([4, 2, 1])
with col_title:
    st.title("📅 Easy Schedule")
with col_user:
    st.markdown(f"<br>👤 **{user}**", unsafe_allow_html=True)
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user = None
        st.session_state.data = None
        st.rerun()

st.divider()

# ─────────────────────────────────────────
# 📅 INTERACTIVE CALENDAR
# ─────────────────────────────────────────
st.markdown("## 📅 Calendar")

nav1, nav2, nav3 = st.columns([1, 3, 1])
with nav1:
    if st.button("◀", use_container_width=True):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()

with nav2:
    month_name = datetime(st.session_state.cal_year, st.session_state.cal_month, 1).strftime("%B %Y")
    st.markdown(f"<h3 style='text-align:center'>{month_name}</h3>", unsafe_allow_html=True)

with nav3:
    if st.button("▶", use_container_width=True):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()

# Category color legend
st.markdown("**Category Colors:**")
legend_html = " &nbsp; ".join(
    f"<span style='background:{CATEGORY_COLORS[c]};color:{CATEGORY_TEXT[c]};padding:2px 8px;border-radius:10px;font-size:11px;font-weight:bold;border:1px solid #ccc'>{c}</span>"
    for c in CATEGORIES
)
st.markdown(legend_html, unsafe_allow_html=True)
st.markdown("")

# Build calendar task lookup
cal_tasks = {}
for p in data["people"]:
    for t in data["people"][p]:
        d = t.get("date", "")
        if d:
            cal_tasks.setdefault(d, []).append({
                "person": p,
                "task": t["task"],
                "status": t.get("status", "Incomplete"),
                "category": t.get("category", "Other"),
                "time": t.get("time", "")
            })

# Day headers
day_cols = st.columns(7)
for i, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    day_cols[i].markdown(f"<center><b>{day_name}</b></center>", unsafe_allow_html=True)

# Calendar grid
cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.markdown(" ")
            else:
                day_date = date(st.session_state.cal_year, st.session_state.cal_month, day)
                day_str = str(day_date)
                is_today = day_date == today
                tasks_on_day = cal_tasks.get(day_str, [])

                if is_today:
                    st.markdown(
                        f"<div style='background:#1f77b4;color:white;border-radius:6px;"
                        f"padding:2px 6px;text-align:center'><b>{day}</b></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div style='text-align:center'>{day}</div>", unsafe_allow_html=True)

                # Show category color dots
                if tasks_on_day:
                    dots = ""
                    for entry in tasks_on_day:
                        bg = CATEGORY_COLORS.get(entry["category"], "#cccccc")
                        dots += f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{bg};margin:1px;border:1px solid #aaa'></span>"
                    st.markdown(f"<center>{dots}</center>", unsafe_allow_html=True)

                if st.button("👁", key=f"cal_{day_str}", use_container_width=True):
                    st.session_state["selected_date"] = day_str
                    st.rerun()

# Selected day detail
if st.session_state.get("selected_date"):
    sel = st.session_state["selected_date"]
    sel_display = datetime.strptime(sel, "%Y-%m-%d").strftime("%A, %B %d %Y")
    st.markdown(f"### 📋 {sel_display}")

    day_entries = cal_tasks.get(sel, [])
    if day_entries:
        # Sort by time
        day_entries_sorted = sorted(day_entries, key=lambda x: x["time"] or "00:00:00")
        for entry in day_entries_sorted:
            bg  = CATEGORY_COLORS.get(entry["category"], "#ccc")
            fg  = CATEGORY_TEXT.get(entry["category"], "white")
            icon = STATUS_ICON.get(entry["status"], "🔴")
            time_str = f" ⏰ {entry['time']}" if entry["time"] else ""
            st.markdown(
                f"<div style='background:{bg};color:{fg};padding:8px 12px;border-radius:8px;margin:4px 0'>"
                f"{icon} <b>{entry['person']}</b> has <b>{entry['task']}</b>{time_str} "
                f"<span style='font-size:11px;opacity:0.85'>[{entry['category']}]</span>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No tasks on this day")

    if st.button("✖ Close", use_container_width=True):
        st.session_state["selected_date"] = None
        st.rerun()

st.divider()

# ─────────────────────────────────────────
# 🚨 TODAY'S ALERTS
# ─────────────────────────────────────────
st.markdown("## 🚨 Today's Tasks")

today_tasks = []
for p in data["people"]:
    for t in data["people"][p]:
        if t.get("date") == today_str:
            today_tasks.append((p, t))

if today_tasks:
    today_tasks_sorted = sorted(today_tasks, key=lambda x: x[1].get("time") or "00:00:00")
    for p, t in today_tasks_sorted:
        icon = STATUS_ICON.get(t.get("status", "Incomplete"), "🔴")
        bg   = CATEGORY_COLORS.get(t.get("category", "Other"), "#ccc")
        fg   = CATEGORY_TEXT.get(t.get("category", "Other"), "white")
        time_str = f" ⏰ {t['time']}" if t.get("time") else ""
        st.markdown(
            f"<div style='background:{bg};color:{fg};padding:8px 12px;border-radius:8px;margin:4px 0'>"
            f"{icon} <b>{p}</b> — {t['task']}{time_str} "
            f"<span style='font-size:11px;opacity:0.85'>[{t.get('category','Other')}]</span>"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.success("✅ Nothing due today!")

st.divider()

# ─────────────────────────────────────────
# 🏆 LEADERBOARD
# ─────────────────────────────────────────
st.markdown("## 🏆 Leaderboard")

all_time = data.get("all_time_points", {})
archived = data.get("archived_points", {})

lb = sorted(
    [
        (
            p,
            all_time.get(p, 0),
            sum(t["points"] for t in data["people"][p]) + archived.get(p, 0)
        )
        for p in data["people"]
    ],
    key=lambda x: x[1],
    reverse=True
)

if lb:
    medals = ["🥇", "🥈", "🥉"]
    for i, (p, all_pts, cur_pts) in enumerate(lb):
        medal = medals[i] if i < 3 else f"{i+1}."
        st.write(f"{medal} **{p}**")
        st.caption(f"🏅 All Time: {all_pts} pts | ⭐ Today: {cur_pts} pts")
else:
    st.info("No people added yet")

st.divider()

# ─────────────────────────────────────────
# 👤 ADD PERSON
# ─────────────────────────────────────────
st.markdown("## 👤 Add Person")

col_input, col_btn = st.columns([4, 1])
with col_input:
    new_p = st.text_input("Name", label_visibility="collapsed", placeholder="Enter name...")
with col_btn:
    if st.button("Add", use_container_width=True):
        if new_p and new_p not in data["people"]:
            data["people"][new_p] = []
            save()
            st.rerun()
        elif new_p in data["people"]:
            st.error("Already exists")

st.divider()

# ─────────────────────────────────────────
# ➕ ADD TASK
# ─────────────────────────────────────────
st.markdown("## ➕ Add Task")

if not data["people"]:
    st.warning("Add a person first!")
else:
    person = st.selectbox("Person", list(data["people"].keys()))

    history = data.get("task_history", [])
    if history:
        prev = st.selectbox("Quick add from previous tasks", ["-- Type a new task --"] + history)
        prefill = "" if prev == "-- Type a new task --" else prev
    else:
        prefill = ""

    task = st.text_input("Task", value=prefill, placeholder="Enter task...")
    add_to_cal = st.radio("Add to Calendar?", ["Yes", "No"], horizontal=True)

    show_more = st.toggle("More Options")

    task_date = today_str
    task_time = ""
    cat = "Other"
    apply_all = False

    if show_more or add_to_cal == "Yes":
        task_date = str(st.date_input("Date", value=today))
        task_time = str(st.time_input("Time"))
        cat = st.selectbox("Category", CATEGORIES)
        if show_more:
            apply_all = st.checkbox("Apply to ALL people")

    # Live category badge preview
    if cat:
        st.markdown(f"Category: {cat_badge(cat)}", unsafe_allow_html=True)

    if st.button("➕ Add Task", use_container_width=True):
        if not task:
            st.error("Enter a task name!")
        else:
            targets = list(data["people"].keys()) if apply_all else [person]
            for p in targets:
                data["people"][p].append({
                    "task": task,
                    "date": task_date if add_to_cal == "Yes" else "",
                    "time": task_time if add_to_cal == "Yes" else "",
                    "category": cat,
                    "status": "Incomplete",
                    "points": 0,
                    "on_calendar": add_to_cal == "Yes"
                })
            if task not in data["task_history"]:
                data["task_history"].append(task)
            save()

            if add_to_cal == "Yes":
                day_display = datetime.strptime(task_date, "%Y-%m-%d").strftime("%A, %B %d")
                time_display = f" at {task_time}" if task_time else ""
                for p in targets:
                    st.success(f"📅 {p} has **{task}** on {day_display}{time_display}")
            else:
                st.success(f"Task added to {', '.join(targets)}!")
            st.rerun()

st.divider()

# ─────────────────────────────────────────
# 👥 PEOPLE LIST
# ─────────────────────────────────────────
st.markdown("## 👥 People & Tasks")

if not data["people"]:
    st.info("No people added yet")

for p, tasks in data["people"].items():

    toggle_key = f"toggle_{p}"
    del_key    = f"del_confirm_{p}"

    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = False
    if del_key not in st.session_state:
        st.session_state[del_key] = False

    archived_pts  = data.get("archived_points", {}).get(p, 0)
    daily_pts     = sum(t["points"] for t in tasks) + archived_pts
    all_time_pts  = data.get("all_time_points", {}).get(p, 0)
    lvl           = all_time_pts // 50
    total         = len(tasks)
    done          = sum(1 for t in tasks if t["status"] == "Complete")
    progress      = done / total if total else 0

    col1, col2, col3 = st.columns([5, 1, 1])

    with col1:
        st.markdown(f"### 👤 {p}")
        st.caption(f"⭐ Today: {daily_pts} pts | 🎖️ Level {lvl} | ✅ {done}/{total} tasks done")
        st.progress(progress)

    with col2:
        arrow = "▲" if st.session_state[toggle_key] else "▼"
        if st.button(arrow, key=f"toggle_btn_{p}", use_container_width=True):
            st.session_state[toggle_key] = not st.session_state[toggle_key]

    with col3:
        if not st.session_state[del_key]:
            if st.button("🗑️", key=f"delbtn_{p}", use_container_width=True):
                st.session_state[del_key] = True
        else:
            st.warning("Sure?")
            if st.button("✅ YES", key=f"yes_{p}"):
                del data["people"][p]
                save()
                st.rerun()
            if st.button("❌ NO", key=f"no_{p}"):
                st.session_state[del_key] = False

    if st.session_state[toggle_key]:
        if not tasks:
            st.info("No tasks yet")
        else:
            for i, t in enumerate(tasks):
                cat       = t.get("category", "Other")
                bg        = CATEGORY_COLORS.get(cat, "#cccccc")
                fg        = CATEGORY_TEXT.get(cat, "white")
                icon      = STATUS_ICON.get(t.get("status", "Incomplete"), "🔴")
                time_str  = f" ⏰ {t['time']}" if t.get("time") else ""

                st.markdown(
                    f"<div style='background:{bg};color:{fg};padding:6px 10px;"
                    f"border-radius:8px;margin:4px 0;font-weight:bold'>"
                    f"{icon} {t['task']}{time_str} "
                    f"<span style='font-size:11px;font-weight:normal;opacity:0.85'>[{cat}]</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                with st.container(border=True):
                    c1, c2 = st.columns([3, 2])

                    with c1:
                        if t.get("on_calendar") and t.get("date"):
                            day_display = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%A, %B %d")
                            st.caption(f"📅 {day_display}{time_str}")
                        else:
                            st.caption(f"{time_str} 🏷️ {cat}" if time_str else f"🏷️ {cat}")

                    with c2:
                        ns = st.selectbox(
                            "Status",
                            STATUSES,
                            index=STATUSES.index(t.get("status", "Incomplete")),
                            key=f"status_{p}_{i}"
                        )
                        if ns != t["status"]:
                            t["status"] = ns
                            save()
                            st.rerun()

                        if ns == "Complete":
                            g = st.selectbox("Points", ["10", "5", "0"], key=f"pts_{p}_{i}")
                            new_pts = int(g)
                            old_pts = t["points"]
                            if new_pts != old_pts:
                                diff = max(0, new_pts - old_pts)
                                t["points"] = new_pts
                                if p not in data["all_time_points"]:
                                    data["all_time_points"][p] = 0
                                data["all_time_points"][p] += diff
                                save()

                    # Delete task — preserve points
                    confirm_key = f"confirm_task_{p}_{i}"
                    if confirm_key not in st.session_state:
                        st.session_state[confirm_key] = False

                    if not st.session_state[confirm_key]:
                        if st.button("❌ Delete Task", key=f"deltask_{p}_{i}"):
                            st.session_state[confirm_key] = True
                    else:
                        st.warning("Delete this task?")
                        col_y, col_n = st.columns(2)
                        with col_y:
                            if st.button("✅ YES", key=f"yes_task_{p}_{i}"):
                                removed = tasks[i]
                                if p not in data["archived_points"]:
                                    data["archived_points"][p] = 0
                                data["archived_points"][p] += removed.get("points", 0)
                                tasks.pop(i)
                                save()
                                st.rerun()
                        with col_n:
                            if st.button("❌ NO", key=f"no_task_{p}_{i}"):
                                st.session_state[confirm_key] = False

    st.divider()

# ─────────────────────────────────────────
# 📊 REVIEW DASHBOARD
# ─────────────────────────────────────────
st.markdown("## 📊 Review Dashboard")

if st.toggle("Show Completed Tasks"):
    any_done = False
    for p in data["people"]:
        done_tasks = [t for t in data["people"][p] if t["status"] == "Complete"]
        if done_tasks:
            any_done = True
            st.subheader(f"👤 {p}")
            for t in done_tasks:
                cat = t.get("category", "Other")
                bg  = CATEGORY_COLORS.get(cat, "#ccc")
                fg  = CATEGORY_TEXT.get(cat, "white")
                st.markdown(
                    f"<div style='background:{bg};color:{fg};padding:6px 12px;"
                    f"border-radius:8px;margin:3px 0'>"
                    f"🟢 {t['task']} — ⭐ {t['points']} pts [{cat}]"
                    f"</div>",
                    unsafe_allow_html=True
                )
    if not any_done:
        st.info("No completed tasks yet")
