-- REVIEW ONLY. Confirm athlete_profiles PK and privileges before running.
-- Phase 2: encrypted Garmin session ciphertext only. Apply manually after review.
-- This table contains no Garmin passwords, plain OAuth tokens, or encryption keys.
create table if not exists public.pf_garmin_sessions (
  athlete_id uuid primary key references public.athlete_profiles(id) on delete cascade,
  ciphertext text not null check (length(ciphertext) between 1 and 131072),
  updated_at timestamptz not null default now()
);
alter table public.pf_garmin_sessions enable row level security;
revoke all on public.pf_garmin_sessions from anon, authenticated;
-- No client-facing RLS policies: service_role is exclusively used by Python bridge.
-- Do not run this script until the athlete_profiles FK is verified in the target DB.

-- REVIEW ONLY: check the current schema before applying.
-- Requires pf_garmin_sessions(athlete_id uuid primary key, ciphertext text).
alter table public.pf_garmin_sessions
  add column if not exists revision bigint not null default 0;

create or replace function public.pf_garmin_session_cas(
  p_athlete uuid, p_expected_revision bigint, p_ciphertext text
) returns bigint
language plpgsql security definer
set search_path = ''
as $$
declare v_revision bigint;
begin
  if p_expected_revision < 0 or p_ciphertext is null
     or length(p_ciphertext) not between 1 and 131072 then
    raise exception 'invalid session update';
  end if;
  if p_expected_revision = 0 then
    insert into public.pf_garmin_sessions (athlete_id,ciphertext,revision)
    values (p_athlete,p_ciphertext,1)
    on conflict (athlete_id) do nothing
    returning revision into v_revision;
  else
    update public.pf_garmin_sessions
      set ciphertext=p_ciphertext, revision=revision+1, updated_at=now()
      where athlete_id=p_athlete and revision=p_expected_revision
      returning revision into v_revision;
  end if;
  return v_revision; -- null = concurrent update; never overwrite
end;
$$;
revoke all on function public.pf_garmin_session_cas(uuid,bigint,text) from public, anon, authenticated;
grant execute on function public.pf_garmin_session_cas(uuid,bigint,text) to service_role;
