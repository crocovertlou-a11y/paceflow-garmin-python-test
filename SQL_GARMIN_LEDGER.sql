-- Apply in Supabase SQL editor before deploying Review 7.
-- Fail closed on errors. No browser/client grants to the ledger functions.
create table if not exists public.paceflow_garmin_send_ledger (
 athlete_id uuid not null references public.athlete_profiles(id),
 workout_id uuid not null references public.workouts(id),
 status text not null check (status in ('in_progress','sent','partial','uncertain','auth_failed')),
 garmin_workout_id text,
 updated_at timestamptz not null default now(),
 primary key (athlete_id, workout_id)
);
alter table public.paceflow_garmin_send_ledger enable row level security;
revoke all on public.paceflow_garmin_send_ledger from anon, authenticated;
create or replace function public.paceflow_garmin_claim(p_athlete uuid, p_workout uuid)
returns boolean language plpgsql security definer set search_path = '' as $$
begin
 if not exists (select 1 from public.workouts where id=p_workout and athlete_id=p_athlete) then
   return false;
 end if;
 insert into public.paceflow_garmin_send_ledger(athlete_id,workout_id,status)
 values(p_athlete,p_workout,'in_progress')
 on conflict (athlete_id,workout_id) do update
 set status='in_progress', garmin_workout_id=null, updated_at=now()
 where public.paceflow_garmin_send_ledger.status='auth_failed';
 return found;
end; $$;
create or replace function public.paceflow_garmin_finish(p_athlete uuid, p_workout uuid, p_status text, p_garmin_id text default null)
returns void language plpgsql security definer set search_path = '' as $$
begin
 if p_status not in ('sent','partial','uncertain','auth_failed') then raise exception 'Invalid status'; end if;
 update public.paceflow_garmin_send_ledger set status=p_status,
 garmin_workout_id=coalesce(p_garmin_id,garmin_workout_id), updated_at=now()
 where athlete_id=p_athlete and workout_id=p_workout and status='in_progress';
 if not found then raise exception 'No active send'; end if;
end; $$;
revoke all on function public.paceflow_garmin_claim(uuid,uuid) from public,anon,authenticated;
revoke all on function public.paceflow_garmin_finish(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.paceflow_garmin_claim(uuid,uuid) to service_role;
grant execute on function public.paceflow_garmin_finish(uuid,uuid,text,text) to service_role;
