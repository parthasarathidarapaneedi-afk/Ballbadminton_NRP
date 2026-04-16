
import json
import os
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st
from streamlit_autorefresh import st_autorefresh

SUPABASE_OK = False
try:
    from supabase import create_client
    SUPABASE_OK = True
except Exception:
    create_client = None

SET_POINTS = 35
COURT_CHG = [9, 18, 27]
PLAYERS = 5
ALL_PLAYERS = 10
MAX_SCORE_CAP = 39
DATA_FILE = "bb_data.json"
USERS_FILE = "bb_users.json"
ADMIN_USER = "Ballbadminton"
ADMIN_PASS = "partha@2025"

st.set_page_config(page_title="🏸 Ball Badminton Live", page_icon="🏸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700;800&display=swap');
#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],.stDeployButton,section[data-testid="stSidebar"],[data-testid="stSidebarNav"],.viewerBadge_container__1QSob,a[href*="streamlit.io"],a[href*="github.com"]{display:none!important;}
:root{--bg:#07101f;--surf:#0d1a2e;--card:#112038;--bdr:rgba(255,255,255,.07);--acc:#f97316;--blue:#3b82f6;--grn:#22c55e;--red:#ef4444;--gold:#f59e0b;--txt:#f0f4f8;--muted:#5a7090;--r:14px;}
html,body,.stApp{background:var(--bg)!important;color:var(--txt)!important;font-family:'Inter',sans-serif!important;}
.block-container{max-width:100%!important;padding:.5rem .65rem 4.8rem!important;}
.stButton>button{background:linear-gradient(135deg,#f97316,#c2410c)!important;color:#fff!important;border:none!important;font-weight:800!important;font-size:13px!important;padding:10px 12px!important;border-radius:12px!important;width:100%!important;box-shadow:0 4px 14px rgba(249,115,22,.24)!important;}
.stButton>button:disabled{opacity:.45!important;}
.stTextInput input,.stSelectbox>div>div,.stMultiSelect>div>div,.stNumberInput input{background:var(--card)!important;color:var(--txt)!important;border:1px solid var(--bdr)!important;border-radius:10px!important;}
[data-testid="stContainer"]{background:var(--card)!important;border:1px solid var(--bdr)!important;border-radius:var(--r)!important;padding:12px!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--surf)!important;border-radius:10px!important;padding:4px!important;gap:4px!important;}
.stTabs [data-baseweb="tab"]{color:var(--muted)!important;border-radius:8px!important;font-weight:700!important;padding:8px 12px!important;font-size:12px!important;}
.stTabs [aria-selected="true"]{background:var(--acc)!important;color:#fff!important;}
[data-testid="stMetricValue"]{color:var(--txt)!important;font-weight:800!important;}
[data-testid="stMetricLabel"]{color:var(--muted)!important;}
.scoreboard{background:linear-gradient(135deg,var(--surf),var(--card));border:1px solid rgba(249,115,22,.15);border-radius:18px;padding:18px 14px 14px;position:relative;overflow:hidden;}
.scoreboard::before{content:'';position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg,var(--acc),var(--gold),var(--acc));}
.score-num{font-family:'Bebas Neue',sans-serif;font-size:92px;line-height:1;color:#fff;}
.score-num.hot{color:var(--acc);text-shadow:0 0 30px rgba(249,115,22,.4);}
.tname{font-size:17px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.tmeta{font-size:12px;color:var(--muted);margin-top:2px;}
.badge{display:inline-block;padding:2px 9px;border-radius:12px;font-size:10px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;}
.b-o{background:rgba(249,115,22,.15);color:#fdba74;border:1px solid rgba(249,115,22,.25);}
.b-b{background:rgba(59,130,246,.15);color:#93c5fd;border:1px solid rgba(59,130,246,.25);}
.b-g{background:rgba(34,197,94,.15);color:#86efac;border:1px solid rgba(34,197,94,.25);}
.b-r{background:rgba(239,68,68,.15);color:#fca5a5;border:1px solid rgba(239,68,68,.25);}
.b-gold{background:rgba(245,158,11,.15);color:#fbbf24;border:1px solid rgba(245,158,11,.25);}
.winner-wrap{background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:16px;padding:16px;text-align:center;font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:2px;box-shadow:0 6px 24px rgba(245,158,11,.4);margin-bottom:12px;}
.court-alert{background:rgba(249,115,22,.10);border:1px solid rgba(249,115,22,.3);border-radius:12px;padding:12px;margin-bottom:10px;font-weight:800;color:#fdba74;}
.ev{font-size:11px;padding:5px 6px;border-bottom:1px solid var(--bdr);color:var(--muted);}
.ev:first-child{color:var(--txt);font-weight:700;}
.sbox{background:var(--surf);border:1px solid var(--bdr);border-radius:10px;padding:10px;text-align:center;}
.sbox-n{font-family:'Bebas Neue',sans-serif;font-size:32px;color:var(--acc);}
.sbox-l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;}
.pbig .stButton>button{font-size:20px!important;padding:22px 10px!important;border-radius:15px!important;}
.pbig-b .stButton>button{background:linear-gradient(135deg,#3b82f6,#1d4ed8)!important;box-shadow:0 4px 14px rgba(59,130,246,.24)!important;}
.mob-nav-wrap{position:fixed;left:0;right:0;bottom:0;z-index:999;background:rgba(7,16,31,.97);border-top:1px solid rgba(255,255,255,.08);padding:8px 8px calc(8px + env(safe-area-inset-bottom));backdrop-filter:blur(8px);}
.mob-nav-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;}
.mob-nav-btn{background:var(--card);color:#fff;border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:10px 6px;text-align:center;font-size:12px;font-weight:800;}
.mob-nav-btn.active{background:linear-gradient(135deg,#ff7a18,#d9480f);}
@media(max-width:768px){.block-container{padding:.35rem .45rem 4.8rem!important}.score-num{font-size:72px!important}.tname{font-size:14px!important}.pbig .stButton>button{font-size:17px!important;padding:18px 8px!important}}
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

def using_supabase() -> bool:
    return get_supabase() is not None

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _safe(s: str, fb: str) -> str:
    s = (s or "").strip()
    return s if s else fb

def _nxt(i: int, n: int) -> int:
    return (i + 1) % n

def _build_ord(p5, idxs):
    out = []
    for idx in idxs:
        if not (1 <= idx <= len(p5)):
            return []
        out.append(p5[idx-1])
    return out

def data_default() -> dict:
    return {"matches": {}, "history": [], "tournament": [], "t_info": {}, "updated_at": ""}

def data_load() -> dict:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("matches").select("*").eq("id","app_state").execute()
            if res.data:
                payload = res.data[0].get("data") or {}
                base = data_default()
                base.update(payload)
                return base
        except Exception:
            pass
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            base = data_default()
            base.update(d)
            return base
        except Exception:
            pass
    return data_default()

def data_save(data: dict):
    data["updated_at"] = datetime.now().strftime("%d %b %Y %H:%M:%S")
    sb = get_supabase()
    if sb:
        try:
            sb.table("matches").upsert({"id":"app_state","data":data,"updated_at":datetime.now().isoformat()}).execute()
            return
        except Exception:
            pass
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def users_load() -> dict:
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
                    "created_by_admin": row.get("created_by_admin", False),
                    "is_admin": row.get("is_admin", False),
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

def users_save(users: dict):
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
                    "created_by_admin": u.get("created_by_admin", False),
                    "is_admin": u.get("is_admin", False),
                })
            if rows:
                sb.table("viewers").upsert(rows).execute()
            return
        except Exception:
            pass
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def user_register(name: str, contact: str, username: str, password: str, created_by_admin: bool = False, is_admin: bool = False) -> Tuple[bool, str]:
    users = users_load()
    uname = (username or "").strip().lower()
    if not uname or not password or not name or not contact:
        return False, "All fields are required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if uname in users:
        return False, "Username already taken"
    for u in users.values():
        if u.get("contact","").strip().lower() == contact.strip().lower():
            return False, "This mobile/email is already registered"
    users[uname] = {
        "name": name.strip(),
        "contact": contact.strip(),
        "pw_hash": _hash(password),
        "created": datetime.now().strftime("%d %b %Y %H:%M"),
        "created_by_admin": created_by_admin,
        "is_admin": is_admin,
    }
    users_save(users)
    return True, f"Registered! Login as '{uname}'"

def user_login(username: str, password: str) -> Tuple[bool, str, dict]:
    users = users_load()
    uname = (username or "").strip().lower()
    if uname not in users:
        return False, "Username not found", {}
    u = users[uname]
    if u["pw_hash"] != _hash(password):
        return False, "Wrong password", {}
    return True, "OK", u

@dataclass
class Match:
    id: str
    tA: str; tB: str
    allA: List[str]; allB: List[str]
    onA: List[str]; onB: List[str]
    ordA: List[str]; ordB: List[str]
    setno: int; sA: int; sB: int; scA: int; scB: int
    srv: str; swapped: bool
    curA: Optional[str]; curB: Optional[str]
    nxtA: int; nxtB: int
    subA: int; subB: int; toA: int; toB: int
    ms: Dict[int, bool]
    first_court_popup_point: Optional[int]
    first_court_popup_team: Optional[str] = None
    show_court_popup: bool = False
    history: List[Dict] = None
    events: List[str] = None
    over: bool = False; winner: Optional[str] = None
    psA: List[int] = None; psB: List[int] = None
    ppA: Dict[str, int] = None; ppB: Dict[str, int] = None
    started: str = ""; ended: Optional[str] = None
    tnm: Optional[str] = None; trd: Optional[str] = None
    target: int = SET_POINTS
    updated_at: Optional[str] = None
    created_by: str = "admin"

def _restore(d):
    if not d:
        return None
    try:
        d = dict(d)
        d.setdefault("first_court_popup_team", None)
        d.setdefault("show_court_popup", False)
        d.setdefault("history", [])
        d.setdefault("events", [])
        d.setdefault("psA", [])
        d.setdefault("psB", [])
        d.setdefault("ppA", {})
        d.setdefault("ppB", {})
        d.setdefault("created_by", "admin")
        return Match(**d)
    except Exception:
        return None

def _snap(m: Match):
    d = asdict(m)
    d["history"] = []
    return d

def _push_event(m: Match, txt: str):
    m.events.insert(0, txt)
    m.events = m.events[:60]
    m.updated_at = datetime.now().strftime("%d %b %Y %H:%M:%S")

def current_server(m: Match) -> str:
    return (m.curA if m.srv == "A" else m.curB) or "—"

def maybe_update_target(m: Match):
    if m.scA == m.scB:
        if m.scA >= 36:
            m.target = 39
        elif m.scA >= 34:
            m.target = 36
        else:
            m.target = 35

def new_match(match_id, tA,tB,allA,allB,pA,pB,oA,oB,first,creator,tnm=None,trd=None) -> Match:
    cA,cB,nA,nB = (oA[0],None,1,0) if first=="A" else (None,oB[0],0,1)
    now = datetime.now()
    return Match(
        id=match_id,
        tA=tA,tB=tB,allA=allA,allB=allB,onA=pA,onB=pB,ordA=oA,ordB=oB,
        setno=1,sA=0,sB=0,scA=0,scB=0,srv=first,swapped=False,
        curA=cA,curB=cB,nxtA=nA,nxtB=nB,subA=3,subB=3,toA=1,toB=1,
        ms={9:False,18:False,27:False}, first_court_popup_point=None,
        first_court_popup_team=None, show_court_popup=False,
        history=[],events=[f"Match started · {tA if first=='A' else tB} serves first"],
        over=False,winner=None,psA=[],psB=[],
        ppA={p:0 for p in pA}, ppB={p:0 for p in pB},
        started=now.strftime("%d %b %Y %H:%M"), ended=None,
        tnm=tnm, trd=trd, target=35,
        updated_at=now.strftime("%d %b %Y %H:%M:%S"), created_by=creator
    )

def get_match(data: dict, match_id: str) -> Optional[Match]:
    return _restore(data.get("matches", {}).get(match_id))

def save_match(data: dict, m: Match):
    data.setdefault("matches", {})[m.id] = asdict(m)
    data_save(data)

def delete_match(data: dict, match_id: str):
    data.setdefault("matches", {}).pop(match_id, None)
    data_save(data)

def do_point(data: dict, match_id: str, winner: str):
    m = get_match(data, match_id)
    if not m or m.over:
        return
    score = m.scA if winner == "A" else m.scB
    if score >= MAX_SCORE_CAP:
        return
    m.history.append(_snap(m))
    m.history = m.history[-20:]
    if winner == "A":
        m.scA += 1
        if m.curA: m.ppA[m.curA] = m.ppA.get(m.curA, 0) + 1
    else:
        m.scB += 1
        if m.curB: m.ppB[m.curB] = m.ppB.get(m.curB, 0) + 1
    if winner != m.srv:
        m.srv = winner
        if winner == "A":
            m.curA = m.ordA[m.nxtA]; m.nxtA = _nxt(m.nxtA, PLAYERS)
        else:
            m.curB = m.ordB[m.nxtB]; m.nxtB = _nxt(m.nxtB, PLAYERS)
    _push_event(m, f"▸ {m.tA if winner=='A' else m.tB}  {m.scA}–{m.scB}  srv:{current_server(m)}")
    if m.first_court_popup_point is None:
        for p in COURT_CHG:
            if not m.ms.get(p, False) and (m.scA == p or m.scB == p):
                m.ms[p] = True
                m.first_court_popup_point = p
                m.first_court_popup_team = "A" if m.scA == p else "B"
                m.show_court_popup = True
                _push_event(m, f"🔄 First to {p} reached by {m.tA if m.first_court_popup_team=='A' else m.tB}")
                break
    maybe_update_target(m)
    if m.show_court_popup and m.first_court_popup_point is not None:
        first_score_now = m.scA if m.first_court_popup_team == "A" else m.scB
        if first_score_now != m.first_court_popup_point:
            m.show_court_popup = False
    if m.target == 39 and (m.scA == 39 or m.scB == 39):
        m.over = True; m.winner = "A" if m.scA == 39 else "B"
    elif max(m.scA, m.scB) >= m.target and abs(m.scA - m.scB) >= 2:
        set_winner = "A" if m.scA > m.scB else "B"
        if set_winner == "A": m.sA += 1
        else: m.sB += 1
        m.psA.append(m.scA); m.psB.append(m.scB)
        _push_event(m, f"✅ Set {m.setno} → {m.tA if set_winner=='A' else m.tB} ({m.scA}–{m.scB})")
        if m.sA == 2 or m.sB == 2:
            m.over = True; m.winner = "A" if m.sA == 2 else "B"
        else:
            m.setno += 1; m.scA = 0; m.scB = 0
            m.subA = 3; m.subB = 3; m.toA = 1; m.toB = 1
            m.ms = {9:False,18:False,27:False}
            m.first_court_popup_point = None; m.first_court_popup_team = None; m.show_court_popup = False
            m.target = 35
            _push_event(m, f"▶️ Set {m.setno} begins")
    if m.over:
        if not m.ended: m.ended = datetime.now().strftime("%d %b %Y %H:%M")
        _push_event(m, f"🏆 {m.tA if m.winner=='A' else m.tB} wins!")
        hist = data.get("history", [])
        hist.append({"id": m.id, "date": m.started, "tA": m.tA, "tB": m.tB, "sA": m.sA, "sB": m.sB,
                     "sets": list(zip(m.psA, m.psB)), "winner": m.tA if m.winner=="A" else m.tB, "tnm": m.tnm, "trd": m.trd})
        data["history"] = hist
    save_match(data, m)

def do_undo(data, match_id):
    m = get_match(data, match_id)
    if not m or not m.history: return
    restored = _restore(m.history.pop())
    data["matches"][match_id] = asdict(restored)
    data_save(data)

def do_court(data, match_id):
    m = get_match(data, match_id)
    if not m: return
    m.swapped = not m.swapped
    m.first_court_popup_point = None; m.first_court_popup_team = None; m.show_court_popup = False
    _push_event(m, "🔄 Court sides changed")
    save_match(data, m)

def do_timeout(data, match_id, team):
    m = get_match(data, match_id)
    if not m: return
    if team=="A" and m.toA>0:
        m.toA-=1; _push_event(m, f"⏱️ Timeout: {m.tA}")
    elif team=="B" and m.toB>0:
        m.toB-=1; _push_event(m, f"⏱️ Timeout: {m.tB}")
    save_match(data, m)

def do_sub(data, match_id, team, on, off):
    m = get_match(data, match_id)
    if not m or not on or not off or on == off: return
    if team=="A":
        if m.subA<=0 or on in m.onA or off not in m.onA: return
        m.onA[m.onA.index(off)] = on; m.ppA.setdefault(on, 0); m.subA -= 1
        _push_event(m, f"🔁 {m.tA}: {off}→{on}")
    else:
        if m.subB<=0 or on in m.onB or off not in m.onB: return
        m.onB[m.onB.index(off)] = on; m.ppB.setdefault(on, 0); m.subB -= 1
        _push_event(m, f"🔁 {m.tB}: {off}→{on}")
    save_match(data, m)

def admin_adjust_score(data, match_id, team, value):
    m = get_match(data, match_id)
    if not m or m.over: return
    value = max(0, min(MAX_SCORE_CAP, int(value)))
    if team=="A": m.scA = value
    else: m.scB = value
    maybe_update_target(m)
    _push_event(m, f"✏️ Score adjusted → {m.tA} {m.scA} · {m.tB} {m.scB}")
    save_match(data, m)

for k, v in [
    ("role", None), ("username", ""), ("user_name", ""), ("tab", "score"),
    ("active_match_id", None), ("selected_view_match_id", None),
    ("show_score_adjust", False), ("show_subs_panel", False),
    ("setup", {"tA":"", "tB":"", "allA":[""]*ALL_PLAYERS, "allB":[""]*ALL_PLAYERS, "ordA":[1,2,3,4,5], "ordB":[1,2,3,4,5], "first":"A", "tnm":"", "trd":""}),
]:
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.role is None:
    st.markdown("""
    <div style='text-align:center;padding:24px 0 12px'>
      <div style='font-size:58px'>🏸</div>
      <div style='font-family:Bebas Neue,sans-serif;font-size:38px;letter-spacing:3px;margin-top:4px'>BALL BADMINTON LIVE</div>
      <div style='color:#5a7090;font-size:12px;margin-top:3px'>Multi-match Mobile Scoreboard</div>
    </div>
    """, unsafe_allow_html=True)
    vt, rt, at = st.tabs(["🔑 Viewer Login", "📝 Register", "🔐 Admin"])
    with vt:
        vu = st.text_input("Username", key="vl_u")
        vp = st.text_input("Password", type="password", key="vl_p")
        if st.button("▶️ Open Live Score", use_container_width=True, key="vlogin"):
            ok, msg, udata = user_login(vu, vp)
            if ok:
                st.session_state.role = "viewer"
                st.session_state.username = vu.strip().lower()
                st.session_state.user_name = udata.get("name","Viewer")
                st.rerun()
            st.error(msg)
    with rt:
        rn = st.text_input("Full Name", key="reg_name")
        rc = st.text_input("Mobile / Email", key="reg_contact")
        ru = st.text_input("Choose Username", key="reg_user")
        rp = st.text_input("Create Password", type="password", key="reg_pass")
        rp2 = st.text_input("Confirm Password", type="password", key="reg_pass2")
        if st.button("✅ Create Account", use_container_width=True, key="reg_btn"):
            if rp != rp2:
                st.error("Passwords don't match")
            else:
                ok, msg = user_register(rn, rc, ru, rp)
                (st.success if ok else st.error)(msg)
    with at:
        au = st.text_input("Username", key="al_u")
        ap = st.text_input("Password", type="password", key="al_p")
        if st.button("🔐 Admin Login", use_container_width=True, key="alogin"):
            if au == ADMIN_USER and ap == ADMIN_PASS:
                st.session_state.role = "admin"
                st.session_state.username = ADMIN_USER
                st.session_state.user_name = "Admin"
                st.rerun()
            else:
                ok, msg, udata = user_login(au, ap)
                if ok and udata.get("is_admin"):
                    st.session_state.role = "admin"
                    st.session_state.username = au.strip().lower()
                    st.session_state.user_name = udata.get("name","Admin")
                    st.rerun()
                st.error("Invalid admin credentials")
    st.stop()

is_admin = st.session_state.role == "admin"
data = data_load()
matches = data.get("matches", {})
active_match_id = st.session_state.active_match_id or (next(iter(matches.keys()), None) if matches else None)
st.session_state.active_match_id = active_match_id

nav_items = [("score","🏸 Score"),("stats","📊 Stats"),("history","📜 History")]
if is_admin:
    nav_items += [("tournament","🏆 Tournament"),("users","👥 Users"),("admin","⚙️ Admin")]
nav_cols = st.columns(len(nav_items) + (2 if is_admin else 1))
for i,(k,lbl) in enumerate(nav_items):
    with nav_cols[i]:
        if st.button(lbl, key=f"nav_{k}", use_container_width=True):
            st.session_state.tab = k
            st.rerun()
idx = len(nav_items)
if is_admin:
    with nav_cols[idx]:
        if st.button("🔄 New Match", key="new_match_top", use_container_width=True):
            st.session_state.tab = "score"
            st.session_state.active_match_id = None
            st.session_state.show_score_adjust = False
            st.session_state.show_subs_panel = False
            st.rerun()
    idx += 1
with nav_cols[idx]:
    if st.button("🚪 Exit", key="logout_btn_top", use_container_width=True):
        st.session_state.role = None
        st.session_state.username = ""
        st.session_state.user_name = ""
        st.rerun()
st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:4px 0 8px'>", unsafe_allow_html=True)

if matches:
    opt_map = {}
    for mid, md in matches.items():
        m = _restore(md)
        if m:
            status = "Finished" if m.over else "Live"
            opt_map[f"{m.tA} vs {m.tB} · {status} · {mid[-4:]}"] = mid
    label = "Manage Match" if is_admin else "View Match"
    selected = st.selectbox(label, list(opt_map.keys()), index=0 if st.session_state.get("selected_view_match_id") not in opt_map.values() else list(opt_map.values()).index(st.session_state.get("selected_view_match_id")))
    chosen_id = opt_map[selected]
    if is_admin:
        st.session_state.active_match_id = chosen_id
    else:
        st.session_state.selected_view_match_id = chosen_id

if not is_admin:
    if st.session_state.tab not in ("score","stats","history"):
        st.session_state.tab = "score"
    if not matches:
        st.info("⏳ No active matches right now")
        st_autorefresh(interval=2500, key="viewer_wait_refresh")
        st.stop()
    current_id = st.session_state.selected_view_match_id or next(iter(matches.keys()))
    m = get_match(data, current_id)
    st_autorefresh(interval=2500, key="viewer_live_refresh")
    if st.session_state.tab == "score":
        if m.show_court_popup and m.first_court_popup_point:
            first_team_name = m.tA if m.first_court_popup_team == "A" else m.tB
            st.markdown(f"<div class='court-alert'>🔄 Court change at {m.first_court_popup_point} — first reached by {first_team_name}</div>", unsafe_allow_html=True)
        if m.over:
            st.markdown(f"<div class='winner-wrap'>🏆 {m.tA if m.winner=='A' else m.tB} WINS!</div>", unsafe_allow_html=True)
        lt = "B" if m.swapped else "A"; rt = "A" if m.swapped else "B"
        tn=lambda t:m.tA if t=="A" else m.tB; sc=lambda t:m.scA if t=="A" else m.scB; ss=lambda t:m.sA if t=="A" else m.sB
        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'><div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div><div class='score-num {'hot' if m.srv==lt else ''}'>{sc(lt)}</div><div class='tmeta'>Sets: {ss(lt)} · Left</div></div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'><div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div><div class='score-num {'hot' if m.srv==rt else ''}'>{sc(rt)}</div><div class='tmeta'>Sets: {ss(rt)} · Right</div></div>
          </div>
          <div style='text-align:center;color:#5a7090;font-size:10px;margin-top:8px'>SET {m.setno}/3 · TARGET {m.target} · FINAL CAP {MAX_SCORE_CAP}</div>
        </div>
        """, unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Serving", m.tA if m.srv=="A" else m.tB)
        with c2: st.metric("Server", current_server(m))
        with c3: st.metric("Target", m.target)
        with st.container(border=True):
            st.markdown("**Live Events**")
            for e in m.events[:12]:
                st.markdown(f"<div class='ev'>{e}</div>", unsafe_allow_html=True)
    elif st.session_state.tab == "stats":
        total = m.scA + m.scB + sum(m.psA) + sum(m.psB)
        c1,c2,c3,c4 = st.columns(4)
        for col,val,lbl in [(c1,f"Set {m.setno}","Set"),(c2,f"{m.sA}–{m.sB}","Sets"),(c3,f"{m.scA}–{m.scB}","Score"),(c4,total,"Total")]:
            with col: st.markdown(f"<div class='sbox'><div class='sbox-n'>{val}</div><div class='sbox-l'>{lbl}</div></div>", unsafe_allow_html=True)
        p1,p2 = st.columns(2)
        with p1:
            st.markdown(f"**{m.tA}**")
            for p,pts in sorted(m.ppA.items(), key=lambda x:-x[1]): st.write(f"{p}: {pts}")
        with p2:
            st.markdown(f"**{m.tB}**")
            for p,pts in sorted(m.ppB.items(), key=lambda x:-x[1]): st.write(f"{p}: {pts}")
    else:
        hist = [h for h in data.get("history", []) if h.get("id") == current_id]
        if not hist: st.info("No completed history for this match yet.")
        else:
            for h in reversed(hist):
                with st.container(border=True):
                    st.markdown(f"### {h['tA']} vs {h['tB']}")
                    st.caption(h["date"])
                    st.write(f"Sets: **{h['sA']}–{h['sB']}** · Winner: **{h['winner']}**")
    v1,v2,v3,v4 = st.columns(4)
    with v1:
        if st.button("🏸 Score", key="viewer_nav_score", use_container_width=True): st.session_state.tab="score"; st.rerun()
    with v2:
        if st.button("📊 Stats", key="viewer_nav_stats", use_container_width=True): st.session_state.tab="stats"; st.rerun()
    with v3:
        if st.button("📜 History", key="viewer_nav_history", use_container_width=True): st.session_state.tab="history"; st.rerun()
    with v4:
        if st.button("🔄 Refresh", key="viewer_nav_refresh", use_container_width=True): st.rerun()
    st.stop()

# admin
tab = st.session_state.tab
current_id = st.session_state.active_match_id
m = get_match(data, current_id) if current_id else None

if tab == "score" and current_id is None:
    st.markdown("<div style='font-family:Bebas Neue,sans-serif;font-size:28px;letter-spacing:2px;margin-bottom:12px'>CREATE NEW MATCH</div>", unsafe_allow_html=True)
    setup = st.session_state.setup
    with st.expander("🏆 Tournament (optional)"):
        tnm = st.text_input("Tournament Name", value=setup.get("tnm",""))
        trd = st.text_input("Round", value=setup.get("trd",""))
    c1,c2 = st.columns(2)
    with c1: tA = st.text_input("Team A", value=setup.get("tA",""))
    with c2: tB = st.text_input("Team B", value=setup.get("tB",""))
    st.markdown("### 👥 Enter All Players")
    ca,cb = st.columns(2)
    allA,allB=[],[]
    with ca:
        st.markdown(f"**{tA or 'Team A'}**")
        for i in range(ALL_PLAYERS): allA.append(st.text_input(f"Player {i+1}", value=setup["allA"][i], key=f"pA{i}"))
    with cb:
        st.markdown(f"**{tB or 'Team B'}**")
        for i in range(ALL_PLAYERS): allB.append(st.text_input(f"Player {i+1}", value=setup["allB"][i], key=f"pB{i}"))
    allA_f=[_safe(v,f"A{i+1}") for i,v in enumerate(allA)]
    allB_f=[_safe(v,f"B{i+1}") for i,v in enumerate(allB)]
    st.markdown("### ⭐ Select 5 Starters")
    s1,s2 = st.columns(2)
    with s1: mpA = st.multiselect(f"{tA or 'Team A'}", allA_f, default=allA_f[:PLAYERS], max_selections=PLAYERS, key="mpA")
    with s2: mpB = st.multiselect(f"{tB or 'Team B'}", allB_f, default=allB_f[:PLAYERS], max_selections=PLAYERS, key="mpB")
    errs=[]; oA2=[]; oB2=[]
    if len(mpA)==PLAYERS and len(mpB)==PLAYERS:
        st.markdown("### 🔁 Service Order")
        o1,o2 = st.columns(2); oAi=[]; oBi=[]
        with o1:
            for k in range(PLAYERS):
                opts=[f"{i+1}. {mpA[i]}" for i in range(PLAYERS)]
                sel=st.selectbox(f"Serve {k+1}", opts, index=setup["ordA"][k]-1, key=f"oA{k}")
                oAi.append(int(sel.split(".")[0]))
        with o2:
            for k in range(PLAYERS):
                opts=[f"{i+1}. {mpB[i]}" for i in range(PLAYERS)]
                sel=st.selectbox(f"Serve {k+1}", opts, index=setup["ordB"][k]-1, key=f"oB{k}")
                oBi.append(int(sel.split(".")[0]))
        if len(set(oAi)) != 5: errs.append("Team A service order must be unique")
        if len(set(oBi)) != 5: errs.append("Team B service order must be unique")
        oA2=_build_ord(list(mpA), oAi); oB2=_build_ord(list(mpB), oBi)
        if not oA2 or not oB2: errs.append("Invalid service order")
        fs_label = st.radio("First serve", [tA or "Team A", tB or "Team B"], horizontal=True)
        fs = "A" if fs_label == (tA or "Team A") else "B"
    else:
        fs="A"; errs.append("Select exactly 5 players per team")
    for e in errs: st.error(e)
    if st.button("▶️ START MATCH", use_container_width=True, disabled=bool(errs)):
        mid = datetime.now().strftime("%Y%m%d%H%M%S%f")
        nm = new_match(mid, _safe(tA,"Team A"), _safe(tB,"Team B"), allA_f, allB_f, list(mpA), list(mpB), oA2, oB2, fs, st.session_state.username or "admin", tnm or None, trd or None)
        save_match(data, nm)
        st.session_state.active_match_id = mid
        st.rerun()

elif tab == "score":
    if not m:
        st.info("Create or select a match.")
    else:
        if m.show_court_popup and m.first_court_popup_point:
            first_team_name = m.tA if m.first_court_popup_team == "A" else m.tB
            st.markdown(f"<div class='court-alert'>🔄 Court change at {m.first_court_popup_point} — first reached by {first_team_name}</div>", unsafe_allow_html=True)
        if m.over:
            st.markdown(f"<div class='winner-wrap'>🏆 {m.tA if m.winner=='A' else m.tB} WINS THE MATCH!</div>", unsafe_allow_html=True)
        lt="B" if m.swapped else "A"; rt="A" if m.swapped else "B"
        tn=lambda t:m.tA if t=="A" else m.tB; sc=lambda t:m.scA if t=="A" else m.scB; ss=lambda t:m.sA if t=="A" else m.sB
        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'><div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div><div class='score-num {'hot' if m.srv==lt else ''}'>{sc(lt)}</div><div class='tmeta'>Sets: {ss(lt)} · Left</div></div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'><div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div><div class='score-num {'hot' if m.srv==rt else ''}'>{sc(rt)}</div><div class='tmeta'>Sets: {ss(rt)} · Right</div></div>
          </div>
          <div style='text-align:center;color:#5a7090;font-size:10px;margin-top:8px'>SET {m.setno}/3 · TARGET {m.target} · FINAL CAP {MAX_SCORE_CAP}</div>
        </div>
        """, unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Serving", m.tA if m.srv=="A" else m.tB)
        with c2: st.metric("Server", current_server(m))
        with c3: st.metric("Target", m.target)
        with c4: st.metric("Match", m.id[-4:])
        pb1,pb2 = st.columns(2)
        with pb1:
            st.markdown("<div class='pbig'>", unsafe_allow_html=True)
            if st.button(f"＋ {m.tA}", key="ptA", use_container_width=True, disabled=(m.over or m.scA>=MAX_SCORE_CAP)):
                do_point(data, current_id, "A"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with pb2:
            st.markdown("<div class='pbig pbig-b'>", unsafe_allow_html=True)
            if st.button(f"＋ {m.tB}", key="ptB", use_container_width=True, disabled=(m.over or m.scB>=MAX_SCORE_CAP)):
                do_point(data, current_id, "B"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        r1 = st.columns(4)
        with r1[0]:
            if st.button("🔄 Court", use_container_width=True): do_court(data, current_id); st.rerun()
        with r1[1]:
            if st.button("↩️ Undo", use_container_width=True, disabled=not m.history): do_undo(data, current_id); st.rerun()
        with r1[2]:
            if st.button("⚙️ Score Adjust", use_container_width=True):
                st.session_state.show_score_adjust = not st.session_state.show_score_adjust; st.rerun()
        with r1[3]:
            if st.button("🔁 Subs / Timeout", use_container_width=True):
                st.session_state.show_subs_panel = not st.session_state.show_subs_panel; st.rerun()
        if st.session_state.show_score_adjust:
            with st.container(border=True):
                st.markdown("### Manual Score Adjust")
                a1,a2 = st.columns(2)
                with a1:
                    new_a = st.number_input(f"{m.tA} Score", min_value=0, max_value=MAX_SCORE_CAP, value=int(m.scA), step=1, key="adjA")
                    if st.button(f"Set {m.tA}", key="setA", use_container_width=True): admin_adjust_score(data, current_id, "A", new_a); st.rerun()
                with a2:
                    new_b = st.number_input(f"{m.tB} Score", min_value=0, max_value=MAX_SCORE_CAP, value=int(m.scB), step=1, key="adjB")
                    if st.button(f"Set {m.tB}", key="setB", use_container_width=True): admin_adjust_score(data, current_id, "B", new_b); st.rerun()
        if st.session_state.show_subs_panel:
            with st.container(border=True):
                st.markdown("### Substitutions & Timeouts")
                sc1,sc2 = st.columns(2)
                fm = get_match(data_load(), current_id) or m
                for team,col in [("A",sc1),("B",sc2)]:
                    tname = fm.tA if team=="A" else fm.tB
                    subs = fm.subA if team=="A" else fm.subB
                    tos = fm.toA if team=="A" else fm.toB
                    p_on = fm.onA if team=="A" else fm.onB
                    all_p = fm.allA if team=="A" else fm.allB
                    with col:
                        st.markdown(f"**{tname}** <span class='badge {'b-g' if subs>0 else 'b-r'}'>Subs {subs}</span> <span class='badge {'b-b' if tos>0 else 'b-r'}'>T/O {tos}</span>", unsafe_allow_html=True)
                        bench = [p for p in all_p if p and p not in p_on]
                        if subs > 0 and bench:
                            on_p = st.selectbox("In", bench, key=f"in_{team}")
                            off_p = st.selectbox("Out", p_on, key=f"out_{team}")
                            if st.button(f"Sub {tname}", key=f"sub_{team}", use_container_width=True): do_sub(data, current_id, team, on_p, off_p); st.rerun()
                        if tos > 0:
                            if st.button(f"Timeout {tname}", key=f"to_{team}", use_container_width=True): do_timeout(data, current_id, team); st.rerun()
        with st.container(border=True):
            st.markdown("**Live Events**")
            for e in m.events[:16]: st.markdown(f"<div class='ev'>{e}</div>", unsafe_allow_html=True)

elif tab == "stats":
    if not m: st.info("Select a match.")
    else:
        total = m.scA + m.scB + sum(m.psA) + sum(m.psB)
        c1,c2,c3,c4 = st.columns(4)
        for col,val,lbl in [(c1,f"Set {m.setno}","Set"),(c2,f"{m.sA}–{m.sB}","Sets"),(c3,f"{m.scA}–{m.scB}","Score"),(c4,total,"Total Pts")]:
            with col: st.markdown(f"<div class='sbox'><div class='sbox-n'>{val}</div><div class='sbox-l'>{lbl}</div></div>", unsafe_allow_html=True)
        p1,p2 = st.columns(2)
        with p1:
            st.markdown(f"**{m.tA}**")
            for p,pts in sorted(m.ppA.items(), key=lambda x:-x[1]): st.write(f"{p}: {pts}")
        with p2:
            st.markdown(f"**{m.tB}**")
            for p,pts in sorted(m.ppB.items(), key=lambda x:-x[1]): st.write(f"{p}: {pts}")

elif tab == "history":
    hist = data.get("history", [])
    if not hist: st.info("No completed matches yet.")
    else:
        for h in reversed(hist):
            with st.container(border=True):
                st.markdown(f"### {h['tA']} vs {h['tB']}")
                st.caption(h["date"])
                st.write(f"Sets: **{h['sA']}–{h['sB']}** · Winner: **{h['winner']}**")

elif tab == "tournament":
    st.markdown("## Tournament")
    with st.container(border=True):
        tn2 = st.text_input("Tournament Name", key="tn2")
        ntm = st.selectbox("Teams", [4,8,16], key="ntm")
        cols = st.columns(2); tnames=[]
        for i in range(ntm):
            with cols[i%2]: tnames.append(st.text_input(f"Team {i+1}", key=f"brt{i}"))
        if st.button("🎯 Generate Bracket", use_container_width=True):
            import random
            names = [_safe(t, f"Team {i+1}") for i,t in enumerate(tnames)]
            random.shuffle(names)
            data["tournament"] = [{"r":"Round 1","tA":names[i],"tB":names[i+1],"w":None} for i in range(0, len(names)-1, 2)]
            data["t_info"] = {"name": tn2, "teams": names}
            data_save(data)
            st.rerun()
    if data.get("tournament"):
        st.markdown(f"### 🎯 {data.get('t_info',{}).get('name','Tournament')}")
        for i, mb in enumerate(data["tournament"]):
            with st.container(border=True):
                c1,c2,c3 = st.columns([2,.4,2])
                with c1: st.write(f"**{mb['tA']}**")
                with c2: st.write("vs")
                with c3: st.write(f"**{mb['tB']}**")
                if not mb["w"]:
                    w = st.radio("Winner", [mb["tA"], mb["tB"]], key=f"bw{i}", horizontal=True)
                    if st.button("✅ Confirm", key=f"bc{i}"): data["tournament"][i]["w"] = w; data_save(data); st.rerun()
                else: st.markdown(f"<span class='badge b-gold'>🏆 {mb['w']}</span>", unsafe_allow_html=True)

elif tab == "users":
    st.markdown("## Users")
    users = users_load()
    st.markdown("### Registered Users")
    if not users: st.info("No users registered yet.")
    else:
        st.write(f"**{len(users)} user(s)**")
        for uname,ud in users.items():
            with st.container(border=True):
                c1,c2,c3 = st.columns([2,2,1])
                with c1:
                    st.markdown(f"**{ud.get('name','—')}**")
                    st.caption(f"@{uname}")
                with c2:
                    st.write(ud.get("contact","—"))
                    role_label = "Admin" if ud.get("is_admin") else "Viewer"
                    st.caption(f"{role_label} · Joined: {ud.get('created','—')}")
                with c3:
                    st.write("Admin add" if ud.get("created_by_admin") else "Self")
    st.markdown("---")
    st.markdown("### ➕ Add User Manually")
    with st.container(border=True):
        mn = st.text_input("Name", key="mu_n")
        mc = st.text_input("Mobile/Email", key="mu_c")
        muu = st.text_input("Username", key="mu_u")
        mp = st.text_input("Password", type="password", key="mu_p")
        is_admin_new = st.checkbox("Give Admin Access", key="mu_admin")
        if st.button("✅ Add User", use_container_width=True, key="mu_btn"):
            ok,msg = user_register(mn,mc,muu,mp,created_by_admin=True,is_admin=is_admin_new)
            (st.success if ok else st.error)(msg)

elif tab == "admin":
    st.markdown("## Admin Panel")
    with st.container(border=True):
        st.write(f"**Registered users:** {len(users_load())}")
        st.write(f"**Matches played:** {len(data.get('history',[]))}")
        st.write(f"**Live matches now:** {len(data.get('matches',{}))}")
        st.write(f"**Storage:** {'Supabase with JSON fallback' if using_supabase() else 'JSON only'}")
        if m:
            st.write(f"**Selected match:** {m.tA} vs {m.tB}")
            if st.button("🗑️ Delete Selected Match", use_container_width=True):
                delete_match(data, m.id)
                st.session_state.active_match_id = next(iter(data_load().get("matches", {}).keys()), None)
                st.rerun()
