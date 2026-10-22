// Shared helpers for question batches (questions/batches/*.json).
// Format: see questions/README.md
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve, basename, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
export const BATCH_DIR = join(ROOT, 'questions', 'batches');
export const TEMPLATE_DIR = join(ROOT, 'questions', 'templates');
export const UPDATES_DIR = join(ROOT, 'supabase', 'updates');

export const STATUSES = ['pending', 'approved', 'rejected'];
export const VERIFY_TYPES = ['output', 'value', 'exception', 'timeout', 'which-line', 'which-input', 'none'];

/** Read a JSON file (UTF-8, optional BOM). */
export function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8').replace(/^﻿/, ''));
}

/** Write JSON with 2-space indent and CRLF line endings (repo convention). */
export function writeJson(path, data) {
  writeFileSync(path, JSON.stringify(data, null, 2).replace(/\n/g, '\r\n') + '\r\n', 'utf8');
}

/** Batch files given on the command line, or all files in questions/batches. */
export function batchFiles(args) {
  const files = args.filter((a) => !a.startsWith('--'));
  if (files.length) return files.map((f) => resolve(f));
  if (!existsSync(BATCH_DIR)) return [];
  return readdirSync(BATCH_DIR)
    .filter((f) => f.endsWith('.json'))
    .sort()
    .map((f) => join(BATCH_DIR, f));
}

export function flag(args, name) {
  return args.includes(`--${name}`);
}

export function option(args, name, fallback) {
  const i = args.findIndex((a) => a === `--${name}` || a.startsWith(`--${name}=`));
  if (i < 0) return fallback;
  const a = args[i];
  return a.includes('=') ? a.slice(a.indexOf('=') + 1) : args[i + 1];
}

/** Templates of a topic, as a Map id → template (null when the file is missing). */
export function loadTemplates(topic) {
  const path = join(TEMPLATE_DIR, `${topic}.json`);
  if (!existsSync(path)) return null;
  return new Map(readJson(path).templates.map((t) => [t.id, t]));
}

const norm = (s) => String(s ?? '').replace(/\r/g, '');

/** Question body as stored in the DB: {code} replaced by a ```csharp block. */
export function composeBody(text, code) {
  const t = norm(text);
  if (code == null || code === '') return t.trim();
  const block = '```csharp\n' + norm(code).replace(/\n+$/, '') + '\n```';
  return t.replace('{code}', block).trim();
}

/** The SK and EN versions of a question, ready for the DB. */
export function compose(q) {
  const sk = {
    body: composeBody(q.sk.body, q.code),
    answers: q.sk.answers.map(norm),
    explanation: q.sk.explanation ? norm(q.sk.explanation) : null,
  };
  const en = q.en
    ? {
        body: composeBody(q.en.body, q.en.code ?? q.code),
        answers: (q.en.answers ?? q.sk.answers).map(norm),
        explanation: q.en.explanation ? norm(q.en.explanation) : null,
      }
    : null;
  return { sk, en };
}

/** Strip one pair of surrounding backticks (`x` → x); other text unchanged. */
export function unwrapCode(answer) {
  const a = norm(answer).trim();
  const m = /^`([^`]*)`$/.exec(a);
  return m ? m[1] : null;
}

/**
 * Validate one batch. Returns { errors: [..], warnings: [..] } with messages
 * prefixed by the question id.
 */
export function validateBatch(batch, file = 'batch') {
  const errors = [];
  const warnings = [];
  const err = (id, msg) => errors.push(`${id}: ${msg}`);
  const warn = (id, msg) => warnings.push(`${id}: ${msg}`);

  for (const key of ['batch', 'subject', 'topic', 'questions']) {
    if (batch[key] == null) err(basename(file), `missing "${key}"`);
  }
  if (!Array.isArray(batch.questions)) return { errors, warnings };

  const templates = batch.topic ? loadTemplates(batch.topic) : null;
  if (!templates) warn(basename(file), `no templates file for topic "${batch.topic}"`);

  const ids = new Set();
  const bodies = new Map();

  for (const [i, q] of batch.questions.entries()) {
    const id = q.id ?? `#${i + 1}`;
    if (!q.id) err(id, 'missing "id"');
    else if (ids.has(q.id)) err(id, 'duplicate id');
    ids.add(q.id);

    if (!STATUSES.includes(q.status)) err(id, `status must be one of ${STATUSES.join(', ')}`);
    if (!Number.isInteger(q.difficulty) || q.difficulty < 1 || q.difficulty > 10) err(id, 'difficulty must be 1–10');

    const tpl = templates?.get(q.template);
    if (templates && !tpl) err(id, `unknown template "${q.template}"`);
    if (tpl && tpl.difficulty !== q.difficulty) err(id, `difficulty ${q.difficulty} ≠ template difficulty ${tpl.difficulty}`);

    if (!q.sk?.body) { err(id, 'missing sk.body'); continue; }
    if (!Array.isArray(q.sk.answers)) { err(id, 'missing sk.answers'); continue; }

    for (const [lang, part] of [['sk', q.sk], ['en', q.en]]) {
      if (!part) { if (lang === 'en') warn(id, 'no English version'); continue; }
      if (!part.body) err(id, `missing ${lang}.body`);
      const answers = part.answers ?? (lang === 'en' ? q.sk.answers : null);
      if (!Array.isArray(answers) || answers.length !== 4) { err(id, `${lang}: exactly 4 answers needed`); continue; }
      if (answers.some((a) => !norm(a).trim())) err(id, `${lang}: empty answer`);
      if (new Set(answers.map((a) => norm(a).trim())).size !== 4) err(id, `${lang}: answers are not all different`);
      const body = part.body ?? '';
      if (q.code && !body.includes('{code}')) err(id, `${lang}.body has code but no {code} placeholder`);
      if (!q.code && body.includes('{code}')) err(id, `${lang}.body has {code} but the question has no code`);
      const leftover = body.replace('{code}', '').match(/\{[a-z_]+\}/);
      if (leftover) err(id, `${lang}.body contains an unfilled placeholder: ${leftover[0]}`);
      for (const a of answers) {
        if ((norm(a).match(/`/g) ?? []).length % 2) err(id, `${lang}: unbalanced backticks in answer ${a}`);
      }
      if (part.explanation && /\{[a-z_]+\}/.test(part.explanation)) err(id, `${lang}.explanation contains an unfilled placeholder`);
      if (!part.explanation) warn(id, `${lang}: no explanation`);
    }

    // Generation rules that apply to every topic
    const all = [q.sk.body, q.code ?? '', ...(q.sk.answers ?? [])].join('\n');
    if (/foreach\s*\(/.test(q.code ?? '')) err(id, 'uses foreach (not in the course)');
    if (/=>/.test(q.code ?? '')) warn(id, 'contains => (lambda / switch expression?)');

    // Verification block
    const v = q.verify;
    if (!v) warn(id, 'no "verify" block');
    else if (!VERIFY_TYPES.includes(v.type)) err(id, `verify.type must be one of ${VERIFY_TYPES.join(', ')}`);
    else if (['output', 'exception', 'timeout'].includes(v.type) && !q.code && !v.setup) err(id, `verify.type ${v.type} needs code`);
    else if (v.type === 'which-input' && (!v.input || !v.input.includes('{answer}') || v.output == null)) err(id, 'verify.input (with {answer}) and verify.output are needed');
    else if (v.type === 'value' && !v.expr) err(id, 'verify.expr missing (value check)');
    else if (['output', 'value'].includes(v.type) && v.expected == null && unwrapCode(q.sk.answers[0]) == null)
      err(id, 'correct answer is not inline code – set verify.expected');
    else if (v.type === 'exception' && !v.name) err(id, 'verify.name missing (exception type)');
    else if (v.type === 'which-line' && !['compile-error', 'exception', 'timeout'].includes(v.expect)) err(id, 'verify.expect must be compile-error, exception or timeout');

    // Duplicates: same text AND same answers = the same question twice
    const key = composeBody(q.sk.body, q.code) + '\n' + [...q.sk.answers].map(norm).sort().join('|');
    if (bodies.has(key)) err(id, `duplicate of ${bodies.get(key)}`);
    else bodies.set(key, id);
    void all;
  }
  return { errors, warnings };
}
