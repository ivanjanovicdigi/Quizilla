-- Quizilla – coding assignments: tables + student API (2026-11-05)
--   Students read a client brief, write a C# console app, and the app compiles and runs it
--   IN THE BROWSER against the assignment's test scenarios. The server stores every
--   submission and recomputes the score from the scenario points it holds (the browser only
--   says which scenarios passed). Spec: docs/prompts/coding-assignments-mvp.md
--
--   Tables (private schema quiz, RLS on, no direct access – same as every other table):
--     quiz.assignments             – one row per assignment; filled by the importer (031+)
--         scenarios           jsonb [{ name_sk, name_en, input, expected, points }] – sent to the app
--         design              jsonb – hidden reference design, NEVER returned by the API
--         reference_solution  text  – hidden, NEVER returned by the API
--     quiz.assignment_submissions  – every submission (code, compile errors, per-scenario results,
--                                    score). Unlimited; the LATEST one per assignment counts.
--     quiz.assignment_latest       – view: latest submission per student and assignment
--     quiz.v_assignment_scores     – report view for the SQL Editor (like v_student_totals)
--
--   Public RPCs (p_student_id null = guest: content only, nothing read or saved):
--     get_assignments(p_student_id)                         – list + my latest score
--     get_assignment(p_assignment_id, p_student_id)         – brief, scenarios, my latest submission
--     submit_assignment(p_student_id, p_assignment_id,      – saves one submission, returns score
--                       p_code, p_compiled, p_compile_errors, p_results)
--     get_assignment_submissions(p_student_id, p_assignment_id) – my history (no code)
--     get_assignment_submission(p_student_id, p_submission_id)  – one of my old submissions
--
--     assignments_enabled(p_student_id)                     – may this user see coding assignments?
--
--   ACCESS (while the feature is being built): quiz.config 'assignments_access' = comma separated
--   list of emails allowed to use assignments; '*' = everyone, guests included. Starts as
--   'ivan.janovic@lyceum.sk' only. Everyone else (and guests) gets error 'assignments_disabled'
--   from every assignment RPC. Re-running this file does NOT reset a changed value. Open it with:
--     update quiz.config set value = '*' where key = 'assignments_access';
--
--   Students only ever see their own submissions: every RPC that returns submissions filters
--   by the student id it was called with. Points do NOT count in totals yet – that is the next
--   update (stats + leaderboard integration).
--
-- Run after 029:  npm run q:import -- supabase/updates/030_coding_assignments.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ access

insert into quiz.config (key, value) values ('assignments_access', 'ivan.janovic@lyceum.sk')
on conflict (key) do nothing;

-- true when the student (null = guest) may use coding assignments
create or replace function quiz.assignments_access_ok(p_student_id uuid)
returns boolean language sql stable as $$
  select case
           when btrim(c.value) = '*' then true
           when p_student_id is null then false
           else exists (select 1 from quiz.students s
                         where s.id = p_student_id
                           and s.email = any (string_to_array(lower(replace(c.value, ' ', '')), ',')))
         end
    from (select coalesce((select value from quiz.config where key = 'assignments_access'), '') as value) c;
$$;

create or replace function quiz.require_assignments(p_student_id uuid)
returns void language plpgsql stable as $$
begin
  if not quiz.assignments_access_ok(p_student_id) then
    perform quiz.raise_error('assignments_disabled');
  end if;
end $$;

revoke all on function quiz.assignments_access_ok(uuid) from public, anon, authenticated;
revoke all on function quiz.require_assignments(uuid)   from public, anon, authenticated;

-- ------------------------------------------------------------------ tables

-- true when p is a non-empty array of well-formed scenarios whose points add up to p_total
create or replace function quiz.assignment_scenarios_ok(p jsonb, p_total int)
returns boolean language plpgsql immutable as $$
declare
  s     jsonb;
  v_sum int := 0;
begin
  if p is null or jsonb_typeof(p) <> 'array' or jsonb_array_length(p) not between 1 and 20 then
    return false;
  end if;
  for s in select * from jsonb_array_elements(p) loop
    if jsonb_typeof(s) <> 'object'
       or jsonb_typeof(s->'name_sk')  is distinct from 'string'
       or jsonb_typeof(s->'name_en')  is distinct from 'string'
       or jsonb_typeof(s->'input')    is distinct from 'string'
       or jsonb_typeof(s->'expected') is distinct from 'string'
       or jsonb_typeof(s->'points')   is distinct from 'number' then
      return false;
    end if;
    if (s->>'points') !~ '^[0-9]{1,4}$' or (s->>'points')::int = 0 then
      return false;   -- whole positive number of points
    end if;
    v_sum := v_sum + (s->>'points')::int;
  end loop;
  return v_sum = p_total;
end $$;

create table if not exists quiz.assignments (
  id                 int generated always as identity primary key,
  slug               text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{1,60}$'),
  subject_id         int references quiz.subjects(id) on delete set null,
  sort_order         int not null default 0,
  is_active          boolean not null default true,
  title_sk           text not null,
  title_en           text not null,
  brief_sk           text not null,            -- Markdown subset (same as questions)
  brief_en           text not null,
  max_points         int  not null default 100 check (max_points > 0),
  time_limit_ms      int  not null default 3000 check (time_limit_ms between 100 and 30000),
  scenarios          jsonb not null,
  design             jsonb,                    -- hidden
  reference_solution text,                     -- hidden
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  constraint assignments_scenarios_ok check (quiz.assignment_scenarios_ok(scenarios, max_points))
);

create table if not exists quiz.assignment_submissions (
  id             bigint generated always as identity primary key,
  student_id     uuid not null references quiz.students(id) on delete cascade,
  assignment_id  int  not null references quiz.assignments(id) on delete cascade,
  code           text not null check (char_length(code) between 1 and 100000),
  compiled       boolean not null,
  compile_errors jsonb not null default '[]' check (jsonb_typeof(compile_errors) = 'array'),
  -- [{ scenario, passed, points, actual }] – points = what the server awarded for that scenario
  results        jsonb not null default '[]' check (jsonb_typeof(results) = 'array'),
  score          int  not null check (score >= 0),
  max_points     int  not null check (max_points > 0),
  submitted_at   timestamptz not null default now()
);
create index if not exists assignment_submissions_latest_idx
  on quiz.assignment_submissions (student_id, assignment_id, submitted_at desc, id desc);

alter table quiz.assignments            enable row level security;
alter table quiz.assignment_submissions enable row level security;
revoke all on quiz.assignments, quiz.assignment_submissions from public, anon, authenticated;

-- Latest submission per student and assignment – the one that counts.
create or replace view quiz.assignment_latest as
  select distinct on (s.student_id, s.assignment_id) s.*
    from quiz.assignment_submissions s
   order by s.student_id, s.assignment_id, s.submitted_at desc, s.id desc;

-- Report: latest score of every student on every assignment they tried.
create or replace view quiz.v_assignment_scores as
  select c.name as class, st.name as student, st.email, a.slug as assignment,
         l.score, l.max_points, l.submitted_at as last_submitted_at,
         (select count(*) from quiz.assignment_submissions x
           where x.student_id = l.student_id and x.assignment_id = l.assignment_id) as submissions
    from quiz.assignment_latest l
    join quiz.students st on st.id = l.student_id
    join quiz.classes c   on c.id = st.class_id
    join quiz.assignments a on a.id = l.assignment_id
   order by c.name, st.name, a.sort_order, a.slug;

revoke all on quiz.assignment_latest, quiz.v_assignment_scores from public, anon, authenticated;

-- ------------------------------------------------------------------ helpers

-- Student-facing scenarios: name, input, expected output, points (+ index).
create or replace function quiz.assignment_public_scenarios(p jsonb)
returns jsonb language sql immutable as $$
  select coalesce(jsonb_agg(jsonb_build_object(
           'index', e.i - 1, 'name_sk', e.s->>'name_sk', 'name_en', e.s->>'name_en',
           'input', e.s->>'input', 'expected', e.s->>'expected',
           'points', (e.s->>'points')::int) order by e.i), '[]'::jsonb)
    from jsonb_array_elements(p) with ordinality as e(s, i);
$$;

create or replace function quiz.submission_json(s quiz.assignment_submissions, p_with_code boolean)
returns jsonb language sql stable as $$
  select jsonb_build_object(
           'id', s.id, 'assignment_id', s.assignment_id, 'submitted_at', s.submitted_at,
           'compiled', s.compiled, 'score', s.score, 'max_points', s.max_points,
           'passed', (select count(*) from jsonb_array_elements(s.results) r
                       where (r->>'passed')::boolean),
           'scenarios', jsonb_array_length(s.results))
      || case when p_with_code
              then jsonb_build_object('code', s.code, 'compile_errors', s.compile_errors,
                                      'results', s.results)
              else '{}'::jsonb end;
$$;

revoke all on function quiz.assignment_scenarios_ok(jsonb, int)                  from public, anon, authenticated;
revoke all on function quiz.assignment_public_scenarios(jsonb)                   from public, anon, authenticated;
revoke all on function quiz.submission_json(quiz.assignment_submissions, boolean) from public, anon, authenticated;

-- ------------------------------------------------------------------ public API

-- Should the app show coding assignments to this user (null = guest)? Never raises.
create or replace function public.assignments_enabled(p_student_id uuid default null)
returns boolean
language sql stable security definer set search_path = '' as $$
  select quiz.assignments_access_ok(p_student_id);
$$;

-- [{ id, slug, title_sk, title_en, max_points, scenario_count,
--    latest: null | { score, max_points, submitted_at }, submissions }]
create or replace function public.get_assignments(p_student_id uuid default null)
returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  if p_student_id is not null then
    perform quiz.require_student(p_student_id);
  end if;
  perform quiz.require_assignments(p_student_id);

  return coalesce((
    select jsonb_agg(jsonb_build_object(
             'id', a.id, 'slug', a.slug, 'title_sk', a.title_sk, 'title_en', a.title_en,
             'max_points', a.max_points, 'scenario_count', jsonb_array_length(a.scenarios),
             'latest', case when l.id is null then null else jsonb_build_object(
                         'score', l.score, 'max_points', l.max_points,
                         'submitted_at', l.submitted_at) end,
             'submissions', coalesce(n.cnt, 0))
           order by a.sort_order, a.slug)
      from quiz.assignments a
      left join quiz.assignment_latest l
             on l.assignment_id = a.id and l.student_id = p_student_id
      left join lateral (select count(*)::int as cnt from quiz.assignment_submissions x
                          where x.assignment_id = a.id and x.student_id = p_student_id) n on true
     where a.is_active), '[]'::jsonb);
end $$;

-- { id, slug, title_*, brief_*, max_points, time_limit_ms, scenarios: [...], latest: null | submission with code }
create or replace function public.get_assignment(p_assignment_id int, p_student_id uuid default null)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  a quiz.assignments;
  l quiz.assignment_submissions;
begin
  if p_student_id is not null then
    perform quiz.require_student(p_student_id);
  end if;
  perform quiz.require_assignments(p_student_id);

  select * into a from quiz.assignments where id = p_assignment_id and is_active;
  if not found then
    perform quiz.raise_error('unknown_assignment');
  end if;

  if p_student_id is not null then
    select s.* into l from quiz.assignment_submissions s
     where s.student_id = p_student_id and s.assignment_id = a.id
     order by s.submitted_at desc, s.id desc limit 1;
  end if;

  return jsonb_build_object(
    'id', a.id, 'slug', a.slug, 'title_sk', a.title_sk, 'title_en', a.title_en,
    'brief_sk', a.brief_sk, 'brief_en', a.brief_en,
    'max_points', a.max_points, 'time_limit_ms', a.time_limit_ms,
    'scenarios', quiz.assignment_public_scenarios(a.scenarios),
    'latest', case when l.id is null then null else quiz.submission_json(l, true) end);
end $$;

-- Saves one submission. p_results: [{ scenario: <index>, passed: bool, actual: text }].
-- The score is the sum of the stored points of the passed scenarios (0 if it did not compile).
-- Errors: unknown_student, unknown_assignment, invalid_code, invalid_results.
create or replace function public.submit_assignment(p_student_id uuid, p_assignment_id int,
                                                    p_code text, p_compiled boolean,
                                                    p_compile_errors jsonb, p_results jsonb)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  st      quiz.students;
  a       quiz.assignments;
  v_n     int;
  v_res   jsonb;
  v_score int;
  v_errs  jsonb;
  v_prev  int;
  s       quiz.assignment_submissions;
begin
  st := quiz.require_student(p_student_id);
  perform quiz.require_assignments(st.id);

  select * into a from quiz.assignments where id = p_assignment_id and is_active;
  if not found then
    perform quiz.raise_error('unknown_assignment');
  end if;

  if p_code is null or char_length(p_code) not between 1 and 100000 then
    perform quiz.raise_error('invalid_code');
  end if;
  if p_results is null or jsonb_typeof(p_results) <> 'array' then
    perform quiz.raise_error('invalid_results');
  end if;

  v_n := jsonb_array_length(a.scenarios);

  -- one row per scenario of the assignment, in order; missing / unknown entries = not passed
  select jsonb_agg(jsonb_build_object(
           'scenario', i,
           'passed',   coalesce(p_compiled, false) and coalesce(r.passed, false),
           'points',   case when coalesce(p_compiled, false) and coalesce(r.passed, false)
                            then (a.scenarios->i->>'points')::int else 0 end,
           'actual',   left(coalesce(r.actual, ''), 4000))
           order by i)
    into v_res
    from generate_series(0, v_n - 1) i
    left join lateral (
      select bool_or(case when jsonb_typeof(x->'passed') = 'boolean'
                          then (x->>'passed')::boolean else false end) as passed,
             max(x->>'actual') as actual
        from jsonb_array_elements(p_results) x
       where case when jsonb_typeof(x) = 'object'
                       and jsonb_typeof(x->'scenario') = 'number'
                       and (x->>'scenario') ~ '^[0-9]{1,4}$'
                  then (x->>'scenario')::int end = i
    ) r on true;

  select coalesce(sum((e->>'points')::int), 0) into v_score from jsonb_array_elements(v_res) e;

  -- keep at most 50 compile errors with line, column and message
  select coalesce(jsonb_agg(jsonb_build_object(
           'line',    case when (e->>'line')   ~ '^[0-9]{1,6}$' then (e->>'line')::int   end,
           'column',  case when (e->>'column') ~ '^[0-9]{1,6}$' then (e->>'column')::int end,
           'id',      left(e->>'id', 20),
           'message', left(coalesce(e->>'message', ''), 500))), '[]'::jsonb)
    into v_errs
    from (select e from jsonb_array_elements(
                   case when jsonb_typeof(p_compile_errors) = 'array' then p_compile_errors
                        else '[]'::jsonb end) e
           where jsonb_typeof(e) = 'object' limit 50) x;

  -- same per-student lock as submit_answer / admin_reset_progress
  perform pg_advisory_xact_lock(hashtextextended(st.id::text, 0));

  select score into v_prev from quiz.assignment_latest
   where student_id = st.id and assignment_id = a.id;

  insert into quiz.assignment_submissions
         (student_id, assignment_id, code, compiled, compile_errors, results, score, max_points)
  values (st.id, a.id, p_code, coalesce(p_compiled, false), v_errs, v_res, v_score, a.max_points)
  returning * into s;

  return quiz.submission_json(s, true)
      || jsonb_build_object('previous_score', v_prev,
                            'points_change', v_score - coalesce(v_prev, 0));
end $$;

-- My submissions of one assignment, newest first (no code). Max 100.
create or replace function public.get_assignment_submissions(p_student_id uuid, p_assignment_id int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform quiz.require_student(p_student_id);
  perform quiz.require_assignments(p_student_id);
  return coalesce((
    select jsonb_agg(quiz.submission_json(s, false) order by s.submitted_at desc, s.id desc)
      from (select * from quiz.assignment_submissions x
             where x.student_id = p_student_id and x.assignment_id = p_assignment_id
             order by x.submitted_at desc, x.id desc limit 100) s), '[]'::jsonb);
end $$;

-- One of my submissions with code and results. Error: unknown_submission (also for others' ids).
create or replace function public.get_assignment_submission(p_student_id uuid, p_submission_id bigint)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.assignment_submissions;
begin
  perform quiz.require_student(p_student_id);
  perform quiz.require_assignments(p_student_id);
  select * into s from quiz.assignment_submissions
   where id = p_submission_id and student_id = p_student_id;
  if not found then
    perform quiz.raise_error('unknown_submission');
  end if;
  return quiz.submission_json(s, true);
end $$;

revoke all on function public.assignments_enabled(uuid)                              from public;
revoke all on function public.get_assignments(uuid)                                  from public;
revoke all on function public.get_assignment(int, uuid)                              from public;
revoke all on function public.submit_assignment(uuid, int, text, boolean, jsonb, jsonb) from public;
revoke all on function public.get_assignment_submissions(uuid, int)                  from public;
revoke all on function public.get_assignment_submission(uuid, bigint)                from public;

grant execute on function public.assignments_enabled(uuid)                              to anon, authenticated;
grant execute on function public.get_assignments(uuid)                                  to anon, authenticated;
grant execute on function public.get_assignment(int, uuid)                              to anon, authenticated;
grant execute on function public.submit_assignment(uuid, int, text, boolean, jsonb, jsonb) to anon, authenticated;
grant execute on function public.get_assignment_submissions(uuid, int)                  to anon, authenticated;
grant execute on function public.get_assignment_submission(uuid, bigint)                to anon, authenticated;

commit;

-- check: tables exist and are private; 0 assignments until the importer runs
select (select count(*) from quiz.assignments)            as assignments,
       (select count(*) from quiz.assignment_submissions) as submissions,
       has_table_privilege('anon', 'quiz.assignments', 'select')            as anon_can_read_assignments,
       has_table_privilege('anon', 'quiz.assignment_submissions', 'select') as anon_can_read_submissions;
-- check: who may use assignments, and can that email log in (must be on the active roster)?
select (select value from quiz.config where key = 'assignments_access') as assignments_access,
       exists (select 1 from quiz.roster where email = 'ivan.janovic@lyceum.sk' and is_active) as ivan_on_roster;
