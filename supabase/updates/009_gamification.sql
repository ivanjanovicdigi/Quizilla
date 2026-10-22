-- Quizilla – gamification
--   * tiers: T1 = data-types, logic, cycles · T2 = functions, arrays, lists, classes · T3 = git
--   * a topic is PASSED with more than 30 answers on medium or harder and at least 75 % correct
--     (passes are sticky – once passed, always passed)
--   * a tier unlocks when ALL topics of the previous tier are passed
--   * ranks over all topics (at least 50 answers on the difficulty):
--       Padawan 95 % easy · Jedi 95 % medium · Master 95 % hard · Grand Master 99 % on every difficulty
--   * learning mode: check_answer() – nothing is recorded (no points, no progress)
--   * statistics: get_stats() – accuracy per topic per day
-- Only answers in testing mode are stored in quiz.attempts, so every rule above
-- counts testing answers only.
-- Run once:  npm run q:import -- supabase/updates/009_gamification.sql   (or SQL Editor). Safe to re-run.
begin;

-- ------------------------------------------------------------------ settings
insert into quiz.config (key, value) values
  ('topic_pass_min_answers',    '31'),    -- "more than 30" answers ...
  ('topic_pass_min_difficulty', '2'),     -- ... on medium (2) or harder ...
  ('topic_pass_accuracy',       '0.75'),  -- ... with at least 75 % correct
  ('rank_min_answers',          '50'),    -- answers needed on a difficulty before a rank counts
  ('rank_accuracy',             '0.95'),  -- Padawan / Jedi / Master
  ('rank_grand_accuracy',       '0.99')   -- Grand Master (every difficulty)
on conflict (key) do nothing;

-- ------------------------------------------------------------------ tiers
alter table quiz.topics add column if not exists tier smallint not null default 1;
alter table quiz.topics drop constraint if exists topics_tier_check;
alter table quiz.topics add constraint topics_tier_check check (tier between 1 and 9);

update quiz.topics set tier = 1 where slug in ('data-types', 'logic', 'cycles');
update quiz.topics set tier = 2 where slug in ('functions', 'arrays', 'lists', 'classes');
update quiz.topics set tier = 3 where slug in ('git');

-- passed topics (sticky)
create table if not exists quiz.topic_passes (
  student_id uuid not null references quiz.students(id) on delete cascade,
  topic_id   int  not null references quiz.topics(id)   on delete cascade,
  passed_at  timestamptz not null default now(),
  primary key (student_id, topic_id)
);
alter table quiz.topic_passes enable row level security;
revoke all on quiz.topic_passes from public, anon, authenticated;

create index if not exists attempts_student_time_idx
  on quiz.attempts (student_id, answered_at);

-- ------------------------------------------------------------------ helpers
create or replace function quiz.cfg_num(p_key text, p_default numeric)
returns numeric language sql stable as $$
  select coalesce((select value::numeric from quiz.config where key = p_key), p_default);
$$;

-- Pass state of one topic. Records the pass when the rule is met.
-- { min_answers, min_difficulty, accuracy, answers, correct, passed }
create or replace function quiz.topic_pass(p_student_id uuid, p_topic_id int)
returns jsonb language plpgsql as $$
declare
  v_min   int     := quiz.cfg_num('topic_pass_min_answers', 31)::int;
  v_diff  int     := quiz.cfg_num('topic_pass_min_difficulty', 2)::int;
  v_acc   numeric := quiz.cfg_num('topic_pass_accuracy', 0.75);
  v_total int;
  v_ok    int;
  v_passed boolean;
begin
  select count(*)::int, count(*) filter (where a.is_correct)::int
    into v_total, v_ok
    from quiz.attempts a
   where a.student_id = p_student_id
     and a.topic_id   = p_topic_id
     and a.difficulty >= v_diff;

  v_passed := v_total >= v_min and v_ok >= v_total * v_acc;

  if v_passed then
    insert into quiz.topic_passes (student_id, topic_id) values (p_student_id, p_topic_id)
    on conflict do nothing;
  else
    v_passed := exists (select 1 from quiz.topic_passes p
                         where p.student_id = p_student_id and p.topic_id = p_topic_id);
  end if;

  return jsonb_build_object(
    'min_answers',    v_min,
    'min_difficulty', v_diff,
    'accuracy',       v_acc,
    'answers',        v_total,
    'correct',        v_ok,
    'passed',         v_passed);
end $$;

-- All tiers with lock state and accuracy (all testing answers in the tier).
-- [{ tier, unlocked, topic_count, passed_count, answers, correct }]
create or replace function quiz.tier_states(p_student_id uuid)
returns jsonb language plpgsql as $$
declare
  r             record;
  tp            record;
  is_first      boolean := true;
  prev_unlocked boolean := true;
  prev_all      boolean := true;
  v_unlocked    boolean;
  v_count       int;
  v_passed      int;
  v_total       int;
  v_ok          int;
  res           jsonb := '[]'::jsonb;
begin
  for r in
    select distinct t.tier
      from quiz.topics t
     where t.is_active
       and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)
     order by t.tier
  loop
    v_unlocked := is_first or (prev_unlocked and prev_all);
    v_count  := 0;
    v_passed := 0;
    for tp in
      select t.id from quiz.topics t
       where t.tier = r.tier and t.is_active
         and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)
    loop
      v_count := v_count + 1;
      if (quiz.topic_pass(p_student_id, tp.id)->>'passed')::boolean then
        v_passed := v_passed + 1;
      end if;
    end loop;

    select count(*)::int, count(*) filter (where a.is_correct)::int
      into v_total, v_ok
      from quiz.attempts a
      join quiz.topics t on t.id = a.topic_id
     where a.student_id = p_student_id and t.tier = r.tier;

    res := res || jsonb_build_object(
      'tier',         r.tier,
      'unlocked',     v_unlocked,
      'topic_count',  v_count,
      'passed_count', v_passed,
      'answers',      v_total,
      'correct',      v_ok);

    prev_unlocked := v_unlocked;
    prev_all      := v_passed = v_count;
    is_first      := false;
  end loop;
  return res;
end $$;

create or replace function quiz.tier_unlocked(p_student_id uuid, p_tier int)
returns boolean language sql as $$
  select coalesce((select (e->>'unlocked')::boolean
                     from jsonb_array_elements(quiz.tier_states(p_student_id)) e
                    where (e->>'tier')::int = p_tier), false);
$$;

create or replace function quiz.require_playable(p_student_id uuid, p_topic_id int)
returns void language plpgsql as $$
declare
  v_tier int;
begin
  select tier into v_tier from quiz.topics where id = p_topic_id and is_active;
  if v_tier is null then
    perform quiz.raise_error('unknown_topic');
  end if;
  if not quiz.tier_unlocked(p_student_id, v_tier) then
    perform quiz.raise_error('tier_locked');
  end if;
end $$;

-- Ranks over all topics.
-- { current: 'padawan'|'jedi'|'master'|'grand_master'|null, min_answers,
--   ranks: [{ key, difficulty, accuracy, answers, correct, earned }] }
create or replace function quiz.rank_json(p_student_id uuid)
returns jsonb language plpgsql stable as $$
declare
  v_min   int     := quiz.cfg_num('rank_min_answers', 50)::int;
  v_acc   numeric := quiz.cfg_num('rank_accuracy', 0.95);
  v_grand numeric := quiz.cfg_num('rank_grand_accuracy', 0.99);
  d       record;
  v_ranks jsonb := '[]'::jsonb;
  v_key   text;
  v_earn  boolean;
  v_grand_ok boolean := true;
  v_grand_total int := 0;
  v_grand_correct int := 0;
  v_current text;
begin
  for d in
    select x.difficulty, x.key,
           coalesce(s.total, 0) as total, coalesce(s.ok, 0) as ok
      from (values (1, 'padawan'), (2, 'jedi'), (3, 'master')) as x(difficulty, key)
      left join (select a.difficulty, count(*)::int as total,
                        count(*) filter (where a.is_correct)::int as ok
                   from quiz.attempts a
                  where a.student_id = p_student_id
                  group by a.difficulty) s on s.difficulty = x.difficulty
     order by x.difficulty
  loop
    v_earn := d.total >= v_min and d.ok >= d.total * v_acc;
    if v_earn then v_current := d.key; end if;
    v_grand_ok := v_grand_ok and d.total >= v_min and d.ok >= d.total * v_grand;
    v_grand_total := v_grand_total + d.total;
    v_grand_correct := v_grand_correct + d.ok;
    v_ranks := v_ranks || jsonb_build_object(
      'key', d.key, 'difficulty', d.difficulty, 'accuracy', v_acc,
      'answers', d.total, 'correct', d.ok, 'earned', v_earn);
  end loop;

  if v_grand_ok then v_current := 'grand_master'; end if;
  v_ranks := v_ranks || jsonb_build_object(
    'key', 'grand_master', 'difficulty', null, 'accuracy', v_grand,
    'answers', v_grand_total, 'correct', v_grand_correct, 'earned', v_grand_ok);

  return jsonb_build_object('current', v_current, 'min_answers', v_min, 'ranks', v_ranks);
end $$;

-- topic now also carries its tier and pass state
create or replace function quiz.topic_json(p_student_id uuid, p_topic_id int)
returns jsonb language sql as $$
  select jsonb_build_object(
           'id', t.id, 'slug', t.slug, 'subject_id', t.subject_id, 'tier', t.tier,
           'name_sk', t.name_sk, 'name_en', t.name_en,
           'description_sk', t.description_sk, 'description_en', t.description_en,
           'question_count', (select count(*) from quiz.questions q
                               where q.topic_id = t.id and q.is_active),
           'progress', quiz.topic_progress(p_student_id, t.id),
           'pass',     quiz.topic_pass(p_student_id, t.id))
    from quiz.topics t
   where t.id = p_topic_id;
$$;

revoke all on all functions in schema quiz from public, anon, authenticated;

-- ------------------------------------------------------------------ API
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
                 select jsonb_agg(quiz.topic_json(s.id, t.id) order by t.tier, t.sort_order, t.name_sk)
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
    'tiers',    quiz.tier_states(s.id),
    'rank',     quiz.rank_json(s.id),
    'subjects', v_subjects);
end $$;

create or replace function public.get_topic(p_student_id uuid, p_topic_id int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
  v jsonb;
begin
  s := quiz.require_student(p_student_id);
  select quiz.topic_json(s.id, t.id)
         || jsonb_build_object('tier_unlocked', quiz.tier_unlocked(s.id, t.tier))
    into v
    from quiz.topics t where t.id = p_topic_id and t.is_active;
  if v is null then
    perform quiz.raise_error('unknown_topic');
  end if;
  return v;
end $$;

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
  perform quiz.require_playable(s.id, p_topic_id);

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

-- Testing mode: records the answer and returns the result with updated progress.
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
  v_was_passed boolean;
  v_pass      jsonb;
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
  perform quiz.require_playable(s.id, q.topic_id);

  v_before := quiz.topic_progress(s.id, q.topic_id);
  select (e->>'unlocked')::boolean into v_unlocked
    from jsonb_array_elements(v_before->'levels') e
   where (e->>'difficulty')::int = q.difficulty;
  if not coalesce(v_unlocked, false) then
    perform quiz.raise_error('level_locked');
  end if;
  v_was_passed := exists (select 1 from quiz.topic_passes
                           where student_id = s.id and topic_id = q.topic_id);

  v_correct := (p_chosen = q.correct_index);

  if v_correct and not exists (select 1 from quiz.attempts
                                where student_id = s.id and question_id = q.id and is_correct) then
    select coalesce(value::int, 10) into v_ppd from quiz.config where key = 'points_per_difficulty';
    v_points := q.difficulty * coalesce(v_ppd, 10);
  end if;

  insert into quiz.attempts (student_id, question_id, topic_id, difficulty, chosen_index, is_correct, points)
  values (s.id, q.id, q.topic_id, q.difficulty, p_chosen, v_correct, v_points);

  v_after := quiz.topic_progress(s.id, q.topic_id);
  v_pass  := quiz.topic_pass(s.id, q.topic_id);

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
    'newly_passed',    (v_pass->>'passed')::boolean and not v_was_passed,
    'pass',            v_pass,
    'progress',        v_after);
end $$;

-- Learning mode: checks the answer, records NOTHING.
create or replace function public.check_answer(p_student_id uuid, p_question_id bigint, p_chosen int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s          quiz.students;
  q          quiz.questions;
  v_progress jsonb;
  v_unlocked boolean;
begin
  s := quiz.require_student(p_student_id);

  select * into q from quiz.questions where id = p_question_id and is_active;
  if not found then
    perform quiz.raise_error('unknown_question');
  end if;
  if p_chosen is null or p_chosen not between 0 and 3 then
    perform quiz.raise_error('invalid_choice');
  end if;
  perform quiz.require_playable(s.id, q.topic_id);

  v_progress := quiz.topic_progress(s.id, q.topic_id);
  select (e->>'unlocked')::boolean into v_unlocked
    from jsonb_array_elements(v_progress->'levels') e
   where (e->>'difficulty')::int = q.difficulty;
  if not coalesce(v_unlocked, false) then
    perform quiz.raise_error('level_locked');
  end if;

  return jsonb_build_object(
    'correct',         p_chosen = q.correct_index,
    'correct_index',   q.correct_index,
    'explanation',     q.explanation,
    'explanation_en',  q.explanation_en,
    'points',          0,
    'newly_unlocked',  '[]'::jsonb,
    'newly_passed',    false,
    'progress',        v_progress);
end $$;

-- Statistics for the profile: tiers, ranks and accuracy per topic per day
-- (Slovak calendar days). p_days: null = everything, 30 = last 30 days, ...
create or replace function public.get_stats(p_student_id uuid, p_days int default null)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
begin
  s := quiz.require_student(p_student_id);
  return jsonb_build_object(
    'tiers', quiz.tier_states(s.id),
    'rank',  quiz.rank_json(s.id),
    'topics', (
      select coalesce(jsonb_agg(jsonb_build_object(
                       'id', t.id, 'slug', t.slug, 'tier', t.tier,
                       'name_sk', t.name_sk, 'name_en', t.name_en,
                       'answers', coalesce(d.answers, 0),
                       'correct', coalesce(d.correct, 0),
                       'days',    coalesce(d.days, '[]'::jsonb))
                     order by t.tier, t.sort_order), '[]'::jsonb)
        from quiz.topics t
        left join lateral (
          select sum(x.answers)::int as answers, sum(x.correct)::int as correct,
                 jsonb_agg(jsonb_build_object('day', x.day, 'answers', x.answers, 'correct', x.correct)
                           order by x.day) as days
            from (select (a.answered_at at time zone 'Europe/Bratislava')::date as day,
                         count(*)::int as answers,
                         count(*) filter (where a.is_correct)::int as correct
                    from quiz.attempts a
                   where a.student_id = s.id and a.topic_id = t.id
                     and (p_days is null or a.answered_at >= now() - make_interval(days => p_days))
                   group by 1) x
        ) d on true
       where t.is_active
         and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)));
end $$;

revoke all on function public.check_answer(uuid, bigint, int) from public;
revoke all on function public.get_stats(uuid, int)            from public;
grant execute on function public.check_answer(uuid, bigint, int) to anon, authenticated;
grant execute on function public.get_stats(uuid, int)            to anon, authenticated;

commit;

-- check
select t.tier, t.sort_order, t.slug,
       (select count(*) from quiz.questions q where q.topic_id = t.id and q.is_active) as questions
  from quiz.topics t order by t.tier, t.sort_order;
