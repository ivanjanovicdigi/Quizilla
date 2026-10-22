-- Quizilla – personal statistics per topic (2026-10-22)
--   get_stats(p_student_id, p_days) returns for every topic, besides the old fields:
--     points        – sum of the student's points in the topic (all time, may be negative
--                     because penalties are stored per answer; the overall total is ≥ 0)
--     tier_unlocked – is the topic's tier unlocked for the student
--     progress      – quiz.topic_progress (levels, unlocked, answers / correct per level,
--                     unlock rule) → current level and progress to the next unlock
--     trend         – running accuracy over ALL testing answers in the topic, in answer order:
--                     [[n, correct_so_far], …] – at most ~60 points (every k-th answer + the last)
--   The old fields answers / correct / days still honour p_days (null = all time).
--   Each student only ever gets their own data (the RPC takes the student id).
-- Run after 013:  npm run q:import -- supabase/updates/014_topic_stats.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ helpers
-- Running accuracy of a student in a topic, downsampled to about p_max points.
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

-- ------------------------------------------------------------------ API
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

-- check: topics in the trend helper work (expects one row per topic, no error)
select t.slug, jsonb_array_length(quiz.topic_trend(null, t.id)) as trend_points
  from quiz.topics t order by t.tier, t.sort_order;
