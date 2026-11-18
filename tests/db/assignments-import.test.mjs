// 031: the generated import of the assignments (031: 8, 034: cafe) matches the JSON files in assignments/.
import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { replay, helpers, read, updateFiles } from './replay.mjs';

const importFile = updateFiles().find((f) => /^\d{3}_assignments_all\.sql$/.test(f));
let db, h, ivan, eva;

before(async () => {
  db = await replay();
  h = helpers(db);
  await db.exec(read(`supabase/updates/${importFile}`)); // a second time: must not duplicate
  await h.addRoster([['ivan.janovic@lyceum.sk', 'Ivan', 'Teachers'], ['eva@lyceum.sk', 'Eva', 'Lambda']]);
  await h.as('anon');
  ivan = (await h.rpc(`select public.login_student('ivan.janovic@lyceum.sk') r`)).id;
  eva = (await h.rpc(`select public.login_student('eva@lyceum.sk') r`)).id;
});

test('9 assignments (8 + cafe), no duplicates after a re-run, hidden parts stored', async () => {
  await h.as(null);
  assert.equal((await h.row('select count(*)::int c from quiz.assignments')).c, 9);
  assert.equal((await h.row('select count(*)::int c from quiz.assignments where design is null or reference_solution is null')).c, 0);
  // the file's CRLF line ends must not end up in the texts
  assert.equal((await h.row(`select count(*)::int c from quiz.assignments
                              where position(chr(13) in brief_en || brief_sk || reference_solution) > 0`)).c, 0);
  await h.as('anon');
});

test('since 033 everyone sees them in order, guests included; closing the gate blocks the others again', async () => {
  const slugs = ['hotel', 'library', 'car-rental', 'gym', 'cinema', 'parking-garage', 'vet-clinic', 'school-cafeteria', 'cafe'];
  for (const who of [ivan, eva, null]) {
    const list = await h.rpc('select public.get_assignments($1) r', [who]);
    assert.deepEqual(list.map((a) => a.slug), slugs, String(who));
    assert.equal(await h.rpc('select public.assignments_enabled($1) r', [who]), true, String(who));
  }

  await h.as(null);
  await db.exec(`update quiz.config set value = 'ivan.janovic@lyceum.sk' where key = 'assignments_access'`);
  await h.as('anon');
  assert.equal((await h.rpc('select public.get_assignments($1) r', [ivan])).length, 9);
  assert.match(await h.error('select public.get_assignments($1)', [eva]) ?? '', /assignments_disabled/);
  assert.match(await h.error('select public.get_assignments(null)') ?? '', /assignments_disabled/);

  // 033 is safe to re-run and opens the gate again
  await h.as(null);
  await db.exec(read('supabase/updates/033_assignments_open.sql'));
  await h.as('anon');
  assert.equal((await h.rpc('select public.get_assignments($1) r', [eva])).length, 9);
});

test('each assignment in the database matches its JSON file', async () => {
  const text = (lines) => lines.map((l) => l + '\n').join('');
  for (const a of await h.rpc('select public.get_assignments($1) r', [ivan])) {
    const d = await h.rpc('select public.get_assignment($1, $2) r', [a.id, ivan]);
    const src = JSON.parse(read(`assignments/${a.slug}/assignment.json`));
    assert.equal(d.max_points, 100, a.slug);
    assert.equal(d.brief_en, src.en.brief.map((p) => p.trim()).join('\n\n'), a.slug);
    assert.equal(d.brief_sk, src.sk.brief.map((p) => p.trim()).join('\n\n'), a.slug);
    assert.deepEqual(d.scenarios.map((s) => [s.name_sk, s.name_en, s.input, s.expected, s.points]),
      src.scenarios.map((s) => [s.sk, s.en, text(s.input), text(s.expected), s.points]), a.slug);
    const json = JSON.stringify(d);
    assert.ok(!json.includes('Console.ReadLine') && !json.includes('"role"'), `${a.slug}: hidden parts leaked`);
  }
});
