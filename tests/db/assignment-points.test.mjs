// 032: each assignment adds its LATEST score to the points everywhere points are shown.
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { replay, helpers, read } from './replay.mjs';

let db, h, ivan, eva, ids;

before(async () => {
  db = await replay();
  h = helpers(db);
  await db.exec(read('supabase/updates/032_assignment_points.sql')); // a second time: safe to re-run
  await h.addRoster([['ivan.janovic@lyceum.sk', 'Ivan Janovič', 'Teachers'], ['eva@lyceum.sk', 'Eva Malá', 'Lambda']]);
  await db.exec(`select quiz.set_admin_passphrase('test admin phrase')`);

  await h.as('anon');
  ivan = (await h.rpc(`select public.login_student('ivan.janovic@lyceum.sk') r`)).id;
  eva = (await h.rpc(`select public.login_student('eva@lyceum.sk') r`)).id;
  ids = Object.fromEntries((await h.rpc('select public.get_assignments($1) r', [ivan])).map((a) => [a.slug, a.id]));
  const submit = (aid, passed) => h.rpc(`select public.submit_assignment($1, $2, 'class P {}', true, '[]', $3) r`,
    [ivan, aid, JSON.stringify(passed.map((i) => ({ scenario: i, passed: true })))]);
  await submit(ids.hotel, [0, 1, 3, 4]);    // 80
  await submit(ids.hotel, [0, 1, 2, 3, 4]); // 100 – replaces the 80
  await submit(ids.library, [1, 4]);        // 25 + 15 = 40

  // quiz points: Ivan 20 + 10, Eva 12
  await h.as(null);
  const topic = (await h.row('select id from quiz.topics order by id limit 1')).id;
  const qid = (await h.row(`insert into quiz.questions (topic_id, difficulty, body, answers, correct_index)
                            values ($1, 1, 'q', array['a','b','c','d'], 0) returning id`, [topic])).id;
  await db.query(`insert into quiz.attempts (student_id, question_id, topic_id, difficulty, chosen_index, is_correct, points)
                  values ($1,$3,$4,1,0,true,20), ($1,$3,$4,1,0,true,10), ($2,$3,$4,1,0,true,12)`, [ivan, eva, qid, topic]);
  await h.as('anon');
});

test('assignment points = latest score of each assignment (100 + 40)', async () => {
  await h.as(null);
  assert.equal((await h.row('select quiz.assignment_points($1) p', [ivan])).p, 140);
  await h.as('anon');
});

test('home page points = quiz points + assignment points', async () => {
  assert.equal(Number((await h.rpc('select public.get_catalog($1) r', [ivan])).points), 170);
  assert.equal(Number((await h.rpc('select public.get_catalog($1) r', [eva])).points), 12);
});

test('class leaderboard includes assignment points', async () => {
  const board = await h.rpc('select public.get_class_leaderboard() r');
  assert.equal(Number(board.find((c) => c.name === 'Teachers').points), 170);
  assert.equal(Number(board.find((c) => c.name === 'Lambda').points), 12);
});

test('statistics: assignments section with points, solved and per-task scores', async () => {
  const st = await h.rpc('select public.get_stats($1) r', [ivan]);
  const as = st.assignments;
  assert.deepEqual([as.points, as.max_points, as.done, as.tried, as.count, as.items.length], [140, 800, 1, 2, 8, 8]);
  const hotel = as.items.find((i) => i.slug === 'hotel');
  assert.equal(hotel.score, 100);
  assert.equal(hotel.submissions, 2);
  assert.equal(as.items.find((i) => i.slug === 'gym').score, null);
  assert.ok(Array.isArray(st.topics) && st.rank && st.tiers);
});

test('statistics: no assignments section without access and submissions', async () => {
  assert.equal((await h.rpc('select public.get_stats($1) r', [eva])).assignments, null);
});

test('get_stats is quiz.stats_json plus the assignments section (no drift)', async () => {
  const { assignments, ...rest } = await h.rpc('select public.get_stats($1) r', [ivan]);
  assert.ok(assignments);
  await h.as(null);
  assert.deepEqual(rest, (await h.row('select quiz.stats_json($1, null) r', [ivan])).r);
  await h.as('anon');
});

test('report views have assignment_points and total_points', async () => {
  await h.as(null);
  const s = await h.row(`select points, assignment_points, total_points from quiz.v_student_totals where email = 'ivan.janovic@lyceum.sk'`);
  assert.deepEqual([Number(s.points), s.assignment_points, Number(s.total_points)], [30, 140, 170]);
  const c = await h.row(`select points, assignment_points, total_points from quiz.v_class_totals where class = 'Teachers'`);
  assert.deepEqual([Number(c.points), Number(c.assignment_points), Number(c.total_points)], [30, 140, 170]);
  await h.as('anon');
});

test('admin: user list, student statistics, reset also deletes submissions', async () => {
  const login = await h.rpc(`select public.admin_login('test admin phrase') r`);
  assert.ok(login.ok);
  const users = await h.rpc('select public.admin_list_users($1) r', [login.token]);
  const u = users.find((x) => x.email === 'ivan.janovic@lyceum.sk');
  assert.equal(u.points, 170);
  assert.equal(u.assignment_points, 140);
  assert.equal((await h.rpc(`select public.admin_student_stats($1, 'ivan.janovic@lyceum.sk') r`, [login.token])).assignments.points, 140);

  const reset = await h.rpc(`select public.admin_reset_progress($1, 'ivan.janovic@lyceum.sk') r`, [login.token]);
  assert.equal(reset.assignment_submissions, 3);
  assert.equal(reset.answers, 2);
  assert.equal(Number((await h.rpc('select public.get_catalog($1) r', [ivan])).points), 0);
  const st = await h.rpc('select public.get_stats($1) r', [ivan]);
  assert.equal(st.assignments.points, 0);
  assert.equal(st.assignments.tried, 0);
  const board = await h.rpc('select public.get_class_leaderboard() r');
  assert.equal(Number(board.find((c) => c.name === 'Teachers').points), 0);
});
