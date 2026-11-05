// Scoring of one check in the browser (src/lib/assignments/scoring.ts): pass/fail per scenario
// and the total. Partial points = sum of the points of passed scenarios.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { evaluateRun, totalScore, type Scenario } from '../src/lib/assignments/scoring.ts';
import type { RunResult } from '../src/lib/assignments/protocol.ts';

const scenario: Scenario = {
  index: 2, name_sk: 'Obsadená', name_en: 'Taken', points: 20,
  input: 'addroom 101 double\nexit\n', expected: 'Room 101 added.\n',
};
const run = (stdout: string, extra: Partial<RunResult> = {}): RunResult => ({ stdout, stderr: '', output_limit: false, ...extra });

test('right output passes and earns the scenario points', () => {
  const r = evaluateRun(scenario, run('room 101 added.'), false, 12);
  assert.equal(r.passed, true);
  assert.equal(r.points, 20);
  assert.equal(r.index, 2);
  assert.equal(r.ms, 12);
  assert.equal(r.actual, 'room 101 added.');
});

test('wrong output fails with 0 points and keeps what was printed', () => {
  const r = evaluateRun(scenario, run('Room 101 created.'), false);
  assert.equal(r.passed, false);
  assert.equal(r.points, 0);
  assert.equal(r.actual, 'Room 101 created.');
});

test('a timeout fails even if the output so far was right', () => {
  const r = evaluateRun(scenario, run('Room 101 added.'), true);
  assert.equal(r.passed, false);
  assert.equal(r.timed_out, true);
});

test('a timeout without any result fails', () => {
  const r = evaluateRun(scenario, null, true, 3000);
  assert.equal(r.passed, false);
  assert.equal(r.points, 0);
  assert.equal(r.actual, '');
  assert.equal(r.timed_out, true);
});

test('too much output fails', () => {
  const r = evaluateRun(scenario, run('Room 101 added.', { output_limit: true }), false);
  assert.equal(r.passed, false);
  assert.equal(r.output_limit, true);
});

test('a crash fails only when the output is wrong (tests check console output)', () => {
  const crashedRight = evaluateRun(scenario, run('Room 101 added.', { exception: 'System.FormatException', exception_message: 'bad' }), false);
  assert.equal(crashedRight.passed, true);
  assert.equal(crashedRight.exception, 'System.FormatException');
  const crashedEarly = evaluateRun(scenario, run('', { exception: 'System.NullReferenceException' }), false);
  assert.equal(crashedEarly.passed, false);
});

test('Environment.Exit is recorded and output still decides', () => {
  const r = evaluateRun(scenario, run('Room 101 added.', { exit_code: 0 }), false);
  assert.equal(r.passed, true);
  assert.equal(r.exit_code, 0);
});

test('totalScore adds the points of passed scenarios only', () => {
  assert.equal(totalScore([
    { index: 0, passed: true, points: 15 },
    { index: 1, passed: true, points: 25 },
    { index: 2, passed: false, points: 0 },
    { index: 3, passed: true, points: 25 },
    { index: 4, passed: false, points: 0 },
  ]), 65);
});

test('totalScore counts each scenario once (no farming by duplicates)', () => {
  assert.equal(totalScore([
    { index: 0, passed: true, points: 15 },
    { index: 0, passed: true, points: 15 },
    { index: 1, passed: false, points: 25 },
  ]), 15);
});

test('totalScore: nothing passed = 0, everything passed = 100', () => {
  assert.equal(totalScore([]), 0);
  const all = [15, 25, 20, 25, 15].map((points, index) => ({ index, passed: true, points }));
  assert.equal(totalScore(all), 100);
});
