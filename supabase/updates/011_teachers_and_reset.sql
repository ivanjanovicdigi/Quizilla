-- Quizilla – new class "Teachers" + ONE-TIME reset of all students (2026-10-22)
--   * Adds the class "Teachers" (sort order 3). It is a normal class: teachers log in via
--     the roster like students and the class shows in the class leaderboard.
--   * ONE-TIME RESET (cannot be undone): deletes ALL students with all their progress
--     (attempts / points, unlocks, topic passes) AND empties the roster.
--     Afterwards nobody can log in until the roster is loaded again:
--       npm run q:roster -- private/roster.csv
--     Devices that are still logged in are logged out on the next app start.
--   * The reset runs only once: it records 'reset_011_done' in quiz.config and is skipped
--     when the file is run again. (To reset again on purpose, delete that config row first.)
-- Run after 010:  npm run q:import -- supabase/updates/011_teachers_and_reset.sql
begin;

-- ------------------------------------------------------------------ class Teachers
insert into quiz.classes (name, sort_order) values ('Teachers', 3)
on conflict (name) do update set sort_order = excluded.sort_order, is_active = true;

-- ------------------------------------------------------------------ one-time reset
do $$
begin
  if exists (select 1 from quiz.config where key = 'reset_011_done') then
    raise notice '011: students and roster were already reset earlier – skipped';
    return;
  end if;

  delete from quiz.roster;
  delete from quiz.students;   -- cascades to quiz.attempts, quiz.unlocks, quiz.topic_passes

  insert into quiz.config (key, value) values ('reset_011_done', now()::text);
end $$;

commit;

-- check
select (select string_agg(name, ', ' order by sort_order) from quiz.classes where is_active) as classes,
       (select count(*) from quiz.students)                                       as students,
       (select count(*) from quiz.attempts)                                       as answers,
       (select count(*) from quiz.roster)                                         as roster,
       (select value from quiz.config where key = 'reset_011_done')               as reset_done_at;
