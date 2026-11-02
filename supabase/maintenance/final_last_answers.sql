-- Quizilla – FINAL RESULTS: the last 10 students to answer before the cutoff (read-only, changes nothing)
--   One row per student: the time of their LAST answer before 2026-11-02 23:59:59 Bratislava time,
--   newest first. Answers after the cutoff are ignored, so the result stays the same after midnight.
--   Only active roster students; the Teachers class (and with it the test accounts) is excluded.
--   Columns: answered_at (Bratislava time, with milliseconds), name, class, topic, difficulty (1–3), correct,
--   points of that answer, and how many answers the student gave in total before the cutoff.
-- Run after midnight:  npm run q:import -- supabase/maintenance/final_last_answers.sql
-- Safe to re-run.
begin;

with cutoff as (
  select timestamptz '2026-11-03 00:00:00 Europe/Bratislava' as t
),
last_answer as (
  select distinct on (a.student_id)
         a.student_id, a.answered_at, a.topic_id, a.difficulty, a.is_correct, a.points
    from quiz.attempts a
   where a.answered_at < (select t from cutoff)
   order by a.student_id, a.answered_at desc, a.id desc
),
totals as (
  select a.student_id, count(*) as answers
    from quiz.attempts a
   where a.answered_at < (select t from cutoff)
   group by a.student_id
)
select to_char(la.answered_at at time zone 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS.MS') as answered_at,
       s.name,
       c.name        as class,
       tp.name_sk    as topic,
       la.difficulty as difficulty,
       la.is_correct as correct,
       la.points,
       t.answers     as total_answers
  from last_answer la
  join quiz.students s on s.id = la.student_id
  join quiz.roster   r on r.email = s.email and r.is_active
  join quiz.classes  c on c.id = r.class_id
  join quiz.topics  tp on tp.id = la.topic_id
  join totals        t on t.student_id = la.student_id
 where c.name <> 'Teachers'
 order by la.answered_at desc
 limit 10;

commit;
