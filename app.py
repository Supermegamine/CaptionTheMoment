import streamlit as st
from uuid import uuid4
from pathlib import Path
import io

import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client

# --- Configuration ---
st.set_page_config(page_title="Caption The Moment", layout="wide")
secrets = st.secrets

try:
    SUPABASE_URL = secrets["supabase"]["url"]
    SUPABASE_KEY = secrets["supabase"]["key"]
    POSTGRES_URI = secrets["postgres"]["uri"]
except Exception:
    st.error("Missing required secrets. Please set supabase.url, supabase.key and postgres.uri in Streamlit secrets.")
    st.stop()

APP_BASE_URL = secrets.get("app", {}).get("url", "http://localhost:8501")
SUPABASE_BUCKET = "images"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Database helpers ---
def get_conn():
    return psycopg2.connect(POSTGRES_URI, cursor_factory=RealDictCursor)

def create_room_db(title=""):
    rid = str(uuid4())
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO rooms (id, title, created_at) VALUES (%s, %s, now())",
                (rid, title),
            )
    return rid

def save_image_db(room_id, img_id, filename, storage_path, public_url):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO images (id, room_id, filename, storage_path, public_url, uploaded_at) VALUES (%s, %s, %s, %s, %s, now())",
                (img_id, room_id, filename, storage_path, public_url),
            )

def list_room_images(room_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, filename, storage_path, public_url FROM images WHERE room_id = %s ORDER BY uploaded_at",
                (room_id,)
            )
            return cur.fetchall()

def add_caption_db(image_id, player_name, text):
    cid = str(uuid4())
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO captions (id, image_id, player_name, text, created_at) VALUES (%s, %s, %s, %s, now())",
                (cid, image_id, player_name, text),
            )

def get_captions_for_image(image_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT player_name, text, created_at FROM captions WHERE image_id = %s ORDER BY created_at",
                (image_id,)
            )
            return cur.fetchall()

def delete_image_db(image_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT storage_path FROM images WHERE id = %s", (image_id,))
            row = cur.fetchone()
            storage_path = row["storage_path"] if row else None

            cur.execute("DELETE FROM images WHERE id = %s", (image_id,))
            cur.execute("DELETE FROM captions WHERE image_id = %s", (image_id,))
    return storage_path

def delete_from_supabase(storage_path):
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([storage_path])
    except Exception as e:
        st.warning(f"Could not delete from storage: {e}")

# --- Upload function (no debug) ---
def upload_image(room_id, uploaded_file):
    """Upload an image to Supabase. Returns (img_id, filename, storage_path, public_url, success)."""
    img_id = str(uuid4())
    original_name = uploaded_file.name
    ext = Path(original_name).suffix or ""
    storage_path = f"{room_id}/{img_id}{ext}"

    # Read file as bytes
    try:
        file_bytes = uploaded_file.read()
    except Exception as e:
        st.error(f"Failed to read file {original_name}: {e}")
        return None, None, None, None, False

    # Try uploading bytes
    res = None
    try:
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(storage_path, file_bytes)
    except Exception as e:
        # Fallback: try as file-like object
        try:
            bio = io.BytesIO(file_bytes)
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                storage_path, bio, {"Content-Type": "application/octet-stream"}
            )
        except Exception as e2:
            st.error(f"Upload failed for {original_name}: {e2}")
            return None, None, None, None, False

    # Check success (simple heuristic: no error in response)
    success = res is not None and not (isinstance(res, dict) and res.get("error"))
    if not success:
        st.error(f"Upload failed for {original_name}: unexpected response")
        return None, None, None, None, False

    # Get public URL (or signed URL if bucket is private)
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

# --- URL parameter helpers ---
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

# --- Main UI ---
room_id = _get_param("room_id", None)
role = _get_param("role", "host")

st.title("Caption The Moment")

# Host UI
if role == "host":
    col1, col2 = st.columns([1, 3])
    with col1:
        st.header("Host")
        if st.button("Create new room"):
            room_id = create_room_db()
            _set_params(room_id=room_id, role="host")
            st.rerun()

        if room_id:
            st.markdown("**Shareable link for players:**")
            st.code(f"{APP_BASE_URL}/?room_id={room_id}&role=player")
        else:
            st.info("Create a room first (press the button).")

    if not room_id:
        st.stop()

    st.header("Upload images")
    with st.form("upload_form"):
        uploaded = st.file_uploader(
            "Upload image(s)", accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'gif']
        )
        submitted = st.form_submit_button("Upload")

    if submitted and uploaded:
        for f in uploaded:
            img_id, filename, storage_path, public_url, success = upload_image(room_id, f)
            if success:
                save_image_db(room_id, img_id, filename, storage_path, public_url)
                st.success(f"Uploaded {filename}")
            else:
                st.error(f"Upload failed for {filename}")
        st.rerun()

    st.markdown("---")
    st.subheader("Room images & captions")
    imgs = list_room_images(room_id)
    if not imgs:
        st.info("No images yet.")
    else:
        for img in imgs:
            left, right = st.columns([4, 1])
            with left:
                public_url = img.get("public_url")
                if not public_url and img.get("storage_path"):
                    try:
                        signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                            img["storage_path"], 3600
                        )
                        public_url = signed.get("signedURL") if isinstance(signed, dict) else None
                    except Exception:
                        pass

                if public_url:
                    st.image(public_url, width=800)
                else:
                    st.write(f"Image: {img['filename']} (not accessible)")

                caps = get_captions_for_image(img["id"])
                if caps:
                    st.write("**Captions:**")
                    for i, c in enumerate(caps, 1):
                        st.write(f"{i}. **{c['player_name']}** — {c['text']}")
                else:
                    st.write("_No captions yet_")
            with right:
                if st.button("Delete", key=f"del_{img['id']}"):
                    storage_path = delete_image_db(img["id"])
                    if storage_path:
                        delete_from_supabase(storage_path)
                    st.rerun()

# Player UI
else:
    st.header("How to play")
    st.markdown("1. Choose your player name.")
    player_name = st.text_input("Your name", value="Player1")

    if not room_id:
        st.info("Open the link the host shared (it has ?room_id=...)")
        st.stop()

    st.markdown("2. Type your caption below the image.")
    st.markdown("3. Submit as many captions as you want.")
    st.markdown("4. When the host has chosen the winner... all will be revealed :)")
    st.subheader("HAVE FUN!")
    st.markdown("---")

    imgs = list_room_images(room_id)
    if not imgs:
        st.info("No images uploaded yet. Ask the host to upload some.")
    else:
        for img in imgs:
            public_url = img.get("public_url")
            if not public_url and img.get("storage_path"):
                try:
                    signed = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
                        img["storage_path"], 3600
                    )
                    public_url = signed.get("signedURL") if isinstance(signed, dict) else None
                except Exception:
                    pass

            if public_url:
                st.image(public_url, width=700)
            else:
                st.write(f"Image: {img['filename']} (not accessible)")

            with st.form(f"form_{img['id']}"):
                caption_text = st.text_input("Your caption", key=f"input_{img['id']}")
                submitted = st.form_submit_button("Submit caption")
                if submitted and caption_text.strip():
                    add_caption_db(img["id"], player_name, caption_text.strip())
                    st.success("Caption submitted!")
                    st.rerun()
