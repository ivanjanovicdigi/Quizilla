-- Quizilla – admin: detailed statistics of any student (2026-10-26)
--   The admin page can open a student and see the same statistics the student sees on their
--   own Statistics page: ranks, tiers and per topic points, accuracy, level unlock progress, trend.
--   * quiz.stats_json(student_id, days) – builds the statistics JSON. Exact copy of the body of
--     public.get_stats from 020 (same output). get_stats itself is NOT changed by this file.
--     If get_stats ever changes, change quiz.stats_json the same way.
--   * admin_student_stats(token, email) – needs an admin token (error 'not_admin'). Returns the
--     statistics JSON, or null if the user has never logged in. Error 'unknown_user' if the email
--     is not in the roster. Works for deactivated users too. Does NOT change last_seen_at.
-- Run after 023:  npm run q:import -- supabase/updates/024_admin_student_stats.sql   Safe to re-run.
begin;

-- Statistics JSON of one student (no checks – callers check access).
create or replace function quiz.stats_json(p_student_id uuid, p_days int default null)
returns jsonb
language plpgsql set search_path = '' as $$
declare
  v_tiers jsonb;
begin
  v_tiers := quiz.tier_states(p_student_id);
  return jsonb_build_object(
    'tiers', v_tiers,
    'rank',  quiz.rank_json(p_student_id),
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
                       'progress', quiz.topic_progress(p_student_id, t.id),
                       'trend',    quiz.topic_trend(p_student_id, t.id))
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
                   where a.student_id = p_student_id and a.topic_id = t.id
                     and (p_days is null or a.answered_at >= now() - make_interval(days => p_days))
                   group by 1) x
        ) d on true
        left join lateral (
          select sum(a.points)::int as points
            from quiz.attempts a
           where a.student_id = p_student_id and a.topic_id = t.id
        ) p on true
       where t.is_active
         and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)));
end $$;

revoke all on function quiz.stats_json(uuid, int) from public, anon, authenticated;

create or replace function public.admin_student_stats(p_token text, p_email text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_email text := lower(btrim(coalesce(p_email, '')));
  v_id    uuid;
begin
  perform quiz.require_admin(p_token);
  if not exists (select 1 from quiz.roster where email = v_email) then
    perform quiz.raise_error('unknown_user');
  end if;
  select id into v_id from quiz.students where email = v_email;
  if v_id is null then
    return null; -- never logged in, no statistics yet
  end if;
  return quiz.stats_json(v_id, null);
end $$;

revoke all on function public.admin_student_stats(text, text) from public;
grant execute on function public.admin_student_stats(text, text) to anon, authenticated;

commit;

-- check: both functions exist (expect true, true)
select to_regprocedure('quiz.stats_json(uuid,int)') is not null             as stats_json_ok,
       to_regprocedure('public.admin_student_stats(text,text)') is not null as admin_student_stats_ok;
