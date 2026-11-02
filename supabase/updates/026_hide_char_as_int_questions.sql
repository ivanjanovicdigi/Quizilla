-- Quizilla – hide questions that rely on char being a number (2026-10-29, GitHub issue #2)
--   Prog 1 does not teach that a char is stored as a number, but 9 "Which of these lines causes a
--   compile error?" questions (data types, level 3) use `int n = 'A';` or `double d = 'A';` as a
--   valid line, and their note says "`double d = 'A';` is fine". Students find that confusing (Q3033).
--   This sets is_active = false on them, so they are no longer picked for quizzes (students or guests).
--   Answers already given stay in quiz.attempts: points, stats and unlocks do not change.
--   The same questions are marked "rejected" in questions/batches/2026-10-22_data-types_3.json,
--   so a later rebuild of the questions SQL keeps them hidden.
-- Run:  npm run q:import -- supabase/updates/026_hide_char_as_int_questions.sql   Safe to re-run.
begin;

update quiz.questions
   set is_active = false
 where source_id in ('dt-compile-error-001', 'dt-compile-error-005', 'dt-compile-error-006',
                     'dt-compile-error-010', 'dt-compile-error-012', 'dt-compile-error-015',
                     'dt-compile-error-016', 'dt-compile-error-022', 'dt-compile-error-025');

commit;

-- check: 9 rows, all is_active = false
select id, source_id, is_active, body_en
  from quiz.questions
 where source_id in ('dt-compile-error-001', 'dt-compile-error-005', 'dt-compile-error-006',
                     'dt-compile-error-010', 'dt-compile-error-012', 'dt-compile-error-015',
                     'dt-compile-error-016', 'dt-compile-error-022', 'dt-compile-error-025')
 order by source_id;
