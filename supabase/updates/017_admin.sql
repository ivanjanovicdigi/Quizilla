-- Quizilla – admin account (2026-10-22)
--   * Typing the admin PHRASE instead of an email on the login page logs in as admin.
--     The phrase is NOT in this file (the repo is public). Only a salted SHA-256 hash is stored in
--     quiz.config (admin_passphrase_hash / admin_passphrase_salt). Set or change it once with:
--         select quiz.set_admin_passphrase('your phrase');
--     e.g. from a git-ignored file:  npm run q:import -- private/set_admin_passphrase.sql
--     Until a phrase is set, admin login is impossible.
--   * admin_login(phrase) → { ok, token, expires_at } – a random session token (valid
--     admin_session_hours, default 12). Only the token's hash is stored (quiz.admin_sessions).
--     Wrong phrases: at most 10 per 15 minutes (then { ok: false, error: 'too_many_attempts' }).
--   * Admin RPCs (all need p_token, error 'not_admin' otherwise):
--       admin_check(token)                       – { expires_at } or null
--       admin_logout(token)
--       admin_list_users(token)                  – roster with class, active, login, answers, points
--       admin_set_active(token, email, active)   – activate / deactivate a roster user
--                                                  (deactivated users are logged out on next start)
--       admin_reset_progress(token, email)       – deletes ALL progress of the user: answers/points,
--                                                  unlocked levels, topic passes, medals. Cannot be undone.
--   * Every admin action is written to quiz.admin_log.
-- Run after 016:  npm run q:import -- supabase/updates/017_admin.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ tables
create table if not exists quiz.admin_sessions (
  token_hash text primary key,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);

create table if not exists quiz.admin_login_failures (
  id bigint generated always as identity primary key,
  at timestamptz not null default now()
);

create table if not exists quiz.admin_log (
  id     bigint generated always as identity primary key,
  at     timestamptz not null default now(),
  action text not null,
  email  text,
  detail jsonb
);

alter table quiz.admin_sessions       enable row level security;
alter table quiz.admin_login_failures enable row level security;
alter table quiz.admin_log            enable row level security;
revoke all on quiz.admin_sessions, quiz.admin_login_failures, quiz.admin_log
  from public, anon, authenticated;

insert into quiz.config (key, value) values ('admin_session_hours', '12')
on conflict (key) do nothing;

-- ------------------------------------------------------------------ helpers
create or replace function quiz.sha256_hex(p text)
returns text language sql immutable as $$
  select encode(sha256(convert_to(p, 'UTF8')), 'hex');
$$;

-- Sets / changes the admin phrase (lower-cased, trimmed). Run by the owner only.
-- Also logs out every admin session.
create or replace function quiz.set_admin_passphrase(p_phrase text)
returns text language plpgsql as $$
declare
  v_phrase text := lower(btrim(coalesce(p_phrase, '')));
  v_salt   text := replace(gen_random_uuid()::text, '-', '');
begin
  if char_length(v_phrase) < 8 or v_phrase like '%@%' then
    raise exception 'admin phrase must have at least 8 characters and no @';
  end if;
  insert into quiz.config (key, value) values
    ('admin_passphrase_salt', v_salt),
    ('admin_passphrase_hash', quiz.sha256_hex(v_salt || v_phrase))
  on conflict (key) do update set value = excluded.value;
  delete from quiz.admin_sessions;
  insert into quiz.admin_log (action) values ('set_passphrase');
  return 'admin phrase set';
end $$;

create or replace function quiz.require_admin(p_token text)
returns void language plpgsql as $$
begin
  if p_token is null or not exists (
       select 1 from quiz.admin_sessions
        where token_hash = quiz.sha256_hex(p_token) and expires_at > now()) then
    perform quiz.raise_error('not_admin');
  end if;
end $$;

revoke all on function quiz.sha256_hex(text)            from public, anon, authenticated;
revoke all on function quiz.set_admin_passphrase(text)  from public, anon, authenticated;
revoke all on function quiz.require_admin(text)         from public, anon, authenticated;

-- ------------------------------------------------------------------ API
-- Returns { ok: true, token, expires_at } or { ok: false, error: 'invalid' | 'too_many_attempts' }.
-- (No exception on a wrong phrase, so the failure is recorded for the attempt limit.)
create or replace function public.admin_login(p_phrase text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_salt    text;
  v_hash    text;
  v_token   text;
  v_expires timestamptz;
begin
  delete from quiz.admin_login_failures where at < now() - interval '1 day';
  delete from quiz.admin_sessions where expires_at < now();

  if (select count(*) from quiz.admin_login_failures
       where at > now() - interval '15 minutes') >= 10 then
    return jsonb_build_object('ok', false, 'error', 'too_many_attempts');
  end if;

  select value into v_salt from quiz.config where key = 'admin_passphrase_salt';
  select value into v_hash from quiz.config where key = 'admin_passphrase_hash';
  if v_hash is null or v_salt is null
     or quiz.sha256_hex(v_salt || lower(btrim(coalesce(p_phrase, '')))) <> v_hash then
    insert into quiz.admin_login_failures default values;
    return jsonb_build_object('ok', false, 'error', 'invalid');
  end if;

  v_token   := replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', '');
  v_expires := now() + make_interval(hours => quiz.cfg_num('admin_session_hours', 12)::int);
  insert into quiz.admin_sessions (token_hash, expires_at) values (quiz.sha256_hex(v_token), v_expires);
  insert into quiz.admin_log (action) values ('login');
  return jsonb_build_object('ok', true, 'token', v_token, 'expires_at', v_expires);
end $$;

-- { expires_at } for a valid session, null otherwise (used to validate the stored session).
create or replace function public.admin_check(p_token text)
returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object('expires_at', s.expires_at)
    from quiz.admin_sessions s
   where s.token_hash = quiz.sha256_hex(coalesce(p_token, '')) and s.expires_at > now();
$$;

create or replace function public.admin_logout(p_token text)
returns void
language sql security definer set search_path = '' as $$
  delete from quiz.admin_sessions where token_hash = quiz.sha256_hex(coalesce(p_token, ''));
$$;

-- All roster users (also inactive) with their progress.
-- [{ email, name, class_id, class_name, is_active, student_id, logged_in, last_seen_at,
--    answers, points }]
create or replace function public.admin_list_users(p_token text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform quiz.require_admin(p_token);
  return (
    select coalesce(jsonb_agg(jsonb_build_object(
                     'email',        r.email,
                     'name',         r.name,
                     'class_id',     c.id,
                     'class_name',   c.name,
                     'is_active',    r.is_active,
                     'student_id',   s.id,
                     'logged_in',    s.id is not null,
                     'last_seen_at', s.last_seen_at,
                     'answers',      coalesce(a.answers, 0),
                     'points',       coalesce(a.points, 0))
                   order by c.sort_order, r.name), '[]'::jsonb)
      from quiz.roster r
      join quiz.classes c on c.id = r.class_id
      left join quiz.students s on s.email = r.email
      left join lateral (
        select count(*)::int as answers, sum(x.points)::int as points
          from quiz.attempts x where x.student_id = s.id
      ) a on true);
end $$;

create or replace function public.admin_set_active(p_token text, p_email text, p_active boolean)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_email text := lower(btrim(coalesce(p_email, '')));
begin
  perform quiz.require_admin(p_token);
  if p_active is null then
    perform quiz.raise_error('bad_request');
  end if;
  update quiz.roster set is_active = p_active, updated_at = now() where email = v_email;
  if not found then
    perform quiz.raise_error('unknown_user');
  end if;
  insert into quiz.admin_log (action, email) values (case when p_active then 'activate' else 'deactivate' end, v_email);
  return jsonb_build_object('email', v_email, 'is_active', p_active);
end $$;

-- Deletes ALL progress of one user (the account stays). Returns the deleted counts.
create or replace function public.admin_reset_progress(p_token text, p_email text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_email    text := lower(btrim(coalesce(p_email, '')));
  v_id       uuid;
  v_attempts int;
  v_unlocks  int;
  v_passes   int;
  v_clears   int;
  v_res      jsonb;
begin
  perform quiz.require_admin(p_token);
  if not exists (select 1 from quiz.roster where email = v_email) then
    perform quiz.raise_error('unknown_user');
  end if;
  select id into v_id from quiz.students where email = v_email;

  -- wait for an answer of this student that is being saved right now (same lock as submit_answer)
  if v_id is not null then
    perform pg_advisory_xact_lock(hashtextextended(v_id::text, 0));
  end if;

  delete from quiz.attempts     where student_id = v_id;  get diagnostics v_attempts = row_count;
  delete from quiz.unlocks      where student_id = v_id;  get diagnostics v_unlocks  = row_count;
  delete from quiz.topic_passes where student_id = v_id;  get diagnostics v_passes   = row_count;
  delete from quiz.level_clears where student_id = v_id;  get diagnostics v_clears   = row_count;

  v_res := jsonb_build_object('email', v_email, 'answers', v_attempts, 'unlocks', v_unlocks,
                              'passes', v_passes, 'medal_levels', v_clears);
  insert into quiz.admin_log (action, email, detail) values ('reset_progress', v_email, v_res);
  return v_res;
end $$;

revoke all on function public.admin_login(text)                     from public;
revoke all on function public.admin_check(text)                     from public;
revoke all on function public.admin_logout(text)                    from public;
revoke all on function public.admin_list_users(text)                from public;
revoke all on function public.admin_set_active(text, text, boolean) from public;
revoke all on function public.admin_reset_progress(text, text)      from public;
grant execute on function public.admin_login(text)                     to anon, authenticated;
grant execute on function public.admin_check(text)                     to anon, authenticated;
grant execute on function public.admin_logout(text)                    to anon, authenticated;
grant execute on function public.admin_list_users(text)                to anon, authenticated;
grant execute on function public.admin_set_active(text, text, boolean) to anon, authenticated;
grant execute on function public.admin_reset_progress(text, text)      to anon, authenticated;

commit;

-- check: is an admin phrase set?
select exists (select 1 from quiz.config where key = 'admin_passphrase_hash') as admin_phrase_set,
       (select count(*) from quiz.admin_sessions where expires_at > now())    as active_admin_sessions;
