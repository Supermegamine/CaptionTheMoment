# CaptionTheMoment — Gameplay Upgrade: Phases, Voting, Reactions, Identity

**Date:** 2026-06-23
**Status:** Approved (sections 1–3); host-as-player resolved to MC-only by default during implementation kickoff.

## Goal

Make the game more fun by adding a phased play loop with hidden captions, player voting
that decides winners, lightweight emoji reactions, stable player identity, and a periodic
auto-refresh so phase changes propagate without manual reloads.

## Feature Set (locked)

- **Phases** (room-wide, host-driven): `submit` → `reveal` → `results`.
- **Captions hidden** from other players during `submit`. The **host always sees** captions
  (for moderation) in every phase.
- **Voting decides the winner**: 1 vote per player per image, no self-voting. Per image, the
  caption with the most votes wins. Ties broken by earliest `created_at`.
- **Player identity**: a generated `player_id` (UUID) stored in the URL query params; display
  name set once via a join gate. Survives refresh.
- **Reactions**: fixed set of 4 emojis (😂 🔥 ❤️ 😮), available in `reveal` and `results`
  only, one of each emoji per player per caption, purely cosmetic (do not affect winner).
- **Auto-refresh**: periodic poll (~3s) so players pick up phase changes, new captions,
  votes, and reactions.
- **Host = MC only**: host runs phases and moderates; does not submit/vote. To play, a host
  opens a separate player link.

## Data Model (Approach A — normalized)

### Changed tables

**`rooms`**
- Add `phase TEXT NOT NULL DEFAULT 'submit'` — one of `submit` | `reveal` | `results`.
- `finished` boolean is superseded by `phase = 'results'`; drop it.

**`captions`**
- Add `player_id UUID` referencing the submitting player.
- Keep `player_name` denormalized on the row for display.
- Drop `winner BOOLEAN` — winner is derived from vote counts, not stored.

### New tables

**`players`**
- `id UUID PRIMARY KEY` (the player_id from the URL)
- `room_id UUID` (FK → rooms)
- `display_name TEXT`
- `created_at TIMESTAMP DEFAULT now()`

**`votes`**
- `id UUID PRIMARY KEY`
- `image_id UUID` (FK → images)
- `caption_id UUID` (FK → captions)
- `voter_id UUID` (FK → players)
- `created_at TIMESTAMP DEFAULT now()`
- `UNIQUE(image_id, voter_id)` — DB-enforced one vote per player per image. Re-voting
  updates the existing row.

**`reactions`**
- `id UUID PRIMARY KEY`
- `caption_id UUID` (FK → captions)
- `player_id UUID` (FK → players)
- `emoji TEXT` — one of the 4 allowed
- `created_at TIMESTAMP DEFAULT now()`
- `UNIQUE(caption_id, player_id, emoji)` — one of each emoji per player per caption.

### Winner derivation (at results)

For each image: winner = caption with the most `votes` rows; ties broken by earliest
caption `created_at`. No stored winner flag.

## Game Phases & Host Controls

State machine (room-wide):

```
SUBMIT --(Reveal & Open Voting)--> REVEAL --(Close Voting & Show Results)--> RESULTS
   ^                                  |                                         |
   +------(Back to Submit)------------+----------(Back to Voting)---------------+
```

Backward navigation **preserves** all captions, votes, and reactions.

| Phase    | Players can…                                              | Host sees…                                  |
|----------|----------------------------------------------------------|---------------------------------------------|
| SUBMIT   | Submit captions; cannot see others' captions             | All captions (moderation), counts, controls |
| REVEAL   | See all captions; vote (1/image, not own); react         | All captions + live tallies + reactions     |
| RESULTS  | See all captions, winners, final tallies; react          | Same results view; can reopen               |

**Host controls:**
- SUBMIT: "🎭 Reveal & Open Voting" → REVEAL
- REVEAL: "🏁 Close Voting & Show Results" → RESULTS; "◀ Back to Submit" → SUBMIT
- RESULTS: "◀ Back to Voting" → REVEAL
- "➕ Create New Room" retained.
- **Per-caption moderation**: host gets a 🗑️ on each caption in every phase to remove
  inappropriate entries (new; today only whole-image delete exists). Whole-image delete retained.

## Player Flow & Identity

- **First visit** (no `player_id`): generate UUID → write to URL → show "Enter your name to
  join" gate → insert `players` row → enter game.
- **Return/refresh**: `player_id` present → look up `players` row → skip gate.
- **Names not unique**: identity is the `player_id`; duplicate display names are allowed.
- **Name change**: small field updates `players.display_name` and re-labels the player's
  existing captions' denormalized `player_name`.
- **Stale/invalid `player_id`** (not found for this room): re-show name gate, create fresh row.
- **Known limitation**: sharing a link containing `player_id` hands over that identity. No
  auth was in scope; acceptable for a casual party game.

## Reactions

- Fixed 4: 😂 🔥 ❤️ 😮.
- Available in REVEAL and RESULTS only.
- One of each emoji per player per caption (toggle on/off); DB `UNIQUE` enforces it.
- Purely cosmetic — never affect the winner.
- Displayed as emoji + count next to each caption.

## Auto-refresh

- Add `streamlit-autorefresh` dependency; poll ~every 3 seconds on player and host views so
  phase transitions, new captions, votes, and reactions appear without manual reload.

## Code-health rider

The image/caption rendering is currently duplicated across the three views. Extract shared
helpers (e.g. `render_image`, `render_caption_card`) while implementing, to dedupe the code
being touched. No broader refactor of unrelated code.

## Migration & deployment note

Schema changes are delivered as a SQL migration file to be run manually in the Supabase SQL
editor. The app code targets the new schema. DDL is not applied to the hosted DB by the
implementation.

## Out of scope (deferred)

- Full real-time / websockets (only lightweight polling is in scope).
- Scoring/leaderboard across images, rounds, timers (not selected).
- Authentication / accounts.
- Host-as-player built-in mode.
