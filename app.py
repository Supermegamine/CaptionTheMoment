
import streamlit as st
from uuid import uuid4
import os
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil
import re

# --- config ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
BERLIN = ZoneInfo("Europe/Berlin")

st.set_page_config(page_title="Caption Game", layout="wide")

# --- helpers ---
def make_room_dir(room_id: str) -> Path:
    d = DATA_DIR / room_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "images").mkdir(exist_ok=True)
    if not (d / "captions.json").exists():
        with open(d / "captions.json", "w") as f:
            json.dump({}, f)
    return d

def save_image(room_dir: Path, uploaded_file):
    # save with timestamp to avoid collisions
    ts = datetime.now(BERLIN).strftime("%Y%m%d%H%M%S%f")
    name = f"{ts}_{uploaded_file.name}"
    out = room_dir / "images" / name
    with open(out, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return name

def load_captions(room_dir: Path):
    p = room_dir / "captions.json"
    with open(p, "r") as f:
        return json.load(f)

def save_captions(room_dir: Path, captions_dict):
    p = room_dir / "captions.json"
    with open(p, "w") as f:
        json.dump(captions_dict, f, indent=2)

def delete_image_and_captions(room_dir: Path, img_name: str, move_to_trash: bool = True):
    img_path = room_dir / "images" / img_name
    trash_dir = room_dir / "deleted_images"
    if img_path.exists():
        if move_to_trash:
            trash_dir.mkdir(exist_ok=True)
            shutil.move(str(img_path), str(trash_dir / img_name))
        else:
            img_path.unlink()
    captions = load_captions(room_dir)
    if img_name in captions:
        captions.pop(img_name)
        save_captions(room_dir, captions)

def keyify(s: str) -> str:
    # convert image name into a safe widget/session_state key
    return re.sub(r"\W+", "_", s)

# --- query params / role / room handling ---
params = st.query_params
room_id = params.get("room_id")
role = params.get("role", "player")
room_dir = make_room_dir(room_id)


st.title("Caption The Moment")


# --- HOST UI: upload images & see captions ---
if role == "host":
    col1, col2 = st.columns([1, 3])

    with col1:
        st.header("Room")
        if st.button("Create new room (host)"):
            new_room = str(uuid4())[:8]
            # set URL params to new room and role=host
            st.query_params.clear()
            st.query_params.update({
                "room_id": new_room,
                "role": "host"
            })
            st.rerun()

        if room_id:
            st.markdown("**Shareable link for players:**")
            full_link_hint = f"http://localhost:8502/?room_id={room_id}&role=player"
            st.code(full_link_hint)
        else:
            st.info("Create a room first (press the button).")

    # If no room, stop here
    if not room_id:
        st.stop()

    st.header("Upload an image")
    with st.form("upload_form"):
        uploaded = st.file_uploader(
            "Upload image(s) for players to caption", accept_multiple_files=True, type=['png','jpg','jpeg','gif']
        )
        submitted = st.form_submit_button("Upload")
    if submitted and uploaded:
        names = []
        for f in uploaded:
            saved = save_image(room_dir, f)
            names.append(saved)
        st.success(f"Saved {len(names)} image(s).")
        st.rerun()

    st.markdown("---")
    st.subheader("Images & captions")
    captions = load_captions(room_dir)
    img_files = sorted((room_dir / "images").glob("*"), key=os.path.getmtime, reverse=True)

    for img_path in img_files:
        img_name = img_path.name
        safe = keyify(img_name)

        # define unique keys
        flag_key = f"confirm_delete_flag_{safe}"  # session_state flag
        delete_btn_key = f"delete_btn_{safe}"  # Delete button widget key
        confirm_btn_key = f"confirm_btn_{safe}"  # Confirm button widget key
        cancel_btn_key = f"cancel_btn_{safe}"  # Cancel button widget key

        # initialize the session_state flag BEFORE creating any widgets
        if flag_key not in st.session_state:
            st.session_state[flag_key] = False

        st.image(str(img_path), width=700, caption=img_name)

        left, right = st.columns([4, 1])
        with left:
            cap_list = captions.get(img_name, [])
            if cap_list:
                st.write("**Captions:**")
                for i, c in enumerate(cap_list, 1):
                    st.write(f"{i}. **{c['player_name']}**: {c['text']}")
            else:
                st.write("_No captions yet_")

        with right:
            # Delete button sets the session_state flag (allowed because key exists)
            if st.button("Delete", key=delete_btn_key):
                st.session_state[flag_key] = True

        # If delete was requested, show a confirmation prompt with Confirm / Cancel
        if st.session_state.get(flag_key, False):
            st.warning(f"Are you sure you want to delete **{img_name}**? This will remove the image and its captions.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm delete", key=confirm_btn_key):
                    try:
                        delete_image_and_captions(room_dir, img_name, move_to_trash=True)
                        st.success(f"{img_name} deleted.")
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")
                    # reset flag and refresh UI
                    st.session_state[flag_key] = False
                    st.rerun()
            with c2:
                if st.button("Cancel", key=cancel_btn_key):
                    st.session_state[flag_key] = False
                    st.rerun()

# --- PLAYER UI: show images & submit captions ---
else:
    st.header("Player view — submit captions")
    # simple player identity (not secure, demo only)
    player_name = st.text_input("Your name (displayed with caption)", value="Player")
    st.markdown("Submit a caption to any image below.")
    captions = load_captions(room_dir)
    img_files = sorted((room_dir / "images").glob("*"), key=os.path.getmtime, reverse=True)

    if not img_files:
        st.info("No images uploaded yet. Ask the host to upload some.")
    else:
        for img_path in img_files:
            img_name = img_path.name
            st.image(str(img_path), width=600)

            with st.form(f"form_{img_name}"):
                caption_text = st.text_input("Your caption", key=f"input_{img_name}")
                submitted = st.form_submit_button("Submit caption")
                if submitted and caption_text.strip():
                    # load fresh to avoid overwrite
                    captions = load_captions(room_dir)
                    captions.setdefault(img_name, [])
                    captions[img_name].append({
                        "player_name": player_name or "Player",
                        "text": caption_text.strip(),
                        "ts": datetime.now(BERLIN).isoformat()
                    })
                    save_captions(room_dir, captions)
                    st.success("Caption submitted! (it will appear for the host)")
                    # optional: force a rerun so player sees the cleared form
                    st.rerun()

        # show recent captions (read-only)
        st.markdown("---")
        st.subheader("Recent captions")
        for img_name, caps in captions.items():
            st.write(f"**{img_name}** — {len(caps)} caption(s)")
            for c in caps[-5:]:
                st.write(f"- **{c['player_name']}**: {c['text']}")

