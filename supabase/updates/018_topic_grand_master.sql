-- Quizilla – topic Grand Master (2026-10-23)
--   Above the gold topic medal (012) there is now one more step per topic: GRAND MASTER (crown).
--   A student is Grand Master of a topic when:
--     * the topic medal is gold (all levels cleared – sticky, as before), AND
--     * on EVERY level of the topic: at least topic_gm_min_answers testing answers (default 50)
--       and at least topic_gm_accuracy of them correct (default 0.99).
--   It is NOT sticky: it is shown only while the rule holds (the gold medal always stays).
--   topic JSON (get_catalog, get_topic):
--     "medal": "bronze" | "silver" | "gold" | "grand_master" | null      (grand_master replaces gold)
--     "grand_master": { min_answers, accuracy, earned,
--                       levels: [{ level, difficulty, answers, correct }] }
--   The global ranks (Padawan … Grand Master over all topics, 009) are unchanged.
-- Run after 017:  npm run q:import -- supabase/updates/018_topic_grand_master.sql   Safe to re-run.
begin;

insert into quiz.config (key, value) values
  ('topic_gm_min_answers', '50'),
  ('topic_gm_accuracy',    '0.99')
on conflict (key) do nothing;

-- Medal of a student in a topic, from the topic progress (quiz.topic_progress).
-- Saves newly cleared levels. Returns { medal, levels_cleared, grand_master }.
-- (Same as 012, plus the Grand Master step.)
create or replace function quiz.topic_medal(p_student_id uuid, p_topic_id int, p_progress jsonb)
returns jsonb language plpgsql as $$
declare
  v_levels  jsonb := coalesce(p_progress->'levels', '[]'::jsonb);
  v_n       int   := jsonb_array_length(coalesce(p_progress->'levels', '[]'::jsonb));
  v_cleared int;
  v_step    int;
  v_medal   text;
  v_gm_min  int     := quiz.cfg_num('topic_gm_min_answers', 50)::int;
  v_gm_acc  numeric := quiz.cfg_num('topic_gm_accuracy', 0.99);
  v_gm_lvls jsonb;
  v_gm      boolean;
begin
  if v_n = 0 then
    return jsonb_build_object('medal', null, 'levels_cleared', 0, 'grand_master', null);
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
  v_medal := (array['bronze', 'silver', 'gold'])[nullif(v_step, 0)];

  -- Grand Master: gold + every level at least v_gm_min answers with v_gm_acc correct
  select jsonb_agg(jsonb_build_object(
           'level',      (l.e->>'level')::int,
           'difficulty', (l.e->>'difficulty')::int,
           'answers',    coalesce(a.total, 0),
           'correct',    coalesce(a.ok, 0)) order by (l.e->>'difficulty')::int),
         bool_and(coalesce(a.total, 0) >= v_gm_min and coalesce(a.ok, 0) >= coalesce(a.total, 0) * v_gm_acc)
    into v_gm_lvls, v_gm
    from jsonb_array_elements(v_levels) l(e)
    left join lateral (
      select count(*)::int as total, count(*) filter (where x.is_correct)::int as ok
        from quiz.attempts x
       where x.student_id = p_student_id and x.topic_id = p_topic_id
         and x.difficulty = (l.e->>'difficulty')::int
    ) a on true;

  v_gm := coalesce(v_gm, false) and v_medal = 'gold';
  if v_gm then v_medal := 'grand_master'; end if;

  return jsonb_build_object(
    'medal', v_medal,
    'levels_cleared', v_cleared,
    'grand_master', jsonb_build_object(
      'min_answers', v_gm_min,
      'accuracy',    v_gm_acc,
      'earned',      v_gm,
      'levels',      coalesce(v_gm_lvls, '[]'::jsonb)));
end $$;

revoke all on function quiz.topic_medal(uuid, int, jsonb) from public, anon, authenticated;

commit;

-- check: topic Grand Masters right now
select s.email, t.slug
  from quiz.students s
  cross join quiz.topics t
 where t.is_active
   and exists (select 1 from quiz.attempts a where a.student_id = s.id and a.topic_id = t.id)
   and quiz.topic_json(s.id, t.id)->>'medal' = 'grand_master'
 order by 1, 2;
