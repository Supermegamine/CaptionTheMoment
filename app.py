import os
import io
from uuid import uuid4
from pathlib import Path
import uuid
from typing import List, Dict, Optional

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client

# Page config must come after importing streamlit
st.set_page_config(page_title="Caption The Moment", layout="wide")

# ── Custom CSS to match the screenshot design ──────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;700;900&family=Nunito:wght@400;600;700;800&display=swap');

/* ── Root palette ── */
:root {
  --bg-gradient: linear-gradient(135deg, #4a1a7a 0%, #7b2d9e 40%, #c0367a 100%);
  --panel-bg: rgba(60, 20, 100, 0.7);
  --panel-border: rgba(180, 100, 255, 0.3);
  --accent-cyan: #00e5ff;
  --accent-green: #4cff72;
  --accent-purple: #b64bff;
  --accent-pink: #ff4bae;
  --text-primary: #ffffff;
  --text-secondary: rgba(255,255,255,0.7);
  --card-bg: rgba(255, 255, 255, 0.08);
  --card-hover: rgba(255, 255, 255, 0.14);
  --winner-gold: #ffd700;
}

/* ── Global reset & background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  background: var(--bg-gradient) !important;
  background-attachment: fixed !important;
  font-family: 'Nunito', sans-serif !important;
  color: var(--text-primary) !important;
}

/* Noise texture overlay */
[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
}

/* ── Main title ── */
h1 {
  font-family: 'Exo 2', sans-serif !important;
  font-weight: 900 !important;
  font-size: 3rem !important;
  text-align: center !important;
  letter-spacing: 3px !important;
  text-transform: uppercase !important;
  background: linear-gradient(90deg, #ffffff 0%, var(--accent-cyan) 50%, #ffffff 100%) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  margin-bottom: 0.2rem !important;
  text-shadow: none !important;
}

/* ── Section headers ── */
h2, h3 {
  font-family: 'Exo 2', sans-serif !important;
  font-weight: 800 !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  color: var(--accent-cyan) !important;
}

h2 { font-size: 1.6rem !important; }
h3 { font-size: 1.2rem !important; }

/* ── Streamlit sidebar & main area ── */
[data-testid="stSidebar"] {
  background: var(--panel-bg) !important;
  border-right: 1px solid var(--panel-border) !important;
  backdrop-filter: blur(12px) !important;
}

section.main > div { padding-top: 1.5rem !important; }

/* ── Metric containers ── */
[data-testid="stMetric"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 16px !important;
  padding: 1rem !important;
  backdrop-filter: blur(8px) !important;
}

/* ── Buttons ── */
button[kind="primary"], .stButton > button {
  background: linear-gradient(135deg, var(--accent-green) 0%, #00c853 100%) !important;
  color: #1a1a1a !important;
  font-family: 'Exo 2', sans-serif !important;
  font-weight: 900 !important;
  font-size: 1rem !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  border: none !important;
  border-radius: 40px !important;
  padding: 0.6rem 2rem !important;
  box-shadow: 0 6px 24px rgba(76, 255, 114, 0.35) !important;
  transition: transform 0.15s, box-shadow 0.15s !important;
  cursor: pointer !important;
}

.stButton > button:hover {
  transform: translateY(-2px) scale(1.03) !important;
  box-shadow: 0 10px 32px rgba(76, 255, 114, 0.55) !important;
}

/* Delete buttons — red */
.stButton > button[data-testid*="del"] ,
button[title*="Delete"] {
  background: linear-gradient(135deg, #ff4b6e, #c0004e) !important;
  box-shadow: 0 4px 16px rgba(255, 75, 110, 0.4) !important;
  color: #fff !important;
}

/* ── Text inputs ── */
input[type="text"], textarea, .stTextInput > div > div > input {
  background: rgba(255,255,255,0.12) !important;
  border: 2px solid var(--panel-border) !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  font-family: 'Nunito', sans-serif !important;
  font-size: 1rem !important;
  padding: 0.6rem 1rem !important;
  transition: border-color 0.2s !important;
}

input[type="text"]:focus, textarea:focus, .stTextInput > div > div > input:focus {
  border-color: var(--accent-cyan) !important;
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.2) !important;
}

input::placeholder { color: rgba(255,255,255,0.4) !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  background: var(--card-bg) !important;
  border: 2px dashed var(--panel-border) !important;
  border-radius: 16px !important;
  padding: 1rem !important;
}

/* ── Image display ── */
[data-testid="stImage"] img {
  border-radius: 18px !important;
  border: 3px solid var(--panel-border) !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.5) !important;
  transition: transform 0.2s, box-shadow 0.2s !important;
}

[data-testid="stImage"] img:hover {
  transform: scale(1.01) !important;
  box-shadow: 0 12px 50px rgba(182, 75, 255, 0.4) !important;
}

/* ── Info / toast boxes ── */
[data-testid="stAlert"],
.stAlert {
  background: rgba(0, 229, 255, 0.08) !important;
  border: 1px solid rgba(0, 229, 255, 0.3) !important;
  border-radius: 12px !important;
  color: var(--accent-cyan) !important;
}

/* ── Code blocks (shareable link) ── */
code, pre, [data-testid="stCode"] {
  background: rgba(0,0,0,0.4) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 10px !important;
  color: var(--accent-cyan) !important;
  font-size: 0.85rem !important;
  padding: 0.4rem 0.8rem !important;
}

/* ── Horizontal divider ── */
hr {
  border-color: var(--panel-border) !important;
  margin: 1.5rem 0 !important;
}

/* ── Checkboxes ── */
[data-testid="stCheckbox"] label {
  color: var(--text-secondary) !important;
  font-size: 0.95rem !important;
}

/* ── Caption cards ── */
.caption-card {
  background: var(--card-bg);
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  padding: 0.8rem 1.2rem;
  margin-bottom: 0.6rem;
  backdrop-filter: blur(6px);
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.caption-card:hover { background: var(--card-hover); }

.caption-winner {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 165, 0, 0.08)) !important;
  border-color: var(--winner-gold) !important;
  box-shadow: 0 0 16px rgba(255, 215, 0, 0.25) !important;
}

.caption-player {
  font-family: 'Exo 2', sans-serif;
  font-weight: 800;
  color: var(--accent-cyan);
  font-size: 0.95rem;
  letter-spacing: 0.5px;
}

.caption-text {
  color: var(--text-primary);
  font-size: 1rem;
}

.live-badge {
  display: inline-block;
  background: #ff4b6e;
  color: #fff;
  font-family: 'Exo 2', sans-serif;
  font-weight: 800;
  font-size: 0.7rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  padding: 2px 10px;
  border-radius: 30px;
  animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
  0%,100% { opacity: 1; }
  50%      { opacity: 0.6; }
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(0,229,255,0.15);
  border: 1px solid rgba(0,229,255,0.4);
  border-radius: 30px;
  padding: 0.35rem 1rem;
  font-family: 'Exo 2', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 1px;
  color: var(--accent-cyan);
  text-transform: uppercase;
}

.panel-box {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 20px;
  padding: 1.5rem;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  margin-bottom: 1rem;
}

.tag-label {
  display: inline-block;
  background: var(--accent-cyan);
  color: #1a1a1a;
  font-family: 'Exo 2', sans-serif;
  font-weight: 900;
  font-size: 0.75rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 3px 14px;
  border-radius: 30px;
  margin-bottom: 0.8rem;
}

/* ── Streamlit form ── */
[data-testid="stForm"] {
  background: var(--panel-bg) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 20px !important;
  padding: 1.5rem !important;
  backdrop-filter: blur(12px) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: var(--accent-cyan) !important; }

/* ── Toast notifications ── */
[data-testid="stToast"] {
  background: rgba(76, 255, 114, 0.15) !important;
  border: 1px solid rgba(76, 255, 114, 0.4) !important;
  color: var(--accent-green) !important;
  border-radius: 12px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--accent-purple);
  border-radius: 10px;
}

/* ── Select boxes ── */
[data-testid="stSelectbox"] > div {
  background: rgba(255,255,255,0.1) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 10px !important;
  color: #fff !important;
}

/* ── Remove Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden !important; }

/* ── Column gap ── */
[data-testid="column"] { padding: 0 0.5rem !important; }

/* ── Markdown ── */
.stMarkdown p { color: rgba(255,255,255,0.85) !important; line-height: 1.7 !important; }
.stMarkdown strong { color: var(--accent-cyan) !important; }
.stMarkdown em { color: rgba(255,255,255,0.6) !important; }

/* ── "OTHER CAPTIONS" panel header ── */
.captions-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.captions-panel-title {
  font-family: 'Exo 2', sans-serif;
  font-weight: 900;
  font-size: 1rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Avatar circle */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-pink));
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Exo 2', sans-serif;
  font-weight: 900;
  font-size: 0.8rem;
  color: #fff;
  flex-shrink: 0;
  border: 2px solid rgba(255,255,255,0.25);
}

/* Room / round info bar */
.info-bar {
  display: inline-flex;
  gap: 0.6rem;
}
.info-chip {
  background: rgba(0,0,0,0.35);
  border: 1px solid var(--panel-border);
  border-radius: 30px;
  padding: 3px 14px;
  font-family: 'Exo 2', sans-serif;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: rgba(255,255,255,0.7);
}

/* ── REAL PANEL WRAPPING FOR STREAMLIT CONTAINERS ── */
.panel-scope {
  display: none;
}

div[data-testid="stVerticalBlock"]:has(.panel-scope) {
  background: var(--panel-bg) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 20px !important;
  padding: 1.5rem !important;
  backdrop-filter: blur(12px) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
  margin-bottom: 1rem !important;
}

div[data-testid="stVerticalBlock"]:has(.panel-scope-tight) {
  padding-top: 0.9rem !important;
  padding-bottom: 0.9rem !important;
}

/* Better spacing inside panels */
div[data-testid="stVerticalBlock"]:has(.panel-scope) .element-container:last-child {
  margin-bottom: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# Now safely read env vars (Render provides these as env vars)
SUPABASE_URL = (
        os.environ.get('SUPABASE_URL')
        or st.secrets["supabase"]["url"]
)

SUPABASE_KEY = (
        os.environ.get('SUPABASE_KEY')
        or st.secrets["supabase"]["key"]
)

POSTGRES_URI = (
        os.environ.get('POSTGRES_URI')
        or st.secrets["postgres"]["uri"]
)

SERVICE_ROLE = (
        os.environ.get('SUPABASE_SERVICE_ROLE')
        or st.secrets["supabase"].get("role")
)

SUPABASE_BUCKET = (
        os.environ.get('SUPABASE_BUCKET')
        or st.secrets.get("supabase", {}).get("bucket", "images")
)

APP_BASE_URL = (
        os.environ.get('APP_BASE_URL')
        or st.secrets.get("app", {}).get("url", "http://localhost:8501")
)

sb_admin = create_client(SUPABASE_URL, SERVICE_ROLE)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Database helpers ---
def get_conn():
    return psycopg2.connect(POSTGRES_URI, cursor_factory=RealDictCursor)

def create_room_db(title: str = "") -> str:
    rid = str(uuid.uuid4())
    payload = {"id": rid, "title": title}
    res = sb_admin.table("rooms").insert(payload).execute()
    _extract_data(res)
    return rid

def save_image_db(room_id: str, img_id: str, filename: str, storage_path: str, public_url: Optional[str]):
    payload = {
        "id": img_id,
        "room_id": room_id,
        "filename": filename,
        "storage_path": storage_path,
        "public_url": public_url
    }
    res = sb_admin.table("images").insert(payload).execute()

def list_room_images(room_id: str) -> List[Dict]:
    builder = sb_admin.table("images").select("id,filename,storage_path,public_url").eq("room_id", room_id)
    builder = _apply_order(builder, "uploaded_at", ascending=True)
    res = builder.execute()
    return _extract_data(res)

def add_caption_db(image_id: str, player_name: str, text: str):
    cid = str(uuid.uuid4())
    payload = {
        "id": cid,
        "image_id": image_id,
        "player_name": player_name,
        "text": text,
        "winner": False
    }
    res = sb_admin.table("captions").insert(payload).execute()

def get_captions_for_image(image_id: str) -> List[Dict]:
    builder = sb_admin.table("captions").select("id,player_name,text,created_at,winner").eq("image_id", image_id)
    builder = _apply_order(builder, "created_at", ascending=True)
    res = builder.execute()
    return _extract_data(res)

def delete_image_db(image_id: str):
    res = sb_admin.table("images").select("storage_path").eq("id", image_id).execute()
    rows = _extract_data(res)
    storage_path = rows[0]["storage_path"] if rows else None
    _ = sb_admin.table("images").delete().eq("id", image_id).execute()
    _ = sb_admin.table("captions").delete().eq("image_id", image_id).execute()
    return storage_path

def upload_image(room_id, uploaded_file):
    img_id = str(uuid4())
    original_name = uploaded_file.name
    ext = Path(original_name).suffix or ""
    storage_path = f"{room_id}/{img_id}{ext}"

    try:
        file_bytes = uploaded_file.read()
    except Exception as e:
        st.error(f"Failed to read file {original_name}: {e}")
        return None, None, None, None, False

    res = None
    try:
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(storage_path, file_bytes)
    except Exception as e:
        try:
            bio = io.BytesIO(file_bytes)
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                storage_path, bio, {"Content-Type": "application/octet-stream"}
            )
        except Exception as e2:
            st.error(f"Upload failed for {original_name}: {e2}")
            return None, None, None, None, False

    success = res is not None and not (isinstance(res, dict) and res.get("error"))
    if not success:
        st.error(f"Upload failed for {original_name}: unexpected response")
        return None, None, None, None, False

    public_url = None
    try:
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(storage_path)
    except Exception:
        try:
            signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(storage_path, 60*60)
            public_url = signed.get("signedURL") if isinstance(signed, dict) else None
        except Exception:
            pass

    return img_id, original_name, storage_path, public_url, True

def _apply_order(builder, column: str, ascending=True):
    try:
        return builder.order(column, ascending=True)
    except TypeError:
        try:
            return builder.order(column, {"ascending": ascending})
        except Exception:
            return builder.order(column)

def _get_param(key, default=None):
    params = st.query_params
    val = params.get(key, default)
    if isinstance(val, list):
        return val[0] if val else default
    return val

def _set_params(**kwargs):
    if hasattr(st, "query_params"):
        for k, v in kwargs.items():
            st.query_params[k] = v if isinstance(v, list) else [v]
    elif hasattr(st, "experimental_set_query_params"):
        st.experimental_set_query_params(**kwargs)

def _extract_data(response):
    if hasattr(response, "data"):
        return response.data
    elif isinstance(response, dict) and "data" in response:
        return response["data"]
    else:
        return response or []

def _choose_winner_caption(image_id, caption_id):
    sb_admin.table("captions").update({"winner": False}).eq("image_id", image_id).execute()
    sb_admin.table("captions").update({"winner": True}).eq("id", caption_id).execute()

def _finish_game(room_id):
    sb_admin.table("rooms").update({"finished": True}).eq("id", room_id).execute()

def _reopen_game(room_id):
    sb_admin.table("rooms").update({"finished": False}).eq("id", room_id).execute()

def _is_game_finished(room_id):
    res = sb_admin.table("rooms").select("finished").eq("id", room_id).execute()
    data = _extract_data(res)
    return data[0]["finished"] if data else False

def _avatar_html(name: str) -> str:
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    return f'<div class="avatar">{initials}</div>'

def panel_marker(tight: bool = False):
    klass = "panel-scope panel-scope-tight" if tight else "panel-scope"
    st.markdown(f'<div class="{klass}"></div>', unsafe_allow_html=True)

# ── Main UI ─────────────────────────────────────────────────────────────────────
room_id = _get_param("room_id", None)
role = _get_param("role", "host")

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown("""
<h1>Caption The<br><span style="color:#00e5ff;">Moment</span></h1>
""", unsafe_allow_html=True)

st.markdown("---")

# ── HOST UI ──────────────────────────────────────────────────────────────────────
if role == "host":

    if _is_game_finished(room_id):
        # ── FINISHED VIEW ──
        st.markdown('<div class="tag-label">🏁 Game Finished</div>', unsafe_allow_html=True)
        st.header("Results")

        col_a, col_b = st.columns([1, 2])
        with col_a:
            if st.button("➕ Create New Room"):
                room_id = create_room_db()
                _set_params(room_id=room_id, role="host")
                st.rerun()

            if room_id:
                st.markdown("**Shareable link for players:**")
                st.code(f"{APP_BASE_URL}/?room_id={room_id}&role=player")
            else:
                st.info("Create a room first (press the button).")

        imgs = list_room_images(room_id)
        if not imgs:
            st.info("No images uploaded yet.")
        else:
            for img in imgs:
                public_url = img.get("public_url")
                if not public_url and img.get("storage_path"):
                    try:
                        signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(img["storage_path"], 3600)
                        public_url = signed.get("signedURL") if isinstance(signed, dict) else None
                    except Exception:
                        pass

                with st.container():
                    panel_marker()
                    st.markdown('<span class="tag-label">📸 The Moment</span>', unsafe_allow_html=True)
                    if public_url:
                        st.image(public_url, width=700)
                    else:
                        st.write(f"Image: {img['filename']} (not accessible)")

                    caps = get_captions_for_image(img["id"])
                    if caps:
                        st.markdown("""
                        <div class="captions-panel-header">
                          <div class="captions-panel-title">💬 Captions</div>
                        </div>
                        """, unsafe_allow_html=True)
                        for c in caps:
                            winner_class = "caption-winner" if c['winner'] else ""
                            crown = "👑 " if c['winner'] else ""
                            st.markdown(f"""
                            <div class="caption-card {winner_class}">
                              {_avatar_html(c['player_name'])}
                              <div>
                                <div class="caption-player">{crown}{c['player_name']}</div>
                                <div class="caption-text">"{c['text']}"</div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("_No captions were submitted_")

        st.markdown("---")
        if st.checkbox("I want to reopen or edit the game") and st.button("🔓 Reopen Game"):
            _reopen_game(room_id)
            st.rerun()

    else:
        # ── ACTIVE HOST VIEW ──
        col_left, col_right = st.columns([1, 3])

        with col_left:
            with st.container():
                panel_marker()
                st.markdown('<span class="tag-label">🎮 Host Controls</span>', unsafe_allow_html=True)

                if st.button("➕ Create New Room"):
                    room_id = create_room_db()
                    _set_params(room_id=room_id, role="host")
                    st.rerun()

                if room_id:
                    st.markdown("**Shareable link for players:**")
                    st.code(f"{APP_BASE_URL}/?room_id={room_id}&role=player")
                    st.markdown(f"""
                    <div class="info-bar">
                      <span class="info-chip">Room: #{str(room_id)[:6].upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Create a room first (press the button).")

        if not room_id:
            st.stop()

        with col_right:
            with st.container():
                panel_marker()
                st.markdown('<span class="tag-label">📤 Upload Images</span>', unsafe_allow_html=True)
                with st.form("upload_form"):
                    uploaded = st.file_uploader(
                        "Upload image(s)", accept_multiple_files=True,
                        type=['png', 'jpg', 'jpeg', 'gif']
                    )
                    submitted = st.form_submit_button("Upload ▶")

                if submitted and uploaded:
                    for f in uploaded:
                        img_id, filename, storage_path, public_url, success = upload_image(room_id, f)
                        if success:
                            save_image_db(room_id, img_id, filename, storage_path, public_url)
                            st.toast(f"✅ Uploaded {filename}")
                        else:
                            st.error(f"Upload failed for {filename}")
                    st.rerun()

                st.text_input("📝 Photo context / title", "e.g. My recent trip to the Bahamas")

        st.markdown("---")

        st.markdown("""
        <div class="captions-panel-header">
          <div class="captions-panel-title">📸 Images &amp; Captions</div>
          <span class="live-badge">LIVE</span>
        </div>
        """, unsafe_allow_html=True)

        imgs = list_room_images(room_id)
        if not imgs:
            st.info("No images yet — upload some above.")
        else:
            for img in imgs:
                with st.container():
                    panel_marker()
                    left, right = st.columns([4, 1])
                    with left:
                        public_url = img.get("public_url")
                        if not public_url and img.get("storage_path"):
                            try:
                                signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(img["storage_path"], 3600)
                                public_url = signed.get("signedURL") if isinstance(signed, dict) else None
                            except Exception:
                                pass

                        st.markdown('<span class="tag-label">📸 The Moment</span>', unsafe_allow_html=True)
                        if public_url:
                            st.image(public_url, width=800)
                        else:
                            st.write(f"Image: {img['filename']} (not accessible)")

                        caps = get_captions_for_image(img["id"])
                        if caps:
                            st.markdown("""
                            <div class="captions-panel-header" style="margin-top:1rem;">
                              <div class="captions-panel-title">💬 Other Captions</div>
                              <span class="live-badge">LIVE</span>
                            </div>
                            """, unsafe_allow_html=True)
                            for c in caps:
                                winner_class = "caption-winner" if c['winner'] else ""
                                crown = "👑 " if c['winner'] else ""
                                col1, col2 = st.columns([5, 1])
                                with col1:
                                    st.markdown(f"""
                                    <div class="caption-card {winner_class}">
                                      {_avatar_html(c['player_name'])}
                                      <div>
                                        <div class="caption-player">{crown}{c['player_name']}</div>
                                        <div class="caption-text">"{c['text']}"</div>
                                      </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    if c['winner']:
                                        st.write("👑")
                                    else:
                                        if st.button("👑", key=f"win_{c['id']}"):
                                            _choose_winner_caption(img['id'], c['id'])
                                            st.rerun()
                        else:
                            st.markdown("_No captions yet — waiting for players..._")

                    with right:
                        if st.button("🗑️ Delete", key=f"del_{img['id']}"):
                            delete_image_db(img["id"])
                            st.rerun()

        st.markdown("---")
        if st.checkbox("✅ I have chosen a winner for every image") and st.button("🏁 Submit Winners"):
            _finish_game(room_id)
            st.rerun()


# ── PLAYER UI ───────────────────────────────────────────────────────────────────
else:
    # Top bar
    col_name, col_spacer, col_status = st.columns([2, 3, 2])
    with col_name:
        with st.container():
            panel_marker(tight=True)
            player_name = st.text_input("Your name", value="Player1", label_visibility="collapsed")
    with col_status:
        finished = _is_game_finished(room_id) if room_id else False
        status_text = "🏁 Game Finished" if finished else "⏳ Waiting for Host..."
        st.markdown(f'<div class="status-badge">{status_text}</div>', unsafe_allow_html=True)

    if not room_id:
        st.info("Open the link the host shared (it has ?room_id=...)")
        st.stop()

    # How to play
    with st.container():
        panel_marker()
        st.markdown('<span class="tag-label">🎮 How to Play</span>', unsafe_allow_html=True)
        st.markdown("""
        1. **Choose your player name** above.
        2. **Type your caption** below the image.
        3. **Submit** as many captions as you want.
        4. When the host has chosen the winner... **all will be revealed** 🎉
        """)
        st.subheader("HAVE FUN! 🚀")

    st.markdown("---")

    imgs = list_room_images(room_id)
    if not imgs:
        st.info("No images uploaded yet. Ask the host to upload some.")
    else:
        for img in imgs:
            col_img, col_caps = st.columns([3, 2])

            with col_img:
                public_url = img.get("public_url")
                if not public_url and img.get("storage_path"):
                    try:
                        signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(img["storage_path"], 3600)
                        public_url = signed.get("signedURL") if isinstance(signed, dict) else None
                    except Exception:
                        pass

                with st.container():
                    panel_marker()
                    st.markdown('<span class="tag-label">📸 The Moment</span>', unsafe_allow_html=True)
                    if public_url:
                        st.image(public_url, width=700)
                    else:
                        st.write(f"Image: {img['filename']} (not accessible)")

                    if not _is_game_finished(room_id):
                        st.markdown('<span class="tag-label" style="background:var(--accent-purple);color:#fff;">✏️ Your Caption</span>', unsafe_allow_html=True)
                        with st.form(f"form_{img['id']}"):
                            caption_text = st.text_input("", placeholder="Type something funny here...", key=f"input_{img['id']}", label_visibility="collapsed")
                            submitted = st.form_submit_button("SUBMIT ▶")
                            if submitted and caption_text.strip():
                                add_caption_db(img["id"], player_name, caption_text.strip())
                                st.toast("✅ Caption submitted!")
                                st.rerun()

            with col_caps:
                with st.container():
                    panel_marker()
                    st.markdown("""
                    <div class="captions-panel-header">
                      <div class="captions-panel-title">💬 Other Captions</div>
                      <span class="live-badge">LIVE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    caps = get_captions_for_image(img["id"])
                    if caps:
                        for c in caps:
                            winner_class = "caption-winner" if c.get('winner') else ""
                            crown = "👑 " if c.get('winner') else ""
                            st.markdown(f"""
                            <div class="caption-card {winner_class}">
                              {_avatar_html(c['player_name'])}
                              <div>
                                <div class="caption-player">{crown}{c['player_name']}</div>
                                <div class="caption-text">"{c['text']}"</div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="caption-card" style="opacity:0.5; border-style: dashed;">
                          <div class="caption-text">⏳ Waiting for more...</div>
                        </div>
                        """, unsafe_allow_html=True)

        # Footer info bar
        if room_id:
            st.markdown(f"""
            <div style="margin-top:2rem;" class="info-bar">
              <span class="info-chip">Room: #{str(room_id)[:6].upper()}</span>
            </div>
            """, unsafe_allow_html=True)