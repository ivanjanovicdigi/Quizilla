-- Quizilla – coding assignment points count with quiz points (2026-11-05)
--   Each coding assignment adds the score of its LATEST submission (030) to the student's points –
--   resubmitting replaces the old score, it never adds up. Quiz scoring itself is unchanged:
--   penalties still only cut quiz points (attempts), never assignment points, so the "never below
--   0" rule keeps working; total = quiz points + assignment points.
--
--   New helpers:
--     quiz.assignment_points(student)      – sum of latest scores (all assignments, also hidden ones)
--     quiz.assignment_stats_json(student)  – the "assignments" section of the statistics, or null
--                                            when the student has no access (030) and no submissions
--   Changed (copied from their latest definition, only the points part changed):
--     public.get_catalog          (009) – 'points' = quiz + assignment points (home page)
--     public.get_class_leaderboard (015) – class totals include assignment points
--     public.admin_list_users     (017) – 'points' = total, new 'assignment_points'
--     public.admin_reset_progress (017) – also deletes coding assignment submissions
--     public.get_stats            (020) – now = quiz.stats_json (024, identical body) + 'assignments'
--     public.admin_student_stats  (024) – same + 'assignments'
--     quiz.v_student_totals, quiz.v_class_totals – new columns assignment_points, total_points
--   NOT changed: admin_final_results (027) – the final results counted answers before
--   2026-11-03 only, so they stay as they were.
--
-- Run after 031:  npm run q:import -- supabase/updates/032_assignment_points.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ helpers

create or replace function quiz.assignment_points(p_student_id uuid)
returns int language sql stable as $$
  select coalesce(sum(l.score), 0)::int
    from quiz.assignment_latest l
   where l.student_id = p_student_id;
$$;

-- { points, max_points, done, tried, count, items: [{ id, slug, title_sk, title_en, score, max_points,
--   submissions, submitted_at }] } – null when the student cannot use assignments and never did.
create or replace function quiz.assignment_stats_json(p_student_id uuid)
returns jsonb language sql stable as $$
  with items as (
    select a.id, a.slug, a.title_sk, a.title_en, a.sort_order, a.is_active,
           coalesce(l.max_points, a.max_points) as max_points,
           l.score, l.submitted_at,
           (select count(*)::int from quiz.assignment_submissions x
             where x.student_id = p_student_id and x.assignment_id = a.id) as submissions
      from quiz.assignments a
      left join quiz.assignment_latest l on l.assignment_id = a.id and l.student_id = p_student_id
     where a.is_active or l.id is not null
  )
  select case
           when not quiz.assignments_access_ok(p_student_id)
                and not exists (select 1 from items where score is not null) then null
           else jsonb_build_object(
             'points',     coalesce((select sum(score) from items), 0)::int,
             'max_points', coalesce((select sum(max_points) from items where is_active), 0)::int,
             'done',       (select count(*) from items where score = max_points)::int,
             'tried',      (select count(*) from items where score is not null)::int,
             'count',      (select count(*) from items where is_active)::int,
             'items',      coalesce((select jsonb_agg(jsonb_build_object(
                                       'id', id, 'slug', slug, 'title_sk', title_sk, 'title_en', title_en,
                                       'score', score, 'max_points', max_points,
                                       'submissions', submissions, 'submitted_at', submitted_at)
                                     order by sort_order, slug) from items), '[]'::jsonb))
         end;
$$;

revoke all on function quiz.assignment_points(uuid)     from public, anon, authenticated;
revoke all on function quiz.assignment_stats_json(uuid) from public, anon, authenticated;

-- ------------------------------------------------------------------ home page points (009 + assignments)

create or replace function public.get_catalog(p_student_id uuid)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
  v_subjects jsonb;
begin
  s := quiz.require_student(p_student_id);

  select coalesce(jsonb_agg(sub.obj order by sub.sort_order, sub.name_sk), '[]'::jsonb)
    into v_subjects
    from (
      select su.sort_order, su.name_sk,
             jsonb_build_object(
               'id', su.id, 'slug', su.slug,
               'name_sk', su.name_sk, 'name_en', su.name_en,
               'topics', (
                 select jsonb_agg(quiz.topic_json(s.id, t.id) order by t.tier, t.sort_order, t.name_sk)
                   from quiz.topics t
                  where t.subject_id = su.id and t.is_active
                    and exists (select 1 from quiz.questions q
                                 where q.topic_id = t.id and q.is_active))) as obj
        from quiz.subjects su
       where su.is_active
         and exists (select 1 from quiz.topics t
                       join quiz.questions q on q.topic_id = t.id and q.is_active
                      where t.subject_id = su.id and t.is_active)
    ) sub;

  return jsonb_build_object(
    'student',  quiz.student_json(s.id),
    'points',   (select coalesce(sum(points), 0) from quiz.attempts where student_id = s.id)
                + quiz.assignment_points(s.id),
    'tiers',    quiz.tier_states(s.id),
    'rank',     quiz.rank_json(s.id),
    'subjects', v_subjects);
end $$;

-- ------------------------------------------------------------------ class leaderboard (015 + assignments)

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
          select coalesce(sum(coalesce(q.points, 0) + quiz.assignment_points(s.id)), 0)::bigint as points
            from quiz.roster r
            join quiz.students s on s.email = r.email
            left join lateral (select sum(a.points) as points from quiz.attempts a
                                where a.student_id = s.id) q on true
           where r.class_id = c.id and r.is_active
        ) p
       where c.is_active
    ) x;
$$;

-- ------------------------------------------------------------------ admin (017 + assignments)

create or replace function public.admin_list_users(p_token text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform quiz.require_admin(p_token);
  return (
    select coalesce(jsonb_agg(jsonb_build_object(
                     'email',        r.email,
                     'name',         r.name,
                     'class_id',     c.id,
                     'class_name',   c.name,
                     'is_active',    r.is_active,
                     'student_id',   s.id,
                     'logged_in',    s.id is not null,
                     'last_seen_at', s.last_seen_at,
                     'answers',      coalesce(a.answers, 0),
                     'points',       coalesce(a.points, 0) + coalesce(ap.points, 0),
                     'assignment_points', coalesce(ap.points, 0))
                   order by c.sort_order, r.name), '[]'::jsonb)
      from quiz.roster r
      join quiz.classes c on c.id = r.class_id
      left join quiz.students s on s.email = r.email
      left join lateral (
        select count(*)::int as answers, sum(x.points)::int as points
          from quiz.attempts x where x.student_id = s.id
      ) a on true
      left join lateral (select quiz.assignment_points(s.id) as points where s.id is not null) ap on true);
end $$;

create or replace function public.admin_reset_progress(p_token text, p_email text)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  v_email    text := lower(btrim(coalesce(p_email, '')));
  v_id       uuid;
  v_attempts int;
  v_unlocks  int;
  v_passes   int;
  v_clears   int;
  v_subs     int;
  v_res      jsonb;
begin
  perform quiz.require_admin(p_token);
  if not exists (select 1 from quiz.roster where email = v_email) then
    perform quiz.raise_error('unknown_user');
  end if;
  select id into v_id from quiz.students where email = v_email;

  -- wait for an answer of this student that is being saved right now (same lock as submit_answer)
  if v_id is not null then
    perform pg_advisory_xact_lock(hashtextextended(v_id::text, 0));
  end if;

  delete from quiz.attempts               where student_id = v_id;  get diagnostics v_attempts = row_count;
  delete from quiz.unlocks                where student_id = v_id;  get diagnostics v_unlocks  = row_count;
  delete from quiz.topic_passes           where student_id = v_id;  get diagnostics v_passes   = row_count;
  delete from quiz.level_clears           where student_id = v_id;  get diagnostics v_clears   = row_count;
  delete from quiz.assignment_submissions where student_id = v_id;  get diagnostics v_subs     = row_count;

  v_res := jsonb_build_object('email', v_email, 'answers', v_attempts, 'unlocks', v_unlocks,
                              'passes', v_passes, 'medal_levels', v_clears,
                              'assignment_submissions', v_subs);
  insert into quiz.admin_log (action, email, detail) values ('reset_progress', v_email, v_res);
  return v_res;
end $$;

-- ------------------------------------------------------------------ statistics (020/024 + assignments)

-- get_stats now builds on quiz.stats_json (024), whose body was an exact copy of get_stats (020),
-- so the student's and the admin's statistics can no longer drift apart.
create or replace function public.get_stats(p_student_id uuid, p_days int default null)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
begin
  s := quiz.require_student(p_student_id);
  return quiz.stats_json(s.id, p_days)
      || jsonb_build_object('assignments', quiz.assignment_stats_json(s.id));
end $$;

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
  return quiz.stats_json(v_id, null)
      || jsonb_build_object('assignments', quiz.assignment_stats_json(v_id));
end $$;

-- ------------------------------------------------------------------ report views (new columns at the end)

create or replace view quiz.v_student_totals as
select c.name                                   as class,
       s.name                                   as student,
       s.email,
       count(a.id)                              as answers,
       count(a.id) filter (where a.is_correct)  as correct,
       round(100.0 * count(a.id) filter (where a.is_correct) / nullif(count(a.id), 0), 1) as accuracy_pct,
       coalesce(sum(a.points), 0)               as points,
       max(a.answered_at)                       as last_answer_at,
       s.created_at                             as registered_at,
       quiz.assignment_points(s.id)             as assignment_points,
       coalesce(sum(a.points), 0) + quiz.assignment_points(s.id) as total_points
  from quiz.students s
  join quiz.classes c on c.id = s.class_id
  left join quiz.attempts a on a.student_id = s.id
 group by c.name, s.id
 order by c.name, points desc;

create or replace view quiz.v_class_totals as
select c.name                                        as class,
       count(distinct s.id)                          as students,
       count(distinct a.student_id)                  as active_students,
       count(a.id)                                   as answers,
       coalesce(sum(a.points), 0)                    as points,
       round(coalesce(sum(a.points), 0)::numeric / greatest(count(distinct s.id), 1), 1) as avg_points_per_student,
       (select coalesce(sum(quiz.assignment_points(x.id)), 0) from quiz.students x
         where x.class_id = c.id)                    as assignment_points,
       coalesce(sum(a.points), 0)
         + (select coalesce(sum(quiz.assignment_points(x.id)), 0) from quiz.students x
             where x.class_id = c.id)                as total_points
  from quiz.classes c
  left join quiz.students s on s.class_id = c.id
  left join quiz.attempts a on a.student_id = s.id
 group by c.id, c.name
 order by avg_points_per_student desc;

revoke all on quiz.v_student_totals, quiz.v_class_totals from public, anon, authenticated;

revoke all on function public.get_catalog(uuid)                from public;
revoke all on function public.get_class_leaderboard()          from public;
revoke all on function public.admin_list_users(text)           from public;
revoke all on function public.admin_reset_progress(text, text) from public;
revoke all on function public.get_stats(uuid, int)             from public;
revoke all on function public.admin_student_stats(text, text)  from public;
grant execute on function public.get_catalog(uuid)                to anon, authenticated;
grant execute on function public.get_class_leaderboard()          to anon, authenticated;
grant execute on function public.admin_list_users(text)           to anon, authenticated;
grant execute on function public.admin_reset_progress(text, text) to anon, authenticated;
grant execute on function public.get_stats(uuid, int)             to anon, authenticated;
grant execute on function public.admin_student_stats(text, text)  to anon, authenticated;

commit;

-- check: students with assignment points, and the class totals
select class, student, points as quiz_points, assignment_points, total_points
  from quiz.v_student_totals where assignment_points > 0;
select jsonb_pretty(public.get_class_leaderboard());
