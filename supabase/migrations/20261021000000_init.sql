-- =====================================================================
-- Quizilla – initial database schema
--
-- Design:
--   * All tables live in the private schema "quiz", which is NOT exposed
--     through the Supabase Data API. The browser cannot read or write any
--     table directly.
--   * The app talks to the database only through the public.* functions
--     below (called via /rest/v1/rpc/<name>). They are SECURITY DEFINER,
--     validate their input and never return answer keys before an answer
--     has been submitted.
--   * MVP identity: a student registers with school email + name + class
--     and gets back a random student id (uuid) that the app stores on the
--     device. No password / OAuth yet.
-- =====================================================================

create schema if not exists quiz;

-- ---------------------------------------------------------------------
-- Configuration
-- ---------------------------------------------------------------------
create table if not exists quiz.config (
  key   text primary key,
  value text not null
);

insert into quiz.config (key, value) values
  ('allowed_email_domains', 'lyceum.sk'),   -- comma separated list
  ('points_per_difficulty', '10')           -- points = difficulty * this, first correct answer only
on conflict (key) do nothing;

-- ---------------------------------------------------------------------
-- Classes & students
-- ---------------------------------------------------------------------
create table if not exists quiz.classes (
  id         smallint generated always as identity primary key,
  name       text not null unique,
  sort_order int  not null default 0,
  is_active  boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists quiz.students (
  id           uuid primary key default gen_random_uuid(),
  email        text not null unique check (email = lower(email)),
  name         text not null check (char_length(btrim(name)) between 2 and 80),
  class_id     smallint not null references quiz.classes(id),
  created_at   timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- Content: subjects -> topics -> questions
-- ---------------------------------------------------------------------
create table if not exists quiz.subjects (
  id         int generated always as identity primary key,
  slug       text not null unique,
  name_sk    text not null,
  name_en    text,
  sort_order int  not null default 0,
  is_active  boolean not null default true
);

create table if not exists quiz.topics (
  id                 int generated always as identity primary key,
  subject_id         int  not null references quiz.subjects(id) on delete cascade,
  slug               text not null,
  name_sk            text not null,
  name_en            text,
  description_sk     text,
  description_en     text,
  sort_order         int  not null default 0,
  is_active          boolean not null default true,
  -- Unlock rule for the NEXT level: at least unlock_min_answers answers on the
  -- current level AND accuracy of the last unlock_window answers >= unlock_accuracy.
  unlock_min_answers int not null default 10 check (unlock_min_answers > 0),
  unlock_window      int not null default 10 check (unlock_window > 0),
  unlock_accuracy    numeric(3,2) not null default 0.80 check (unlock_accuracy between 0 and 1),
  unique (subject_id, slug)
);

-- Levels of a topic are derived dynamically from the distinct difficulty
-- values of its active questions (e.g. difficulties 1,2,5 -> levels 1,2,3).
create table if not exists quiz.questions (
  id            bigint generated always as identity primary key,
  topic_id      int not null references quiz.topics(id) on delete cascade,
  difficulty    smallint not null check (difficulty between 1 and 10),
  body          text not null,             -- Markdown subset: paragraphs, `inline code`, ```csharp blocks```, **bold**
  answers       text[] not null check (array_length(answers, 1) = 4),
  correct_index smallint not null check (correct_index between 0 and 3),
  explanation   text,                      -- shown after answering (optional)
  -- English versions (optional; the app falls back to the Slovak columns above)
  body_en        text,
  answers_en     text[] check (answers_en is null or array_length(answers_en, 1) = 4),
  explanation_en text,
  is_active     boolean not null default true,
  created_at    timestamptz not null default now()
);
create index if not exists questions_topic_difficulty_idx
  on quiz.questions (topic_id, difficulty) where is_active;

-- ---------------------------------------------------------------------
-- Activity
-- ---------------------------------------------------------------------
create table if not exists quiz.attempts (
  id           bigint generated always as identity primary key,
  student_id   uuid     not null references quiz.students(id) on delete cascade,
  question_id  bigint   not null references quiz.questions(id) on delete cascade,
  topic_id     int      not null references quiz.topics(id) on delete cascade,
  difficulty   smallint not null,
  chosen_index smallint not null check (chosen_index between 0 and 3),
  is_correct   boolean  not null,
  points       int      not null default 0,   -- awarded only for the first correct answer of a question
  answered_at  timestamptz not null default now()
);
create index if not exists attempts_student_level_idx
  on quiz.attempts (student_id, topic_id, difficulty, answered_at desc, id desc);
create index if not exists attempts_student_question_idx
  on quiz.attempts (student_id, question_id);
create index if not exists attempts_points_idx
  on quiz.attempts (answered_at) where points > 0;

-- Unlocked levels are sticky: once unlocked, a level stays unlocked even if
-- accuracy later drops.
create table if not exists quiz.unlocks (
  student_id  uuid     not null references quiz.students(id) on delete cascade,
  topic_id    int      not null references quiz.topics(id) on delete cascade,
  difficulty  smallint not null,
  unlocked_at timestamptz not null default now(),
  primary key (student_id, topic_id, difficulty)
);

-- ---------------------------------------------------------------------
-- Lock everything down: no direct table access from the API roles
-- ---------------------------------------------------------------------
alter table quiz.config    enable row level security;
alter table quiz.classes   enable row level security;
alter table quiz.students  enable row level security;
alter table quiz.subjects  enable row level security;
alter table quiz.topics    enable row level security;
alter table quiz.questions enable row level security;
alter table quiz.attempts  enable row level security;
alter table quiz.unlocks   enable row level security;

revoke all on schema quiz from public, anon, authenticated;
revoke all on all tables in schema quiz from public, anon, authenticated;
revoke all on all sequences in schema quiz from public, anon, authenticated;
alter default privileges in schema quiz revoke all on tables from public, anon, authenticated;
alter default privileges in schema quiz revoke all on functions from public, anon, authenticated;

-- =====================================================================
-- Internal helpers (schema quiz, not callable from the API)
-- =====================================================================

create or replace function quiz.raise_error(p_code text)
returns void language plpgsql as $$
begin
  raise exception using message = p_code, errcode = 'P0001';
end $$;

-- Loads a student, refreshes last_seen_at, raises "unknown_student" if missing.
create or replace function quiz.require_student(p_student_id uuid)
returns quiz.students language plpgsql as $$
declare
  s quiz.students;
begin
  update quiz.students set last_seen_at = now()
   where id = p_student_id
  returning * into s;
  if not found then
    perform quiz.raise_error('unknown_student');
  end if;
  return s;
end $$;

create or replace function quiz.student_json(p_student_id uuid)
returns jsonb language sql stable as $$
  select jsonb_build_object(
           'id', s.id, 'email', s.email, 'name', s.name,
           'class_id', c.id, 'class_name', c.name)
    from quiz.students s
    join quiz.classes c on c.id = s.class_id
   where s.id = p_student_id;
$$;

-- Short public display name: "Ján Novák" -> "Ján N."
create or replace function quiz.short_name(p_name text)
returns text language sql immutable as $$
  select case
           when array_length(parts, 1) > 1
             then parts[1] || ' ' || left(parts[array_length(parts, 1)], 1) || '.'
           else parts[1]
         end
    from (select regexp_split_to_array(btrim(p_name), '\s+') as parts) x;
$$;

-- Computes per-level progress of a student in a topic and persists newly
-- reached unlocks. Returns:
-- { topic_id, unlock_min_answers, unlock_window, unlock_accuracy,
--   completed, points,
--   levels: [{ level, difficulty, question_count, unlocked, met,
--              total_answers, recent_total, recent_correct, mastered, points }] }
create or replace function quiz.topic_progress(p_student_id uuid, p_topic_id int)
returns jsonb language plpgsql as $$
declare
  t              quiz.topics;
  lvl            record;
  n              int := 0;
  is_first       boolean := true;
  prev_unlocked  boolean := true;
  prev_met       boolean := true;
  v_unlocked     boolean;
  v_met          boolean;
  v_total        int;
  v_recent_total int;
  v_recent_ok    int;
  v_mastered     int;
  v_points       int;
  v_sum_points   int := 0;
  levels         jsonb := '[]'::jsonb;
begin
  select * into t from quiz.topics where id = p_topic_id;
  if not found then
    return null;
  end if;

  for lvl in
    select q.difficulty, count(*)::int as question_count
      from quiz.questions q
     where q.topic_id = p_topic_id and q.is_active
     group by q.difficulty
     order by q.difficulty
  loop
    n := n + 1;

    v_unlocked := is_first
               or (prev_unlocked and prev_met)
               or exists (select 1 from quiz.unlocks u
                           where u.student_id = p_student_id
                             and u.topic_id   = p_topic_id
                             and u.difficulty = lvl.difficulty);

    if v_unlocked and not is_first then
      insert into quiz.unlocks (student_id, topic_id, difficulty)
      values (p_student_id, p_topic_id, lvl.difficulty)
      on conflict do nothing;
    end if;

    select count(*)::int,
           count(distinct a.question_id) filter (where a.is_correct)::int,
           coalesce(sum(a.points), 0)::int
      into v_total, v_mastered, v_points
      from quiz.attempts a
     where a.student_id = p_student_id
       and a.topic_id   = p_topic_id
       and a.difficulty = lvl.difficulty;

    select count(*)::int, count(*) filter (where r.is_correct)::int
      into v_recent_total, v_recent_ok
      from (select a.is_correct
              from quiz.attempts a
             where a.student_id = p_student_id
               and a.topic_id   = p_topic_id
               and a.difficulty = lvl.difficulty
             order by a.answered_at desc, a.id desc
             limit t.unlock_window) r;

    v_met := v_total >= t.unlock_min_answers
         and v_recent_total > 0
         and v_recent_ok::numeric / v_recent_total >= t.unlock_accuracy;

    v_sum_points := v_sum_points + v_points;

    levels := levels || jsonb_build_object(
      'level',          n,
      'difficulty',     lvl.difficulty,
      'question_count', lvl.question_count,
      'unlocked',       v_unlocked,
      'met',            v_met,
      'total_answers',  v_total,
      'recent_total',   v_recent_total,
      'recent_correct', v_recent_ok,
      'mastered',       v_mastered,
      'points',         v_points);

    prev_unlocked := v_unlocked;
    prev_met      := v_met;
    is_first      := false;
  end loop;

  return jsonb_build_object(
    'topic_id',           t.id,
    'unlock_min_answers', t.unlock_min_answers,
    'unlock_window',      t.unlock_window,
    'unlock_accuracy',    t.unlock_accuracy,
    'completed',          n > 0 and prev_met,
    'points',             v_sum_points,
    'levels',             levels);
end $$;

create or replace function quiz.topic_json(p_student_id uuid, p_topic_id int)
returns jsonb language sql as $$
  select jsonb_build_object(
           'id', t.id, 'slug', t.slug, 'subject_id', t.subject_id,
           'name_sk', t.name_sk, 'name_en', t.name_en,
           'description_sk', t.description_sk, 'description_en', t.description_en,
           'question_count', (select count(*) from quiz.questions q
                               where q.topic_id = t.id and q.is_active),
           'progress', quiz.topic_progress(p_student_id, t.id))
    from quiz.topics t
   where t.id = p_topic_id;
$$;

-- Points of all students in a period (null = all time), per student.
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
   group by s.id;
$$;

revoke all on all functions in schema quiz from public, anon, authenticated;

-- =====================================================================
-- Public API (POST /rest/v1/rpc/<function>)
-- =====================================================================

-- List of classes for the registration form.
create or replace function public.list_classes()
returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object('id', c.id, 'name', c.name)
                            order by c.sort_order, c.name), '[]'::jsonb)
    from quiz.classes c
   where c.is_active;
$$;

-- Register (or log back in on a new device). Email must belong to an
-- allowed domain. If the email already exists the name is updated but the
-- class is kept (class changes are done by the teacher in the database),
-- so points cannot be moved between competing classes.
create or replace function public.register_student(p_email text, p_name text, p_class_id int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_email   text := lower(btrim(coalesce(p_email, '')));
  v_name    text := regexp_replace(btrim(coalesce(p_name, '')), '\s+', ' ', 'g');
  v_domains text[];
  v_id      uuid;
begin
  select string_to_array(replace(value, ' ', ''), ',') into v_domains
    from quiz.config where key = 'allowed_email_domains';

  if v_email !~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
     or not (split_part(v_email, '@', 2) = any (v_domains)) then
    perform quiz.raise_error('invalid_email');
  end if;

  if char_length(v_name) < 2 or char_length(v_name) > 80 then
    perform quiz.raise_error('invalid_name');
  end if;

  select id into v_id from quiz.students where email = v_email;

  if v_id is null then
    if not exists (select 1 from quiz.classes where id = p_class_id and is_active) then
      perform quiz.raise_error('invalid_class');
    end if;
    insert into quiz.students (email, name, class_id)
    values (v_email, v_name, p_class_id)
    on conflict (email) do update set name = excluded.name
    returning id into v_id;
  else
    update quiz.students set name = v_name, last_seen_at = now() where id = v_id;
  end if;

  return quiz.student_json(v_id);
end $$;

-- Returns the student (or null) – used by the app to validate a stored session.
create or replace function public.get_student(p_student_id uuid)
returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  update quiz.students set last_seen_at = now() where id = p_student_id;
  return quiz.student_json(p_student_id);
end $$;

-- Subjects with their topics and the student's progress in each topic.
-- Only topics that have at least one active question are returned.
create or replace function public.get_catalog(p_student_id uuid)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
  v_subjects jsonb;
begin
  s := quiz.require_student(p_student_id);

  select coalesce(jsonb_agg(sub.obj order by sub.sort_order, sub.name_sk), '[]'::jsonb)
    into v_subjects
    from (
      select su.sort_order, su.name_sk,
             jsonb_build_object(
               'id', su.id, 'slug', su.slug,
               'name_sk', su.name_sk, 'name_en', su.name_en,
               'topics', (
                 select jsonb_agg(quiz.topic_json(s.id, t.id) order by t.sort_order, t.name_sk)
                   from quiz.topics t
                  where t.subject_id = su.id and t.is_active
                    and exists (select 1 from quiz.questions q
                                 where q.topic_id = t.id and q.is_active))) as obj
        from quiz.subjects su
       where su.is_active
         and exists (select 1 from quiz.topics t
                       join quiz.questions q on q.topic_id = t.id and q.is_active
                      where t.subject_id = su.id and t.is_active)
    ) sub;

  return jsonb_build_object(
    'student',  quiz.student_json(s.id),
    'points',   (select coalesce(sum(points), 0) from quiz.attempts where student_id = s.id),
    'subjects', v_subjects);
end $$;

-- One topic with progress.
create or replace function public.get_topic(p_student_id uuid, p_topic_id int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
  v jsonb;
begin
  s := quiz.require_student(p_student_id);
  select quiz.topic_json(s.id, t.id) into v
    from quiz.topics t where t.id = p_topic_id and t.is_active;
  if v is null then
    perform quiz.raise_error('unknown_topic');
  end if;
  return v;
end $$;

-- A batch of questions for an unlocked level. Questions the student has not
-- answered correctly yet come first, then random order. Answer keys are NOT
-- included.
create or replace function public.get_questions(p_student_id uuid, p_topic_id int,
                                                p_difficulty int, p_limit int default 10)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
  v_progress jsonb;
  v_unlocked boolean;
begin
  s := quiz.require_student(p_student_id);
  v_progress := quiz.topic_progress(s.id, p_topic_id);
  if v_progress is null then
    perform quiz.raise_error('unknown_topic');
  end if;

  select (e->>'unlocked')::boolean into v_unlocked
    from jsonb_array_elements(v_progress->'levels') e
   where (e->>'difficulty')::int = p_difficulty;

  if v_unlocked is null then
    perform quiz.raise_error('unknown_level');
  elsif not v_unlocked then
    perform quiz.raise_error('level_locked');
  end if;

  return (
    select coalesce(jsonb_agg(jsonb_build_object(
                     'id', x.id, 'difficulty', x.difficulty,
                     'body', x.body, 'answers', x.answers,
                     'body_en', x.body_en, 'answers_en', x.answers_en)
                   order by x.ever_correct, x.r), '[]'::jsonb)
      from (
        select q.id, q.difficulty, q.body, q.answers, q.body_en, q.answers_en,
               exists (select 1 from quiz.attempts a
                        where a.student_id = s.id and a.question_id = q.id and a.is_correct) as ever_correct,
               random() as r
          from quiz.questions q
         where q.topic_id = p_topic_id and q.difficulty = p_difficulty and q.is_active
         order by 7, 8
         limit least(greatest(coalesce(p_limit, 10), 1), 50)
      ) x);
end $$;

-- Records an answer and returns the result together with updated progress.
create or replace function public.submit_answer(p_student_id uuid, p_question_id bigint, p_chosen int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s           quiz.students;
  q           quiz.questions;
  v_before    jsonb;
  v_after     jsonb;
  v_unlocked  boolean;
  v_correct   boolean;
  v_points    int := 0;
  v_ppd       int;
  v_new       jsonb;
begin
  s := quiz.require_student(p_student_id);

  -- serialize answers of one student (prevents double points on double-tap)
  perform pg_advisory_xact_lock(hashtextextended(s.id::text, 0));

  select * into q from quiz.questions where id = p_question_id and is_active;
  if not found then
    perform quiz.raise_error('unknown_question');
  end if;
  if p_chosen is null or p_chosen not between 0 and 3 then
    perform quiz.raise_error('invalid_choice');
  end if;

  v_before := quiz.topic_progress(s.id, q.topic_id);
  select (e->>'unlocked')::boolean into v_unlocked
    from jsonb_array_elements(v_before->'levels') e
   where (e->>'difficulty')::int = q.difficulty;
  if not coalesce(v_unlocked, false) then
    perform quiz.raise_error('level_locked');
  end if;

  v_correct := (p_chosen = q.correct_index);

  if v_correct and not exists (select 1 from quiz.attempts
                                where student_id = s.id and question_id = q.id and is_correct) then
    select coalesce(value::int, 10) into v_ppd from quiz.config where key = 'points_per_difficulty';
    v_points := q.difficulty * coalesce(v_ppd, 10);
  end if;

  insert into quiz.attempts (student_id, question_id, topic_id, difficulty, chosen_index, is_correct, points)
  values (s.id, q.id, q.topic_id, q.difficulty, p_chosen, v_correct, v_points);

  v_after := quiz.topic_progress(s.id, q.topic_id);

  select coalesce(jsonb_agg(a->'level'), '[]'::jsonb) into v_new
    from jsonb_array_elements(v_after->'levels') a
    join jsonb_array_elements(v_before->'levels') b on b->'difficulty' = a->'difficulty'
   where (a->>'unlocked')::boolean and not (b->>'unlocked')::boolean;

  return jsonb_build_object(
    'correct',         v_correct,
    'correct_index',   q.correct_index,
    'explanation',     q.explanation,
    'explanation_en',  q.explanation_en,
    'points',          v_points,
    'newly_unlocked',  v_new,
    'progress',        v_after);
end $$;

-- Class vs class leaderboard. Ranked by average points per registered
-- student, so small and big classes compete fairly and every student counts.
-- p_days: null = all time, 7 = last week, ...
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
             count(s.id)                                            as students,
             count(s.id) filter (where sp.answers > 0)              as active_students,
             coalesce(sum(sp.points), 0)                            as points,
             round(coalesce(sum(sp.points), 0)::numeric / greatest(count(s.id), 1), 1) as avg_points,
             rank() over (order by coalesce(sum(sp.points), 0)::numeric / greatest(count(s.id), 1) desc) as rnk
        from quiz.classes c
        left join quiz.students s on s.class_id = c.id
        left join quiz.student_points(p_days) sp on sp.student_id = s.id
       where c.is_active
       group by c.id, c.name
    ) x;
$$;

-- Ranking of students inside the caller's class (classmates' names shortened).
create or replace function public.get_class_ranking(p_student_id uuid, p_days int default null)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
begin
  s := quiz.require_student(p_student_id);
  return jsonb_build_object(
    'class_id',   s.class_id,
    'class_name', (select name from quiz.classes where id = s.class_id),
    'students', (
      select coalesce(jsonb_agg(jsonb_build_object(
                       'name',   case when x.id = s.id then x.name else quiz.short_name(x.name) end,
                       'points', x.points,
                       'rank',   x.rnk,
                       'is_me',  x.id = s.id) order by x.rnk, x.name), '[]'::jsonb)
        from (
          select st.id, st.name, sp.points,
                 rank() over (order by sp.points desc) as rnk
            from quiz.students st
            join quiz.student_points(p_days) sp on sp.student_id = st.id
           where st.class_id = s.class_id
        ) x));
end $$;

-- API permissions: only these functions are callable by the app.
revoke all on function public.list_classes()                         from public;
revoke all on function public.register_student(text, text, int)     from public;
revoke all on function public.get_student(uuid)                      from public;
revoke all on function public.get_catalog(uuid)                      from public;
revoke all on function public.get_topic(uuid, int)                   from public;
revoke all on function public.get_questions(uuid, int, int, int)     from public;
revoke all on function public.submit_answer(uuid, bigint, int)       from public;
revoke all on function public.get_class_leaderboard(int)             from public;
revoke all on function public.get_class_ranking(uuid, int)           from public;

grant execute on function public.list_classes()                      to anon, authenticated;
grant execute on function public.register_student(text, text, int)  to anon, authenticated;
grant execute on function public.get_student(uuid)                   to anon, authenticated;
grant execute on function public.get_catalog(uuid)                   to anon, authenticated;
grant execute on function public.get_topic(uuid, int)                to anon, authenticated;
grant execute on function public.get_questions(uuid, int, int, int)  to anon, authenticated;
grant execute on function public.submit_answer(uuid, bigint, int)    to anon, authenticated;
grant execute on function public.get_class_leaderboard(int)          to anon, authenticated;
grant execute on function public.get_class_ranking(uuid, int)        to anon, authenticated;

-- =====================================================================
-- Teacher reports (run in the Supabase SQL editor / Table editor, export CSV)
-- =====================================================================

create or replace view quiz.v_student_totals as
select c.name                                   as class,
       s.name                                   as student,
       s.email,
       count(a.id)                              as answers,
       count(a.id) filter (where a.is_correct)  as correct,
       round(100.0 * count(a.id) filter (where a.is_correct) / nullif(count(a.id), 0), 1) as accuracy_pct,
       coalesce(sum(a.points), 0)               as points,
       max(a.answered_at)                       as last_answer_at,
       s.created_at                             as registered_at
  from quiz.students s
  join quiz.classes c on c.id = s.class_id
  left join quiz.attempts a on a.student_id = s.id
 group by c.name, s.id
 order by c.name, points desc;

create or replace view quiz.v_student_levels as
select c.name                                   as class,
       s.name                                   as student,
       s.email,
       su.name_sk                               as subject,
       t.name_sk                                as topic,
       a.difficulty,
       count(*)                                 as answers,
       count(*) filter (where a.is_correct)     as correct,
       round(100.0 * count(*) filter (where a.is_correct) / count(*), 1) as accuracy_pct,
       count(distinct a.question_id) filter (where a.is_correct) as questions_mastered,
       sum(a.points)                            as points,
       max(a.answered_at)                       as last_answer_at
  from quiz.attempts a
  join quiz.students s  on s.id  = a.student_id
  join quiz.classes  c  on c.id  = s.class_id
  join quiz.topics   t  on t.id  = a.topic_id
  join quiz.subjects su on su.id = t.subject_id
 group by c.name, s.id, su.name_sk, t.name_sk, a.difficulty
 order by c.name, s.name, su.name_sk, t.name_sk, a.difficulty;

create or replace view quiz.v_class_totals as
select c.name                                        as class,
       count(distinct s.id)                          as students,
       count(distinct a.student_id)                  as active_students,
       count(a.id)                                   as answers,
       coalesce(sum(a.points), 0)                    as points,
       round(coalesce(sum(a.points), 0)::numeric / greatest(count(distinct s.id), 1), 1) as avg_points_per_student
  from quiz.classes c
  left join quiz.students s on s.class_id = c.id
  left join quiz.attempts a on a.student_id = s.id
 group by c.name
 order by avg_points_per_student desc;

revoke all on quiz.v_student_totals, quiz.v_student_levels, quiz.v_class_totals
  from public, anon, authenticated;
