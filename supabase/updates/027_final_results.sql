-- Quizilla – admin: final results of the competition (2026-11-02)
--   The admin page gets a "Final results" presentation (src/components/FinalResults.svelte) that
--   loads live data but counts ONLY answers given before the cutoff, so it shows the same results
--   whenever it is opened after the cutoff (before it, the numbers are still moving).
--   * quiz.config 'final_cutoff' = '2026-11-03 00:00:00 Europe/Bratislava'
--     (= last counted moment 2026-11-02 23:59:59 Bratislava time). Answers at/after it are ignored.
--     To move it later:  update quiz.config set value = '<timestamp> Europe/Bratislava' where key = 'final_cutoff';
--   * admin_final_results(token) – needs an admin token (error 'not_admin'). Returns jsonb:
--       cutoff, now, is_final (now >= cutoff),
--       last    – last 10 students to answer before the cutoff (one row per student, newest first):
--                 answered_at ('YYYY-MM-DD HH24:MI:SS.MS', Bratislava time), name, class
--       top     – students with rank <= 3 by points (rank(): ties share a place):
--                 place, name, class, points, answers, correct
--       classes – per class: place, name, points, students (active roster rows), players (answered)
--     Only active roster students; the Teachers class (and the test accounts in it) is excluded.
--     Points = plain sums of attempts.points (same as get_class_leaderboard / admin_list_users).
--   Admin only: students never see other students' points.
-- Run:  npm run q:import -- supabase/updates/027_final_results.sql   Safe to re-run.
begin;

insert into quiz.config (key, value)
values ('final_cutoff', '2026-11-03 00:00:00 Europe/Bratislava')
on conflict (key) do nothing;

create or replace function quiz.final_cutoff()
returns timestamptz language sql stable set search_path = '' as $$
  select coalesce((select value::timestamptz from quiz.config where key = 'final_cutoff'),
                  timestamptz '2026-11-03 00:00:00 Europe/Bratislava');
$$;
revoke all on function quiz.final_cutoff() from public, anon, authenticated;

create or replace function public.admin_final_results(p_token text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_cut     timestamptz := quiz.final_cutoff();
  v_last    jsonb;
  v_top     jsonb;
  v_classes jsonb;
begin
  perform quiz.require_admin(p_token);

  select coalesce(jsonb_agg(jsonb_build_object(
           'answered_at', to_char(x.answered_at at time zone 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS.MS'),
           'name', x.name, 'class', x.class) order by x.answered_at desc), '[]'::jsonb)
    into v_last
    from (
      select fs.name, fs.class, max(a.answered_at) as answered_at
        from (select s.id as student_id, s.name, c.name as class
                 from quiz.roster r
                 join quiz.classes  c on c.id = r.class_id
                 join quiz.students s on s.email = r.email
                where r.is_active and c.name <> 'Teachers') fs
        join quiz.attempts a on a.student_id = fs.student_id and a.answered_at < v_cut
       group by fs.student_id, fs.name, fs.class
       order by max(a.answered_at) desc
       limit 10
    ) x;

  select coalesce(jsonb_agg(jsonb_build_object(
           'place', y.place, 'name', y.name, 'class', y.class,
           'points', y.points, 'answers', y.answers, 'correct', y.correct) order by y.place, y.name), '[]'::jsonb)
    into v_top
    from (
      select rank() over (order by p.points desc) as place, p.*
        from (
          select fs.name, fs.class,
                 coalesce(sum(a.points), 0)::bigint      as points,
                 count(a.id)                             as answers,
                 count(a.id) filter (where a.is_correct) as correct
            from (select s.id as student_id, s.name, c.name as class
                 from quiz.roster r
                 join quiz.classes  c on c.id = r.class_id
                 join quiz.students s on s.email = r.email
                where r.is_active and c.name <> 'Teachers') fs
            join quiz.attempts a on a.student_id = fs.student_id and a.answered_at < v_cut
           group by fs.student_id, fs.name, fs.class
        ) p
       where p.points > 0
    ) y
   where y.place <= 3;

  select coalesce(jsonb_agg(jsonb_build_object(
           'place', z.place, 'name', z.name, 'points', z.points,
           'students', z.students, 'players', z.players) order by z.place, z.sort_order, z.name), '[]'::jsonb)
    into v_classes
    from (
      select rank() over (order by coalesce(sum(ps.points), 0) desc) as place,
             c.name, c.sort_order,
             coalesce(sum(ps.points), 0)::bigint   as points,
             count(ps.email)                       as students,
             count(*) filter (where ps.answers > 0) as players
        from quiz.classes c
        left join (
          select r.class_id, r.email,
                 coalesce(sum(a.points), 0) as points,
                 count(a.id)                as answers
            from quiz.roster r
            left join quiz.students s on s.email = r.email
            left join quiz.attempts a on a.student_id = s.id and a.answered_at < v_cut
           where r.is_active
           group by r.class_id, r.email
        ) ps on ps.class_id = c.id
       where c.is_active and c.name <> 'Teachers'
       group by c.id, c.name, c.sort_order
    ) z;

  return jsonb_build_object(
    'cutoff',   v_cut,
    'now',      now(),
    'is_final', now() >= v_cut,
    'last',     v_last,
    'top',      v_top,
    'classes',  v_classes);
end $$;

revoke all on function public.admin_final_results(text) from public;
grant execute on function public.admin_final_results(text) to anon, authenticated;

commit;

-- check: functions exist and the cutoff (expect true, true, 2026-11-02 23:00:00+00)
select to_regprocedure('quiz.final_cutoff()') is not null               as final_cutoff_ok,
       to_regprocedure('public.admin_final_results(text)') is not null  as admin_final_results_ok,
       quiz.final_cutoff()                                             as cutoff;
