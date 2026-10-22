-- Quizilla – bilingual questions (Slovak + English)
-- body / answers / explanation stay the Slovak text; *_en columns are the
-- optional English versions. The app shows English when the UI is set to
-- English and the question has it, otherwise Slovak.
-- Run once in Supabase → SQL Editor. Safe to re-run.
begin;

alter table quiz.questions add column if not exists body_en        text;
alter table quiz.questions add column if not exists answers_en     text[];
alter table quiz.questions add column if not exists explanation_en text;

alter table quiz.questions drop constraint if exists questions_answers_en_check;
alter table quiz.questions add constraint questions_answers_en_check
  check (answers_en is null or array_length(answers_en, 1) = 4);

-- API functions now also return the English texts
create or replace function public.get_questions(p_student_id uuid, p_topic_id int,
                                                p_difficulty int, p_limit int default 10)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s quiz.students;
  v_progress jsonb;
  v_unlocked boolean;
begin
  s := quiz.require_student(p_student_id);
  v_progress := quiz.topic_progress(s.id, p_topic_id);
  if v_progress is null then
    perform quiz.raise_error('unknown_topic');
  end if;

  select (e->>'unlocked')::boolean into v_unlocked
    from jsonb_array_elements(v_progress->'levels') e
   where (e->>'difficulty')::int = p_difficulty;

  if v_unlocked is null then
    perform quiz.raise_error('unknown_level');
  elsif not v_unlocked then
    perform quiz.raise_error('level_locked');
  end if;

  return (
    select coalesce(jsonb_agg(jsonb_build_object(
                     'id', x.id, 'difficulty', x.difficulty,
                     'body', x.body, 'answers', x.answers,
                     'body_en', x.body_en, 'answers_en', x.answers_en)
                   order by x.ever_correct, x.r), '[]'::jsonb)
      from (
        select q.id, q.difficulty, q.body, q.answers, q.body_en, q.answers_en,
               exists (select 1 from quiz.attempts a
                        where a.student_id = s.id and a.question_id = q.id and a.is_correct) as ever_correct,
               random() as r
          from quiz.questions q
         where q.topic_id = p_topic_id and q.difficulty = p_difficulty and q.is_active
         order by 7, 8
         limit least(greatest(coalesce(p_limit, 10), 1), 50)
      ) x);
end $$;

-- Records an answer and returns the result together with updated progress.
create or replace function public.submit_answer(p_student_id uuid, p_question_id bigint, p_chosen int)
returns jsonb
language plpgsql security definer set search_path = '' as $$
declare
  s           quiz.students;
  q           quiz.questions;
  v_before    jsonb;
  v_after     jsonb;
  v_unlocked  boolean;
  v_correct   boolean;
  v_points    int := 0;
  v_ppd       int;
  v_new       jsonb;
begin
  s := quiz.require_student(p_student_id);

  -- serialize answers of one student (prevents double points on double-tap)
  perform pg_advisory_xact_lock(hashtextextended(s.id::text, 0));

  select * into q from quiz.questions where id = p_question_id and is_active;
  if not found then
    perform quiz.raise_error('unknown_question');
  end if;
  if p_chosen is null or p_chosen not between 0 and 3 then
    perform quiz.raise_error('invalid_choice');
  end if;

  v_before := quiz.topic_progress(s.id, q.topic_id);
  select (e->>'unlocked')::boolean into v_unlocked
    from jsonb_array_elements(v_before->'levels') e
   where (e->>'difficulty')::int = q.difficulty;
  if not coalesce(v_unlocked, false) then
    perform quiz.raise_error('level_locked');
  end if;

  v_correct := (p_chosen = q.correct_index);

  if v_correct and not exists (select 1 from quiz.attempts
                                where student_id = s.id and question_id = q.id and is_correct) then
    select coalesce(value::int, 10) into v_ppd from quiz.config where key = 'points_per_difficulty';
    v_points := q.difficulty * coalesce(v_ppd, 10);
  end if;

  insert into quiz.attempts (student_id, question_id, topic_id, difficulty, chosen_index, is_correct, points)
  values (s.id, q.id, q.topic_id, q.difficulty, p_chosen, v_correct, v_points);

  v_after := quiz.topic_progress(s.id, q.topic_id);

  select coalesce(jsonb_agg(a->'level'), '[]'::jsonb) into v_new
    from jsonb_array_elements(v_after->'levels') a
    join jsonb_array_elements(v_before->'levels') b on b->'difficulty' = a->'difficulty'
   where (a->>'unlocked')::boolean and not (b->>'unlocked')::boolean;

  return jsonb_build_object(
    'correct',         v_correct,
    'correct_index',   q.correct_index,
    'explanation',     q.explanation,
    'explanation_en',  q.explanation_en,
    'points',          v_points,
    'newly_unlocked',  v_new,
    'progress',        v_after);
end $$;

commit;

-- check
select count(*) as questions,
       count(body_en) as with_english
  from quiz.questions;
