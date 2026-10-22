-- Quizilla – guest mode (2026-10-22)
--   Anyone can try the app without being on the roster ("Try as guest" on the login page).
--   Guests are anonymous: NOTHING is stored – no student row, no attempts, no points, no
--   leaderboard contribution. The guest's progress (answers, unlocked levels) lives only in
--   the app's memory and is gone on the next visit.
--   New RPCs (no student id):
--     get_guest_catalog()                       – subjects → topics → levels + unlock rule
--     get_guest_questions(topic, difficulty,    – questions WITHOUT answer keys; p_seen = ids
--                         limit, p_seen)          the guest already answered correctly (served last)
--     check_guest_answer(question, chosen)      – learning-style check, records nothing
--   Level locks for guests are enforced by the app (the server keeps no guest state).
--   Answer keys stay on the server; a key is only returned after an answer, like learning mode.
-- Run after 015:  npm run q:import -- supabase/updates/016_guest_mode.sql   Safe to re-run.
begin;

-- Subjects → topics → levels, for guests (no progress).
-- [{ id, slug, name_sk, name_en, topics: [{ id, slug, subject_id, tier, name_sk, name_en,
--    description_sk, description_en, question_count, unlock_min_answers, unlock_window,
--    unlock_accuracy, levels: [{ level, difficulty, question_count }] }] }]
create or replace function public.get_guest_catalog()
returns jsonb
language sql stable security definer set search_path = '' as $$
  select coalesce(jsonb_agg(jsonb_build_object(
                   'id', su.id, 'slug', su.slug, 'name_sk', su.name_sk, 'name_en', su.name_en,
                   'topics', (
                     select jsonb_agg(jsonb_build_object(
                              'id', t.id, 'slug', t.slug, 'subject_id', t.subject_id, 'tier', t.tier,
                              'name_sk', t.name_sk, 'name_en', t.name_en,
                              'description_sk', t.description_sk, 'description_en', t.description_en,
                              'question_count', lv.question_count,
                              'unlock_min_answers', t.unlock_min_answers,
                              'unlock_window',      t.unlock_window,
                              'unlock_accuracy',    t.unlock_accuracy,
                              'levels', lv.levels)
                            order by t.tier, t.sort_order, t.name_sk)
                       from quiz.topics t
                       cross join lateral (
                         select sum(x.n)::int as question_count,
                                jsonb_agg(jsonb_build_object(
                                  'level', x.lvl, 'difficulty', x.difficulty, 'question_count', x.n)
                                  order by x.difficulty) as levels
                           from (select q.difficulty, count(*)::int as n,
                                        row_number() over (order by q.difficulty) as lvl
                                   from quiz.questions q
                                  where q.topic_id = t.id and q.is_active
                                  group by q.difficulty) x
                       ) lv
                      where t.subject_id = su.id and t.is_active and lv.question_count > 0))
                 order by su.sort_order, su.name_sk), '[]'::jsonb)
    from quiz.subjects su
   where su.is_active
     and exists (select 1 from quiz.topics t
                   join quiz.questions q on q.topic_id = t.id and q.is_active
                  where t.subject_id = su.id and t.is_active);
$$;

-- Random questions of one level, without answer keys. Questions in p_seen come last.
create or replace function public.get_guest_questions(p_topic_id int, p_difficulty int,
                                                      p_limit int default 10,
                                                      p_seen bigint[] default '{}')
returns jsonb
language plpgsql volatile security definer set search_path = '' as $$
begin
  if not exists (select 1 from quiz.topics where id = p_topic_id and is_active) then
    perform quiz.raise_error('unknown_topic');
  end if;
  return (
    select coalesce(jsonb_agg(jsonb_build_object(
                     'id', x.id, 'difficulty', x.difficulty,
                     'body', x.body, 'answers', x.answers,
                     'body_en', x.body_en, 'answers_en', x.answers_en)
                   order by x.seen, x.r), '[]'::jsonb)
      from (
        select q.id, q.difficulty, q.body, q.answers, q.body_en, q.answers_en,
               q.id = any (coalesce(p_seen, '{}')) as seen,
               random() as r
          from quiz.questions q
         where q.topic_id = p_topic_id and q.difficulty = p_difficulty and q.is_active
         order by 7, 8
         limit least(greatest(coalesce(p_limit, 10), 1), 50)
      ) x);
end $$;

-- Learning-style check for guests: returns the result, records NOTHING.
create or replace function public.check_guest_answer(p_question_id bigint, p_chosen int)
returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare
  q quiz.questions;
begin
  select qq.* into q
    from quiz.questions qq
    join quiz.topics t on t.id = qq.topic_id and t.is_active
   where qq.id = p_question_id and qq.is_active;
  if not found then
    perform quiz.raise_error('unknown_question');
  end if;
  if p_chosen is null or p_chosen not between 0 and 3 then
    perform quiz.raise_error('invalid_choice');
  end if;
  return jsonb_build_object(
    'correct',        p_chosen = q.correct_index,
    'correct_index',  q.correct_index,
    'explanation',    q.explanation,
    'explanation_en', q.explanation_en);
end $$;

revoke all on function public.get_guest_catalog()                          from public;
revoke all on function public.get_guest_questions(int, int, int, bigint[]) from public;
revoke all on function public.check_guest_answer(bigint, int)              from public;
grant execute on function public.get_guest_catalog()                          to anon, authenticated;
grant execute on function public.get_guest_questions(int, int, int, bigint[]) to anon, authenticated;
grant execute on function public.check_guest_answer(bigint, int)              to anon, authenticated;

commit;

-- check: topics and levels a guest sees
select t->>'slug' as topic, jsonb_array_length(t->'levels') as levels, (t->>'question_count')::int as questions
  from jsonb_array_elements(public.get_guest_catalog()) s,
       jsonb_array_elements(s->'topics') t;
