"""Caption The Moment — DEMO build.

Runs entirely in the browser (stlite / Pyodide) on GitHub Pages. There is no
Supabase / Postgres here: all data lives in ``st.session_state`` and is seeded
from ``mock_data.py``. Reloading the page resets the demo.
"""
import html
import uuid
from pathlib import Path
from typing import Dict, List

import streamlit as st

import mock_data

# Fixed set of reactions players can drop on captions (cosmetic only).
ALLOWED_EMOJIS = ["😂", "🔥", "❤️", "😮"]

# Page config must come after importing streamlit
st.set_page_config(page_title="Caption The Moment — Demo", layout="wide")

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

section.main > div {
  padding-top: 1.5rem !important;
}

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
.stButton > button[data-testid*="del"],
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

input::placeholder {
  color: rgba(255,255,255,0.4) !important;
}

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
[data-testid="stAlert"], .stAlert {
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

.caption-card:hover {
  background: var(--card-hover);
}

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
  50% { opacity: 0.6; }
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

.plain-section-label {
  display: inline-block;
  background: transparent !important;
  color: var(--accent-cyan) !important;
  font-family: 'Exo 2', sans-serif;
  font-weight: 900;
  font-size: 1.08rem;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  padding: 0 !important;
  border-radius: 0 !important;
  margin-bottom: 0.8rem;
  box-shadow: none !important;
  border: none !important;
}

.plain-section-label.purple {
  color: var(--accent-purple) !important;
}

/* ── Streamlit form ── */
[data-testid="stForm"] {
  background: var(--panel-bg) !important;
  border: 1px solid var(--panel-border) !important;
  border-radius: 20px !important;
  padding: 1.5rem !important;
  backdrop-filter: blur(12px) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
  margin-bottom: 1rem !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] {
  color: var(--accent-cyan) !important;
}

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
::-webkit-scrollbar-thumb { background: var(--accent-purple); border-radius: 10px; }

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

/* Vote tally badge on a caption */
.vote-badge {
  display: inline-block;
  background: rgba(0, 229, 255, 0.18);
  border: 1px solid rgba(0, 229, 255, 0.45);
  color: var(--accent-cyan);
  font-family: 'Exo 2', sans-serif;
  font-weight: 800;
  font-size: 0.72rem;
  letter-spacing: 0.5px;
  padding: 1px 9px;
  border-radius: 30px;
  margin-left: 0.4rem;
}

/* Reaction tally row under a caption */
.reaction-bar {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.4rem;
  flex-wrap: wrap;
}

.reaction-chip {
  background: rgba(255,255,255,0.10);
  border: 1px solid var(--panel-border);
  border-radius: 30px;
  padding: 1px 10px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #fff;
}
</style>
""", unsafe_allow_html=True)

# ── Mock "database" (lives in st.session_state, local to this browser tab) ────
BASE_DIR = Path(__file__).parent


def _seed() -> Dict:
    """Build a fresh in-memory room from mock_data."""
    images, captions = [], []
    for img in mock_data.IMAGES:
        try:
            data = (BASE_DIR / img["file"]).read_bytes()
        except OSError:
            data = None
        images.append({"id": img["id"], "filename": img["filename"], "data": data})
        for name, text in img["captions"]:
            captions.append({
                "id": str(uuid.uuid4()),
                "image_id": img["id"],
                "player_name": name,
                "text": text,
                "winner": False,
            })
    return {
        "room_id": mock_data.ROOM_ID,
        "title": mock_data.ROOM_TITLE,
        "finished": False,
        "images": images,
        "captions": captions,
    }


if "db" not in st.session_state:
    st.session_state.db = _seed()
if "view" not in st.session_state:
    st.session_state.view = "Host"

DB: Dict = st.session_state.db


def reset_demo():
    st.session_state.db = _seed()


def list_room_images() -> List[Dict]:
    return DB["images"]


def get_captions_for_image(image_id: str) -> List[Dict]:
    return [c for c in DB["captions"] if c["image_id"] == image_id]


def add_caption_db(image_id: str, player_name: str, text: str):
    DB["captions"].append({
        "id": str(uuid.uuid4()),
        "image_id": image_id,
        "player_name": player_name,
        "text": text,
        "winner": False,
    })


def delete_caption_db(caption_id: str):
    DB["captions"] = [c for c in DB["captions"] if c["id"] != caption_id]


def add_image_db(filename: str, data: bytes):
    DB["images"].append({"id": str(uuid.uuid4()), "filename": filename, "data": data})


def delete_image_db(image_id: str):
    DB["images"] = [i for i in DB["images"] if i["id"] != image_id]
    DB["captions"] = [c for c in DB["captions"] if c["image_id"] != image_id]


def _choose_winner_caption(image_id: str, caption_id: str):
    """Exactly one winner per image."""
    for c in DB["captions"]:
        if c["image_id"] == image_id:
            c["winner"] = (c["id"] == caption_id)


def _is_game_finished() -> bool:
    return DB["finished"]


def _finish_game():
    DB["finished"] = True


def _reopen_game():
    DB["finished"] = False


# ── Rendering helpers ─────────────────────────────────────────────────────────
def _avatar_html(name: str) -> str:
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    return f'<div class="avatar">{html.escape(initials)}</div>'


def render_image(img: Dict, width: int = 700):
    st.markdown('<span class="plain-section-label">📸 The Moment</span>', unsafe_allow_html=True)
    if img.get("data"):
        st.image(img["data"], width=width)
    else:
        st.write(f"Image: {img['filename']} (not accessible)")


def caption_card_html(c: Dict) -> str:
    winner_class = "caption-winner" if c.get("winner") else ""
    crown = "👑 " if c.get("winner") else ""
    name = html.escape(c["player_name"])
    text = html.escape(c["text"])
    return f"""
    <div class="caption-card {winner_class}">
        {_avatar_html(c['player_name'])}
        <div style="flex:1;">
            <div class="caption-player">{crown}{name}</div>
            <div class="caption-text">"{text}"</div>
        </div>
    </div>"""


def room_chip_html() -> str:
    return f"""
    <div class="info-bar">
        <span class="info-chip">Room: #{str(DB['room_id'])[:6].upper()}</span>
    </div>"""


# ── Header + demo controls ──────────────────────────────────────────────────────
st.markdown("""
<h1>Caption The<br><span style="color:#00e5ff;">Moment</span></h1>
""", unsafe_allow_html=True)

bar_l, bar_m, bar_r = st.columns([3, 3, 2])
with bar_l:
    st.radio(
        "View", ["Host", "Player"], key="view", horizontal=True,
        format_func=lambda v: "🎮 Host view" if v == "Host" else "🙋 Player view",
        label_visibility="collapsed",
    )
with bar_m:
    st.caption("🧪 **Demo** — mock data, runs fully in your browser. "
               "Nothing is saved; a page reload resets everything.")
with bar_r:
    if st.button("↺ Reset demo data"):
        reset_demo()
        st.rerun()

st.markdown("---")
role = "host" if st.session_state.view == "Host" else "player"

# ── HOST UI ──────────────────────────────────────────────────────────────────────
if role == "host":
    if _is_game_finished():
        # ── FINISHED VIEW ──
        st.markdown('<div class="tag-label">🏁 Game Finished</div>', unsafe_allow_html=True)
        st.header("Results")

        imgs = list_room_images()
        if not imgs:
            st.info("No images uploaded yet.")
        else:
            for img in imgs:
                with st.container():
                    render_image(img, width=700)
                    caps = get_captions_for_image(img["id"])
                    if caps:
                        st.markdown("""
                        <div class="captions-panel-header">
                            <div class="captions-panel-title">💬 Captions</div>
                        </div>
                        """, unsafe_allow_html=True)
                        for c in caps:
                            st.markdown(caption_card_html(c), unsafe_allow_html=True)
                    else:
                        st.markdown("_No captions were submitted_")
                st.markdown("---")

        if st.checkbox("I want to reopen or edit the game") and st.button("🔓 Reopen Game"):
            _reopen_game()
            st.rerun()

    else:
        # ── ACTIVE HOST VIEW ──
        col_left, col_right = st.columns([1, 3])

        with col_left:
            with st.container():
                st.markdown('<span class="tag-label">🎮 Host Controls</span>', unsafe_allow_html=True)
                st.markdown("**Players join via a shared link.** In this demo, use the "
                            "**Player view** toggle above to play along.")
                st.markdown(room_chip_html(), unsafe_allow_html=True)

        with col_right:
            with st.container():
                st.markdown('<span class="tag-label">📤 Upload Images</span>', unsafe_allow_html=True)

                with st.form("upload_form", clear_on_submit=True):
                    uploaded = st.file_uploader(
                        "Upload image(s)",
                        accept_multiple_files=True,
                        type=["png", "jpg", "jpeg", "gif"],
                    )
                    submitted = st.form_submit_button("Upload ▶")

                    if submitted and uploaded:
                        for f in uploaded:
                            add_image_db(f.name, f.read())
                            st.toast(f"✅ Added {f.name} (local only)")
                        st.rerun()

                st.text_input("📝 Photo context / title", DB["title"])

        st.markdown("---")
        st.markdown("""
        <div class="captions-panel-header">
            <div class="captions-panel-title">📸 Images &amp; Captions</div>
            <span class="live-badge">LIVE</span>
        </div>
        """, unsafe_allow_html=True)

        imgs = list_room_images()
        if not imgs:
            st.info("No images yet — upload some above.")
        else:
            for img in imgs:
                with st.container():
                    left, right = st.columns([4, 1])

                    with left:
                        render_image(img, width=800)
                        caps = get_captions_for_image(img["id"])
                        if caps:
                            st.markdown("""
                            <div class="captions-panel-header" style="margin-top:1rem;">
                                <div class="captions-panel-title">💬 Other Captions</div>
                                <span class="live-badge">LIVE</span>
                            </div>
                            """, unsafe_allow_html=True)

                            for c in caps:
                                col1, col2 = st.columns([5, 1])
                                with col1:
                                    st.markdown(caption_card_html(c), unsafe_allow_html=True)
                                with col2:
                                    if c["winner"]:
                                        st.write("👑")
                                    else:
                                        if st.button("👑", key=f"win_{c['id']}"):
                                            _choose_winner_caption(img["id"], c["id"])
                                            st.rerun()
                                    if st.button("🗑️", key=f"delcap_{c['id']}"):
                                        delete_caption_db(c["id"])
                                        st.rerun()
                        else:
                            st.markdown("_No captions yet — waiting for players..._")

                    with right:
                        if st.button("🗑️ Delete", key=f"del_{img['id']}"):
                            delete_image_db(img["id"])
                            st.rerun()

                st.markdown("---")

        if st.checkbox("✅ I have chosen a winner for every image") and st.button("🏁 Submit Winners"):
            _finish_game()
            st.rerun()

# ── PLAYER UI ───────────────────────────────────────────────────────────────────
else:
    # Top bar
    col_name, col_spacer, col_status = st.columns([2, 3, 2])

    with col_name:
        with st.container():
            player_name = st.text_input("Your name", value="Player1", label_visibility="collapsed")

    with col_status:
        finished = _is_game_finished()
        status_text = "🏁 Game Finished" if finished else "⏳ Waiting for Host..."
        st.markdown(f'<div class="status-badge">{status_text}</div>', unsafe_allow_html=True)

    # How to play
    with st.container():
        st.markdown('<span class="plain-section-label">🎮 How to Play</span>', unsafe_allow_html=True)
        st.markdown("""
        1. **Choose your player name** above.
        2. **Type your caption** below the image.
        3. **Submit** as many captions as you want.
        4. When the host has chosen the winner... **all will be revealed** 🎉
        """)
        st.subheader("HAVE FUN! 🚀")

    st.markdown("---")

    imgs = list_room_images()
    if not imgs:
        st.info("No images uploaded yet. Ask the host to upload some.")
    else:
        for img in imgs:
            col_img, col_caps = st.columns([3, 2])

            with col_img:
                with st.container():
                    render_image(img, width=700)

                    if not _is_game_finished():
                        st.markdown(
                            '<span class="plain-section-label purple">✏️ Your Caption</span>',
                            unsafe_allow_html=True,
                        )
                        with st.form(f"form_{img['id']}", clear_on_submit=True):
                            caption_text = st.text_input(
                                "caption",
                                placeholder="Type something funny here...",
                                key=f"input_{img['id']}",
                                label_visibility="collapsed",
                            )
                            submitted = st.form_submit_button("SUBMIT ▶")

                            if submitted and caption_text.strip():
                                add_caption_db(img["id"], player_name.strip() or "Player1",
                                               caption_text.strip())
                                st.toast("✅ Caption submitted!")
                                st.rerun()

            with col_caps:
                with st.container():
                    st.markdown("""
                    <div class="captions-panel-header">
                        <div class="captions-panel-title">💬 Other Captions</div>
                        <span class="live-badge">LIVE</span>
                    </div>
                    """, unsafe_allow_html=True)

                    caps = get_captions_for_image(img["id"])
                    if caps:
                        for c in caps:
                            st.markdown(caption_card_html(c), unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="caption-card" style="opacity:0.5; border-style: dashed;">
                            <div class="caption-text">⏳ Waiting for more...</div>
                        </div>
                        """, unsafe_allow_html=True)

    # Footer info bar
    st.markdown(f'<div style="margin-top:2rem;">{room_chip_html()}</div>', unsafe_allow_html=True)
