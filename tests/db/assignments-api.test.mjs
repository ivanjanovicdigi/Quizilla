// 030: coding assignment tables and API – privacy, access gate, server-side scoring, bad input.
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { replay, helpers, read } from './replay.mjs';

const hotel = [
  { name_sk: 'Pridanie izby', name_en: 'Add a room', input: 'addroom 101 double\nexit\n', expected: 'Room 101 added.\n', points: 15 },
  { name_sk: 'Rezervácia', name_en: 'Booking', input: 'x', expected: 'y', points: 25 },
  { name_sk: 'Obsadená', name_en: 'Taken', input: 'x', expected: 'y', points: 20 },
  { name_sk: 'Voľné', name_en: 'Free', input: 'x', expected: 'y', points: 25 },
  { name_sk: 'Neexistuje', name_en: 'Missing', input: 'x', expected: 'y', points: 15 },
];

let db, h, aid, ivan, eva, jan;
const insertAssignment = (slug, scenarios, max = 100) => db.query(
  `insert into quiz.assignments (slug, title_sk, title_en, brief_sk, brief_en, max_points, scenarios, design, reference_solution)
   values ($1, 'T', 'T', 'b', 'b', $3, $2, '{"classes":["Room"]}', 'class Secret {}') returning id`,
  [slug, JSON.stringify(scenarios), max]);
const submit = (sid, results, compiled = true, code = 'class P {}', errs = '[]') =>
  h.rpc('select public.submit_assignment($1, $2, $3, $4, $5, $6) r', [sid, aid, code, compiled, errs, JSON.stringify(results)]);
const allPassed = () => [0, 1, 2, 3, 4].map((i) => ({ scenario: i, passed: true }));
const setAccess = async (value) => {
  await h.as(null);
  await db.query(`update quiz.config set value = $1 where key = 'assignments_access'`, [value]);
  await h.as('anon');
};

before(async () => {
  db = await replay({ skip: ['031_assignments_all.sql'] }); // own test data instead of the 8 assignments
  h = helpers(db);
  await db.exec('delete from quiz.assignment_submissions; delete from quiz.assignments;');
  aid = (await insertAssignment('hotel', hotel)).rows[0].id;
  await h.addRoster([
    ['ivan.janovic@lyceum.sk', 'Ivan Janovič', 'Teachers'], ['eva@lyceum.sk', 'Eva Malá', 'Lambda'], ['jan@lyceum.sk', 'Ján Novák', 'Lambda'],
  ]);
  await h.as('anon');
  ivan = (await h.rpc(`select public.login_student('ivan.janovic@lyceum.sk') r`)).id;
  eva = (await h.rpc(`select public.login_student('eva@lyceum.sk') r`)).id;
  jan = (await h.rpc(`select public.login_student('jan@lyceum.sk') r`)).id;
});

test('030 is safe to re-run and keeps a changed access value', async () => {
  await setAccess('*');
  await h.as(null);
  await db.exec(read('supabase/updates/030_coding_assignments.sql'));
  assert.equal((await h.row(`select value from quiz.config where key = 'assignments_access'`)).value, '*');
  await setAccess('ivan.janovic@lyceum.sk');
});

test('scenario points must be whole, positive and add up to max_points', async () => {
  await h.as(null);
  const bad = [
    hotel.slice(0, 4),
    [{ ...hotel[0], points: 'abc' }, ...hotel.slice(1)],
    [{ ...hotel[0], points: 14.5 }, { ...hotel[1], points: 25.5 }, ...hotel.slice(2)],
    [{ ...hotel[0], expected: undefined }, ...hotel.slice(1)],
    [],
  ];
  for (const [i, sc] of bad.entries()) {
    await assert.rejects(insertAssignment(`bad-${i}`, sc), undefined, `case ${i}`);
  }
  await h.as('anon');
});

test('tables are private for the app role', async () => {
  assert.ok(await h.error('select count(*) from quiz.assignments'));
  assert.ok(await h.error('select count(*) from quiz.assignment_submissions'));
});

test('access gate: only listed users (default: Ivan), guests blocked', async () => {
  assert.equal(await h.rpc('select public.assignments_enabled($1) r', [ivan]), true);
  assert.equal(await h.rpc('select public.assignments_enabled($1) r', [eva]), false);
  assert.equal(await h.rpc('select public.assignments_enabled() r'), false);
  assert.equal(await h.rpc('select public.assignments_enabled(gen_random_uuid()) r'), false);
  for (const [sql, p] of [
    ['select public.get_assignments($1)', [eva]],
    ['select public.get_assignments()', []],
    ['select public.get_assignment($1)', [aid]],
    ['select public.get_assignment($1, $2)', [aid, eva]],
    [`select public.submit_assignment($1, $2, 'x', true, '[]', '[]')`, [eva, aid]],
    ['select public.get_assignment_submissions($1, $2)', [eva, aid]],
    ['select public.get_assignment_submission($1, 1)', [eva]],
  ]) {
    assert.match(await h.error(sql, p) ?? '', /assignments_disabled/, sql);
  }
  assert.equal((await h.rpc('select public.get_assignments($1) r', [ivan])).length, 1);
});

test('access list ignores spaces and capitals; * opens it to everyone', async () => {
  await setAccess(' Ivan.Janovic@lyceum.sk , eva@lyceum.sk ');
  assert.equal(await h.rpc('select public.assignments_enabled($1) r', [eva]), true);
  assert.equal(await h.rpc('select public.assignments_enabled($1) r', [jan]), false);
  await setAccess('*');
  assert.equal(await h.rpc('select public.assignments_enabled() r'), true);
});

test('detail sends scenarios but never the hidden design or reference solution', async () => {
  const d = await h.rpc('select public.get_assignment($1) r', [aid]);
  assert.equal(d.scenarios.length, 5);
  assert.equal(d.scenarios[1].points, 25);
  assert.equal(d.scenarios[0].index, 0);
  const text = JSON.stringify(d);
  assert.ok(!text.includes('Secret') && !text.includes('classes'));
  assert.match(await h.error('select public.get_assignment(9999)') ?? '', /unknown_assignment/);
});

test('server score = stored points of really passed scenarios (cheating attempts ignored)', async () => {
  const r = await submit(eva, [
    { scenario: 0, passed: true, actual: 'Room 101 added.' },
    { scenario: 0, passed: true },              // duplicate
    { scenario: 1, passed: true, points: 1000 }, // fake points
    { scenario: 99, passed: true },             // unknown scenario
    { scenario: '3', passed: true },            // index as text
    { scenario: 2, passed: 'yes' },             // not a boolean
  ]);
  assert.equal(r.score, 40);
  assert.equal(r.results.length, 5);
  assert.equal(r.results[0].actual, 'Room 101 added.');
  assert.equal(r.previous_score, null);
  assert.equal(r.points_change, 40);
});

test('code that did not compile scores 0; compile errors are cleaned', async () => {
  const r = await submit(eva, allPassed(), false, 'class P {',
    JSON.stringify([{ line: 1, column: 10, id: 'CS1513', message: '} expected' }, { line: 'x', message: 5 }]));
  assert.equal(r.score, 0);
  assert.equal(r.compiled, false);
  assert.equal(r.compile_errors[0].line, 1);
  assert.equal(r.compile_errors[0].id, 'CS1513');
  assert.equal(r.compile_errors[1].line, null);
  assert.equal(r.points_change, -40);
});

test('the latest submission counts; history is newest first', async () => {
  assert.equal((await submit(eva, allPassed())).score, 100);
  const list = await h.rpc('select public.get_assignments($1) r', [eva]);
  assert.equal(list[0].latest.score, 100);
  assert.equal(list[0].submissions, 3);
  const d = await h.rpc('select public.get_assignment($1, $2) r', [aid, eva]);
  assert.equal(d.latest.score, 100);
  assert.equal(d.latest.code, 'class P {}');
  const hist = await h.rpc('select public.get_assignment_submissions($1, $2) r', [eva, aid]);
  assert.deepEqual(hist.map((x) => x.score), [100, 0, 40]);
  assert.ok(!('code' in hist[0]));
  const old = await h.rpc('select public.get_assignment_submission($1, $2) r', [eva, hist[2].id]);
  assert.equal(old.score, 40);
});

test('students only see their own submissions', async () => {
  const hist = await h.rpc('select public.get_assignment_submissions($1, $2) r', [eva, aid]);
  assert.match(await h.error('select public.get_assignment_submission($1, $2)', [jan, hist[0].id]) ?? '', /unknown_submission/);
  const list = await h.rpc('select public.get_assignments($1) r', [jan]);
  assert.equal(list[0].latest, null);
  assert.equal(list[0].submissions, 0);
  assert.deepEqual(await h.rpc('select public.get_assignment_submissions($1, $2) r', [jan, aid]), []);
});

test('bad input is rejected', async () => {
  assert.match(await h.error(`select public.submit_assignment(gen_random_uuid(), $1, 'x', true, '[]', '[]')`, [aid]) ?? '', /unknown_student/);
  assert.match(await h.error(`select public.submit_assignment($1, $2, '', true, '[]', '[]')`, [eva, aid]) ?? '', /invalid_code/);
  assert.match(await h.error(`select public.submit_assignment($1, $2, repeat('x', 100001), true, '[]', '[]')`, [eva, aid]) ?? '', /invalid_code/);
  assert.match(await h.error(`select public.submit_assignment($1, $2, 'x', true, '[]', '{}')`, [eva, aid]) ?? '', /invalid_results/);
});

test('report view shows the latest score', async () => {
  await h.as(null);
  const r = await h.row(`select score, submissions from quiz.v_assignment_scores where email = 'eva@lyceum.sk'`);
  assert.equal(r.score, 100);
  assert.equal(Number(r.submissions), 3);
  await h.as('anon');
});
