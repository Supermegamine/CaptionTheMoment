# 📸 Caption The Moment

**A real-time, multiplayer party game where friends compete to write the funniest caption for a photo.**

Think *Cards Against Humanity* meets *Jackbox*: a host uploads a picture, players race to caption it from their own phones, and everyone laughs at the results together.

**🎮 Live demo:** [captionthemoment.onrender.com](https://captionthemoment.onrender.com/)

> ⚠️ The app is hosted on Render's free tier, so the first request after a period of inactivity can take **30–60 seconds** to spin up. Please be patient on the first load.

---

## What it does

- **Host a game** — create a room, upload one or more photos, and get a shareable link for your friends.
- **Play from any device** — players open the link on their own phone or laptop, pick a name, and submit a caption for each photo. No installs, no accounts.
- **Live updates** — captions and game state sync across all connected players in real time.
- **Reveal the winners** — the host reviews submissions and crowns a winning caption per photo, then reveals the results to everyone at once.

Built with [Streamlit](https://streamlit.io/) for the UI, [Supabase](https://supabase.com/) (Postgres + storage) for data and image hosting, and deployed on [Render](https://render.com/).

## How to test it

You'll need two browser windows (or tabs) to play both roles — the host and a player.

1. **Open the app** as the host: [captionthemoment.onrender.com](https://captionthemoment.onrender.com/)
2. **Create a room** using the host controls, then **upload a photo** (or a few).
3. **Copy the shareable player link** shown on the host screen.
4. **Open that link in a second tab** (or send it to a friend / open it on your phone) — this is the player view.
5. As the player, **enter a name** and **type a caption** for the photo, then submit.
6. Back in the host tab, watch the caption appear live, then **pick a winner** for each photo.
7. **Reveal the results** — both the host and player views update to show the winning caption.

Repeat with multiple player tabs to simulate a full group playing at once.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend / App | [Streamlit](https://streamlit.io/) (Python) |
| Database | [Supabase](https://supabase.com/) (PostgreSQL) |
| Image storage | Supabase Storage |
| Hosting | [Render](https://render.com/) (Docker) |

## Running it locally

```bash
git clone https://github.com/Supermegamine/CaptionTheMoment.git
cd CaptionTheMoment
pip install -r requirements.txt
streamlit run app.py
```

You'll need your own Supabase project (URL + API keys) configured via environment variables to connect the database and image storage.

## Project status

This is an actively developed side project — currently in progress is an upgrade from host-picks-the-winner to a full **voting-based gameplay loop** with distinct submit/reveal/results phases, player-cast votes, and emoji reactions. See [`docs/superpowers/specs`](docs/superpowers/specs) for the design write-up.
