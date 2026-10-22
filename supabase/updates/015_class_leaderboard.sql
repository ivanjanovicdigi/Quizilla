-- Quizilla – global class leaderboard (2026-10-22)
--   * get_class_leaderboard() – visible to everyone (no student id needed). For every active
--     class (Lambda, Ró, Teachers): the class total = plain sum of the all-time points of its
--     students. Class membership comes from the roster (active roster rows only).
--     No averages, no student counts, no accuracy, no period switch (all time only).
--     Returns [{ class_id, name, points, rank }] in class order (sort_order).
--   * The old get_class_leaderboard(p_days) (with averages) is dropped.
--   * get_class_ranking (classmates' individual points, "My class" tab) is dropped –
--     students only see their own statistics.
-- Run after 014:  npm run q:import -- supabase/updates/015_class_leaderboard.sql   Safe to re-run.
begin;

drop function if exists public.get_class_ranking(uuid, int);
drop function if exists public.get_class_leaderboard(int);

create or replace function public.get_class_leaderboard()
returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object(
                   'class_id', x.id,
                   'name',     x.name,
                   'points',   x.points,
                   'rank',     x.rnk) order by x.sort_order, x.name), '[]'::jsonb)
    from (
      select c.id, c.name, c.sort_order, p.points,
             rank() over (order by p.points desc) as rnk
        from quiz.classes c
        cross join lateral (
          select coalesce(sum(a.points), 0)::bigint as points
            from quiz.roster r
            join quiz.students s on s.email = r.email
            join quiz.attempts a on a.student_id = s.id
           where r.class_id = c.id and r.is_active
        ) p
       where c.is_active
    ) x;
$$;

revoke all on function public.get_class_leaderboard() from public;
grant execute on function public.get_class_leaderboard() to anon, authenticated;

commit;

-- check
select jsonb_pretty(public.get_class_leaderboard());
