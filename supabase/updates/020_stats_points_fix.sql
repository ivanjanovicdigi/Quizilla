-- Quizilla – fix: topic points in Statistics show 0 (2026-10-23)
--   Statistics → "My topics" showed 0 points for every topic while Home showed points.
--   The app reads "points" per topic from get_stats (added in 014). A get_stats WITHOUT that
--   field (the older version from 009) makes every topic show 0. This happens when
--   009_gamification.sql is imported again after 014.
--   This file:
--     1. records which version of the key functions is live BEFORE the fix (printed at the end),
--     2. re-creates get_stats exactly as in 014 (with points, progress, trend).
--   If the printed check shows submit_answer_ok / topic_json_ok = false, 009 was re-run and
--   more functions are old – tell Claude before doing anything else (do NOT re-run 013).
-- Run:  npm run q:import -- supabase/updates/020_stats_points_fix.sql   Safe to re-run.

-- 1. what is live right now (before the fix)
drop table if exists pg_temp.quizilla_diag;
create temp table quizilla_diag as
select position('topic_trend'   in pg_get_functiondef('public.get_stats(uuid,int)'::regprocedure)) > 0         as get_stats_had_points,
       position('answer_points' in pg_get_functiondef('public.submit_answer(uuid,bigint,int)'::regprocedure)) > 0 as submit_answer_ok,
       position('topic_medal'   in pg_get_functiondef('quiz.topic_json(uuid,int)'::regprocedure)) > 0          as topic_json_ok,
       exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
                where n.nspname = 'quiz' and p.proname = 'topic_trend')                                     as topic_trend_exists;

begin;

-- 2. get_stats as in 014_topic_stats.sql
create or replace function quiz.topic_trend(p_student_id uuid, p_topic_id int, p_max int default 60)
returns jsonb language sql stable as $$
  with r as (
    select row_number() over w                          as n,
           count(*) filter (where a.is_correct) over w  as c,
           count(*) over ()                             as total
      from quiz.attempts a
     where a.student_id = p_student_id
       and a.topic_id   = p_topic_id
    window w as (order by a.answered_at, a.id rows between unbounded preceding and current row)
  )
  select coalesce(jsonb_agg(jsonb_build_array(r.n, r.c) order by r.n), '[]'::jsonb)
    from r
   where r.n = r.total
      or r.n % greatest(ceil(r.total::numeric / greatest(p_max, 1))::int, 1) = 0;
$$;
revoke all on function quiz.topic_trend(uuid, int, int) from public, anon, authenticated;

create or replace function public.get_stats(p_student_id uuid, p_days int default null)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s       quiz.students;
  v_tiers jsonb;
begin
  s := quiz.require_student(p_student_id);
  v_tiers := quiz.tier_states(s.id);
  return jsonb_build_object(
    'tiers', v_tiers,
    'rank',  quiz.rank_json(s.id),
    'topics', (
      select coalesce(jsonb_agg(jsonb_build_object(
                       'id', t.id, 'slug', t.slug, 'tier', t.tier,
                       'name_sk', t.name_sk, 'name_en', t.name_en,
                       'answers', coalesce(d.answers, 0),
                       'correct', coalesce(d.correct, 0),
                       'days',    coalesce(d.days, '[]'::jsonb),
                       'points',  coalesce(p.points, 0),
                       'tier_unlocked', coalesce((select (e->>'unlocked')::boolean
                                                    from jsonb_array_elements(v_tiers) e
                                                   where (e->>'tier')::int = t.tier), false),
                       'progress', quiz.topic_progress(s.id, t.id),
                       'trend',    quiz.topic_trend(s.id, t.id))
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
        left join lateral (
          select sum(a.points)::int as points
            from quiz.attempts a
           where a.student_id = s.id and a.topic_id = t.id
        ) p on true
       where t.is_active
         and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)));
end $$;

revoke all on function public.get_stats(uuid, int) from public;
grant execute on function public.get_stats(uuid, int) to anon, authenticated;

commit;

-- check (printed): state BEFORE the fix, and get_stats with points now
select d.*,
       position('topic_trend' in pg_get_functiondef('public.get_stats(uuid,int)'::regprocedure)) > 0 as get_stats_has_points_now
  from quizilla_diag d;
