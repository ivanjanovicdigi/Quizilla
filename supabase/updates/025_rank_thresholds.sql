-- Quizilla – separate accuracy threshold for every global rank (2026-10-26)
--   Before: Padawan, Jedi and Master all used one value (rank_accuracy = 0.95),
--   Grand Master used rank_grand_accuracy (0.99).
--   Now (quiz.config):
--     rank_accuracy_padawan = 0.75   (level 1)
--     rank_accuracy_jedi    = 0.85   (level 2)
--     rank_accuracy_master  = 0.95   (level 3)
--     rank_grand_accuracy   = 0.99   (every level, unchanged)
--   rank_min_answers (50 answers per level) is unchanged. A missing per-rank key falls back to
--   rank_accuracy. Ranks are not stored – the new thresholds apply immediately to everyone.
--   quiz.rank_json is re-created from the version that was LIVE in production on 2026-10-26.
--   That version (ranks must be earned in order: rule_met / blocked_by) was never in the repo
--   before this file; only the threshold lookup changed.
-- Run after 024:  npm run q:import -- supabase/updates/025_rank_thresholds.sql   Safe to re-run.
begin;

insert into quiz.config (key, value) values
  ('rank_accuracy_padawan', '0.75'),
  ('rank_accuracy_jedi',    '0.85'),
  ('rank_accuracy_master',  '0.95'),
  ('rank_grand_accuracy',   '0.99')
on conflict (key) do update set value = excluded.value;

create or replace function quiz.rank_json(p_student_id uuid)
returns jsonb language plpgsql stable as $$
declare
  v_min     int     := quiz.cfg_num('rank_min_answers', 50)::int;
  v_default numeric := quiz.cfg_num('rank_accuracy', 0.95);
  v_grand   numeric := quiz.cfg_num('rank_grand_accuracy', 0.99);
  v_acc     numeric;
  d         record;
  v_ranks   jsonb := '[]'::jsonb;
  v_rule    boolean;
  v_earn    boolean;
  v_missing text;           -- first earlier rank that is not earned
  v_grand_rule boolean := true;
  v_grand_total   int := 0;
  v_grand_correct int := 0;
  v_current text;
begin
  for d in
    select x.difficulty, x.key,
           coalesce(s.total, 0) as total, coalesce(s.ok, 0) as ok
      from (values (1, 'padawan'), (2, 'jedi'), (3, 'master')) as x(difficulty, key)
      left join (select a.difficulty, count(*)::int as total,
                        count(*) filter (where a.is_correct)::int as ok
                   from quiz.attempts a
                  where a.student_id = p_student_id
                  group by a.difficulty) s on s.difficulty = x.difficulty
     order by x.difficulty
  loop
    v_acc  := quiz.cfg_num('rank_accuracy_' || d.key, v_default);
    v_rule := d.total >= v_min and d.ok >= d.total * v_acc;
    v_earn := v_rule and v_missing is null;
    v_ranks := v_ranks || jsonb_build_object(
      'key', d.key, 'difficulty', d.difficulty, 'accuracy', v_acc,
      'answers', d.total, 'correct', d.ok,
      'rule_met', v_rule, 'earned', v_earn, 'blocked_by', v_missing);
    if v_earn then
      v_current := d.key;
    elsif v_missing is null then
      v_missing := d.key;
    end if;

    v_grand_rule    := v_grand_rule and d.total >= v_min and d.ok >= d.total * v_grand;
    v_grand_total   := v_grand_total + d.total;
    v_grand_correct := v_grand_correct + d.ok;
  end loop;

  v_earn := v_grand_rule and v_missing is null;
  if v_earn then v_current := 'grand_master'; end if;
  v_ranks := v_ranks || jsonb_build_object(
    'key', 'grand_master', 'difficulty', null, 'accuracy', v_grand,
    'answers', v_grand_total, 'correct', v_grand_correct,
    'rule_met', v_grand_rule, 'earned', v_earn, 'blocked_by', v_missing);

  return jsonb_build_object('current', v_current, 'min_answers', v_min, 'ranks', v_ranks);
end $$;

commit;

-- check: thresholds per rank (expect padawan 75, jedi 85, master 95, grand_master 99)
select r->>'key' as rank, round((r->>'accuracy')::numeric * 100) as accuracy_pct
  from jsonb_array_elements(quiz.rank_json('00000000-0000-0000-0000-000000000000')->'ranks') r;
