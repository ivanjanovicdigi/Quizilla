-- Quizilla – FINAL RESULTS: total points per class / team (read-only, changes nothing)
--   Same rule as the in-app class leaderboard (get_class_leaderboard, 015): the plain sum of the
--   points of all active roster students in the class – but only answers given up to the cutoff
--   2026-11-02 23:59:59 Bratislava time. Answers after the cutoff are ignored.
--   The Teachers class (and with it the test accounts) is excluded; inactive classes too.
--   Columns: place, class, points, students (active roster students), players (answered at least once).
-- Run after midnight:  npm run q:import -- supabase/maintenance/final_class_scores.sql
-- Safe to re-run.
begin;

with cutoff as (
  select timestamptz '2026-11-03 00:00:00 Europe/Bratislava' as t
),
per_student as (
  select r.class_id,
         s.id                         as student_id,
         coalesce(sum(a.points), 0)   as points,
         count(a.id)                  as answers
    from quiz.roster r
    left join quiz.students s on s.email = r.email
    left join quiz.attempts a on a.student_id = s.id and a.answered_at < (select t from cutoff)
   where r.is_active
   group by r.class_id, r.email, s.id
)
select rank() over (order by coalesce(sum(p.points), 0) desc) as place,
       c.name                                        as class,
       coalesce(sum(p.points), 0)::bigint            as points,
       count(p.class_id)                             as students,
       count(*) filter (where p.answers > 0)         as players
  from quiz.classes c
  left join per_student p on p.class_id = c.id
 where c.is_active
   and c.name <> 'Teachers'
 group by c.id, c.name, c.sort_order
 order by place, c.sort_order, c.name;

commit;
