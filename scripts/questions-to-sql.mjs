#!/usr/bin/env node
// Turns APPROVED questions from batch files into the next numbered SQL update
// (supabase/updates/NNN_questions_<name>.sql) that you paste into the Supabase SQL Editor.
//
//   node scripts/questions-to-sql.mjs questions/batches/2026-10-23_data-types_1.json …
//   node scripts/questions-to-sql.mjs            → all batch files
//   --name=<text>   file name part (default: the batch name, or "batches" for several)
//   --dry           print the summary only, don't write the file
//   --skip-failed   leave out approved questions whose dotnet check failed (instead of stopping)
//   --chunk=<n>     split into several files with at most n questions each (e.g. --chunk=400)
//   --replace-all   first DELETE all questions (and with them all students' answers and points), then insert
//
// The script is re-runnable: questions are matched by quiz.questions.source_id (= the question id
// in the batch), so running it again updates texts instead of creating duplicates.
// Questions that are "rejected" in the batch are deactivated if they were imported before.
// Requires supabase/updates/005_question_source_id.sql.
import { readdirSync, writeFileSync, existsSync } from 'node:fs';
import { join, basename, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { batchFiles, readJson, validateBatch, compose, flag, option, ROOT, UPDATES_DIR } from './lib/batch.mjs';

const args = process.argv.slice(2);
const files = batchFiles(args);
if (!files.length) { console.error('No batch files found.'); process.exit(1); }

const approved = [];
const rejected = [];
const batches = [];
let errors = 0;

for (const file of files) {
  const batch = readJson(file);
  const res = validateBatch(batch, file);
  if (res.errors.length) {
    console.error(`✖ ${basename(file)} has ${res.errors.length} error(s) – run scripts/check-batch.mjs first.`);
    errors += res.errors.length;
    continue;
  }
  batches.push(batch);
  for (const q of batch.questions) {
    if (q.status === 'approved') approved.push({ batch, q });
    else if (q.status === 'rejected') rejected.push(q.id);
  }
}
if (errors) process.exit(1);
if (!approved.length && !rejected.length) { console.log('Nothing approved yet – no SQL written.'); process.exit(0); }

let failedChecks = approved.filter(({ q }) => q.check?.status === 'fail');
if (failedChecks.length && flag(args, 'skip-failed')) {
  console.warn(`⚠ skipping ${failedChecks.length} approved question(s) that failed the dotnet check:`);
  for (const { q } of failedChecks) console.warn(`   ${q.id}: ${q.check.detail}`);
  const skip = new Set(failedChecks.map(({ q }) => q.id));
  approved.splice(0, approved.length, ...approved.filter(({ q }) => !skip.has(q.id)));
  failedChecks = [];
}
const unchecked = approved.filter(({ q }) => q.verify && q.verify.type !== 'none' && !q.check);
if (unchecked.length) console.warn(`⚠ ${unchecked.length} approved question(s) were never checked with dotnet (run npm run q:verify first).`);
if (failedChecks.length) {
  console.error(`✖ ${failedChecks.length} approved question(s) failed the dotnet check:`);
  for (const { q } of failedChecks) console.error(`   ${q.id}: ${q.check.detail}`);
  console.error('Fix them or reject them, then run again.');
  process.exit(1);
}

// ------------------------------------------------------------------ SQL helpers
/** Dollar-quoted literal with a tag that does not occur in the text. */
function lit(s) {
  if (s == null) return 'null';
  const text = String(s);
  let tag = 'q';
  for (let i = 1; text.includes(`$${tag}$`); i++) tag = `q${i}`;
  return `$${tag}$${text}$${tag}$`;
}
const arr = (a) => (a ? `array[${a.map(lit).join(', ')}]` : 'null');

/** Deterministic permutation of [0, 1, 2, 3] from the question id. */
function shuffledOrder(id) {
  const h = createHash('sha256').update(String(id)).digest();
  const a = [0, 1, 2, 3];
  for (let i = 3; i > 0; i--) {
    const j = h[i] % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ------------------------------------------------------------------ file name
const existing = existsSync(UPDATES_DIR) ? readdirSync(UPDATES_DIR) : [];
const nextNo = Math.max(0, ...existing.map((f) => Number(/^(\d{3})_/.exec(f)?.[1] ?? 0))) + 1;
if (nextNo <= 5 && !existing.some((f) => f.startsWith('005_'))) {
  console.error('✖ supabase/updates/005_question_source_id.sql is missing.');
  process.exit(1);
}
const name = (option(args, 'name') ?? (batches.length === 1 ? batches[0].batch : `batches_${new Date().toISOString().slice(0, 10)}`))
  .replace(/[^\w.-]+/g, '_');
const prefix = String(nextNo).padStart(3, '0');
const CHUNK = Number(option(args, 'chunk', 0)) || 0; // max questions per file (Supabase SQL Editor can't take huge files)
const today = new Date().toISOString().slice(0, 10);
const REPLACE = flag(args, 'replace-all');

const FUNCTION = [
  `create or replace function pg_temp.upsert_question(`,
  `  p_source_id text, p_subject text, p_topic text, p_difficulty int,`,
  `  p_body text, p_answers text[], p_correct int, p_explanation text,`,
  `  p_body_en text, p_answers_en text[], p_explanation_en text)`,
  `returns void language plpgsql as $f$`,
  `declare`,
  `  v_topic int;`,
  `  v_id    bigint;`,
  `  v_same  boolean;`,
  `begin`,
  `  -- line endings: store LF only, whatever the file / editor used`,
  `  p_body := replace(p_body, E'\\r', '');`,
  `  p_body_en := replace(p_body_en, E'\\r', '');`,
  `  p_explanation := replace(p_explanation, E'\\r', '');`,
  `  p_explanation_en := replace(p_explanation_en, E'\\r', '');`,
  `  p_answers := array(select replace(a, E'\\r', '') from unnest(p_answers) with ordinality u(a, n) order by n);`,
  `  if p_answers_en is not null then`,
  `    p_answers_en := array(select replace(a, E'\\r', '') from unnest(p_answers_en) with ordinality u(a, n) order by n);`,
  `  end if;`,
  ``,
  `  select t.id into v_topic`,
  `    from quiz.topics t join quiz.subjects s on s.id = t.subject_id`,
  `   where s.slug = p_subject and t.slug = p_topic;`,
  `  if v_topic is null then`,
  `    raise exception 'Unknown topic %/% (question %)', p_subject, p_topic, p_source_id;`,
  `  end if;`,
  ``,
  `  select id, (topic_id, difficulty, body, answers, correct_index, explanation, body_en, answers_en, explanation_en, is_active)`,
  `             is not distinct from (v_topic, p_difficulty::smallint, p_body, p_answers, p_correct::smallint, p_explanation,`,
  `                                   p_body_en, p_answers_en, p_explanation_en, true)`,
  `    into v_id, v_same`,
  `    from quiz.questions where source_id = p_source_id;`,
  ``,
  `  if v_id is null then`,
  `    insert into quiz.questions (source_id, topic_id, difficulty, body, answers, correct_index, explanation,`,
  `                                body_en, answers_en, explanation_en)`,
  `    values (p_source_id, v_topic, p_difficulty, p_body, p_answers, p_correct, p_explanation,`,
  `            p_body_en, p_answers_en, p_explanation_en);`,
  `    insert into import_log values (p_source_id, 'inserted');`,
  `  elsif v_same then`,
  `    insert into import_log values (p_source_id, 'unchanged');`,
  `  else`,
  `    update quiz.questions`,
  `       set topic_id = v_topic, difficulty = p_difficulty, body = p_body, answers = p_answers,`,
  `           correct_index = p_correct, explanation = p_explanation, body_en = p_body_en,`,
  `           answers_en = p_answers_en, explanation_en = p_explanation_en, is_active = true`,
  `     where id = v_id;`,
  `    insert into import_log values (p_source_id, 'updated');`,
  `  end if;`,
  `end $f$;`,
  ``,
];

function questionSql({ batch, q }) {
  const { sk, en } = compose(q);
  // In the batch the correct answer is always first (easy to review). In the DB the order is
  // shuffled – otherwise the API response would reveal the answer (always index 0).
  // The order is derived from the question id, so re-running the script gives the same order.
  const order = shuffledOrder(q.id);
  const correct = order.indexOf(0);
  sk.answers = order.map((i) => sk.answers[i]);
  if (en) en.answers = order.map((i) => en.answers[i]);
  return [
    `-- ${q.id} (${q.template}, difficulty ${q.difficulty})`,
    `select pg_temp.upsert_question(${lit(q.id)}, ${lit(batch.subject)}, ${lit(batch.topic)}, ${q.difficulty},`,
    `  ${lit(sk.body)},`,
    `  ${arr(sk.answers)}, ${correct}, ${lit(sk.explanation)},`,
    `  ${en ? lit(en.body) : 'null'},`,
    `  ${en ? arr(en.answers) : 'null'}, ${en ? lit(en.explanation) : 'null'});`,
    ``,
  ];
}

/** One self-contained SQL file (own transaction, own helper function, own result table). */
function buildFile(part, partNo, partCount) {
  const first = partNo === 1;
  const last = partNo === partCount;
  const lines = [
    `-- Quizilla – questions generated from: ${files.map((f) => relative(ROOT, f).replace(/\\/g, '/')).join(', ')}`,
    partCount > 1
      ? `-- PART ${partNo} of ${partCount} (${part.length} questions). Run the parts in order: 1, 2, 3, …`
      : `-- ${approved.length} approved question(s), ${rejected.length} rejected (deactivated if imported earlier).`,
    `-- Built ${today} by scripts/questions-to-sql.mjs – do not edit by hand, change the batch file and rebuild.`,
    `-- Run in Supabase → SQL Editor. Safe to re-run (matched by quiz.questions.source_id).`,
    `begin;`,
    ``,
    `create temp table if not exists import_log (source_id text, result text);`,
    `truncate import_log;`,
    ``,
  ];
  if (REPLACE && first) {
    lines.push(
      `-- --replace-all: remove every existing question first (only in part 1).`,
      `-- WARNING: this also deletes all students' answers (quiz.attempts) and their points.`,
      `-- Unlocked levels (quiz.unlocks) are reset too, so everybody starts again from level 1.`,
      `delete from quiz.unlocks;`,
      `delete from quiz.questions;`,
      ``,
    );
  }
  lines.push(...FUNCTION);
  for (const item of part) lines.push(...questionSql(item));
  if (last && rejected.length) {
    lines.push(
      `-- rejected in the batch → hide if imported earlier (answers history is kept)`,
      `with hidden as (`,
      `  update quiz.questions set is_active = false`,
      `   where is_active and source_id in (${rejected.map(lit).join(', ')})`,
      `  returning source_id)`,
      `insert into import_log select source_id, 'deactivated' from hidden;`,
      ``,
    );
  }
  lines.push(
    `commit;`,
    ``,
    `-- result` + (partCount > 1 ? ` of part ${partNo}/${partCount}` : ''),
    `select result, count(*) as questions from import_log group by result order by result;`,
    ``,
  );
  // CRLF like the other update files; the helper function strips \r from the stored texts.
  return lines.join('\n').replace(/\n/g, '\r\n');
}

const parts = [];
if (CHUNK > 0) for (let i = 0; i < approved.length; i += CHUNK) parts.push(approved.slice(i, i + CHUNK));
else parts.push(approved);
if (!parts.length) parts.push([]);

const outFiles = parts.map((_, i) =>
  join(UPDATES_DIR, parts.length > 1 ? `${prefix}_questions_${name}_part${String(i + 1).padStart(2, '0')}.sql` : `${prefix}_questions_${name}.sql`));

console.log(`${approved.length} approved, ${rejected.length} rejected → ${parts.length} file(s):`);
for (const f of outFiles) console.log(`   ${relative(ROOT, f)}`);
if (flag(args, 'dry')) process.exit(0);
parts.forEach((part, i) => writeFileSync(outFiles[i], buildFile(part, i + 1, parts.length), 'utf8'));
console.log(parts.length > 1 ? 'Done. Paste the files into Supabase → SQL Editor one by one, in order, and Run each.' : 'Done. Paste the file into Supabase → SQL Editor → Run.');
