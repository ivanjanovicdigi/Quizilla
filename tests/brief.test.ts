// The assignment brief: prose kept as written, code spans marked (src/lib/assignments/brief.ts).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { briefParagraphs, briefParts } from '../src/lib/assignments/brief.ts';

test('code spans: one lowercase word is a command, anything else is program output', () => {
  assert.deepEqual(briefParts('Type `free` to get `101 double`.'), [
    { kind: 'text', text: 'Type ' }, { kind: 'command', text: 'free' }, { kind: 'text', text: ' to get ' },
    { kind: 'output', text: '101 double' }, { kind: 'text', text: '.' },
  ]);
  assert.equal(briefParts('`No free rooms.`')[0].kind, 'output');
});

test('the brief keeps its paragraphs and wording', () => {
  const paragraphs = briefParagraphs('One `add` here.\n\nTwo.\n\n\nThree.');
  assert.equal(paragraphs.length, 3);
  assert.equal(paragraphs[0].map((p) => p.text).join(''), 'One add here.');
});

test('every assignment brief (SK + EN): typed commands are marked as commands, replies as output', () => {
  for (const slug of readdirSync('assignments', { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name)) {
    const a = JSON.parse(readFileSync(`assignments/${slug}/assignment.json`, 'utf8'));
    const typed = new Set<string>(a.scenarios.flatMap((s: { input: string[] }) => s.input.map((l) => l.split(' ')[0])));
    for (const lang of ['sk', 'en']) {
      const paragraphs = briefParagraphs(a[lang].brief.join('\n\n'));
      assert.equal(paragraphs.length, a[lang].brief.length, `${slug} ${lang}`);
      const parts = paragraphs.flat();
      const commands = new Set(parts.filter((p) => p.kind === 'command').map((p) => p.text));
      assert.deepEqual([...commands].sort(), [...typed].sort(), `${slug} ${lang}`);
      assert.ok(parts.some((p) => p.kind === 'output'), `${slug} ${lang}`);
    }
  }
});
