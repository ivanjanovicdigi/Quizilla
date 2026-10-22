-- Quizilla – unlock rule: next level after at least 10 answers on the current
-- level AND at least 80 % of ALL answers on that level correct.
-- unlock_window null = count all answers (not just the last N).
-- Every answer counts, repeats of the same question included.
-- Run once in Supabase → SQL Editor. Safe to re-run.
begin;

alter table quiz.topics alter column unlock_window drop not null;
alter table quiz.topics alter column unlock_window set default null;
alter table quiz.topics drop constraint if exists topics_unlock_window_check;
alter table quiz.topics add constraint topics_unlock_window_check
  check (unlock_window is null or unlock_window > 0);

update quiz.topics
   set unlock_min_answers = 10,
       unlock_window      = null,
       unlock_accuracy    = 0.80;

commit;

-- check
select t.sort_order, t.slug, t.unlock_min_answers, t.unlock_window, t.unlock_accuracy
  from quiz.topics t order by t.subject_id, t.sort_order;
