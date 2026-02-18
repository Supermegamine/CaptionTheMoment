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

# Service role key (for admin operations) – fallback to secrets if env var not set
SERVICE_ROLE = (
    os.environ.get('SUPABASE_SERVICE_ROLE')
    or st.secrets["supabase"].get("role")  # note: .get() avoids KeyError if missing
)

# Bucket name – fallback to a default if neither env var nor secret provided
SUPABASE_BUCKET = (
    os.environ.get('SUPABASE_BUCKET')
    or st.secrets.get("supabase", {}).get("bucket", "images")
)

# App base URL – fallback to a sensible default (useful for localhost)
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
    _extract_data(res)  # just to ensure no error; we don't need the data
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
    # handle errors as above

def list_room_images(room_id: str) -> List[Dict]:
    builder = sb_admin.table("images").select("id,filename,storage_path,public_url").eq("room_id", room_id)
    builder = _apply_order(builder, "uploaded_at", ascending=True)
    res = builder.execute()
    return _extract_data(res)

def add_caption_db(image_id: str, player_name: str, text: str):
    cid = str(uuid.uuid4())  # generate a unique ID
    payload = {
        "id": cid,
        "image_id": image_id,
        "player_name": player_name,
        "text": text
    }
    res = sb_admin.table("captions").insert(payload).execute()

def get_captions_for_image(image_id: str) -> List[Dict]:
    builder = sb_admin.table("captions").select("player_name,text,created_at").eq("image_id", image_id)
    builder = _apply_order(builder, "created_at", ascending=True)
    res = builder.execute()
    return _extract_data(res)

def delete_image_db(image_id: str):
    # get storage_path first
    res = sb_admin.table("images").select("storage_path").eq("id", image_id).execute()
    rows = _extract_data(res)
    storage_path = rows[0]["storage_path"] if rows else None
    # delete rows
    _ = sb_admin.table("images").delete().eq("id", image_id).execute()
    _ = sb_admin.table("captions").delete().eq("image_id", image_id).execute()
    return storage_path

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

def _apply_order(builder, column: str, ascending = True):
    """
    Accepts a select/Builder-like object and attempts to call .order() in a way
    compatible with multiple supabase-py versions.
    Returns the builder (chained).
    """
    try:
        # preferred: keyword arg style
        return builder.order(column, ascending= True)
    except TypeError:
        try:
            # fallback: pass options dict as second positional arg (older style)
            return builder.order(column, {"ascending": ascending})
        except Exception:
            # last-resort: try calling with just the column (no ordering options)
            return builder.order(column)
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

def _extract_data(response):
    """Safely extract the 'data' field from a Supabase response."""
    if hasattr(response, "data"):
        return response.data
    elif isinstance(response, dict) and "data" in response:
        return response["data"]
    else:
        # Fallback: assume the response itself is the data
        return response or []

def _clear_caption(key):
    blank = ''
    st.session_state[key] = blank

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
                st.toast(f"Uploaded {filename}")
            else:
                st.error(f"Upload failed for {filename}")
        st.rerun()
        st.toast(f"Uploaded {filename}")

    st.markdown("---")



    st.markdown("---")
    st.subheader("images & captions")
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
                caption_text = st.text_input("Your caption", on_change=_clear_caption(f"input_{img['id']}"), key=f"input_{img['id']}")
                submitted = st.form_submit_button("Submit caption")
                if submitted and caption_text.strip():
                    add_caption_db(img["id"], player_name, caption_text.strip())
                    st.toast("Caption submitted!")
                    st.rerun()