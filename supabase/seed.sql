-- =====================================================================
-- Quizilla – sample data (safe to run once on an empty database)
-- Classes are examples – rename/add your real classes.
-- Questions are not seeded any more – they are generated from
-- questions/templates and imported via supabase/updates.
-- =====================================================================

insert into quiz.classes (name, sort_order) values
  ('I.A', 1), ('I.B', 2), ('II.A', 3), ('II.B', 4)
on conflict (name) do nothing;

insert into quiz.subjects (slug, name_sk, name_en, sort_order) values
  ('programming-1', 'Programovanie 1 (C#)', 'Programming 1 (C#)', 1)
on conflict (slug) do nothing;

insert into quiz.topics (subject_id, slug, name_sk, name_en, description_sk, description_en, sort_order)
select s.id, v.slug, v.name_sk, v.name_en, v.dsk, v.den, v.ord
  from quiz.subjects s,
       (values
         ('variables',  'Premenné a dátové typy', 'Variables and data types',
          'Deklarácia, typy, operátory a pretypovanie.', 'Declarations, types, operators and casting.', 1),
         ('conditions', 'Podmienky', 'Conditions',
          'if / else, logické operátory, switch.', 'if / else, logical operators, switch.', 2),
         ('loops',      'Cykly', 'Loops',
          'for, while, do-while, break a continue.', 'for, while, do-while, break and continue.', 3)
       ) as v(slug, name_sk, name_en, dsk, den, ord)
 where s.slug = 'programming-1'
on conflict (subject_id, slug) do nothing;
