
import json
import os
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st
from streamlit_autorefresh import st_autorefresh

try:
    from supabase import create_client
    SUPABASE_OK = True
except Exception:
    create_client = None
    SUPABASE_OK = False

ROOT_ADMIN_USER = "Ballbadminton"
ROOT_ADMIN_PASS = "partha@2025"

SET_POINTS = 35
PLAYERS = 5
ALL_PLAYERS = 10
COURT_CHG = [9, 18, 27]
MAX_SCORE_CAP = 39
DATA_FILE = "bb_state.json"
USERS_FILE = "bb_users.json"

st.set_page_config(page_title="Ball Badminton Live", page_icon="🏸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
section[data-testid="stSidebar"], [data-testid="stSidebarNav"] {display:none !important;}
html, body, .stApp {background:#07101f !important; color:#f3f4f6 !important;}
.block-container {padding:0.5rem 0.6rem 4.8rem !important; max-width:100% !important;}
.stButton>button {width:100% !important; border:none !important; border-radius:12px !important; font-weight:700 !important;
background:linear-gradient(135deg,#f97316,#c2410c) !important; color:#fff !important;}
.stTextInput input,.stSelectbox>div>div,.stMultiSelect>div>div,.stNumberInput input{
background:#112038 !important; color:#f3f4f6 !important; border:1px solid rgba(255,255,255,.08) !important; border-radius:10px !important;}
[data-testid="stContainer"]{background:#112038 !important; border:1px solid rgba(255,255,255,.08) !important; border-radius:14px !important; padding:12px !important;}
.scoreboard{background:linear-gradient(135deg,#0d1a2e,#112038); border-radius:18px; padding:16px 14px; border:1px solid rgba(249,115,22,.15);}
.score-num{font-size:80px; font-weight:900; line-height:1;}
.smallnav .stButton>button{padding:.4rem .5rem !important; font-size:12px !important; border-radius:10px !important;}
.bigpoint .stButton>button{padding:1rem .6rem !important; font-size:20px !important;}
.bigpointblue .stButton>button{background:linear-gradient(135deg,#3b82f6,#1d4ed8) !important;}
.alert{background:rgba(249,115,22,.1); border:1px solid rgba(249,115,22,.3); color:#fdba74; border-radius:12px; padding:10px; font-weight:800; margin-bottom:8px;}
.win{background:linear-gradient(135deg,#f59e0b,#d97706); border-radius:14px; padding:12px; font-weight:900; text-align:center; margin-bottom:8px;}
.ev{font-size:12px; padding:5px 4px; border-bottom:1px solid rgba(255,255,255,.06); color:#9ca3af;}
@media(max-width:768px){ .score-num{font-size:62px;} .smallnav .stButton>button{font-size:11px !important;} .bigpoint .stButton>button{font-size:17px !important;}}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase():
    if not SUPABASE_OK:
        return None
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None

def now_str():
    return datetime.now().strftime("%d %b %Y %H:%M:%S")

def hash_pw(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()

def safe(v: str, fb: str) -> str:
    v = (v or "").strip()
    return v if v else fb

def build_order(players5: List[str], idxs: List[int]) -> List[str]:
    out = []
    for idx in idxs:
        if not (1 <= idx <= len(players5)):
            return []
        out.append(players5[idx-1])
    return out

def next_idx(i: int, n: int) -> int:
    return (i + 1) % n

def default_data():
    return {"matches": {}, "history": [], "updated_at": ""}

def load_data():
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("matches").select("*").eq("id", "app_state").execute()
            if res.data:
                payload = res.data[0].get("data") or {}
                out = default_data()
                out.update(payload)
                return out
        except Exception:
            pass
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            out = default_data()
            out.update(payload)
            return out
        except Exception:
            pass
    return default_data()

def save_data(data):
    data["updated_at"] = now_str()
    sb = get_supabase()
    if sb:
        try:
            sb.table("matches").upsert({"id":"app_state","data":data,"updated_at":datetime.now().isoformat()}).execute()
            return
        except Exception:
            pass
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_users():
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("viewers").select("*").execute()
            out = {}
            for row in (res.data or []):
                out[row["username"]] = {
                    "name": row.get("name",""),
                    "contact": row.get("contact",""),
                    "pw_hash": row.get("pw_hash",""),
                    "created": row.get("created_at",""),
                    "is_admin": row.get("is_admin", False),
                    "created_by_admin": row.get("created_by_admin", False)
                }
            return out
        except Exception:
            pass
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_users(users):
    sb = get_supabase()
    if sb:
        try:
            rows = []
            for uname, u in users.items():
                rows.append({
                    "username": uname,
                    "name": u.get("name",""),
                    "contact": u.get("contact",""),
                    "pw_hash": u.get("pw_hash",""),
                    "created_at": u.get("created",""),
                    "is_admin": u.get("is_admin", False),
                    "created_by_admin": u.get("created_by_admin", False),
                })
            if rows:
                sb.table("viewers").upsert(rows).execute()
            return
        except Exception:
            pass
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def register_user(name, contact, username, password, is_admin=False, created_by_admin=False):
    users = load_users()
    uname = (username or "").strip().lower()
    if not name or not contact or not uname or not password:
        return False, "All fields are required"
    if len(password) < 6:
        return False, "Password min 6 chars"
    if uname == ROOT_ADMIN_USER.lower() or uname in users:
        return False, "Username already exists"
    users[uname] = {
        "name": name.strip(),
        "contact": contact.strip(),
        "pw_hash": hash_pw(password),
        "created": now_str(),
        "is_admin": bool(is_admin),
        "created_by_admin": bool(created_by_admin),
    }
    save_users(users)
    return True, f"Created {uname}"

def login_user(username, password):
    uname = (username or "").strip().lower()
    if uname == ROOT_ADMIN_USER.lower() and password == ROOT_ADMIN_PASS:
        return True, {"name":"Root Admin", "is_admin":True, "root":True}
    users = load_users()
    u = users.get(uname)
    if not u:
        return False, {}
    if u["pw_hash"] != hash_pw(password):
        return False, {}
    return True, u

@dataclass
class Match:
    id: str
    created_by: str
    tA: str
    tB: str
    allA: List[str]
    allB: List[str]
    onA: List[str]
    onB: List[str]
    ordA: List[str]
    ordB: List[str]
    setno: int
    sA: int
    sB: int
    scA: int
    scB: int
    srv: str
    swapped: bool
    curA: Optional[str]
    curB: Optional[str]
    nxtA: int
    nxtB: int
    subA: int
    subB: int
    toA: int
    toB: int
    ms: Dict[int, bool]
    first_court_popup_point: Optional[int]
    first_court_popup_team: Optional[str]
    show_court_popup: bool
    history: List[Dict]
    events: List[str]
    over: bool
    winner: Optional[str]
    psA: List[int]
    psB: List[int]
    ppA: Dict[str, int]
    ppB: Dict[str, int]
    started: str
    ended: Optional[str]
    tnm: Optional[str]
    trd: Optional[str]
    target: int
    updated_at: str

def restore_match(raw):
    if not raw:
        return None
    d = dict(raw)
    d.setdefault("first_court_popup_point", None)
    d.setdefault("first_court_popup_team", None)
    d.setdefault("show_court_popup", False)
    return Match(**d)

def snapshot(m: Match):
    d = asdict(m)
    d["history"] = []
    return d

def current_server(m: Match):
    return (m.curA if m.srv == "A" else m.curB) or "—"

def maybe_update_target(m: Match):
    if m.scA == m.scB:
        if m.scA >= 36:
            m.target = 39
        elif m.scA >= 34:
            m.target = 36
        else:
            m.target = 35

def create_match(match_id, created_by, tA, tB, allA, allB, pA, pB, oA, oB, first, tnm=None, trd=None):
    cA, cB, nA, nB = (oA[0], None, 1, 0) if first == "A" else (None, oB[0], 0, 1)
    now = now_str()
    return Match(
        id=match_id, created_by=created_by, tA=tA, tB=tB,
        allA=allA, allB=allB, onA=pA, onB=pB, ordA=oA, ordB=oB,
        setno=1, sA=0, sB=0, scA=0, scB=0, srv=first, swapped=False, curA=cA, curB=cB, nxtA=nA, nxtB=nB,
        subA=3, subB=3, toA=1, toB=1,
        ms={9:False, 18:False, 27:False}, first_court_popup_point=None, first_court_popup_team=None, show_court_popup=False,
        history=[], events=[f"Match started · {tA if first=='A' else tB} serves first"],
        over=False, winner=None, psA=[], psB=[], ppA={p:0 for p in pA}, ppB={p:0 for p in pB},
        started=now, ended=None, tnm=tnm, trd=trd, target=35, updated_at=now
    )

def save_match(m: Match, data):
    data["matches"][m.id] = asdict(m)
    save_data(data)

def delete_match(match_id, data):
    data["matches"].pop(match_id, None)
    save_data(data)

def list_matches(data):
    items = []
    for mid, raw in (data.get("matches") or {}).items():
        try:
            items.append(restore_match(raw))
        except Exception:
            pass
    items.sort(key=lambda x: x.updated_at or "", reverse=True)
    return items

def apply_point(m: Match, winner: str, data):
    if m.over:
        return m
    m.history.append(snapshot(m))
    m.history = m.history[-20:]

    if winner == "A":
        if m.scA >= MAX_SCORE_CAP:
            return m
        m.scA += 1
        if m.curA:
            m.ppA[m.curA] = m.ppA.get(m.curA, 0) + 1
    else:
        if m.scB >= MAX_SCORE_CAP:
            return m
        m.scB += 1
        if m.curB:
            m.ppB[m.curB] = m.ppB.get(m.curB, 0) + 1

    if winner != m.srv:
        m.srv = winner
        if winner == "A":
            m.curA = m.ordA[m.nxtA]
            m.nxtA = next_idx(m.nxtA, PLAYERS)
        else:
            m.curB = m.ordB[m.nxtB]
            m.nxtB = next_idx(m.nxtB, PLAYERS)

    m.events.insert(0, f"▸ {m.tA if winner=='A' else m.tB}  {m.scA}–{m.scB}  srv:{current_server(m)}")
    m.events = m.events[:60]

    if m.first_court_popup_point is None:
        for p in COURT_CHG:
            if not m.ms.get(p, False) and (m.scA == p or m.scB == p):
                m.ms[p] = True
                m.first_court_popup_point = p
                m.first_court_popup_team = "A" if m.scA == p else "B"
                m.show_court_popup = True
                break

    maybe_update_target(m)

    if m.show_court_popup and m.first_court_popup_point is not None:
        watched_score = m.scA if m.first_court_popup_team == "A" else m.scB
        if watched_score != m.first_court_popup_point:
            m.show_court_popup = False

    if m.target == 39 and (m.scA == 39 or m.scB == 39):
        m.over = True
        m.winner = "A" if m.scA == 39 else "B"
    elif max(m.scA, m.scB) >= m.target and abs(m.scA - m.scB) >= 2:
        sw = "A" if m.scA > m.scB else "B"
        if sw == "A":
            m.sA += 1
        else:
            m.sB += 1
        m.psA.append(m.scA)
        m.psB.append(m.scB)
        m.events.insert(0, f"✅ Set {m.setno} → {m.tA if sw=='A' else m.tB} ({m.scA}–{m.scB})")
        if m.sA == 2 or m.sB == 2:
            m.over = True
            m.winner = "A" if m.sA == 2 else "B"
        else:
            m.setno += 1
            m.scA = 0; m.scB = 0
            m.subA = 3; m.subB = 3; m.toA = 1; m.toB = 1
            m.ms = {9:False, 18:False, 27:False}
            m.first_court_popup_point = None
            m.first_court_popup_team = None
            m.show_court_popup = False
            m.target = 35
            m.events.insert(0, f"▶️ Set {m.setno} begins")

    if m.over and not m.ended:
        m.ended = now_str()
        m.events.insert(0, f"🏆 {m.tA if m.winner=='A' else m.tB} wins!")
        data["history"].append({
            "id": m.id,
            "date": m.started,
            "tA": m.tA,
            "tB": m.tB,
            "sA": m.sA,
            "sB": m.sB,
            "winner": m.tA if m.winner == "A" else m.tB,
            "tnm": m.tnm,
            "trd": m.trd,
            "set_scores": list(zip(m.psA, m.psB)),
            "player_points_A": dict(sorted(m.ppA.items(), key=lambda x: (-x[1], x[0]))),
            "player_points_B": dict(sorted(m.ppB.items(), key=lambda x: (-x[1], x[0]))),
            "created_by": m.created_by,
            "last_set_points": f"{m.psA[-1]}-{m.psB[-1]}" if m.psA and m.psB else None,
        })

    m.updated_at = now_str()
    save_match(m, data)
    return m

def undo_match(m: Match, data):
    if m.history:
        prev = m.history.pop()
        m = restore_match(prev)
        save_match(m, data)
    return m

def toggle_court(m: Match, data):
    m.swapped = not m.swapped
    m.first_court_popup_point = None
    m.first_court_popup_team = None
    m.show_court_popup = False
    m.updated_at = now_str()
    save_match(m, data)
    return m

def timeout_team(m: Match, team: str, data):
    if team == "A" and m.toA > 0:
        m.toA -= 1
    if team == "B" and m.toB > 0:
        m.toB -= 1
    m.updated_at = now_str()
    save_match(m, data)
    return m

def sub_team(m: Match, team: str, on: str, off: str, data):
    if team == "A" and m.subA > 0 and on and off and off in m.onA and on not in m.onA:
        m.onA[m.onA.index(off)] = on
        m.ppA.setdefault(on, 0)
        m.subA -= 1
    if team == "B" and m.subB > 0 and on and off and off in m.onB and on not in m.onB:
        m.onB[m.onB.index(off)] = on
        m.ppB.setdefault(on, 0)
        m.subB -= 1
    m.updated_at = now_str()
    save_match(m, data)
    return m

# session
for k, v in [
    ("role", None), ("username",""), ("user_name",""), ("is_admin_user", False),
    ("tab","score"), ("selected_match_id", None), ("show_score_adjust", False), ("show_subs_panel", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# login
if st.session_state.role is None:
    st.markdown("## Ball Badminton Live")
    t1, t2, t3 = st.tabs(["🔑 Viewer Login", "📝 Register", "🔐 Admin"])
    with t1:
        vu = st.text_input("Username", key="vu")
        vp = st.text_input("Password", type="password", key="vp")
        if st.button("Open Live Score", use_container_width=True):
            ok, u = login_user(vu, vp)
            if ok and not u.get("is_admin", False) and not u.get("root", False):
                st.session_state.role = "viewer"
                st.session_state.username = (vu or "").strip().lower()
                st.session_state.user_name = u.get("name", "Viewer")
                st.rerun()
            elif ok:
                st.error("This account has admin access. Use Admin tab.")
            else:
                st.error("Invalid credentials")
    with t2:
        rn = st.text_input("Full Name", key="rn")
        rc = st.text_input("Mobile/Email", key="rc")
        ru = st.text_input("Username", key="ru")
        rp = st.text_input("Password", type="password", key="rp")
        rp2 = st.text_input("Confirm Password", type="password", key="rp2")
        if st.button("Create Account", use_container_width=True):
            if rp != rp2:
                st.error("Passwords do not match")
            else:
                ok, msg = register_user(rn, rc, ru, rp, is_admin=False, created_by_admin=False)
                if ok: st.success(msg)
                else: st.error(msg)
    with t3:
        au = st.text_input("Admin Username", key="au")
        ap = st.text_input("Admin Password", type="password", key="ap")
        if st.button("Admin Login", use_container_width=True):
            ok, u = login_user(au, ap)
            if ok and (u.get("is_admin", False) or u.get("root", False)):
                st.session_state.role = "admin"
                st.session_state.username = (au or "").strip().lower()
                st.session_state.user_name = u.get("name", "Admin")
                st.session_state.is_admin_user = True
                st.rerun()
            elif ok:
                st.error("This account is viewer only")
            else:
                st.error("Invalid admin credentials")
    st.stop()

# always fresh data
data = load_data()
all_matches = list_matches(data)

# viewer
if st.session_state.role == "viewer":
    st_autorefresh(interval=2500, key="viewer_refresh")
    st.markdown("## Viewer")
    if all_matches:
        options = {f"{m.tA} vs {m.tB} · {m.tnm or 'Live'} · {m.id}": m.id for m in all_matches}
        labels = list(options.keys())
        idx = 0
        if st.session_state.selected_match_id:
            for i, lbl in enumerate(labels):
                if options[lbl] == st.session_state.selected_match_id:
                    idx = i
                    break
        label = st.selectbox("Choose Match", labels, index=idx)
        st.session_state.selected_match_id = options[label]
        m = restore_match(data["matches"][st.session_state.selected_match_id])

        if m.show_court_popup and m.first_court_popup_point:
            team_name = m.tA if m.first_court_popup_team == "A" else m.tB
            st.markdown(f"<div class='alert'>🔄 Court change at {m.first_court_popup_point} · first reached by {team_name}</div>", unsafe_allow_html=True)
        if m.over:
            st.markdown(f"<div class='win'>🏆 {m.tA if m.winner=='A' else m.tB} WINS</div>", unsafe_allow_html=True)

        lt = "B" if m.swapped else "A"; rt = "A" if m.swapped else "B"
        tn = lambda t: m.tA if t == "A" else m.tB
        sc = lambda t: m.scA if t == "A" else m.scB
        ss = lambda t: m.sA if t == "A" else m.sB

        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'>
              <div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div>
              <div class='score-num {'hot' if m.srv==lt else ''}'>{sc(lt)}</div>
              <div style='font-size:12px;color:#6b7280'>Sets: {ss(lt)} · Left</div>
            </div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'>
              <div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div>
              <div class='score-num {'hot' if m.srv==rt else ''}'>{sc(rt)}</div>
              <div style='font-size:12px;color:#6b7280'>Sets: {ss(rt)} · Right</div>
            </div>
          </div>
          <div style='text-align:center;color:#6b7280;font-size:10px;margin-top:8px'>
            SET {m.setno}/3 · TARGET {m.target} · FINAL CAP {MAX_SCORE_CAP}
          </div>
        </div>
        """, unsafe_allow_html=True)

        n1, n2, n3 = st.columns(3)
        with n1: st.metric("Serving", m.tA if m.srv=="A" else m.tB)
        with n2: st.metric("Server", current_server(m))
        with n3: st.metric("Target", m.target)

        nav = st.columns(3)
        with nav[0]:
            if st.button("🏸 Score", key="v_score", use_container_width=True):
                st.session_state.tab = "score"
        with nav[1]:
            if st.button("📊 Stats", key="v_stats", use_container_width=True):
                st.session_state.tab = "stats"
        with nav[2]:
            if st.button("📜 History", key="v_history", use_container_width=True):
                st.session_state.tab = "history"

        if st.session_state.tab == "stats":
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### {m.tA} Player Points")
                for p, pts in sorted(m.ppA.items(), key=lambda x: (-x[1], x[0])):
                    st.write(f"{p}: {pts}")
            with c2:
                st.markdown(f"### {m.tB} Player Points")
                for p, pts in sorted(m.ppB.items(), key=lambda x: (-x[1], x[0])):
                    st.write(f"{p}: {pts}")
        elif st.session_state.tab == "history":
            hist = [h for h in data.get("history", []) if h.get("id") == m.id]
            if not hist:
                st.info("No completed history for this match yet.")
            else:
                for h in reversed(hist):
                    with st.container(border=True):
                        st.markdown(f"### {h['tA']} vs {h['tB']}")
                        st.caption(h["date"])
                        st.write(f"Winner: **{h['winner']}**")
                        st.write(f"Sets: **{h['sA']}–{h['sB']}**")
                        st.write(f"Last set points: **{h.get('last_set_points') or '-'}**")
                        if h.get("set_scores"):
                            st.write(f"Set-wise points: {h['set_scores']}")
                        st.write("Player Points A:", h.get("player_points_A", {}))
                        st.write("Player Points B:", h.get("player_points_B", {}))
    else:
        st.info("No live matches currently.")
    st.stop()

# admin
nav_items = [("score","🏸 Score"),("stats","📊 Stats"),("history","📜 History"),("users","👥 Users"),("admin","⚙️ Admin")]
nav_cols = st.columns(len(nav_items) + 2)
for i, (k, lbl) in enumerate(nav_items):
    with nav_cols[i]:
        if st.button(lbl, key=f"nav_{k}", use_container_width=True):
            st.session_state.tab = k
            st.rerun()
with nav_cols[-2]:
    if st.button("🔄 New Match", use_container_width=True):
        st.session_state.selected_match_id = None
        st.session_state.tab = "score"
        st.session_state.show_score_adjust = False
        st.session_state.show_subs_panel = False
        st.rerun()
with nav_cols[-1]:
    if st.button("🚪 Exit", use_container_width=True):
        st.session_state.role = None
        st.session_state.username = ""
        st.session_state.user_name = ""
        st.session_state.is_admin_user = False
        st.session_state.selected_match_id = None
        st.rerun()

st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:4px 0 8px'>", unsafe_allow_html=True)
tab = st.session_state.tab

admin_matches = [m for m in all_matches if (m.created_by == st.session_state.username or st.session_state.username == ROOT_ADMIN_USER.lower())]

with st.container(border=True):
    st.markdown("### Your Matches")
    if admin_matches:
        opts = {"<Create New Match>": None}
        for m in admin_matches:
            opts[f"{m.tA} vs {m.tB} · {m.id}"] = m.id
        labels = list(opts.keys())
        idx = 0
        if st.session_state.selected_match_id:
            for i, lbl in enumerate(labels):
                if opts[lbl] == st.session_state.selected_match_id:
                    idx = i
                    break
        picked = st.selectbox("Select", labels, index=idx)
        st.session_state.selected_match_id = opts[picked]
    else:
        st.info("No match created yet. Use New Match.")
        st.session_state.selected_match_id = None

selected_match = None
if st.session_state.selected_match_id and st.session_state.selected_match_id in data.get("matches", {}):
    selected_match = restore_match(data["matches"][st.session_state.selected_match_id])

if tab == "score":
    if selected_match is None:
        st.markdown("## Create New Match")
        c1, c2 = st.columns(2)
        with c1: tnm = st.text_input("Tournament Name")
        with c2: trd = st.text_input("Round")
        c3, c4 = st.columns(2)
        with c3: tA = st.text_input("Team A")
        with c4: tB = st.text_input("Team B")
        st.markdown("### Players")
        pa, pb = st.columns(2)
        allA = []; allB = []
        with pa:
            for i in range(ALL_PLAYERS):
                allA.append(st.text_input(f"A Player {i+1}", key=f"A_{i}"))
        with pb:
            for i in range(ALL_PLAYERS):
                allB.append(st.text_input(f"B Player {i+1}", key=f"B_{i}"))
        allA_f = [safe(v, f"A{i+1}") for i, v in enumerate(allA)]
        allB_f = [safe(v, f"B{i+1}") for i, v in enumerate(allB)]

        s1, s2 = st.columns(2)
        with s1:
            mpA = st.multiselect("Team A starters", allA_f, default=allA_f[:PLAYERS], max_selections=PLAYERS)
        with s2:
            mpB = st.multiselect("Team B starters", allB_f, default=allB_f[:PLAYERS], max_selections=PLAYERS)

        errs = []
        oA2=[]; oB2=[]
        if len(mpA) == PLAYERS and len(mpB) == PLAYERS:
            x1, x2 = st.columns(2)
            oAi=[]; oBi=[]
            with x1:
                for k in range(PLAYERS):
                    opts = [f"{i+1}. {mpA[i]}" for i in range(PLAYERS)]
                    sel = st.selectbox(f"A Serve {k+1}", opts, key=f"oa_{k}")
                    oAi.append(int(sel.split(".")[0]))
            with x2:
                for k in range(PLAYERS):
                    opts = [f"{i+1}. {mpB[i]}" for i in range(PLAYERS)]
                    sel = st.selectbox(f"B Serve {k+1}", opts, key=f"ob_{k}")
                    oBi.append(int(sel.split(".")[0]))
            if len(set(oAi)) != 5: errs.append("Team A service order must be unique")
            if len(set(oBi)) != 5: errs.append("Team B service order must be unique")
            oA2 = build_order(list(mpA), oAi)
            oB2 = build_order(list(mpB), oBi)
            if not oA2 or not oB2: errs.append("Invalid service order")
            first = st.radio("First serve", [tA or "Team A", tB or "Team B"], horizontal=True)
            first_side = "A" if first == (tA or "Team A") else "B"
        else:
            first_side = "A"
            errs.append("Select exactly 5 starters per team")

        for e in errs:
            st.error(e)

        if st.button("▶️ Start Match", use_container_width=True, disabled=bool(errs)):
            mid = f"{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            m = create_match(mid, st.session_state.username, safe(tA, "Team A"), safe(tB, "Team B"),
                             allA_f, allB_f, list(mpA), list(mpB), oA2, oB2, first_side, tnm or None, trd or None)
            save_match(m, data)
            st.session_state.selected_match_id = mid
            st.rerun()
    else:
        m = selected_match
        if m.show_court_popup and m.first_court_popup_point:
            team_name = m.tA if m.first_court_popup_team == "A" else m.tB
            st.markdown(f"<div class='alert'>🔄 Court change at {m.first_court_popup_point} · first reached by {team_name}</div>", unsafe_allow_html=True)
        if m.over:
            st.markdown(f"<div class='win'>🏆 {m.tA if m.winner=='A' else m.tB} WINS</div>", unsafe_allow_html=True)

        lt = "B" if m.swapped else "A"; rt = "A" if m.swapped else "B"
        tn = lambda t: m.tA if t == "A" else m.tB
        sc = lambda t: m.scA if t == "A" else m.scB
        ss = lambda t: m.sA if t == "A" else m.sB
        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'>
              <div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div>
              <div class='score-num {'hot' if m.srv==lt else ''}'>{sc(lt)}</div>
              <div style='font-size:12px;color:#6b7280'>Sets: {ss(lt)} · Left</div>
            </div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'>
              <div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div>
              <div class='score-num {'hot' if m.srv==rt else ''}'>{sc(rt)}</div>
              <div style='font-size:12px;color:#6b7280'>Sets: {ss(rt)} · Right</div>
            </div>
          </div>
          <div style='text-align:center;color:#6b7280;font-size:10px;margin-top:8px'>
            SET {m.setno}/3 · TARGET {m.target} · FINAL CAP {MAX_SCORE_CAP}
          </div>
        </div>
        """, unsafe_allow_html=True)
        meta = st.columns(4)
        with meta[0]: st.metric("Serving", m.tA if m.srv == "A" else m.tB)
        with meta[1]: st.metric("Server", current_server(m))
        with meta[2]: st.metric("Target", m.target)
        with meta[3]: st.metric("Created By", m.created_by)

        p1, p2 = st.columns(2)
        with p1:
            st.markdown("<div class='bigpoint'>", unsafe_allow_html=True)
            if st.button(f"＋ {m.tA}", use_container_width=True, disabled=(m.over or m.scA >= MAX_SCORE_CAP)):
                apply_point(m, "A", data); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with p2:
            st.markdown("<div class='bigpoint bigpointblue'>", unsafe_allow_html=True)
            if st.button(f"＋ {m.tB}", key="point_b", use_container_width=True, disabled=(m.over or m.scB >= MAX_SCORE_CAP)):
                apply_point(m, "B", data); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='smallnav'>", unsafe_allow_html=True)
        nav = st.columns(5)
        with nav[0]:
            if st.button("🔄 Court", use_container_width=True):
                toggle_court(m, data); st.rerun()
        with nav[1]:
            if st.button("↩️ Undo", use_container_width=True, disabled=not m.history):
                undo_match(m, data); st.rerun()
        with nav[2]:
            if st.button("⚙️ Score", use_container_width=True):
                st.session_state.show_score_adjust = not st.session_state.show_score_adjust
                st.rerun()
        with nav[3]:
            if st.button("🔁 Subs", use_container_width=True):
                st.session_state.show_subs_panel = not st.session_state.show_subs_panel
                st.rerun()
        with nav[4]:
            if st.button("🗑️ Delete", use_container_width=True):
                delete_match(m.id, data)
                st.session_state.selected_match_id = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.show_score_adjust:
            with st.container(border=True):
                st.markdown("### Manual Score Adjust")
                a1, a2 = st.columns(2)
                with a1:
                    new_a = st.number_input(f"{m.tA} Score", min_value=0, max_value=MAX_SCORE_CAP, value=int(m.scA), step=1)
                    if st.button(f"Set {m.tA}", use_container_width=True):
                        m.scA = int(new_a); maybe_update_target(m); m.updated_at = now_str(); save_match(m, data); st.rerun()
                with a2:
                    new_b = st.number_input(f"{m.tB} Score", min_value=0, max_value=MAX_SCORE_CAP, value=int(m.scB), step=1)
                    if st.button(f"Set {m.tB}", use_container_width=True):
                        m.scB = int(new_b); maybe_update_target(m); m.updated_at = now_str(); save_match(m, data); st.rerun()

        if st.session_state.show_subs_panel:
            with st.container(border=True):
                st.markdown("### Substitutions & Timeouts")
                c1, c2 = st.columns(2)
                for team, col in [("A", c1), ("B", c2)]:
                    tname = m.tA if team == "A" else m.tB
                    subs = m.subA if team == "A" else m.subB
                    tos = m.toA if team == "A" else m.toB
                    on_court = m.onA if team == "A" else m.onB
                    all_p = m.allA if team == "A" else m.allB
                    with col:
                        st.markdown(f"**{tname}**")
                        st.write(f"Subs: {subs} | Timeout: {tos}")
                        bench = [p for p in all_p if p and p not in on_court]
                        if subs > 0 and bench:
                            on_p = st.selectbox("In", bench, key=f"in_{team}")
                            off_p = st.selectbox("Out", on_court, key=f"out_{team}")
                            if st.button(f"Sub {tname}", key=f"sub_{team}", use_container_width=True):
                                sub_team(m, team, on_p, off_p, data); st.rerun()
                        if tos > 0:
                            if st.button(f"Timeout {tname}", key=f"to_{team}", use_container_width=True):
                                timeout_team(m, team, data); st.rerun()

        with st.container(border=True):
            st.markdown("**Live Events**")
            for e in m.events[:18]:
                st.markdown(f"<div class='ev'>{e}</div>", unsafe_allow_html=True)

elif tab == "stats":
    if not selected_match:
        st.info("Select a match first.")
    else:
        m = selected_match
        total = m.scA + m.scB + sum(m.psA) + sum(m.psB)
        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl in [(c1, f"Set {m.setno}", "Set"), (c2, f"{m.sA}–{m.sB}", "Sets"), (c3, f"{m.scA}–{m.scB}", "Score"), (c4, total, "Total")]:
            with col:
                st.markdown(f"<div class='sbox'><div class='score-num' style='font-size:32px'>{val}</div><div style='font-size:10px;color:#6b7280'>{lbl}</div></div>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"### {m.tA} Player Points")
            for p, pts in sorted(m.ppA.items(), key=lambda x: (-x[1], x[0])):
                st.write(f"{p}: {pts}")
        with p2:
            st.markdown(f"### {m.tB} Player Points")
            for p, pts in sorted(m.ppB.items(), key=lambda x: (-x[1], x[0])):
                st.write(f"{p}: {pts}")

elif tab == "history":
    st.markdown("## Match History")
    hist = data.get("history", [])
    if not hist:
        st.info("No completed matches yet.")
    else:
        for h in reversed(hist):
            with st.container(border=True):
                st.markdown(f"### {h['tA']} vs {h['tB']}")
                st.caption(f"{h['date']} · Created by {h.get('created_by','-')}")
                st.write(f"Winner: **{h['winner']}**")
                st.write(f"Sets: **{h['sA']}–{h['sB']}**")
                st.write(f"Last set points: **{h.get('last_set_points') or '-'}**")
                if h.get("set_scores"):
                    st.write(f"Set-wise points: {h['set_scores']}")
                st.write("Player Points A:", h.get("player_points_A", {}))
                st.write("Player Points B:", h.get("player_points_B", {}))

elif tab == "users":
    st.markdown("## Users")
    users = load_users()
    if users:
        for uname, u in users.items():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,2,1])
                with c1:
                    st.markdown(f"**{u.get('name','—')}**")
                    st.caption(f"@{uname}")
                with c2:
                    st.write(u.get("contact","—"))
                    st.caption(f"Joined: {u.get('created','—')}")
                with c3:
                    st.write("Admin" if u.get("is_admin") else "Viewer")
    st.markdown("---")
    st.markdown("### Add User")
    with st.container(border=True):
        n = st.text_input("Name", key="un")
        c = st.text_input("Contact", key="uc")
        u = st.text_input("Username", key="uu")
        p = st.text_input("Password", type="password", key="up")
        is_admin = st.checkbox("Give Admin Access", key="uia")
        if st.button("Create User", use_container_width=True):
            ok, msg = register_user(n, c, u, p, is_admin=is_admin, created_by_admin=True)
            if ok: st.success(msg)
            else: st.error(msg)

elif tab == "admin":
    st.markdown("## Admin Overview")
    st.write(f"**Total live matches:** {len(all_matches)}")
    st.write(f"**Total completed matches:** {len(data.get('history', []))}")
    if all_matches:
        for m in all_matches:
            with st.container(border=True):
                st.write(f"**{m.tA} vs {m.tB}**")
                st.write(f"Created by: {m.created_by}")
                st.write(f"Score: {m.scA}–{m.scB} · Sets {m.sA}–{m.sB}")
                st.write(f"Updated: {m.updated_at}")
