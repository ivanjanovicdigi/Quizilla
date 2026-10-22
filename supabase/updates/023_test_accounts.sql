-- Quizilla – 15 test accounts (2026-10-23)
--   Adds test1@lyceum.sk … test15@lyceum.sk to the roster, class Teachers, names "Test 1" … "Test 15".
--   Log in with the email as usual. Their points count toward the Teachers class until deleted.
--   Delete them (with all their progress) later with:
--     npm run q:import -- supabase/maintenance/delete_test_accounts.sql
--   Note: `npm run q:roster -- … --sync` would DEACTIVATE these accounts (they are not in roster.csv).
-- Run:  npm run q:import -- supabase/updates/023_test_accounts.sql   Safe to re-run (re-activates them).
begin;

insert into quiz.roster (email, name, class_id)
select 'test' || g || '@lyceum.sk', 'Test ' || g, c.id
  from generate_series(1, 15) g
  cross join quiz.classes c
 where c.name = 'Teachers'
on conflict (email) do update
   set name = excluded.name, class_id = excluded.class_id, is_active = true, updated_at = now();

commit;

-- check: 15 active test accounts in Teachers
select count(*) filter (where r.is_active) as active_test_accounts,
       string_agg(distinct c.name, ', ')  as class
  from quiz.roster r
  join quiz.classes c on c.id = r.class_id
 where r.email in (select 'test' || g || '@lyceum.sk' from generate_series(1, 15) g);
