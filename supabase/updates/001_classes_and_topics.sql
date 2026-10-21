-- Quizilla – real classes, subject and topic list
-- Run once in Supabase → SQL Editor. Safe to re-run.
begin;

-- ---------------------------------------------------------------- classes
update quiz.classes set name = 'Lambda', sort_order = 1 where name = 'I.A';
update quiz.classes set name = 'Ró',     sort_order = 2 where name = 'I.B';
insert into quiz.classes (name, sort_order) values ('Lambda', 1), ('Ró', 2)
on conflict (name) do nothing;

-- students registered in the remaining example classes move to Lambda
update quiz.students
   set class_id = (select id from quiz.classes where name = 'Lambda')
 where class_id in (select id from quiz.classes where name in ('II.A', 'II.B'));
delete from quiz.classes where name in ('II.A', 'II.B');

-- ---------------------------------------------------------------- subject
update quiz.subjects
   set slug = 'prog-1-digi', name_sk = 'Prog 1 Digi', name_en = 'Prog 1 Digi', sort_order = 1
 where slug = 'programming-1';
insert into quiz.subjects (slug, name_sk, name_en, sort_order)
values ('prog-1-digi', 'Prog 1 Digi', 'Prog 1 Digi', 1)
on conflict (slug) do nothing;

-- ---------------------------------------------------------------- topics
-- existing sample topics are renamed (their sample questions stay)
update quiz.topics t set slug = 'data-types', sort_order = 1
  from quiz.subjects s
 where s.id = t.subject_id and s.slug = 'prog-1-digi' and t.slug = 'variables';
update quiz.topics t set slug = 'logic', sort_order = 2
  from quiz.subjects s
 where s.id = t.subject_id and s.slug = 'prog-1-digi' and t.slug = 'conditions';
update quiz.topics t set slug = 'cycles', sort_order = 3
  from quiz.subjects s
 where s.id = t.subject_id and s.slug = 'prog-1-digi' and t.slug = 'loops';

insert into quiz.topics (subject_id, slug, name_sk, name_en, description_sk, description_en, sort_order)
select s.id, v.slug, v.name_sk, v.name_en, v.dsk, v.den, v.ord
  from quiz.subjects s,
       (values
         ('data-types', 'Dátové typy', 'Data types',
          'int, double, bool, char, string', 'int, double, bool, char, string', 1),
         ('logic', 'Logika', 'Logic',
          'Operátory ! == != < <= > >=, + - * / %, priradenie =, if / else',
          'Operators ! == != < <= > >=, + - * / %, assignment =, if / else', 2),
         ('cycles', 'Cykly', 'Cycles', 'while, for', 'while, for', 3),
         ('functions', 'Funkcie', 'Functions', null, null, 4),
         ('arrays', 'Polia', 'Arrays', null, null, 5),
         ('lists', 'Zoznamy', 'Lists', null, null, 6),
         ('classes', 'Triedy', 'Classes', null, null, 7),
         ('git', 'Git', 'Git', null, null, 8)
       ) as v(slug, name_sk, name_en, dsk, den, ord)
 where s.slug = 'prog-1-digi'
on conflict (subject_id, slug) do update
   set name_sk = excluded.name_sk, name_en = excluded.name_en,
       description_sk = excluded.description_sk, description_en = excluded.description_en,
       sort_order = excluded.sort_order;

commit;

-- check
select c.name as class, (select count(*) from quiz.students s where s.class_id = c.id) as students
  from quiz.classes c order by c.sort_order;
select t.sort_order, t.name_sk, t.name_en,
       (select count(*) from quiz.questions q where q.topic_id = t.id) as questions
  from quiz.topics t join quiz.subjects s on s.id = t.subject_id
 where s.slug = 'prog-1-digi' order by t.sort_order;
