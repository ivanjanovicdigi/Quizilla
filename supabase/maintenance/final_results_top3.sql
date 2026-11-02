-- Quizilla – FINAL RESULTS: top 3 students by points (read-only, changes nothing)
--   Counts only answers given up to the cutoff 2026-11-02 23:59:59 Bratislava time
--   (= 2026-11-02 22:59:59 UTC). Answers after the cutoff are ignored, so the result
--   stays the same whenever you run it after midnight.
--   Only active roster students; the Teachers class (and with it the test accounts) is excluded.
--   Uses rank(): if students have the same points they share a place, so more than
--   3 rows can appear. Tie info: answers / correct / accuracy are shown for each row.
-- Run after midnight:  npm run q:import -- supabase/maintenance/final_results_top3.sql
-- Then type the names, classes and points into docs/final-results.html (podium graphic).
-- Safe to re-run.
begin;

with cutoff as (
  select timestamptz '2026-11-03 00:00:00 Europe/Bratislava' as t
),
pts as (
  select s.id,
         s.name,
         c.name                                          as class,
         greatest(coalesce(sum(a.points), 0), 0)::bigint as points,
         count(a.id)                                     as answers,
         count(a.id) filter (where a.is_correct)         as correct
    from quiz.students s
    join quiz.roster   r on r.email = s.email and r.is_active
    join quiz.classes  c on c.id = r.class_id
    left join quiz.attempts a
      on a.student_id = s.id
     and a.answered_at < (select t from cutoff)
   where c.name <> 'Teachers'
   group by s.id, s.name, c.name
),
ranked as (
  select rank() over (order by points desc) as place, *
    from pts
   where points > 0
)
-- after_cutoff = false -> you ran it before midnight, the numbers can still change.
select place, name, class, points, answers, correct,
       case when answers > 0 then round(100.0 * correct / answers, 1) end as accuracy_pct,
       now() >= (select t from cutoff) as after_cutoff
  from ranked
 where place <= 3
 order by place, name;

commit;
