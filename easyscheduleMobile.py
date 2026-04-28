import streamlit as st
import json, hashlib, calendar
from datetime import date, datetime
from supabase import create_client, Client

st.set_page_config(page_title="Easy Schedule", page_icon="📅", layout="centered")

# ─────────────────────────────────────────
# SUPABASE CONNECTION
# ─────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

sb = get_supabase()

# ─────────────────────────────────────────
# CATEGORY CONFIG
# ─────────────────────────────────────────
CATEGORIES = ["Sports","Instruments","School","Classes","Homework","Exercise","Work","Other"]
CAT_COLORS = {
    "Sports":      {"bg": "#1a1a1a", "text": "#fff"},
    "Other":       {"bg": "#f5f5f0", "text": "#333"},
    "School":      {"bg": "#f0c040", "text": "#333"},
    "Classes":     {"bg": "#e03030", "text": "#fff"},
    "Exercise":    {"bg": "#f07820", "text": "#fff"},
    "Instruments": {"bg": "#3080e0", "text": "#fff"},
    "Homework":    {"bg": "#40a840", "text": "#fff"},
    "Work":        {"bg": "#e060a0", "text": "#fff"},
}
STATUSES = ["Incomplete", "In Progress", "Complete"]
STATUS_ICONS = {"Incomplete": "🔴", "In Progress": "🟡", "Complete": "🟢"}
MEDALS = ["🥇", "🥈", "🥉"]

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    try:
        res = sb.table("users").select("username, password").execute()
        return {r["username"]: r["password"] for r in res.data}
    except:
        return {}

def save_user(username, hashed_pw):
    try:
        sb.table("users").upsert({"username": username, "password": hashed_pw}).execute()
    except Exception as e:
        st.error(f"Could not save user: {e}")

def load_data(user):
    try:
        res = sb.table("schedules").select("data").eq("username", user).execute()
        if res.data:
            d = res.data[0]["data"]
            if isinstance(d, str):
                d = json.loads(d)
            return d
    except:
        pass
    return {
        "people": {}, "task_history": [],
        "archived_points": {}, "all_time_points": {}, "last_reset": ""
    }

def save_data(user, d):
    try:
        sb.table("schedules").upsert({
            "username": user,
            "data": d
        }).execute()
    except Exception as e:
        st.error(f"Could not save: {e}")

def get_bg(cat):
    return CAT_COLORS.get(cat, {"bg": "#ccc", "text": "#333"})["bg"]

def get_fg(cat):
    return CAT_COLORS.get(cat, {"bg": "#ccc", "text": "#333"})["text"]

def cat_badge(cat):
    bg = get_bg(cat)
    fg = get_fg(cat)
    return (
        f"<span style='background:{bg};color:{fg};padding:3px 10px;"
        f"border-radius:20px;font-size:12px;font-weight:700;"
        f"border:1px solid rgba(0,0,0,0.1)'>{cat}</span>"
    )

def today_str():
    return str(date.today())

# ─────────────────────────────────────────
# SESSION INIT
# ─────────────────────────────────────────
for k, v in [
    ("user", None), ("data", None),
    ("cal_month", date.today().month),
    ("cal_year", date.today().year),
    ("selected_date", None),
    ("screen", "calendar"),
    ("expand", {})
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
.block-container {
    max-width: 480px !important;
    padding: 0 12px 100px !important;
    margin: 0 auto !important;
}
div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
div[data-testid="stHorizontalBlock"] { gap: 0.4rem !important; }

.scard {
    background: #fff;
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stitle {
    font-weight: 900;
    font-size: 20px;
    color: #1a1a2e;
    margin: 8px 0 10px;
}
.pname { font-weight: 800; font-size: 17px; color: #1a1a2e; }
.psub  { font-size: 12px; color: #888; margin-top: 2px; }

.lbrow {
    display: flex;
    align-items: flex-start;
    background: #fff;
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    gap: 10px;
}
.lbmedal { font-size: 26px; margin-top: 2px; }
.lbname  { font-weight: 800; font-size: 15px; color: #1a1a2e; }
.lbsub   { font-size: 12px; color: #888; margin-top: 2px; }

.pbar-wrap { height: 5px; background: #eee; border-radius: 10px; margin-top: 6px; overflow: hidden; }
.pbar-fill { height: 100%; background: #3080e0; border-radius: 10px; }

.sbox { background:#e8f8ed; color:#2a7a3a; border-radius:12px; padding:12px 16px; font-weight:600; font-size:14px; margin-bottom:8px; }
.wbox { background:#fff8e0; color:#7a5a00; border-radius:12px; padding:12px 16px; font-weight:600; font-size:14px; margin-bottom:8px; }
.legend { display:flex; flex-wrap:wrap; gap:5px; margin-top:4px; }

.topbar-title { font-weight:900; font-size:20px; color:#1a1a2e; }
.topbar-user  { font-size:13px; color:#555; }

div[data-testid="stButton"] > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Tiny calendar tap buttons */
[data-testid="stButton"] button[kind="secondary"] {
    padding: 0px 2px !important;
    min-height: 0px !important;
    height: 20px !important;
    font-size: 9px !important;
    line-height: 1 !important;
    border-radius: 4px !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────
if not st.session_state.user:
    st.markdown("<div style='text-align:center;font-size:52px;margin-top:40px'>📅</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;font-weight:900;font-size:28px;color:#1a1a2e'>Easy Schedule</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#aaa;font-size:14px;margin-bottom:20px'>Your daily task tracker</div>", unsafe_allow_html=True)

    users = load_users()
    mode = st.selectbox("", ["Login", "Sign Up"], label_visibility="collapsed")
    u = st.text_input("Username", placeholder="Username")
    p = st.text_input("Password", placeholder="Password", type="password")

    if mode == "Sign Up":
        if st.button("Create Account", use_container_width=True):
            if not u or not p:
                st.error("Fill both fields")
            elif u in users:
                st.error("Username taken")
            else:
                save_user(u, hash_pw(p))
                st.success("Account created! Log in.")

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
# MAIN APP SETUP
# ─────────────────────────────────────────
user = st.session_state.user
data = st.session_state.data

for k, v in [("task_history",[]),("archived_points",{}),("all_time_points",{}),("last_reset","")]:
    if k not in data:
        data[k] = v

def save():
    save_data(user, data)

today = date.today()
ts = today_str()

# Daily reset
if data["last_reset"] != ts:
    for p in data["people"]:
        for t in data["people"][p]:
            t["points"] = 0
    data["last_reset"] = ts
    save()

# Points helpers
def all_time_pts(p): return data.get("all_time_points", {}).get(p, 0)
def archived_pts(p): return data.get("archived_points", {}).get(p, 0)
def daily_pts(p):    return sum(t["points"] for t in data["people"].get(p, [])) + archived_pts(p)
def lvl(p):          return all_time_pts(p) // 50

def build_cal_tasks():
    m = {}
    for p in data["people"]:
        for t in data["people"][p]:
            d = t.get("date", "")
            if d:
                m.setdefault(d, []).append({"person": p, **t})
    return m

# ─────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────
col_title, col_user, col_logout = st.columns([4, 2, 1])
with col_title:
    st.markdown("<div class='topbar-title'>📅 EasySchedule</div>", unsafe_allow_html=True)
with col_user:
    st.markdown(f"<div style='padding-top:6px;font-size:13px;color:#555'>👤 {user}</div>", unsafe_allow_html=True)
with col_logout:
    if st.button("🚪", use_container_width=True):
        st.session_state.user = None
        st.session_state.data = None
        st.rerun()

# ─────────────────────────────────────────
# NAV TABS
# ─────────────────────────────────────────
TABS = [
    ("calendar",    "📅", "Calendar"),
    ("today",       "🚨", "Today"),
    ("leaderboard", "🏆", "Ranks"),
    ("people",      "👥", "People"),
    ("addtask",     "➕", "Add"),
]

screen = st.session_state.screen
nav_cols = st.columns(5)
for i, (key, icon, label) in enumerate(TABS):
    with nav_cols[i]:
        if st.button(f"{icon}\n{label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.screen = key
            st.rerun()

st.divider()

ct = build_cal_tasks()
people = list(data["people"].keys())

# ─────────────────────────────────────────
# 📅 CALENDAR
# ─────────────────────────────────────────
if screen == "calendar":

    yr  = st.session_state.cal_year
    mo  = st.session_state.cal_month
    sel = st.session_state.selected_date or ""

    # ── Month navigation ──
    n1, n2, n3 = st.columns([1, 4, 1])
    with n1:
        if st.button("◀", use_container_width=True, key="cal_prev"):
            if mo == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.session_state.selected_date = None
            st.rerun()
    with n2:
        mn = datetime(yr, mo, 1).strftime("%B %Y")
        st.markdown(
            f"<div style='text-align:center;font-weight:900;font-size:18px;color:#1a1a2e;padding:6px 0'>{mn}</div>",
            unsafe_allow_html=True
        )
    with n3:
        if st.button("▶", use_container_width=True, key="cal_next"):
            if mo == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.session_state.selected_date = None
            st.rerun()

    # ── Build calendar grid as pure HTML (display only, no clicks) ──
    days_in_month = calendar.monthrange(yr, mo)[1]
    first_weekday = calendar.monthrange(yr, mo)[0]

    cells_html = ""
    for _ in range(first_weekday):
        cells_html += "<div></div>"

    for day in range(1, days_in_month + 1):
        ds = f"{yr}-{mo:02d}-{day:02d}"
        is_today = ds == ts
        is_sel   = ds == sel
        day_tasks = ct.get(ds, [])
        cats = list(dict.fromkeys(t["category"] for t in day_tasks))

        dots = ""
        for c in cats[:3]:
            bg = get_bg(c)
            dots += f"<span style='display:inline-block;width:6px;height:6px;border-radius:50%;background:{bg};margin:0 1px'></span>"

        if is_today:
            num_style = "background:#3080e0;color:#fff;font-weight:800;"
        elif is_sel:
            num_style = "background:#e8f0ff;color:#3080e0;font-weight:800;outline:2px solid #3080e0;"
        else:
            num_style = "color:#1a1a2e;font-weight:600;"

        cells_html += (
            f"<div style='display:flex;flex-direction:column;align-items:center;padding:3px 1px'>"
            f"<div style='width:32px;height:32px;border-radius:50%;display:flex;align-items:center;"
            f"justify-content:center;font-size:14px;{num_style}'>{day}</div>"
            f"<div style='display:flex;justify-content:center;margin-top:2px;min-height:8px'>{dots}</div>"
            f"</div>"
        )

    header_cells = "".join(
        f"<div style='text-align:center;font-size:11px;font-weight:700;color:#aaa;padding:4px 0'>{d}</div>"
        for d in ["Mo","Tu","We","Th","Fr","Sa","Su"]
    )

    cal_html = (
        f"<div style='background:#fff;border-radius:16px;padding:8px 4px'>"
        f"<div style='display:grid;grid-template-columns:repeat(7,1fr);margin-bottom:4px'>{header_cells}</div>"
        f"<div style='display:grid;grid-template-columns:repeat(7,1fr);gap:1px'>{cells_html}</div>"
        f"</div>"
    )
    st.markdown(cal_html, unsafe_allow_html=True)

    # ── Day picker — native Streamlit, no logout bug ──
    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    pick_col, clear_col = st.columns([4, 1])
    with pick_col:
        picked = st.date_input(
            "Select a day",
            value=date.fromisoformat(sel) if sel else today,
            label_visibility="collapsed"
        )
        picked_str = str(picked)
        if picked_str != sel:
            st.session_state.selected_date = picked_str
            st.rerun()
    with clear_col:
        if st.button("✖", key="clear_sel"):
            st.session_state.selected_date = None
            st.rerun()

    # ── Selected day detail ──
    if sel:
        try:
            sel_disp = datetime.strptime(sel, "%Y-%m-%d").strftime("%A, %B %d")
        except:
            sel_disp = sel
        entries = sorted(ct.get(sel, []), key=lambda x: x.get("time", ""))

        st.markdown(
            f"<div style='background:#fff;border-radius:14px;padding:12px;"
            f"box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-top:6px'>"
            f"<div style='font-weight:800;font-size:15px;color:#1a1a2e;margin-bottom:8px'>📋 {sel_disp}</div>",
            unsafe_allow_html=True
        )
        if not entries:
            st.markdown(
                "<div style='color:#aaa;font-size:13px;text-align:center;padding:8px'>No tasks this day</div>",
                unsafe_allow_html=True
            )
        else:
            for e in entries:
                bg     = get_bg(e["category"])
                fg     = get_fg(e["category"])
                icon   = STATUS_ICONS.get(e["status"], "🔴")
                tstr   = f" ⏰ {e['time']}" if e.get("time") else ""
                cat    = e["category"]
                person = e["person"]
                task   = e["task"]
                st.markdown(
                    f"<div style='background:{bg};color:{fg};padding:8px 12px;"
                    f"border-radius:10px;margin:4px 0;font-size:14px'>"
                    f"<b>{icon} {person}</b> — {task}{tstr} "
                    f"<span style='font-size:11px;opacity:0.8'>[{cat}]</span></div>",
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Legend ──
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='background:#fff;border-radius:14px;padding:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06)'>"
        "<div style='font-weight:700;font-size:12px;color:#aaa;margin-bottom:6px;"
        "text-transform:uppercase;letter-spacing:0.5px'>Categories</div>"
        "<div style='display:flex;flex-wrap:wrap;gap:5px'>" + "".join(cat_badge(c) for c in CATEGORIES) + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────
# 🚨 TODAY
# ─────────────────────────────────────────
elif screen == "today":
    st.markdown("<div class='stitle'>🚨 Today's Tasks</div>", unsafe_allow_html=True)

    today_tasks = sorted(
        [(p, t) for p in data["people"] for t in data["people"][p] if t.get("date") == ts],
        key=lambda x: x[1].get("time", "")
    )

    if not today_tasks:
        st.markdown("<div class='sbox'>✅ Nothing due today!</div>", unsafe_allow_html=True)
    else:
        for p, t in today_tasks:
            bg       = get_bg(t.get("category", "Other"))
            fg       = get_fg(t.get("category", "Other"))
            icon     = STATUS_ICONS.get(t.get("status", "Incomplete"), "🔴")
            time_str = f" ⏰ {t['time']}" if t.get("time") else ""
            cat      = t.get("category", "Other")
            task     = t["task"]
            st.markdown(
                f"<div style='background:{bg};color:{fg};padding:10px 12px;"
                f"border-radius:10px;margin:4px 0'>"
                f"<div style='font-weight:700;font-size:14px'>{icon} {p} — {task}</div>"
                f"<div style='font-size:11px;opacity:0.85'>{time_str} [{cat}]</div>"
                f"</div>",
                unsafe_allow_html=True
            )

# ─────────────────────────────────────────
# 🏆 LEADERBOARD
# ─────────────────────────────────────────
elif screen == "leaderboard":
    st.markdown("<div class='stitle'>🏆 Leaderboard</div>", unsafe_allow_html=True)

    lb = sorted(
        [(p, all_time_pts(p), daily_pts(p)) for p in people],
        key=lambda x: x[1], reverse=True
    )

    if not lb:
        st.info("No people yet")
    else:
        for i, (p, atp, dp) in enumerate(lb):
            medal    = MEDALS[i] if i < 3 else f"{i+1}."
            lv       = lvl(p)
            prog_pct = (atp % 50) / 50 * 100
            st.markdown(
                f"<div class='lbrow'>"
                f"<div class='lbmedal'>{medal}</div>"
                f"<div style='flex:1'>"
                f"<div class='lbname'>{p}</div>"
                f"<div class='lbsub'>🏅 All Time: {atp} pts &nbsp;|&nbsp; ⭐ Today: {dp} pts</div>"
                f"<div class='pbar-wrap'><div class='pbar-fill' style='width:{prog_pct:.1f}%'></div></div>"
                f"<div style='font-size:10px;color:#aaa;margin-top:2px'>Level {lv} — {atp % 50}/50 to next</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )

# ─────────────────────────────────────────
# 👥 PEOPLE
# ─────────────────────────────────────────
elif screen == "people":
    st.markdown("<div class='stitle'>👥 People & Tasks</div>", unsafe_allow_html=True)

    col_i, col_b = st.columns([4, 1])
    with col_i:
        new_p = st.text_input("", placeholder="Add person...", label_visibility="collapsed", key="new_person_input")
    with col_b:
        if st.button("Add", use_container_width=True, key="add_person_btn"):
            if new_p and new_p not in data["people"]:
                data["people"][new_p] = []
                save()
                st.rerun()
            elif new_p in data["people"]:
                st.error("Already exists")

    if not people:
        st.markdown("<p style='color:#aaa;text-align:center;padding:12px'>No people added yet</p>", unsafe_allow_html=True)

    for p in list(data["people"].keys()):
        tasks    = data["people"][p]
        done     = sum(1 for t in tasks if t["status"] == "Complete")
        total    = len(tasks)
        prog     = (done / total * 100) if total else 0
        atp      = all_time_pts(p)
        dp       = daily_pts(p)
        lv       = lvl(p)
        expanded = st.session_state.expand.get(p, False)

        c1, c2, c3 = st.columns([5, 1, 1])
        with c1:
            st.markdown(
                f"<div class='pname'>👤 {p}</div>"
                f"<div class='psub'>⭐ Today: {dp} | 🎖️ Lv.{lv} | ✅ {done}/{total}</div>"
                f"<div class='pbar-wrap'><div class='pbar-fill' style='width:{prog:.0f}%'></div></div>",
                unsafe_allow_html=True
            )
        with c2:
            if st.button("▲" if expanded else "▼", key=f"tog_{p}", use_container_width=True):
                st.session_state.expand[p] = not expanded
                st.rerun()
        with c3:
            del_key = f"del_confirm_{p}"
            if del_key not in st.session_state:
                st.session_state[del_key] = False
            if not st.session_state[del_key]:
                if st.button("🗑️", key=f"delbtn_{p}", use_container_width=True):
                    st.session_state[del_key] = True
                    st.rerun()
            else:
                st.warning("Sure?")
                if st.button("✅ YES", key=f"yes_{p}"):
                    del data["people"][p]
                    save()
                    st.rerun()
                if st.button("❌ NO", key=f"no_{p}"):
                    st.session_state[del_key] = False
                    st.rerun()

        if expanded:
            if not tasks:
                st.markdown("<p style='color:#aaa;font-size:13px;text-align:center'>No tasks yet</p>", unsafe_allow_html=True)

            for i, t in enumerate(tasks):
                bg       = get_bg(t.get("category", "Other"))
                fg       = get_fg(t.get("category", "Other"))
                icon     = STATUS_ICONS.get(t.get("status", "Incomplete"), "🔴")
                time_str = f" ⏰ {t['time']}" if t.get("time") else ""
                cat      = t.get("category", "Other")
                task     = t["task"]

                st.markdown(
                    f"<div style='background:{bg};color:{fg};padding:8px 12px;"
                    f"border-radius:10px 10px 0 0;font-weight:700;font-size:14px;margin-top:8px'>"
                    f"{icon} {task}{time_str} "
                    f"<span style='font-size:11px;opacity:0.8'>[{cat}]</span></div>",
                    unsafe_allow_html=True
                )

                if t.get("on_calendar") and t.get("date"):
                    try:
                        d_disp = datetime.strptime(t["date"], "%Y-%m-%d").strftime("%a, %b %d")
                        st.markdown(
                            f"<div style='background:#f5f5f5;padding:4px 12px;"
                            f"font-size:12px;color:#555'>📅 {d_disp}</div>",
                            unsafe_allow_html=True
                        )
                    except:
                        pass

                tc1, tc2 = st.columns([3, 2])
                with tc1:
                    ns = st.selectbox(
                        "Status", STATUSES,
                        index=STATUSES.index(t.get("status", "Incomplete")),
                        key=f"st_{p}_{i}",
                        label_visibility="collapsed"
                    )
                    if ns != t["status"]:
                        t["status"] = ns
                        save()
                        st.rerun()

                with tc2:
                    if ns == "Complete":
                        g = st.selectbox(
                            "Points", [10, 5, 0],
                            key=f"pts_{p}_{i}",
                            label_visibility="collapsed"
                        )
                        old = t["points"]
                        if int(g) != old:
                            diff = max(0, int(g) - old)
                            t["points"] = int(g)
                            if p not in data["all_time_points"]:
                                data["all_time_points"][p] = 0
                            data["all_time_points"][p] += diff
                            save()

                confirm_key = f"conf_task_{p}_{i}"
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False

                if not st.session_state[confirm_key]:
                    if st.button("❌ Delete Task", key=f"deltask_{p}_{i}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("Delete this task?")
                    cy, cn = st.columns(2)
                    with cy:
                        if st.button("✅ YES", key=f"yes_t_{p}_{i}"):
                            removed = tasks[i]
                            if p not in data["archived_points"]:
                                data["archived_points"][p] = 0
                            data["archived_points"][p] += removed.get("points", 0)
                            tasks.pop(i)
                            save()
                            st.rerun()
                    with cn:
                        if st.button("❌ NO", key=f"no_t_{p}_{i}"):
                            st.session_state[confirm_key] = False
                            st.rerun()

        st.divider()

# ─────────────────────────────────────────
# ➕ ADD TASK
# ─────────────────────────────────────────
elif screen == "addtask":
    st.markdown("<div class='stitle'>➕ Add Task</div>", unsafe_allow_html=True)

    if not people:
        st.markdown("<div class='wbox'>➡️ Go to People tab and add someone first!</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin-bottom:4px'>Person</div>", unsafe_allow_html=True)
        task_person = st.selectbox("Person", people, label_visibility="collapsed")

        history = data.get("task_history", [])
        prefill = ""
        if history:
            st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin:10px 0 4px'>Quick Add (Previous Tasks)</div>", unsafe_allow_html=True)
            prev = st.selectbox("Previous", ["-- New task --"] + history, label_visibility="collapsed")
            prefill = "" if prev == "-- New task --" else prev

        st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin:10px 0 4px'>Task Name</div>", unsafe_allow_html=True)
        task_name = st.text_input("Task", value=prefill, placeholder="Enter task...", label_visibility="collapsed")

        st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin:10px 0 4px'>Category</div>", unsafe_allow_html=True)
        task_cat = st.selectbox("Category", CATEGORIES, label_visibility="collapsed")

        st.markdown(cat_badge(task_cat), unsafe_allow_html=True)

        st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin:10px 0 4px'>Add to Calendar?</div>", unsafe_allow_html=True)
        add_to_cal = st.radio("Calendar", ["Yes", "No"], horizontal=True, label_visibility="collapsed")

        task_date = ts
        task_time = ""

        if add_to_cal == "Yes":
            st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin:10px 0 4px'>Date</div>", unsafe_allow_html=True)
            task_date = str(st.date_input("Date", value=today, label_visibility="collapsed"))
            st.markdown("<div style='font-weight:600;font-size:13px;color:#555;margin:10px 0 4px'>Time</div>", unsafe_allow_html=True)
            task_time = str(st.time_input("Time", label_visibility="collapsed"))

        apply_all = st.checkbox("Apply to ALL people")

        if st.button("➕ Add Task", use_container_width=True):
            if not task_name.strip():
                st.error("Enter a task name!")
            else:
                targets = people if apply_all else [task_person]
                for p in targets:
                    data["people"][p].append({
                        "task":        task_name,
                        "date":        task_date if add_to_cal == "Yes" else "",
                        "time":        task_time if add_to_cal == "Yes" else "",
                        "category":    task_cat,
                        "status":      "Incomplete",
                        "points":      0,
                        "on_calendar": add_to_cal == "Yes"
                    })
                if task_name not in data["task_history"]:
                    data["task_history"].append(task_name)
                save()

                if add_to_cal == "Yes":
                    try:
                        d_disp    = datetime.strptime(task_date, "%Y-%m-%d").strftime("%A, %B %d")
                        time_disp = f" at {task_time}" if task_time else ""
                        for p in targets:
                            st.success(f"📅 {p} has {task_name} on {d_disp}{time_disp}")
                    except:
                        st.success("Task added!")
                else:
                    st.success(f"Task added to {', '.join(targets)}!")
                st.rerun()
