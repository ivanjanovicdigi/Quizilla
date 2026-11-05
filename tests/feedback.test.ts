// Feedback helpers: expected vs actual line view (diff.ts) and the display model (feedback.ts).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { outputDiff, visibleLines } from '../src/lib/assignments/diff.ts';
import { errorsForServer, fromCheck, fromSubmission } from '../src/lib/assignments/feedback.ts';
import type { Diagnostic } from '../src/lib/assignments/protocol.ts';

test('visibleLines drops empty lines and trailing spaces, keeps the rest as written', () => {
  assert.deepEqual(visibleLines('  Room 101 Added.  \r\n\r\n101 double\n\n'), ['  Room 101 Added.', '101 double']);
  assert.deepEqual(visibleLines(null), []);
});

test('outputDiff aligns lines and marks only real differences', () => {
  const { rows, more } = outputDiff('ROOM 101 added.\nRoom 101 is taken.', 'Room 101 added.\nRoom 101 is not available.\n');
  assert.equal(more, 0);
  assert.deepEqual(rows, [
    { expected: 'Room 101 added.', actual: 'ROOM 101 added.', same: true },
    { expected: 'Room 101 is not available.', actual: 'Room 101 is taken.', same: false },
  ]);
});

test('outputDiff shows missing and extra lines', () => {
  const missing = outputDiff('a', 'a\nb').rows;
  assert.deepEqual(missing[1], { expected: 'b', actual: null, same: false });
  const extra = outputDiff('a\nWelcome', 'a').rows;
  assert.deepEqual(extra[1], { expected: null, actual: 'Welcome', same: false });
});

test('outputDiff stops after max rows and says how many are left', () => {
  const long = Array.from({ length: 250 }, (_, i) => `line ${i}`).join('\n');
  const { rows, more } = outputDiff(long, 'line 0', 200);
  assert.equal(rows.length, 200);
  assert.equal(more, 50);
});

const diags: Diagnostic[] = [
  { line: 3, column: 5, id: 'CS1002', severity: 'error', message: '; expected' },
  { line: 1, column: 1, id: 'CS8618', severity: 'warning', message: 'Non-nullable property' },
];

test('errorsForServer sends errors only, at most 50', () => {
  assert.deepEqual(errorsForServer(diags), [{ line: 3, column: 5, id: 'CS1002', message: '; expected' }]);
  const many = Array.from({ length: 80 }, (_, i) => ({ ...diags[0], line: i + 1 }));
  assert.equal(errorsForServer(many).length, 50);
});

test('fromCheck keeps everything from the browser check', () => {
  const f = fromCheck({ compiled: false, diagnostics: diags, results: [], score: 0, max_points: 100 });
  assert.equal(f.fresh, true);
  assert.equal(f.compiled, false);
  assert.equal(f.diagnostics.length, 2);
});

test('fromSubmission maps a stored submission (latest or older)', () => {
  const s = {
    id: 7, assignment_id: 4, submitted_at: '2026-11-05T19:34:40Z', compiled: true, score: 40, max_points: 100,
    passed: 2, scenarios: 5,
    compile_errors: [{ line: null, column: null, id: null, message: 'x' }],
    results: [{ scenario: 0, passed: true, points: 15, actual: 'Room 101 added.' },
              { scenario: 1, passed: false, points: 0, actual: '' }],
  };
  const f = fromSubmission(s);
  assert.equal(f.fresh, false);
  assert.equal(f.latest, true);
  assert.equal(f.score, 40);
  assert.deepEqual(f.rows[0], { index: 0, passed: true, points: 15, actual: 'Room 101 added.', timed_out: false, output_limit: false });
  assert.deepEqual(f.diagnostics[0], { line: 0, column: 0, id: '', severity: 'error', message: 'x' });
  assert.equal(fromSubmission(s, false).latest, false);
});
