-- Quizilla – scoring repair + check of all updates (2026-10-23)
--   020 showed that in the live database submit_answer was still an OLD version (not 013) and
--   get_stats / topic_trend from 014 were missing – 013 and 014 were never applied there.
--   With the old submit_answer, new answers were scored with the old rules (no penalties,
--   old values). This file makes scoring right, whatever happened before:
--     * point values and unlock rule as in 019 (correct +3/+5/+7, wrong −1/−1/−2, 20 answers)
--     * quiz.answer_points (019), quiz.student_points (013, period sums floored at 0)
--     * public.submit_answer (013: new values, first correct answer only, total never below 0,
--       returns 'total')
--     * rescore of ALL answers with these rules (same as 013 / 019) – deterministic
--   The last query prints one row: is each update 012–020 live? (all should be true)
-- Run:  npm run q:import -- supabase/updates/021_scoring_repair.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ values (019)
insert into quiz.config (key, value) values ('points_first_correct_only', '1')
on conflict (key) do nothing;
insert into quiz.config (key, value) values
  ('points_correct_1', '3'),
  ('points_correct_2', '5'),
  ('points_correct_3', '7'),
  ('points_wrong_1',   '-1'),
  ('points_wrong_2',   '-1'),
  ('points_wrong_3',   '-2')
on conflict (key) do update set value = excluded.value;
delete from quiz.config where key = 'points_per_difficulty';

-- ------------------------------------------------------------------ unlock rule
alter table quiz.topics alter column unlock_min_answers set default 20;
update quiz.topics set unlock_min_answers = 20 where unlock_min_answers <> 20;


-- default values of the helper follow the new config (used only if a config row is missing)
create or replace function quiz.answer_points(p_difficulty int, p_correct boolean)
returns int language sql stable as $$
  select (case when p_correct
               then quiz.cfg_num('points_correct_' || d.d, (array[3, 5, 7])[d.d])
               else quiz.cfg_num('points_wrong_'   || d.d, (array[-1, -1, -2])[d.d])
          end)::int
    from (select least(greatest(coalesce(p_difficulty, 1), 1), 3) as d) d;
$$;
revoke all on function quiz.answer_points(int, boolean) from public, anon, authenticated;

-- Points of roster students in a period (null = all time), per student.
-- A period sum is floored at 0 (penalties in the period can outweigh points earned in it).
create or replace function quiz.student_points(p_days int)
returns table (student_id uuid, points bigint, answers bigint)
language sql stable as $$
  select s.id,
         greatest(coalesce(sum(a.points), 0), 0),
         count(a.id)
    from quiz.students s
    left join quiz.attempts a
      on a.student_id = s.id
     and (p_days is null or a.answered_at >= now() - make_interval(days => p_days))
   where quiz.on_roster(s.email)
   group by s.id;
$$;

revoke all on function quiz.student_points(int)         from public, anon, authenticated;

-- ------------------------------------------------------------------ API
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
  v_total     int;
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

  -- points: correct = configured value (first correct answer only, if configured);
  --         wrong   = penalty, cut so the total never goes below 0
  select coalesce(sum(points), 0)::int into v_total from quiz.attempts where student_id = s.id;
  if v_correct then
    if quiz.cfg_num('points_first_correct_only', 1) <> 1
       or not exists (select 1 from quiz.attempts
                       where student_id = s.id and question_id = q.id and is_correct) then
      v_points := quiz.answer_points(q.difficulty, true);
    end if;
  else
    v_points := -least(greatest(-quiz.answer_points(q.difficulty, false), 0), greatest(v_total, 0));
  end if;
  v_total := v_total + v_points;

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
    'total',           v_total,
    'newly_unlocked',  v_new,
    'newly_passed',    (v_pass->>'passed')::boolean and not v_was_passed,
    'pass',            v_pass,
    'progress',        v_after);
end $$;

revoke all on function public.submit_answer(uuid, bigint, int) from public;
grant execute on function public.submit_answer(uuid, bigint, int) to anon, authenticated;

-- ------------------------------------------------------------------ rescore (same as 013)
-- New answers wait until this transaction commits.
lock table quiz.attempts in exclusive mode;

do $$
declare
  v_first_only boolean := quiz.cfg_num('points_first_correct_only', 1) = 1;
  a          record;
  v_student  uuid;
  v_total    int := 0;
  v_points   int;
  v_changed  int := 0;
begin
  for a in
    select x.id, x.student_id, x.difficulty, x.is_correct, x.points,
           x.is_correct and row_number() over (partition by x.student_id, x.question_id, x.is_correct
                                               order by x.answered_at, x.id) = 1 as first_correct
      from quiz.attempts x
     order by x.student_id, x.answered_at, x.id
  loop
    if v_student is distinct from a.student_id then
      v_student := a.student_id;
      v_total   := 0;
    end if;

    if a.is_correct then
      v_points := case when a.first_correct or not v_first_only
                       then quiz.answer_points(a.difficulty, true) else 0 end;
    else
      v_points := -least(greatest(-quiz.answer_points(a.difficulty, false), 0), v_total);
    end if;
    v_total := v_total + v_points;

    if a.points is distinct from v_points then
      update quiz.attempts set points = v_points where id = a.id;
      v_changed := v_changed + 1;
    end if;
  end loop;

  raise notice '019: rescored attempts, % rows changed', v_changed;
end $$;

commit;

-- check (printed): which updates are live now? All columns should be true.
select
  position('topic_medal'   in pg_get_functiondef('quiz.topic_json(uuid,int)'::regprocedure)) > 0           as u012_medals,
  position('answer_points' in pg_get_functiondef('public.submit_answer(uuid,bigint,int)'::regprocedure)) > 0 as u013_scoring,
  position('topic_trend'   in pg_get_functiondef('public.get_stats(uuid,int)'::regprocedure)) > 0         as u014_stats,
  (to_regprocedure('public.get_class_leaderboard()') is not null
   and to_regprocedure('public.get_class_ranking(uuid,int)') is null)                                  as u015_leaderboard,
  to_regprocedure('public.get_guest_catalog()') is not null                                            as u016_guest,
  (to_regprocedure('public.admin_login(text)') is not null
   and exists (select 1 from quiz.config where key = 'admin_passphrase_hash'))                         as u017_admin,
  position('grand_master'  in pg_get_functiondef('quiz.topic_medal(uuid,int,jsonb)'::regprocedure)) > 0  as u018_grand_master,
  not exists (select 1 from quiz.topics where unlock_min_answers <> 20)                                as u019_unlock20,
  (select string_agg(value, ' ' order by key) from quiz.config
    where key in ('points_correct_1','points_correct_2','points_correct_3',
                  'points_wrong_1','points_wrong_2','points_wrong_3'))                                 as points_values,
  coalesce((select min(x.total) from (select sum(points) as total from quiz.attempts group by student_id) x), 0) >= 0
                                                                                                         as no_total_below_0;
