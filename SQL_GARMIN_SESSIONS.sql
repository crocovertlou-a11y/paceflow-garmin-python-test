-- Execute once in Supabase SQL editor. Server-side service role only.
create table if not exists public.paceflow_garmin_sessions (
 athlete_id uuid primary key references public.athlete_profiles(id) on delete cascade,
 encrypted_tokens text not null,
 updated_at timestamptz not null default now()
);
alter table public.paceflow_garmin_sessions enable row level security;
revoke all on public.paceflow_garmin_sessions from anon, authenticated;
-- No RLS policies: only the trusted service-role server can access.
