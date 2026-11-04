-- Quizilla – easier level unlock: 10 answers, any accuracy; medals keep their rule (2026-11-04)
--   * UNLOCK: the next level unlocks after 10 Play answers on the current level, right or wrong
--     (was 20 answers with at least 80 % correct, 019). Also the default for new topics.
--     Levels already unlocked stay unlocked (sticky).
--   * MEDALS keep the old rule: a level is cleared (bronze / silver / gold, 012) only with at least
--     medal_min_answers (20) answers on it and at least medal_accuracy (0.80) of them correct.
--     quiz.topic_medal (last defined in 018) no longer looks at unlocks. Medals already earned stay.
--     Topic Grand Master (018) is unchanged. Topic JSON also gets "medal_rule": { min_answers, accuracy }.
--   NOTE: re-running 019 or 021 would put unlock_min_answers back to 20 – don't.
-- Run:  npm run q:import -- supabase/updates/025_unlock10_any.sql   Safe to re-run.
begin;

-- ------------------------------------------------------------------ unlock rule
alter table quiz.topics alter column unlock_min_answers set default 10;
alter table quiz.topics alter column unlock_accuracy    set default 0;
alter table quiz.topics alter column unlock_window      set default null;

update quiz.topics
   set unlock_min_answers = 10,
       unlock_accuracy    = 0,
       unlock_window      = null
 where unlock_min_answers <> 10
    or unlock_accuracy    <> 0
    or unlock_window is not null;

-- ------------------------------------------------------------------ medal rule
insert into quiz.config (key, value) values
  ('medal_min_answers', '20'),
  ('medal_accuracy',    '0.80')
on conflict (key) do nothing;

-- Medal of a student in a topic, from the topic progress (quiz.topic_progress).
-- Saves newly cleared levels. Returns { medal, levels_cleared, grand_master, medal_rule }.
-- (Same as 018, but a level is cleared by the medal rule, not by the unlock rule.)
create or replace function quiz.topic_medal(p_student_id uuid, p_topic_id int, p_progress jsonb)
returns jsonb language plpgsql as $$
declare
  v_levels  jsonb := coalesce(p_progress->'levels', '[]'::jsonb);
  v_n       int   := jsonb_array_length(coalesce(p_progress->'levels', '[]'::jsonb));
  v_cleared int;
  v_step    int;
  v_medal   text;
  v_min     int     := quiz.cfg_num('medal_min_answers', 20)::int;
  v_acc     numeric := quiz.cfg_num('medal_accuracy', 0.80);
  v_rule    jsonb   := jsonb_build_object('min_answers', quiz.cfg_num('medal_min_answers', 20)::int,
                                          'accuracy',    quiz.cfg_num('medal_accuracy', 0.80));
  v_gm_min  int     := quiz.cfg_num('topic_gm_min_answers', 50)::int;
  v_gm_acc  numeric := quiz.cfg_num('topic_gm_accuracy', 0.99);
  v_gm_lvls jsonb;
  v_gm      boolean;
  v_lv      jsonb;   -- [{ difficulty, level, total, ok }]
begin
  if v_n = 0 then
    return jsonb_build_object('medal', null, 'levels_cleared', 0, 'grand_master', null,
                              'medal_rule', v_rule);
  end if;

  -- answers per level (Play answers only – attempts holds nothing else)
  select coalesce(jsonb_agg(jsonb_build_object(
           'difficulty', (l.e->>'difficulty')::int,
           'level',      (l.e->>'level')::int,
           'total',      coalesce(a.total, 0),
           'ok',         coalesce(a.ok, 0))), '[]'::jsonb)
    into v_lv
    from jsonb_array_elements(v_levels) l(e)
    left join lateral (
      select count(*)::int as total, count(*) filter (where x.is_correct)::int as ok
        from quiz.attempts x
       where x.student_id = p_student_id and x.topic_id = p_topic_id
         and x.difficulty = (l.e->>'difficulty')::int
    ) a on true;

  -- a level is cleared when the medal rule is met (sticky)
  insert into quiz.level_clears (student_id, topic_id, difficulty)
  select p_student_id, p_topic_id, m.difficulty::smallint
    from jsonb_to_recordset(v_lv) as m(difficulty int, level int, total int, ok int)
   where m.total >= v_min and m.ok >= m.total * v_acc
  on conflict do nothing;

  select count(*)::int into v_cleared
    from quiz.level_clears c
   where c.student_id = p_student_id and c.topic_id = p_topic_id
     and c.difficulty in (select m.difficulty from jsonb_to_recordset(v_lv) as m(difficulty int, level int, total int, ok int));

  -- 1 = bronze, 2 = silver, 3 = gold; the last level always gives gold
  v_step := case when v_cleared = 0 then 0 else least(3, v_cleared + (3 - least(v_n, 3))) end;
  if v_cleared >= v_n then v_step := 3; end if;
  v_medal := (array['bronze', 'silver', 'gold'])[nullif(v_step, 0)];

  -- Grand Master: gold + every level at least v_gm_min answers with v_gm_acc correct
  select jsonb_agg(jsonb_build_object(
           'level',      m.level,
           'difficulty', m.difficulty,
           'answers',    m.total,
           'correct',    m.ok) order by m.difficulty),
         bool_and(m.total >= v_gm_min and m.ok >= m.total * v_gm_acc)
    into v_gm_lvls, v_gm
    from jsonb_to_recordset(v_lv) as m(difficulty int, level int, total int, ok int);

  v_gm := coalesce(v_gm, false) and v_medal = 'gold';
  if v_gm then v_medal := 'grand_master'; end if;

  return jsonb_build_object(
    'medal', v_medal,
    'levels_cleared', v_cleared,
    'medal_rule', v_rule,
    'grand_master', jsonb_build_object(
      'min_answers', v_gm_min,
      'accuracy',    v_gm_acc,
      'earned',      v_gm,
      'levels',      coalesce(v_gm_lvls, '[]'::jsonb)));
end $$;

revoke all on function quiz.topic_medal(uuid, int, jsonb) from public, anon, authenticated;

commit;

-- check: every topic shows 10 / 0.00 / null, and the medal rule
select t.slug, t.unlock_min_answers, t.unlock_accuracy, t.unlock_window
  from quiz.topics t
 order by t.sort_order;
select key, value from quiz.config where key in ('medal_min_answers', 'medal_accuracy');
