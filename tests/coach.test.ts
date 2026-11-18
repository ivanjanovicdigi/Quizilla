// The "what to do next" coach (src/lib/assignments/coach.ts): one step, in learning order.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildCoach, programChecks, COACH_PATH, type CoachInput } from '../src/lib/assignments/coach.ts';
import { DESIGN_CHECKS } from '../src/lib/assignments/guide.ts';
import type { Feedback } from '../src/lib/assignments/feedback.ts';
import type { ScenarioResult } from '../src/lib/assignments/scoring.ts';

// a real student attempt at the cafe: classes, but no reading of commands at all
const NO_INPUT = `namespace ConsoleApp3;
class Program
{
    static void Main(string[] args)
    {
        Menu menucko = new Menu();
        menucko.ZobrazMenu();
        // Console.ReadLine() only in a comment
    }
}
public class Produkt { public string name = ""; public double cena = 0; }
public class Menu { public List<Produkt> Produkty = new List<Produkt>(); public void ZobrazMenu() { } }`;

test('programChecks: no input at all (comments do not count)', () => {
  assert.deepEqual(programChecks(NO_INPUT), { input_read: false, input_loop: false, input_exit: false });
});

test('programChecks: one read outside a loop', () => {
  assert.deepEqual(programChecks('string? line = Console.ReadLine();\nConsole.WriteLine(line);'),
    { input_read: true, input_loop: false, input_exit: false });
});

test('programChecks: read inside while / for / do, or in the while head', () => {
  for (const code of [
    'while (true)\n{\n    if (true) { }\n    string? l = Console.ReadLine();\n    if (l == "exit") break;\n}',
    'for (;;) { var l = Console.ReadLine(); if (l == "EXIT") break; }',
    'do\n{\n  var l = Console.ReadLine(); if (l == "exit") break;\n} while (true);',
    'string? line;\nwhile ((line = Console.ReadLine()) != null && line != "exit") { }',
  ]) assert.deepEqual(programChecks(code), { input_read: true, input_loop: true, input_exit: true }, code);
});

test('programChecks: every reference solution reads commands in a loop until exit', () => {
  for (const slug of ['cafe', 'hotel', 'library']) {
    const code = readFileSync(`assignments/${slug}/Solution.cs`, 'utf8');
    assert.deepEqual(programChecks(code), { input_read: true, input_loop: true, input_exit: true }, slug);
  }
});

const GOOD = 'while (true) { var l = Console.ReadLine(); if (l == "exit") break; }';
const allOk = { classes: [], checks: DESIGN_CHECKS.map((id) => ({ id, ok: true })) };
const scenarios = [
  { index: 0, name_sk: 'Prvý', name_en: 'First', input: 'name Peter\nmenu\nexit\n', expected: 'Hello, Peter!\n1. Espresso 2.00 EUR\n', points: 50 },
  { index: 1, name_sk: 'Druhý', name_en: 'Second', input: 'name Eva\nexit\n', expected: 'Hello, Eva!\n', points: 50 },
];
const row = (index: number, actual: string, extra: Partial<ScenarioResult> = {}): ScenarioResult => ({
  index, passed: false, points: 0, actual, timed_out: false, output_limit: false, ...extra,
});
const fb = (rows: ScenarioResult[]): Feedback => ({ fresh: true, compiled: true, diagnostics: [], rows, score: 0, max_points: 100 });
const input = (o: Partial<CoachInput> = {}): CoachInput => ({
  code: GOOD, errors: [], review: allOk, feedback: null, testedCode: null, scenarios, ...o,
});
const passRow = row(1, 'Hello, Eva!', { passed: true, points: 50 });

test('coach: start, compile error, analysing', () => {
  assert.equal(buildCoach(input({ code: '  ', review: null })).step.id, 'start');
  const c = buildCoach(input({ errors: [{ line: 4, column: 9, id: 'CS1002', severity: 'error', message: '; expected' }, { line: 9, column: 1, id: 'CS0103', severity: 'error', message: 'x' }] }));
  assert.equal(c.step.id, 'compile');
  assert.deepEqual(c.step.vars, { line: 4, message: '; expected', more: 1 });
  assert.deepEqual(c.step.jump, { line: 4, column: 9 });
  assert.equal(buildCoach(input({ review: null })).step.id, 'analysing');
});

test('coach: design first, then reading commands, then the rest of the design', () => {
  const review = { classes: [], checks: [{ id: 'classes', ok: false, n: 2 }, { id: 'link', ok: false }, { id: 'public_fields', ok: false, items: [{ name: 'Produkt.name', line: 12 }] }] };
  const c = buildCoach(input({ code: NO_INPUT, review }));
  assert.equal(c.step.id, 'classes');
  assert.equal(c.step.vars.n, 2);
  const noClassesIssue = { classes: [], checks: review.checks.slice(1) };
  assert.equal(buildCoach(input({ code: NO_INPUT, review: noClassesIssue })).step.id, 'input_read');
  assert.equal(buildCoach(input({ review: noClassesIssue })).step.id, 'link');
  const onlyFields = { classes: [], checks: review.checks.slice(2) };
  assert.equal(buildCoach(input({ review: onlyFields })).step.id, 'run_tests');  // tests before clean-up
});

test('coach: tests – the first failing test becomes one concrete hint', () => {
  const step = (rows: ScenarioResult[]) => buildCoach(input({ feedback: fb(rows), testedCode: GOOD })).step;
  assert.equal(step([row(0, ''), passRow]).id, 'test_silent');
  assert.equal(step([row(0, ''), passRow]).test?.expected, 'Hello, Peter!');
  const extra = step([row(0, 'Vitajte!\nHello, Peter!\n1. Espresso 2.00 EUR'), passRow]);
  assert.equal(extra.id, 'test_extra_start');
  assert.equal(extra.test?.actual, 'Vitajte!');
  const wrong = step([row(0, 'hello,  PETER!\n1. Espresso 2,00 EUR'), passRow]);
  assert.equal(wrong.id, 'test_wrong');
  assert.deepEqual([wrong.test?.line, wrong.test?.expected, wrong.test?.actual], [2, '1. Espresso 2.00 EUR', '1. Espresso 2,00 EUR']);
  assert.equal(step([row(0, 'Hello, Peter!'), passRow]).id, 'test_missing');
  assert.equal(step([row(0, 'Hello, Peter!\n1. Espresso 2.00 EUR\nBye'), passRow]).id, 'test_extra');
  assert.equal(step([row(0, '', { timed_out: true }), passRow]).id, 'test_timeout');
  const crash = step([row(0, 'Hello, Peter!', { exception: 'System.NullReferenceException', exception_message: 'Object reference…' }), passRow]);
  assert.deepEqual([crash.id, crash.vars.exception], ['test_crash', 'NullReferenceException']);
  // the first test passes → the hint is about the second one
  assert.equal(step([row(0, 'Hello, Peter!\n1. Espresso 2.00 EUR', { passed: true }), row(1, '')]).test?.name_en, 'Second');
});

test('coach: changed code after passing tests → run them again; all done at the end', () => {
  const rows = [row(0, '', { passed: true }), passRow];
  const stale = buildCoach(input({ feedback: fb(rows), testedCode: 'older code' }));
  assert.equal(stale.step.id, 'run_tests');
  assert.equal(stale.staleTests, true);
  const done = buildCoach(input({ feedback: fb(rows), testedCode: GOOD }));
  assert.equal(done.step.id, 'done');
  assert.equal(done.done, COACH_PATH.length);
  assert.equal(done.total, COACH_PATH.length);
});
