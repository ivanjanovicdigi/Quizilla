// Output comparison for coding assignments (src/lib/assignments/compare.js).
// Rule: ignore letter case and extra/trailing whitespace; everything else must match.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { normalizeOutput, outputsMatch, firstDifference } from '../src/lib/assignments/compare.js';

const expected = 'Room 101 added.\nRoom 101 booked for John.\n';

test('identical output matches', () => {
  assert.ok(outputsMatch(expected, expected));
});

test('letter case is ignored', () => {
  assert.ok(outputsMatch('ROOM 101 ADDED.\nroom 101 booked for john.\n', expected));
});

test('extra spaces and tabs inside a line count as one space', () => {
  assert.ok(outputsMatch('Room   101\tadded.\nRoom 101  booked for   John.', expected));
});

test('leading and trailing spaces on a line are ignored', () => {
  assert.ok(outputsMatch('  Room 101 added.   \n\tRoom 101 booked for John.\t\n', expected));
});

test('empty lines anywhere are ignored', () => {
  assert.ok(outputsMatch('\n\nRoom 101 added.\n\n   \nRoom 101 booked for John.\n\n\n', expected));
});

test('Windows and old Mac line ends are the same as \\n', () => {
  assert.ok(outputsMatch('Room 101 added.\r\nRoom 101 booked for John.\r\n', expected));
  assert.ok(outputsMatch('Room 101 added.\rRoom 101 booked for John.', expected));
});

test('a missing final newline does not matter', () => {
  assert.ok(outputsMatch('Room 101 added.\nRoom 101 booked for John.', expected));
});

test('different punctuation fails', () => {
  assert.equal(outputsMatch('Room 101 added\nRoom 101 booked for John.', expected), false);
  assert.equal(outputsMatch('Room 101 added.\nRoom 101 booked for John!', expected), false);
});

test('a space that splits a word fails (spaces are collapsed, not removed)', () => {
  assert.equal(outputsMatch('Room 1 01 added.\nRoom 101 booked for John.', expected), false);
  assert.equal(outputsMatch('Room101 added.\nRoom 101 booked for John.', expected), false);
});

test('two replies on one line fail (line breaks matter)', () => {
  assert.equal(outputsMatch('Room 101 added. Room 101 booked for John.', expected), false);
});

test('wrong order fails', () => {
  assert.equal(outputsMatch('Room 101 booked for John.\nRoom 101 added.', expected), false);
});

test('an extra or a missing line fails', () => {
  assert.equal(outputsMatch(expected + 'Welcome!\n', expected), false);
  assert.equal(outputsMatch('Room 101 added.\n', expected), false);
});

test('no output fails, unless nothing is expected', () => {
  assert.equal(outputsMatch('', expected), false);
  assert.equal(outputsMatch(null, expected), false);
  assert.ok(outputsMatch('', ''));
  assert.ok(outputsMatch('\n  \n', undefined));
});

test('diacritics are compared as written (only case is folded)', () => {
  assert.ok(outputsMatch('IZBA ČÍSLO 1', 'izba číslo 1'));
  assert.equal(outputsMatch('izba cislo 1', 'izba číslo 1'), false);
});

test('normalizeOutput gives the compared lines', () => {
  assert.deepEqual(normalizeOutput('  Room   101 Added. \r\n\r\n\tNo FREE rooms.\n'), ['room 101 added.', 'no free rooms.']);
  assert.deepEqual(normalizeOutput(''), []);
});

test('firstDifference points at the first differing line', () => {
  assert.equal(firstDifference(expected, expected), null);
  assert.deepEqual(firstDifference('Room 101 added.\nRoom 101 is taken.', expected),
    { line: 2, actual: 'room 101 is taken.', expected: 'room 101 booked for john.' });
  assert.deepEqual(firstDifference('Room 101 added.', expected),
    { line: 2, actual: null, expected: 'room 101 booked for john.' });
  assert.deepEqual(firstDifference(expected + 'extra', expected), { line: 3, actual: 'extra', expected: null });
});
