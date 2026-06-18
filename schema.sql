-- Run this exact SQL in the Supabase SQL editor after creating the project.
-- It creates the projects table, an updated_at trigger, and an index for the
-- sync upsert key, and enables Row-Level Security (deny-all by default).

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- Projects table
create table public.projects (
  id                uuid primary key default gen_random_uuid(),
  title             text not null,
  slug              text not null unique,
  summary           text not null,
  tech_stack        text[] not null default '{}',
  highlights        text[] not null default '{}',
  repo_url          text,
  live_url          text,
  image_url         text,
  github_repo_name  text unique,
  readme_hash       text,
  source            text not null default 'manual'
                    check (source in ('github', 'manual')),
  ai_generated      boolean not null default false,
  manual_override   boolean not null default false,
  featured          boolean not null default false,
  display_order     integer not null default 0,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

-- Index for the sync upsert lookup
create index projects_github_repo_name_idx
  on public.projects (github_repo_name);

-- Auto-update updated_at on row modification
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger projects_updated_at
  before update on public.projects
  for each row execute function public.set_updated_at();

-- Row-Level Security: deny all by default, backend uses service key to bypass.
-- If the anon key ever leaked, it would return zero rows. Defense in depth.
alter table public.projects enable row level security;
