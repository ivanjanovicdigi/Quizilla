-- Run as superuser; switches to the anon role like the app does.
\set ON_ERROR_STOP 1
set role anon;

-- direct table access must fail
do $$ begin
  begin perform 1 from quiz.questions; raise exception 'FAIL: anon can read questions';
  exception when insufficient_privilege then raise notice 'OK: tables are private'; end;
end $$;

select public.list_classes();

do $$ begin
  begin perform public.register_student('x@gmail.com','Eva Mala',1); raise exception 'FAIL: foreign domain accepted';
  exception when raise_exception then raise notice 'OK: % rejected', sqlerrm; end;
end $$;

create temp table if not exists t_ctx(k text primary key, v text);
reset role;
grant all on t_ctx to anon;
set role anon;

insert into t_ctx select 'sid', public.register_student(' Eva.Mala@Lyceum.sk ','Eva   Malá',1)->>'id';
insert into t_ctx select 'sid2', public.register_student('jan.novak@lyceum.sk','Ján Novák',2)->>'id';
-- re-register with other class keeps class 1
select public.register_student('eva.mala@lyceum.sk','Eva Malá',3);

-- locked level
do $$ declare sid uuid := (select v from t_ctx where k='sid'); begin
  begin perform public.get_questions(sid, (select (public.get_catalog(sid)->'subjects'->0->'topics'->0->>'id')::int), 2);
    raise exception 'FAIL: level 2 was not locked';
  exception when raise_exception then raise notice 'OK: % ', sqlerrm; end;
end $$;

-- answer level 1 of first topic: all correct (we peek at keys as superuser)
reset role;
create temp table keys as select id, correct_index, topic_id, difficulty from quiz.questions;
grant select on keys to anon;
set role anon;

do $$
declare sid uuid := (select v from t_ctx where k='sid');
        tid int := (select (public.get_catalog(sid)->'subjects'->0->'topics'->0->>'id')::int);
        qs jsonb; q jsonb; r jsonb; ck int;
begin
  qs := public.get_questions(sid, tid, 1, 10);
  raise notice 'got % questions, has key field: %', jsonb_array_length(qs), qs->0 ? 'correct_index';
  for q in select * from jsonb_array_elements(qs) loop
    select correct_index into ck from keys where id = (q->>'id')::bigint;
    r := public.submit_answer(sid, (q->>'id')::bigint, ck);
    raise notice 'correct=% points=% newly_unlocked=%', r->'correct', r->'points', r->'newly_unlocked';
  end loop;
  -- answering again the same question correctly gives 0 points
  r := public.submit_answer(sid, (qs->0->>'id')::bigint, (select correct_index from keys where id=(qs->0->>'id')::bigint));
  raise notice 'repeat points=% (expect 0)', r->'points';
  -- now level 2 available
  qs := public.get_questions(sid, tid, 2, 10);
  raise notice 'level 2 questions: %', jsonb_array_length(qs);
  -- answer level 2 wrong 4x -> level 3 stays locked
  for q in select * from jsonb_array_elements(qs) loop
    select correct_index into ck from keys where id = (q->>'id')::bigint;
    r := public.submit_answer(sid, (q->>'id')::bigint, (ck+1)%4);
  end loop;
  raise notice 'after wrong answers levels: %', (select jsonb_agg(jsonb_build_object('lvl',e->'level','unlocked',e->'unlocked','met',e->'met','recent',e->'recent_correct')) from jsonb_array_elements(r->'progress'->'levels') e);
end $$;

select jsonb_pretty(public.get_class_leaderboard(null));
select jsonb_pretty(public.get_class_ranking((select v::uuid from t_ctx where k='sid2'), 7));
select public.get_catalog((select v::uuid from t_ctx where k='sid'))->'student';
reset role;
select * from quiz.v_student_totals;
select * from quiz.v_class_totals;
