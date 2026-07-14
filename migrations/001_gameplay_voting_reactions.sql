-- CaptionTheMoment — Gameplay upgrade migration
-- Phases, player identity, voting, reactions.
-- Run this in the Supabase SQL editor (or psql) against your project's database.
-- Safe to run once. Uses IF [NOT] EXISTS guards where possible.

-- ── rooms: add phase, retire finished ───────────────────────────────────────
alter table public.rooms
    add column if not exists phase text not null default 'submit';

-- Backfill phase from the old finished flag, if that column still exists.
do $$
begin
    if exists (
        select 1 from information_schema.columns
        where table_schema = 'public' and table_name = 'rooms' and column_name = 'finished'
    ) then
        update public.rooms set phase = 'results' where finished = true;
        alter table public.rooms drop column finished;
    end if;
end $$;

alter table public.rooms
    drop constraint if exists rooms_phase_check;
alter table public.rooms
    add constraint rooms_phase_check check (phase in ('submit', 'reveal', 'results'));

-- ── players ─────────────────────────────────────────────────────────────────
create table if not exists public.players (
    id           uuid primary key,
    room_id      uuid not null references public.rooms(id) on delete cascade,
    display_name text,
    created_at   timestamptz not null default now()
);
create index if not exists players_room_id_idx on public.players(room_id);

-- ── captions: add player_id, denormalized name kept, drop winner ─────────────
alter table public.captions
    add column if not exists player_id uuid references public.players(id) on delete set null;

alter table public.captions
    drop column if exists winner;

-- ── votes ─────────────────────────────────────────────────────────────────---
create table if not exists public.votes (
    id         uuid primary key,
    image_id   uuid not null references public.images(id) on delete cascade,
    caption_id uuid not null references public.captions(id) on delete cascade,
    voter_id   uuid not null references public.players(id) on delete cascade,
    created_at timestamptz not null default now(),
    unique (image_id, voter_id)
);
create index if not exists votes_caption_id_idx on public.votes(caption_id);
create index if not exists votes_image_id_idx on public.votes(image_id);

-- ── reactions ────────────────────────────────────────────────────────────────
create table if not exists public.reactions (
    id         uuid primary key,
    caption_id uuid not null references public.captions(id) on delete cascade,
    player_id  uuid not null references public.players(id) on delete cascade,
    emoji      text not null,
    created_at timestamptz not null default now(),
    unique (caption_id, player_id, emoji)
);
create index if not exists reactions_caption_id_idx on public.reactions(caption_id);
