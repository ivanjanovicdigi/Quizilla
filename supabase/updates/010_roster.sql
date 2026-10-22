-- Quizilla – student roster (whitelist) and email-only login
--   * quiz.roster = the list of students allowed to use the app: email, name, class.
--     It is the source of truth – name and class of a student always come from the roster.
--   * login_student(p_email): the student types only the school email. If it is in the
--     roster (and active), the student is logged in; the app remembers the student on
--     the device. register_student (with free class choice) is removed.
--   * Existing students keep all progress (attempts, points, unlocks, passes): their row in
--     quiz.students is matched by email and only name / class are synced from the roster.
--   * A student removed from the roster (is_active = false) is logged out on the next app
--     start and cannot log in again. History is kept.
--   * Leaderboards count only students that are active in the roster.
-- Load the roster afterwards:  npm run q:roster -- private/roster.csv
-- Run once:  npm run q:import -- supabase/updates/010_roster.sql   (or SQL Editor). Safe to re-run.
begin;

-- ------------------------------------------------------------------ roster table
create table if not exists quiz.roster (
  email      text primary key
             check (email = lower(btrim(email)) and email ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'),
  name       text not null check (char_length(btrim(name)) between 2 and 80),
  class_id   smallint not null references quiz.classes(id),
  is_active  boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table quiz.roster enable row level security;
revoke all on quiz.roster from public, anon, authenticated;

-- Roster changes (import script, Table Editor, SQL) are copied to the student at once,
-- so a student who stays logged in on the device sees the new name / class too.
create or replace function quiz.roster_sync_student()
returns trigger language plpgsql as $$
begin
  update quiz.students st
     set name = new.name, class_id = new.class_id
   where st.email = new.email
     and (st.name, st.class_id) is distinct from (new.name, new.class_id);
  return null;
end $$;

drop trigger if exists roster_sync_student on quiz.roster;
create trigger roster_sync_student
  after insert or update of name, class_id on quiz.roster
  for each row execute function quiz.roster_sync_student();

-- ------------------------------------------------------------------ helpers
create or replace function quiz.on_roster(p_email text)
returns boolean language sql stable as $$
  select exists (select 1 from quiz.roster r where r.email = p_email and r.is_active);
$$;

-- Loads a student, refreshes last_seen_at, raises "unknown_student" if the student does
-- not exist or is no longer in the roster (the app then logs the device out).
create or replace function quiz.require_student(p_student_id uuid)
returns quiz.students language plpgsql as $$
declare
  s quiz.students;
begin
  update quiz.students st set last_seen_at = now()
   where st.id = p_student_id
     and quiz.on_roster(st.email)
  returning st.* into s;
  if not found then
    perform quiz.raise_error('unknown_student');
  end if;
  return s;
end $$;

-- Points of roster students in a period (null = all time), per student.
create or replace function quiz.student_points(p_days int)
returns table (student_id uuid, points bigint, answers bigint)
language sql stable as $$
  select s.id,
         coalesce(sum(a.points), 0),
         count(a.id)
    from quiz.students s
    left join quiz.attempts a
      on a.student_id = s.id
     and (p_days is null or a.answered_at >= now() - make_interval(days => p_days))
   where quiz.on_roster(s.email)
   group by s.id;
$$;

revoke all on function quiz.roster_sync_student()     from public, anon, authenticated;
revoke all on function quiz.on_roster(text)           from public, anon, authenticated;
revoke all on function quiz.require_student(uuid)     from public, anon, authenticated;
revoke all on function quiz.student_points(int)       from public, anon, authenticated;

-- ------------------------------------------------------------------ public API
drop function if exists public.register_student(text, text, int);

-- Login with the school email only. Errors: invalid_email, not_on_roster.
create or replace function public.login_student(p_email text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_email   text := lower(btrim(coalesce(p_email, '')));
  v_domains text[];
  r         quiz.roster;
  v_id      uuid;
begin
  select string_to_array(replace(value, ' ', ''), ',') into v_domains
    from quiz.config where key = 'allowed_email_domains';

  if v_email !~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
     or not (split_part(v_email, '@', 2) = any (v_domains)) then
    perform quiz.raise_error('invalid_email');
  end if;

  select * into r from quiz.roster where email = v_email and is_active;
  if not found then
    perform quiz.raise_error('not_on_roster');
  end if;

  insert into quiz.students (email, name, class_id)
  values (r.email, r.name, r.class_id)
  on conflict (email) do update
     set name = excluded.name, class_id = excluded.class_id, last_seen_at = now()
  returning id into v_id;

  return quiz.student_json(v_id);
end $$;

-- Returns the student, or null when unknown / no longer in the roster
-- (used by the app to validate the remembered session).
create or replace function public.get_student(p_student_id uuid)
returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  update quiz.students st set last_seen_at = now()
   where st.id = p_student_id
     and quiz.on_roster(st.email);
  if not found then
    return null;
  end if;
  return quiz.student_json(p_student_id);
end $$;

-- Class vs class leaderboard – only roster students count.
create or replace function public.get_class_leaderboard(p_days int default null)
returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object(
                   'class_id', x.id, 'name', x.name,
                   'students', x.students, 'active_students', x.active_students,
                   'points', x.points, 'avg_points', x.avg_points,
                   'rank', x.rnk) order by x.rnk, x.name), '[]'::jsonb)
    from (
      select c.id, c.name,
             count(sp.student_id)                                   as students,
             count(sp.student_id) filter (where sp.answers > 0)     as active_students,
             coalesce(sum(sp.points), 0)                            as points,
             round(coalesce(sum(sp.points), 0)::numeric / greatest(count(sp.student_id), 1), 1) as avg_points,
             rank() over (order by coalesce(sum(sp.points), 0)::numeric / greatest(count(sp.student_id), 1) desc) as rnk
        from quiz.classes c
        left join quiz.students s on s.class_id = c.id
        left join quiz.student_points(p_days) sp on sp.student_id = s.id
       where c.is_active
       group by c.id, c.name
    ) x;
$$;
-- (get_class_ranking needs no change: it joins quiz.student_points, which now skips
--  students that are not in the roster.)

revoke all on function public.login_student(text)          from public;
revoke all on function public.get_student(uuid)            from public;
revoke all on function public.get_class_leaderboard(int)   from public;
grant execute on function public.login_student(text)        to anon, authenticated;
grant execute on function public.get_student(uuid)          to anon, authenticated;
grant execute on function public.get_class_leaderboard(int) to anon, authenticated;

-- ------------------------------------------------------------------ teacher views
-- Students who have progress but are not (or no longer) in the roster – they cannot log in.
create or replace view quiz.v_students_not_on_roster as
select s.email, s.name, c.name as class, s.created_at as registered_at, s.last_seen_at,
       (select count(*) from quiz.attempts a where a.student_id = s.id) as answers
  from quiz.students s
  join quiz.classes c on c.id = s.class_id
 where not quiz.on_roster(s.email)
 order by c.name, s.name;

-- The roster with login state.
create or replace view quiz.v_roster as
select c.name as class, r.name, r.email, r.is_active,
       s.id is not null as has_logged_in, s.last_seen_at
  from quiz.roster r
  join quiz.classes c on c.id = r.class_id
  left join quiz.students s on s.email = r.email
 order by c.name, r.name;

revoke all on quiz.v_students_not_on_roster, quiz.v_roster from public, anon, authenticated;

commit;

-- check
select (select count(*) from quiz.roster where is_active)        as roster_active,
       (select count(*) from quiz.students)                      as students,
       (select count(*) from quiz.v_students_not_on_roster)      as students_not_on_roster;
