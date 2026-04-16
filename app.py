
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

ROOT_ADMIN_USER = "Ballbadminton"
ROOT_ADMIN_PASS = "partha@2025"

SET_POINTS = 35
PLAYERS = 5
ALL_PLAYERS = 10
COURT_CHG = [9, 18, 27]
MAX_SCORE_CAP = 39

DATA_FILE = "bb_multimatch_data.json"
USERS_FILE = "bb_multimatch_users.json"

st.set_page_config(page_title="🏸 Ball Badminton Live", page_icon="🏸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton, section[data-testid="stSidebar"], [data-testid="stSidebarNav"] {display:none!important;}
:root{--bg:#07101f;--surf:#0d1a2e;--card:#112038;--bdr:rgba(255,255,255,.07);--acc:#f97316;--acc2:#c2410c;--blue:#3b82f6;--txt:#f0f4f8;--muted:#5a7090;}
html,body,.stApp{background:var(--bg)!important;color:var(--txt)!important;}
.block-container{max-width:100%!important;padding:.45rem .55rem 5rem!important;}
.stButton>button{background:linear-gradient(135deg,var(--acc),var(--acc2))!important;color:#fff!important;border:none!important;font-weight:800!important;border-radius:12px!important;width:100%!important;padding:.65rem .8rem!important;}
.stTextInput input,.stSelectbox>div>div,.stMultiSelect>div>div,.stNumberInput input{background:var(--card)!important;color:var(--txt)!important;border:1px solid var(--bdr)!important;border-radius:10px!important;}
[data-testid="stContainer"]{background:var(--card)!important;border:1px solid var(--bdr)!important;border-radius:14px!important;padding:12px!important;}
.scoreboard{background:linear-gradient(135deg,var(--surf),var(--card));border:1px solid rgba(249,115,22,.15);border-radius:18px;padding:16px 14px 14px;position:relative;overflow:hidden;}
.scoreboard::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--acc),#f59e0b,var(--acc));}
.score-num{font-size:84px;line-height:1;font-weight:900;color:#fff;}
.score-num.hot{color:var(--acc);}
.tname{font-size:17px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.tmeta{font-size:12px;color:var(--muted);}
.alert{background:rgba(249,115,22,.10);border:1px solid rgba(249,115,22,.3);border-radius:12px;padding:10px;font-weight:800;color:#fdba74;margin-bottom:8px;}
.win{background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:14px;padding:12px;text-align:center;font-weight:900;margin-bottom:8px;}
.ev{font-size:11px;padding:5px 4px;border-bottom:1px solid var(--bdr);color:var(--muted);}
.ev:first-child{color:#fff;font-weight:700;}
.big .stButton>button{padding:1rem .7rem!important;font-size:18px!important;}
.blue .stButton>button{background:linear-gradient(135deg,#3b82f6,#1d4ed8)!important;}
.small .stButton>button{padding:.42rem .5rem!important;font-size:12px!important;}
.box{background:#0d1a2e;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:10px;text-align:center;}
.n{font-size:28px;font-weight:900;color:#f97316;}
.l{font-size:10px;color:#5a7090;text-transform:uppercase;}
@media(max-width:768px){
 .block-container{padding:.35rem .4rem 5rem!important;}
 .score-num{font-size:64px!important;}
 .tname{font-size:14px!important;}
 .big .stButton>button{font-size:16px!important;padding:.85rem .65rem!important;}
 .small .stButton>button{font-size:11px!important;padding:.38rem .42rem!important;}
}
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

def now_str() -> str:
    return datetime.now().strftime("%d %b %Y %H:%M:%S")

def now_short() -> str:
    return datetime.now().strftime("%d %b %Y %H:%M")

def _hash(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()

def _safe(v: str, fb: str) -> str:
    v = (v or "").strip()
    return v if v else fb

def _nxt(i: int, n: int) -> int:
    return (i + 1) % n

def _build_ord(p5: List[str], idxs: List[int]) -> List[str]:
    out = []
    for idx in idxs:
        if not (1 <= idx <= len(p5)):
            return []
        out.append(p5[idx - 1])
    return out

def _new_match_id(admin_user: str) -> str:
    return f"{admin_user}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ---------- USERS ----------
def users_load() -> dict:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("viewers").select("*").execute()
            out = {}
            for row in (res.data or []):
                out[row["username"]] = {
                    "name": row.get("name", ""),
                    "contact": row.get("contact", ""),
                    "pw_hash": row.get("pw_hash", ""),
                    "created": row.get("created_at", ""),
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
                    "name": u.get("name", ""),
                    "contact": u.get("contact", ""),
                    "pw_hash": u.get("pw_hash", ""),
                    "created_at": u.get("created", ""),
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

def user_register(name: str, contact: str, username: str, password: str, created_by_admin=False, is_admin=False) -> Tuple[bool, str]:
    users = users_load()
    uname = (username or "").strip().lower()
    if not uname or not name or not contact or not password:
        return False, "All fields are required"
    if len(password) < 6:
        return False, "Password min 6 chars"
    if uname in users or uname == ROOT_ADMIN_USER.lower():
        return False, "Username already exists"
    users[uname] = {
        "name": name.strip(),
        "contact": contact.strip(),
        "pw_hash": _hash(password),
        "created": now_short(),
        "created_by_admin": created_by_admin,
        "is_admin": is_admin,
    }
    users_save(users)
    return True, f"Created user {uname}"

def user_login(username: str, password: str):
    uname = (username or "").strip().lower()
    if uname == ROOT_ADMIN_USER.lower() and password == ROOT_ADMIN_PASS:
        return True, "OK", {"name": "Root Admin", "is_admin": True, "root": True}
    users = users_load()
    if uname not in users:
        return False, "Username not found", {}
    u = users[uname]
    if u["pw_hash"] != _hash(password):
        return False, "Wrong password", {}
    return True, "OK", u

# ---------- DATA ----------
def data_default() -> dict:
    return {"matches": {}, "history": [], "updated_at": ""}

def data_load() -> dict:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("matches").select("*").eq("id", "app_state").execute()
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
    data["updated_at"] = now_str()
    sb = get_supabase()
    if sb:
        try:
            sb.table("matches").upsert({"id": "app_state", "data": data, "updated_at": datetime.now().isoformat()}).execute()
            return
        except Exception:
            pass
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

# ---------- MATCH ----------
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
    updated_at: Optional[str]

def _restore(d):
    if not d:
        return None
    dd = dict(d)
    dd.setdefault("first_court_popup_point", None)
    dd.setdefault("first_court_popup_team", None)
    dd.setdefault("show_court_popup", False)
    return Match(**dd)

def _snap(m: Match):
    d = asdict(m)
    d["history"] = []
    return d

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

def new_match(mid, created_by, tA, tB, allA, allB, pA, pB, oA, oB, first, tnm=None, trd=None):
    cA, cB, nA, nB = (oA[0], None, 1, 0) if first == "A" else (None, oB[0], 0, 1)
    return Match(
        id=mid, created_by=created_by, tA=tA, tB=tB, allA=allA, allB=allB, onA=pA, onB=pB, ordA=oA, ordB=oB,
        setno=1, sA=0, sB=0, scA=0, scB=0, srv=first, swapped=False, curA=cA, curB=cB, nxtA=nA, nxtB=nB,
        subA=3, subB=3, toA=1, toB=1, ms={9: False, 18: False, 27: False},
        first_court_popup_point=None, first_court_popup_team=None, show_court_popup=False,
        history=[], events=[f"Match started · {tA if first == 'A' else tB} serves first"],
        over=False, winner=None, psA=[], psB=[], ppA={p:0 for p in pA}, ppB={p:0 for p in pB},
        started=now_short(), ended=None, tnm=tnm, trd=trd, target=35, updated_at=now_str()
    )

def save_match(m: Match, data: dict):
    data["matches"][m.id] = asdict(m)
    data_save(data)

def delete_match(match_id: str, data: dict):
    data["matches"].pop(match_id, None)
    data_save(data)

def list_matches(data: dict) -> List[Match]:
    items = []
    for _, raw in (data.get("matches") or {}).items():
        try:
            items.append(_restore(raw))
        except Exception:
            pass
    items.sort(key=lambda x: x.updated_at or "", reverse=True)
    return items

def do_point(m: Match, winner: str, data: dict) -> Match:
    if m.over:
        return m
    m.history.append(_snap(m))
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
            m.nxtA = _nxt(m.nxtA, PLAYERS)
        else:
            m.curB = m.ordB[m.nxtB]
            m.nxtB = _nxt(m.nxtB, PLAYERS)

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
        watched = m.scA if m.first_court_popup_team == "A" else m.scB
        if watched != m.first_court_popup_point:
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
            m.scA = 0
            m.scB = 0
            m.subA = 3
            m.subB = 3
            m.toA = 1
            m.toB = 1
            m.ms = {9: False, 18: False, 27: False}
            m.first_court_popup_point = None
            m.first_court_popup_team = None
            m.show_court_popup = False
            m.target = 35
            m.events.insert(0, f"▶️ Set {m.setno} begins")

    if m.over and not m.ended:
        m.ended = now_short()
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
            "player_points_A": dict(m.ppA),
            "player_points_B": dict(m.ppB),
            "created_by": m.created_by,
            "last_set_points": f"{m.psA[-1]}-{m.psB[-1]}" if m.psA and m.psB else None,
        })

    m.updated_at = now_str()
    save_match(m, data)
    return m

def do_undo(m: Match, data: dict) -> Match:
    if m.history:
        prev = m.history.pop()
        m = _restore(prev)
        save_match(m, data)
    return m

def do_court(m: Match, data: dict) -> Match:
    m.swapped = not m.swapped
    m.first_court_popup_point = None
    m.first_court_popup_team = None
    m.show_court_popup = False
    m.updated_at = now_str()
    save_match(m, data)
    return m

def do_timeout(m: Match, team: str, data: dict) -> Match:
    if team == "A" and m.toA > 0:
        m.toA -= 1
    if team == "B" and m.toB > 0:
        m.toB -= 1
    m.updated_at = now_str()
    save_match(m, data)
    return m

def do_sub(m: Match, team: str, on: str, off: str, data: dict) -> Match:
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

# ---------- SESSION ----------
for k, v in [
    ("role", None), ("username", ""), ("user_name", ""), ("tab", "score"),
    ("selected_match_id", None), ("show_score_adjust", False), ("show_subs_panel", False)
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- LOGIN ----------
if st.session_state.role is None:
    st.markdown("## Ball Badminton Live")
    t1, t2, t3 = st.tabs(["🔑 Viewer Login", "📝 Register", "🔐 Admin"])
    with t1:
        vu = st.text_input("Username", key="vu")
        vp = st.text_input("Password", type="password", key="vp")
        if st.button("Open Live Score", use_container_width=True):
            ok, msg, u = user_login(vu, vp)
            if ok and not u.get("is_admin", False) and not u.get("root", False):
                st.session_state.role = "viewer"
                st.session_state.username = (vu or "").strip().lower()
                st.session_state.user_name = u.get("name", "Viewer")
                st.rerun()
            elif ok:
                st.error("This account has admin access. Use Admin tab.")
            else:
                st.error(msg)
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
                ok, msg = user_register(rn, rc, ru, rp, created_by_admin=False, is_admin=False)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    with t3:
        au = st.text_input("Admin Username", key="au")
        ap = st.text_input("Admin Password", type="password", key="ap")
        if st.button("Admin Login", use_container_width=True):
            ok, msg, u = user_login(au, ap)
            if ok and (u.get("is_admin", False) or u.get("root", False)):
                st.session_state.role = "admin"
                st.session_state.username = (au or "").strip().lower()
                st.session_state.user_name = u.get("name", "Admin")
                st.rerun()
            elif ok:
                st.error("This account is viewer only")
            else:
                st.error(msg)
    st.stop()

data = data_load()
matches = list_matches(data)

# ---------- VIEWER ----------
if st.session_state.role == "viewer":
    st_autorefresh(interval=2500, key="viewer_refresh")
    st.markdown("## Viewer")
    if matches:
        options = {f"{m.tA} vs {m.tB} · {m.tnm or 'Live'} · {m.id}": m.id for m in matches}
        labels = list(options.keys())
        current = st.session_state.selected_match_id
        idx = 0
        for i, lbl in enumerate(labels):
            if options[lbl] == current:
                idx = i
                break
        picked = st.selectbox("Choose Match", labels, index=idx)
        st.session_state.selected_match_id = options[picked]
        m = _restore(data["matches"][st.session_state.selected_match_id])

        if m.show_court_popup and m.first_court_popup_point:
            team_name = m.tA if m.first_court_popup_team == "A" else m.tB
            st.markdown(f"<div class='alert'>🔄 Court change at {m.first_court_popup_point} · first reached by {team_name}</div>", unsafe_allow_html=True)
        if m.over:
            st.markdown(f"<div class='win'>🏆 {m.tA if m.winner=='A' else m.tB} WINS</div>", unsafe_allow_html=True)

        lt = "B" if m.swapped else "A"
        rt = "A" if m.swapped else "B"
        tn = lambda t: m.tA if t == "A" else m.tB
        sc = lambda t: m.scA if t == "A" else m.scB
        ss = lambda t: m.sA if t == "A" else m.sB
        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'>
              <div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div>
              <div class='score-num {'hot' if m.srv==lt else ''}'>{sc(lt)}</div>
              <div class='tmeta'>Sets: {ss(lt)} · Left</div>
            </div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'>
              <div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div>
              <div class='score-num {'hot' if m.srv==rt else ''}'>{sc(rt)}</div>
              <div class='tmeta'>Sets: {ss(rt)} · Right</div>
            </div>
          </div>
          <div style='text-align:center;color:#5a7090;font-size:10px;margin-top:8px'>SET {m.setno}/3 · TARGET {m.target} · FINAL CAP {MAX_SCORE_CAP}</div>
        </div>
        """, unsafe_allow_html=True)

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("🏸 Score", use_container_width=True):
                st.session_state.tab = "score"
        with b2:
            if st.button("📊 Stats", use_container_width=True):
                st.session_state.tab = "stats"
        with b3:
            if st.button("📜 History", use_container_width=True):
                st.session_state.tab = "history"

        if st.session_state.tab == "stats":
            p1, p2 = st.columns(2)
            with p1:
                st.markdown(f"### {m.tA} Player Points")
                for p, pts in sorted(m.ppA.items(), key=lambda x: -x[1]):
                    st.write(f"{p}: {pts}")
            with p2:
                st.markdown(f"### {m.tB} Player Points")
                for p, pts in sorted(m.ppB.items(), key=lambda x: -x[1]):
                    st.write(f"{p}: {pts}")
        elif st.session_state.tab == "history":
            hist = [h for h in data.get("history", []) if h.get("id") == m.id]
            if hist:
                for h in reversed(hist):
                    with st.container(border=True):
                        st.markdown(f"### {h['tA']} vs {h['tB']}")
                        st.caption(h["date"])
                        st.write(f"Winner: **{h['winner']}**")
                        st.write(f"Sets: **{h['sA']}–{h['sB']}**")
                        if h.get("set_scores"):
                            st.write(f"Set-wise points: {h['set_scores']}")
                        st.write(f"Last set points: {h.get('last_set_points')}")
                        st.write("Player Points A:", h.get("player_points_A", {}))
                        st.write("Player Points B:", h.get("player_points_B", {}))
            else:
                st.info("No completed history for this match yet.")
    else:
        st.info("No live matches currently.")
    st.stop()

# ---------- ADMIN ----------
nav_items = [("score", "🏸 Score"), ("stats", "📊 Stats"), ("history", "📜 History"), ("users", "👥 Users"), ("admin", "⚙️ Admin")]
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
        st.rerun()

st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:4px 0 8px'>", unsafe_allow_html=True)
tab = st.session_state.tab

admin_matches = [m for m in matches if m.created_by == st.session_state.username or st.session_state.username == ROOT_ADMIN_USER.lower()]
with st.container(border=True):
    st.markdown("### Select Match")
    if admin_matches:
        opts = {"<Create New Match>": None}
        for m in admin_matches:
            opts[f"{m.tA} vs {m.tB} · {m.id}"] = m.id
        labels = list(opts.keys())
        idx = 0
        current = st.session_state.selected_match_id
        for i, lbl in enumerate(labels):
            if opts[lbl] == current:
                idx = i
                break
        picked = st.selectbox("Your Matches", labels, index=idx)
        st.session_state.selected_match_id = opts[picked]
    else:
        st.info("No match created yet. Create a new match below.")
        st.session_state.selected_match_id = None

selected_match = None
if st.session_state.selected_match_id and st.session_state.selected_match_id in data.get("matches", {}):
    selected_match = _restore(data["matches"][st.session_state.selected_match_id])

if tab == "score":
    if selected_match is None:
        st.markdown("## Create New Match")
        c1, c2 = st.columns(2)
        with c1:
            tnm = st.text_input("Tournament Name")
        with c2:
            trd = st.text_input("Round")
        c3, c4 = st.columns(2)
        with c3:
            tA = st.text_input("Team A")
        with c4:
            tB = st.text_input("Team B")

        st.markdown("### Enter All Players")
        ca, cb = st.columns(2)
        allA, allB = [], []
        with ca:
            st.markdown(f"**{tA or 'Team A'}**")
            for i in range(ALL_PLAYERS):
                allA.append(st.text_input(f"A Player {i+1}", key=f"A{i}"))
        with cb:
            st.markdown(f"**{tB or 'Team B'}**")
            for i in range(ALL_PLAYERS):
                allB.append(st.text_input(f"B Player {i+1}", key=f"B{i}"))

        allA_f = [_safe(v, f"A{i+1}") for i, v in enumerate(allA)]
        allB_f = [_safe(v, f"B{i+1}") for i, v in enumerate(allB)]

        st.markdown("### Select 5 Starters")
        s1, s2 = st.columns(2)
        with s1:
            mpA = st.multiselect("Team A Starters", allA_f, default=allA_f[:PLAYERS], max_selections=PLAYERS, key="mpA")
        with s2:
            mpB = st.multiselect("Team B Starters", allB_f, default=allB_f[:PLAYERS], max_selections=PLAYERS, key="mpB")

        errs = []
        oA2, oB2 = [], []
        oAi, oBi = [], []
        if len(mpA) == PLAYERS and len(mpB) == PLAYERS:
            o1, o2 = st.columns(2)
            with o1:
                for k in range(PLAYERS):
                    opts = [f"{i+1}. {mpA[i]}" for i in range(PLAYERS)]
                    sel = st.selectbox(f"A Serve {k+1}", opts, key=f"oA{k}")
                    oAi.append(int(sel.split(".")[0]))
            with o2:
                for k in range(PLAYERS):
                    opts = [f"{i+1}. {mpB[i]}" for i in range(PLAYERS)]
                    sel = st.selectbox(f"B Serve {k+1}", opts, key=f"oB{k}")
                    oBi.append(int(sel.split(".")[0]))
            if len(set(oAi)) != 5:
                errs.append("Team A service order must be unique")
            if len(set(oBi)) != 5:
                errs.append("Team B service order must be unique")
            oA2 = _build_ord(list(mpA), oAi)
            oB2 = _build_ord(list(mpB), oBi)
            if not oA2 or not oB2:
                errs.append("Invalid service order")
            fs_label = st.radio("First Serve", [tA or "Team A", tB or "Team B"], horizontal=True)
            first_side = "A" if fs_label == (tA or "Team A") else "B"
        else:
            first_side = "A"
            errs.append("Select exactly 5 starters per team")

        for e in errs:
            st.error(e)

        if st.button("▶️ START MATCH", use_container_width=True, disabled=bool(errs)):
            mid = _new_match_id(st.session_state.username)
            m = new_match(
                mid,
                st.session_state.username,
                _safe(tA, "Team A"),
                _safe(tB, "Team B"),
                allA_f,
                allB_f,
                list(mpA),
                list(mpB),
                oA2,
                oB2,
                first_side,
                tnm or None,
                trd or None,
            )
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

        lt = "B" if m.swapped else "A"
        rt = "A" if m.swapped else "B"
        tn = lambda t: m.tA if t == "A" else m.tB
        sc = lambda t: m.scA if t == "A" else m.scB
        ss = lambda t: m.sA if t == "A" else m.sB

        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'>
              <div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div>
              <div class='score-num {'hot' if m.srv==lt else ''}'>{sc(lt)}</div>
              <div class='tmeta'>Sets: {ss(lt)} · Left</div>
            </div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'>
              <div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div>
              <div class='score-num {'hot' if m.srv==rt else ''}'>{sc(rt)}</div>
              <div class='tmeta'>Sets: {ss(rt)} · Right</div>
            </div>
          </div>
          <div style='text-align:center;color:#5a7090;font-size:10px;margin-top:8px'>SET {m.setno}/3 · TARGET {m.target} · FINAL CAP {MAX_SCORE_CAP}</div>
        </div>
        """, unsafe_allow_html=True)

        p1, p2 = st.columns(2)
        with p1:
            st.markdown("<div class='big'>", unsafe_allow_html=True)
            if st.button(f"＋ {m.tA}", use_container_width=True, disabled=(m.over or m.scA >= MAX_SCORE_CAP)):
                do_point(m, "A", data)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with p2:
            st.markdown("<div class='big blue'>", unsafe_allow_html=True)
            if st.button(f"＋ {m.tB}", key="ptB", use_container_width=True, disabled=(m.over or m.scB >= MAX_SCORE_CAP)):
                do_point(m, "B", data)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='small'>", unsafe_allow_html=True)
        r1 = st.columns(5)
        with r1[0]:
            if st.button("🔄 Court", use_container_width=True):
                do_court(m, data); st.rerun()
        with r1[1]:
            if st.button("↩️ Undo", use_container_width=True, disabled=not m.history):
                do_undo(m, data); st.rerun()
        with r1[2]:
            if st.button("⚙️ Score", use_container_width=True):
                st.session_state.show_score_adjust = not st.session_state.show_score_adjust
                st.rerun()
        with r1[3]:
            if st.button("🔁 Subs", use_container_width=True):
                st.session_state.show_subs_panel = not st.session_state.show_subs_panel
                st.rerun()
        with r1[4]:
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
                        m.scA = int(new_a)
                        maybe_update_target(m)
                        save_match(m, data)
                        st.rerun()
                with a2:
                    new_b = st.number_input(f"{m.tB} Score", min_value=0, max_value=MAX_SCORE_CAP, value=int(m.scB), step=1)
                    if st.button(f"Set {m.tB}", use_container_width=True):
                        m.scB = int(new_b)
                        maybe_update_target(m)
                        save_match(m, data)
                        st.rerun()

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
                        bench = [p for p in all_p if p and p not in on_court]
                        if subs > 0 and bench:
                            on_p = st.selectbox("In", bench, key=f"in_{team}")
                            off_p = st.selectbox("Out", on_court, key=f"out_{team}")
                            if st.button(f"Sub {tname}", key=f"sub_{team}", use_container_width=True):
                                do_sub(m, team, on_p, off_p, data)
                                st.rerun()
                        if tos > 0:
                            if st.button(f"Timeout {tname}", key=f"to_{team}", use_container_width=True):
                                do_timeout(m, team, data)
                                st.rerun()

        with st.container(border=True):
            st.markdown("**Live Events**")
            for e in m.events[:16]:
                st.markdown(f"<div class='ev'>{e}</div>", unsafe_allow_html=True)

elif tab == "stats":
    if selected_match is None:
        st.info("Select a match first.")
    else:
        m = selected_match
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### {m.tA} Player Points")
            for p, pts in sorted(m.ppA.items(), key=lambda x: -x[1]):
                st.write(f"{p}: {pts}")
        with c2:
            st.markdown(f"### {m.tB} Player Points")
            for p, pts in sorted(m.ppB.items(), key=lambda x: -x[1]):
                st.write(f"{p}: {pts}")

elif tab == "history":
    st.markdown("## Match History")
    if not data.get("history"):
        st.info("No completed matches yet.")
    else:
        for h in reversed(data["history"]):
            with st.container(border=True):
                st.markdown(f"### {h['tA']} vs {h['tB']}")
                st.caption(f"{h['date']} · Created by {h.get('created_by', '-')}")
                st.write(f"Winner: **{h['winner']}**")
                st.write(f"Sets: **{h['sA']}–{h['sB']}**")
                st.write(f"Set-wise points: {h.get('set_scores')}")
                st.write(f"Last set points: {h.get('last_set_points')}")
                st.write("Player Points A:", h.get("player_points_A", {}))
                st.write("Player Points B:", h.get("player_points_B", {}))

elif tab == "users":
    st.markdown("## Users")
    users = users_load()
    if users:
        for uname, u in users.items():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    st.markdown(f"**{u.get('name', '—')}**")
                    st.caption(f"@{uname}")
                with c2:
                    st.write(u.get("contact", "—"))
                    st.caption(f"Joined: {u.get('created', '—')}")
                with c3:
                    st.write("Admin" if u.get("is_admin") else "Viewer")
    st.markdown("---")
    st.markdown("### Add User")
    with st.container(border=True):
        n = st.text_input("Name", key="add_n")
        c = st.text_input("Contact", key="add_c")
        u = st.text_input("Username", key="add_u")
        p = st.text_input("Password", type="password", key="add_p")
        is_admin = st.checkbox("Give Admin Access")
        if st.button("Create User", use_container_width=True):
            ok, msg = user_register(n, c, u, p, created_by_admin=True, is_admin=is_admin)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

elif tab == "admin":
    st.markdown("## Admin Overview")
    all_live = list_matches(data)
    st.write(f"**Total live matches:** {len(all_live)}")
    st.write(f"**Total completed matches:** {len(data.get('history', []))}")
    if all_live:
        for m in all_live:
            with st.container(border=True):
                st.write(f"**{m.tA} vs {m.tB}**")
                st.write(f"Created by: {m.created_by}")
                st.write(f"Score: {m.scA}–{m.scB} · Sets {m.sA}–{m.sB}")
                st.write(f"Updated: {m.updated_at}")
