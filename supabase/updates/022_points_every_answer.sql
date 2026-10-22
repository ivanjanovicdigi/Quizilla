-- Quizilla – every answer scores (2026-10-23)
--   Before: only the FIRST correct answer of a question gave points (repeats gave 0).
--   Now:    EVERY correct answer gives points (easy +3, medium +5, hard +7), also repeats.
--           Every wrong answer still deducts (easy −1, medium −1, hard −2); a total never goes
--           below 0 (unchanged).
--   Done with the existing switch quiz.config points_first_correct_only = 0 – submit_answer
--   already reads it. Set it back to 1 (and re-run the rescore) to return to first-correct-only.
--   ALL existing answers are rescored with the new rule, in answer order (same rescore as 019/021).
-- Run after 021:  npm run q:import -- supabase/updates/022_points_every_answer.sql   Safe to re-run.
begin;

insert into quiz.config (key, value) values ('points_first_correct_only', '0')
on conflict (key) do update set value = excluded.value;

-- ------------------------------------------------------------------ rescore (same as 019 / 021)
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

  raise notice '022: rescored attempts, % rows changed', v_changed;
end $$;

commit;

-- check: the switch is 0 and no total is below 0
select (select value from quiz.config where key = 'points_first_correct_only') as first_correct_only,
       count(*)                                                                  as students_with_answers,
       min(x.total)                                                              as lowest_total,
       sum(x.total)                                                              as all_points
  from (select student_id, sum(points) as total from quiz.attempts group by student_id) x;
