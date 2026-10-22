-- Quizilla – topic medals (2026-10-22)
--   Every topic shows a medal for the levels (úrovne) the student has CLEARED in testing mode.
--   A level is cleared when its unlock goal is reached (same rule as unlocking the next level:
--   at least unlock_min_answers answers and unlock_accuracy correct). Medals are sticky.
--     3-level topic: level 1 cleared = bronze, level 2 = silver, level 3 = gold
--     fewer levels:  all levels cleared = gold, one level short = silver (git: 1 level → gold)
--   quiz.level_clears remembers cleared levels (also the last level, which unlocks nothing),
--   so a medal never disappears when accuracy drops later.
--   topic JSON (get_catalog, get_topic) gets: "medal": "bronze" | "silver" | "gold" | null,
--                                             "levels_cleared": n
--   Tier medals are removed in the frontend (tiers keep only the lock / passed count).
-- Run after 011:  npm run q:import -- supabase/updates/012_topic_medals.sql   Safe to re-run.
begin;

create table if not exists quiz.level_clears (
  student_id uuid     not null references quiz.students(id) on delete cascade,
  topic_id   int      not null references quiz.topics(id)   on delete cascade,
  difficulty smallint not null,
  cleared_at timestamptz not null default now(),
  primary key (student_id, topic_id, difficulty)
);
alter table quiz.level_clears enable row level security;
revoke all on quiz.level_clears from public, anon, authenticated;

-- Medal of a student in a topic, from the topic progress (quiz.topic_progress).
-- Saves newly cleared levels. Returns { medal, levels_cleared }.
create or replace function quiz.topic_medal(p_student_id uuid, p_topic_id int, p_progress jsonb)
returns jsonb language plpgsql as $$
declare
  v_levels  jsonb := coalesce(p_progress->'levels', '[]'::jsonb);
  v_n       int   := jsonb_array_length(coalesce(p_progress->'levels', '[]'::jsonb));
  v_cleared int;
  v_step    int;
begin
  if v_n = 0 then
    return jsonb_build_object('medal', null, 'levels_cleared', 0);
  end if;

  -- a level is cleared when its goal is met now, or the next level is unlocked
  insert into quiz.level_clears (student_id, topic_id, difficulty)
  select p_student_id, p_topic_id, (l.e->>'difficulty')::smallint
    from jsonb_array_elements(v_levels) with ordinality as l(e, i)
   where (l.e->>'met')::boolean
      or coalesce((v_levels->(l.i::int)->>'unlocked')::boolean, false)   -- next level (0-based index = i)
  on conflict do nothing;

  select count(*)::int into v_cleared
    from quiz.level_clears c
   where c.student_id = p_student_id and c.topic_id = p_topic_id
     and c.difficulty in (select (e->>'difficulty')::smallint from jsonb_array_elements(v_levels) e);

  -- 1 = bronze, 2 = silver, 3 = gold; the last level always gives gold
  v_step := case when v_cleared = 0 then 0 else least(3, v_cleared + (3 - least(v_n, 3))) end;
  if v_cleared >= v_n then v_step := 3; end if;

  return jsonb_build_object(
    'medal', (array['bronze', 'silver', 'gold'])[nullif(v_step, 0)],
    'levels_cleared', v_cleared);
end $$;

-- topic JSON + medal
create or replace function quiz.topic_json(p_student_id uuid, p_topic_id int)
returns jsonb language sql as $$
  select jsonb_build_object(
           'id', t.id, 'slug', t.slug, 'subject_id', t.subject_id, 'tier', t.tier,
           'name_sk', t.name_sk, 'name_en', t.name_en,
           'description_sk', t.description_sk, 'description_en', t.description_en,
           'question_count', (select count(*) from quiz.questions q
                               where q.topic_id = t.id and q.is_active),
           'progress', pr.p,
           'pass',     quiz.topic_pass(p_student_id, t.id))
         || quiz.topic_medal(p_student_id, t.id, pr.p)
    from quiz.topics t
    cross join lateral (select quiz.topic_progress(p_student_id, t.id) as p) pr
   where t.id = p_topic_id;
$$;

revoke all on function quiz.topic_medal(uuid, int, jsonb) from public, anon, authenticated;
revoke all on function quiz.topic_json(uuid, int)         from public, anon, authenticated;

commit;
