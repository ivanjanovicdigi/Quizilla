-- Quizilla – DELETE the 15 test accounts from 023_test_accounts.sql (cannot be undone)
--   Deletes test1@lyceum.sk … test15@lyceum.sk: the student rows with ALL their progress
--   (answers/points, unlocked levels, topic passes, medals – via on delete cascade) and the
--   roster rows. Their points disappear from the Teachers total. Nothing else is touched.
--   Devices still logged in as a test account are logged out on the next app start.
-- Run when testing is done:  npm run q:import -- supabase/maintenance/delete_test_accounts.sql
-- Safe to re-run (deletes nothing the second time).
begin;

create temp table test_emails on commit drop as
select 'test' || g || '@lyceum.sk' as email from generate_series(1, 15) g;

delete from quiz.students where email in (select email from test_emails);
delete from quiz.roster   where email in (select email from test_emails);

insert into quiz.admin_log (action, detail)
values ('delete_test_accounts', jsonb_build_object('emails', 'test1..test15@lyceum.sk'));

commit;

-- check: nothing left
select (select count(*) from quiz.roster   where email ~ '^test([1-9]|1[0-5])@lyceum\.sk$') as roster_left,
       (select count(*) from quiz.students where email ~ '^test([1-9]|1[0-5])@lyceum\.sk$') as students_left;
