-- Quizilla – all topics open for everyone (2026-11-04)
--   Every tier (and so every topic) is unlocked for every student. Tier passes, ranks and the
--   "passed x / n" counts still work as before; only the lock is gone.
--   Switch: quiz.config 'tiers_all_open' = 1 (open) / 0 (old rule: pass every topic of the
--   previous tier). Levels inside a topic still unlock with the usual rule (20 answers, 80 %).
--   Redefines quiz.tier_states (last defined in 009).
-- Run:  npm run q:import -- supabase/updates/024_all_topics_open.sql   Safe to re-run.
begin;

insert into quiz.config (key, value) values ('tiers_all_open', '1')
on conflict (key) do update set value = excluded.value;

-- All tiers with lock state and accuracy (all testing answers in the tier).
-- [{ tier, unlocked, topic_count, passed_count, answers, correct }]
create or replace function quiz.tier_states(p_student_id uuid)
returns jsonb language plpgsql as $$
declare
  r             record;
  tp            record;
  all_open      boolean := quiz.cfg_num('tiers_all_open', 0) = 1;
  is_first      boolean := true;
  prev_unlocked boolean := true;
  prev_all      boolean := true;
  v_unlocked    boolean;
  v_count       int;
  v_passed      int;
  v_total       int;
  v_ok          int;
  res           jsonb := '[]'::jsonb;
begin
  for r in
    select distinct t.tier
      from quiz.topics t
     where t.is_active
       and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)
     order by t.tier
  loop
    v_unlocked := all_open or is_first or (prev_unlocked and prev_all);
    v_count  := 0;
    v_passed := 0;
    for tp in
      select t.id from quiz.topics t
       where t.tier = r.tier and t.is_active
         and exists (select 1 from quiz.questions q where q.topic_id = t.id and q.is_active)
    loop
      v_count := v_count + 1;
      if (quiz.topic_pass(p_student_id, tp.id)->>'passed')::boolean then
        v_passed := v_passed + 1;
      end if;
    end loop;

    select count(*)::int, count(*) filter (where a.is_correct)::int
      into v_total, v_ok
      from quiz.attempts a
      join quiz.topics t on t.id = a.topic_id
     where a.student_id = p_student_id and t.tier = r.tier;

    res := res || jsonb_build_object(
      'tier',         r.tier,
      'unlocked',     v_unlocked,
      'topic_count',  v_count,
      'passed_count', v_passed,
      'answers',      v_total,
      'correct',      v_ok);

    prev_unlocked := v_unlocked;
    prev_all      := v_passed = v_count;
    is_first      := false;
  end loop;
  return res;
end $$;

commit;

-- check: tiers_all_open = 1
select key, value from quiz.config where key = 'tiers_all_open';
