-- Quizilla – source_id for generated questions
-- Every question imported from questions/batches/*.json keeps its batch id in
-- source_id (e.g. "dt-var-type-001"). The generated update scripts use it to
-- update a question instead of inserting a duplicate when they are run again.
-- Run once in Supabase → SQL Editor. Safe to re-run.
begin;

alter table quiz.questions add column if not exists source_id text;
create unique index if not exists questions_source_id_key on quiz.questions (source_id);

commit;

-- check
select count(*) as questions, count(source_id) as with_source_id from quiz.questions;
