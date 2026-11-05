// Assignment files (assignments/<slug>/) follow the template, and the validator catches mistakes.
// The reference solutions themselves are run by `npm run a:verify` (needs the .NET SDK).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { basename } from 'node:path';
import { assignmentDirs, loadAssignment, validateAssignment, checkHash, linesToText, briefText } from '../scripts/lib/assignments.mjs';

const all = assignmentDirs([]).map(loadAssignment);
const clone = (a) => ({ ...a, data: structuredClone(a.data) });
const errorsOf = (a) => validateAssignment(a).errors;
const hotel = all.find((a) => a.data.slug === 'hotel');

test('there are the 8 initial assignments', () => {
  assert.deepEqual(all.map((a) => a.data.slug).sort(),
    ['car-rental', 'cinema', 'gym', 'hotel', 'library', 'parking-garage', 'school-cafeteria', 'vet-clinic']);
});

for (const a of all) {
  test(`${basename(a.dir)}: valid template, 5 scenarios worth 100, verified`, () => {
    const { errors, warnings } = validateAssignment(a);
    assert.deepEqual(errors, []);
    assert.deepEqual(warnings, []);
    assert.deepEqual(a.data.scenarios.map((s) => s.points), [15, 25, 20, 25, 15]);
    assert.equal(a.data.check?.status, 'ok', 'run npm run a:verify');
    assert.equal(a.data.check?.hash, checkHash(a), 'changed since the last a:verify');
  });
}

test('validator: points must add up to max_points', () => {
  const a = clone(hotel);
  a.data.scenarios[0].points = 10;
  assert.ok(errorsOf(a).some((e) => /add up to 95, not 100/.test(e)));
});

test('validator: every input must end with exit', () => {
  const a = clone(hotel);
  a.data.scenarios[1].input.pop();
  assert.ok(errorsOf(a).some((e) => /must end with "exit"/.test(e)));
});

test('validator: every command must be named in both briefs', () => {
  const a = clone(hotel);
  a.data.scenarios[0].input.unshift('checkout 101');
  const errs = errorsOf(a);
  assert.ok(errs.some((e) => /sk\.brief never mentions the command `checkout`/.test(e)));
  assert.ok(errs.some((e) => /en\.brief never mentions the command `checkout`/.test(e)));
});

test('validator: hidden design needs item, person and a manager with 3 operations', () => {
  const a = clone(hotel);
  a.data.design.classes = a.data.design.classes.filter((c) => c.role !== 'person');
  const errs = errorsOf(a);
  assert.ok(errs.some((e) => /at least 3 classes/.test(e)));
  assert.ok(errs.some((e) => /role "person"/.test(e)));
  const b = clone(hotel);
  b.data.design.classes.find((c) => c.role === 'manager').operations.pop();
  assert.ok(errorsOf(b).some((e) => /exactly 3 operations/.test(e)));
  const c = clone(hotel);
  c.data.design.classes[1].properties = ['string Name'];
  assert.ok(errorsOf(c).some((e) => /at least 2 properties/.test(e)));
});

test('validator: ids, expected output, slug and solution are checked', () => {
  const a = clone(hotel);
  a.data.scenarios[1].id = a.data.scenarios[0].id;
  a.data.scenarios[2].expected = ['', '  '];
  a.data.slug = 'Hotel Tatra';
  a.solution = null;
  const errs = errorsOf(a);
  assert.ok(errs.some((e) => /duplicate id/.test(e)));
  assert.ok(errs.some((e) => /expected output must not be empty/.test(e)));
  assert.ok(errs.some((e) => /slug must be/.test(e)));
  assert.ok(errs.some((e) => /Solution\.cs is missing/.test(e)));
});

test('validator: not 5 scenarios is only a warning', () => {
  const a = clone(hotel);
  a.data.scenarios = a.data.scenarios.slice(0, 4);
  a.data.max_points = 85;
  const { errors, warnings } = validateAssignment(a);
  assert.deepEqual(errors, []);
  assert.ok(warnings.some((w) => /4 scenarios/.test(w)));
});

test('checkHash changes when the solution or a scenario changes', () => {
  const h = checkHash(hotel);
  const a = clone(hotel);
  a.solution = hotel.solution + '\n// changed';
  assert.notEqual(checkHash(a), h);
  const b = clone(hotel);
  b.data.scenarios[0].expected[0] = 'Room 101 added!';
  assert.notEqual(checkHash(b), h);
  const c = clone(hotel);
  c.data.en.title = 'Another title'; // texts do not need a new dotnet run
  assert.equal(checkHash(c), h);
});

test('text helpers: input lines → program input, brief paragraphs → Markdown', () => {
  assert.equal(linesToText(['addroom 101 double', 'exit']), 'addroom 101 double\nexit\n');
  assert.equal(briefText([' First. ', 'Second.']), 'First.\n\nSecond.');
});
