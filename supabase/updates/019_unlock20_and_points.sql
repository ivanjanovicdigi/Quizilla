-- Quizilla – unlock rule 20 answers + new point values (2026-10-23)
--   * Unlocking the next level now needs at least 20 answers on the current level (was 10),
--     still with at least 80 % of them correct. Levels / medals already unlocked stay (sticky).
--     Also the default for new topics.
--   * New points (quiz.config):
--         correct: easy +3, medium +5, hard +7      (first correct answer of a question only, as before)
--         wrong:   easy −1, medium −1, hard −2      (a total still never goes below 0)
--   * ALL existing answers are rescored with the new values, in answer order, with the same
--     rules as 013 (first-correct-only, floor at 0). Deterministic – running it again changes nothing.
--   NOTE: do not re-run 013_scoring.sql after this file – it would put the old values back.
-- Run after 018:  npm run q:import -- supabase/updates/019_unlock20_and_points.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ unlock rule
alter table quiz.topics alter column unlock_min_answers set default 20;
update quiz.topics set unlock_min_answers = 20 where unlock_min_answers <> 20;

-- ------------------------------------------------------------------ points
insert into quiz.config (key, value) values
  ('points_correct_1', '3'),
  ('points_correct_2', '5'),
  ('points_correct_3', '7'),
  ('points_wrong_1',   '-1'),
  ('points_wrong_2',   '-1'),
  ('points_wrong_3',   '-2')
on conflict (key) do update set value = excluded.value;

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

-- check: rule, point values, and no student below 0
select distinct unlock_min_answers, unlock_accuracy from quiz.topics;
select key, value from quiz.config where key like 'points%' order by key;
select count(*) as students_with_answers, min(x.total) as lowest_total, sum(x.total) as all_points
  from (select student_id, sum(points) as total from quiz.attempts group by student_id) x;
