-- Quizilla – coding assignments open for everyone (2026-11-16)
--   Until now only the emails listed in quiz.config 'assignments_access' could use coding
--   assignments (030 started with ivan.janovic@lyceum.sk). This sets the value to '*':
--     * every logged-in student sees the "Coding assignments" card on Home and can open, run and
--       submit assignments; their points count as described in 032;
--     * guests can open and try them too – nothing of a guest is saved (same as quizzes).
--   Nothing else changes: no function, table or score is touched.
--   To close it again (one person or a list of emails, comma separated):
--     update quiz.config set value = 'ivan.janovic@lyceum.sk' where key = 'assignments_access';
-- Run after 032:  npm run q:import -- supabase/updates/033_assignments_open.sql   Safe to re-run.
begin;

insert into quiz.config (key, value) values ('assignments_access', '*')
on conflict (key) do update set value = excluded.value;

commit;

-- check: the gate is open, and these are the assignments users will see
select (select value from quiz.config where key = 'assignments_access')   as assignments_access,
       quiz.assignments_access_ok(null)                                   as guests_allowed,
       (select count(*) from quiz.assignments where is_active)            as active_assignments,
       (select count(*) from quiz.assignments where not is_active)        as hidden_assignments;
