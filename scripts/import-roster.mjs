#!/usr/bin/env node
// Loads the student roster (who may log in: email, name, class) into quiz.roster.
//
//   npm run q:roster -- private/roster.csv             add new students, update changed ones
//   npm run q:roster -- private/roster.csv --dry-run   only show what would change
//   npm run q:roster -- private/roster.csv --sync      also DEACTIVATE students missing from the file
//
// CSV (Excel: "Save as → CSV UTF-8"), separator ; or , – first row is the header:
//   name;email;class
//   Ján Novák;jan.novak@lyceum.sk;Lambda
// Columns are found by header name, in any order. Header names may also be Slovak: meno / e-mail / trieda.
// Class = class name in the app (Lambda, Ró, Teachers).
//
// Keep the file in private/ (gitignored) – it contains students' personal data.
// Needs SUPABASE_DB_URL in .env.local (same as q:import). Nothing is changed when the file has errors.
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import pg from 'pg';
import { ROOT } from './lib/batch.mjs';

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith('--'));
const dryRun = args.includes('--dry-run');
const sync = args.includes('--sync');

if (!file) {
  console.error('Usage: npm run q:roster -- private/roster.csv [--dry-run] [--sync]');
  process.exit(1);
}
if (!existsSync(file)) {
  console.error(`File not found: ${file}`);
  process.exit(1);
}

function envValue(key) {
  if (process.env[key]) return process.env[key];
  for (const f of ['.env.local', '.env']) {
    const p = join(ROOT, f);
    if (!existsSync(p)) continue;
    for (const line of readFileSync(p, 'utf8').split(/\r?\n/)) {
      const m = /^\s*([\w.]+)\s*=\s*(.*)\s*$/.exec(line);
      if (m && m[1] === key) return m[2].replace(/^["']|["']$/g, '');
    }
  }
  return null;
}

// ------------------------------------------------------------------ CSV
function parseCsv(text) {
  text = text.replace(/^﻿/, '');
  const firstLine = text.split(/\r?\n/, 1)[0];
  const count = (ch) => firstLine.split(ch).length - 1;
  const sep = [';', ',', '\t'].sort((a, b) => count(b) - count(a))[0];
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === sep) { row.push(field); field = ''; }
    else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(field); rows.push(row); row = []; field = '';
    } else field += ch;
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  return rows.filter((r) => r.some((c) => c.trim() !== ''));
}

const fold = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').trim().toLowerCase();
const HEADERS = {
  email: ['email', 'e-mail', 'mail'],
  name: ['name', 'meno', 'meno a priezvisko', 'full name', 'full_name'],
  class: ['class', 'trieda', 'class_name', 'skupina']
};

const rows = parseCsv(readFileSync(file, 'utf8'));
if (rows.length < 2) {
  console.error('The file has no students (expected a header row and at least one student).');
  process.exit(1);
}
const header = rows[0].map(fold);
const col = {};
for (const [key, names] of Object.entries(HEADERS)) {
  col[key] = header.findIndex((h) => names.includes(h));
  if (col[key] < 0) {
    console.error(`Column "${key}" not found in the header. Expected columns: name;email;class – any order (found: ${rows[0].join(' | ')})`);
    process.exit(1);
  }
}

// ------------------------------------------------------------------ database
const url = envValue('SUPABASE_DB_URL');
if (!url) {
  console.error('SUPABASE_DB_URL is missing in .env.local (see .env.example).');
  process.exit(1);
}
const local = /@(localhost|127\.0\.0\.1)[:/]/.test(url) || url.includes('host=/');
const client = new pg.Client({ connectionString: url, ssl: local ? false : { rejectUnauthorized: false } });
try {
  await client.connect();
} catch (e) {
  console.error(`Cannot connect to the database: ${e.message}`);
  process.exit(1);
}

let exitCode = 0;
try {
  const classes = (await client.query('select id, name, is_active from quiz.classes')).rows;
  const classByName = new Map(classes.filter((c) => c.is_active).map((c) => [fold(c.name), c]));
  const domains = ((await client.query(
    "select value from quiz.config where key = 'allowed_email_domains'")).rows[0]?.value ?? '')
    .split(',').map((d) => d.trim().toLowerCase()).filter(Boolean);

  // ---------------------------------------------------------------- validate
  const errors = [];
  const students = [];
  const seen = new Map();
  rows.slice(1).forEach((r, i) => {
    const line = i + 2;
    const email = (r[col.email] ?? '').trim().toLowerCase();
    const name = (r[col.name] ?? '').trim().replace(/\s+/g, ' ');
    const className = (r[col.class] ?? '').trim();
    if (!/^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/.test(email)) errors.push(`line ${line}: invalid email "${email}"`);
    else if (domains.length && !domains.includes(email.split('@')[1]))
      errors.push(`line ${line}: ${email} – domain not allowed (allowed: ${domains.join(', ')})`);
    if (name.length < 2 || name.length > 80) errors.push(`line ${line}: invalid name "${name}" (2–80 characters)`);
    const cls = classByName.get(fold(className));
    if (!cls) errors.push(`line ${line}: unknown class "${className}" (classes: ${[...classByName.values()].map((c) => c.name).join(', ')})`);
    if (seen.has(email)) errors.push(`line ${line}: ${email} is already on line ${seen.get(email)}`);
    seen.set(email, line);
    if (cls) students.push({ email, name, class_id: cls.id, class: cls.name });
  });
  if (errors.length) {
    console.error(`${errors.length} error(s) – nothing was changed:`);
    for (const e of errors) console.error('  ' + e);
    exitCode = 1;
  } else {
    // -------------------------------------------------------------- diff
    const current = new Map((await client.query(
      'select r.email, r.name, r.class_id, r.is_active, c.name as class from quiz.roster r join quiz.classes c on c.id = r.class_id'
    )).rows.map((r) => [r.email, r]));
    const added = [], changed = [], reactivated = [];
    for (const s of students) {
      const c = current.get(s.email);
      if (!c) added.push(s);
      else if (!c.is_active) reactivated.push(s);
      else if (c.name !== s.name || c.class_id !== s.class_id)
        changed.push({ email: s.email, name: c.name === s.name ? s.name : `${c.name} → ${s.name}`,
                       class: c.class_id === s.class_id ? s.class : `${c.class} → ${s.class}` });
    }
    const inFile = new Set(students.map((s) => s.email));
    const missing = [...current.values()].filter((c) => c.is_active && !inFile.has(c.email));
    const unchanged = students.length - added.length - changed.length - reactivated.length;

    console.log(`${file}: ${students.length} students`);
    console.log(`  new: ${added.length}, changed: ${changed.length}, reactivated: ${reactivated.length}, unchanged: ${unchanged}`);
    if (added.length) console.table(added.map(({ email, name, class: c }) => ({ email, name, class: c })));
    if (changed.length) console.table(changed);
    if (reactivated.length) console.table(reactivated.map(({ email, name, class: c }) => ({ reactivated: email, name, class: c })));
    if (missing.length) {
      console.log(sync
        ? `  ${missing.length} student(s) not in the file will be DEACTIVATED (they can no longer log in, history is kept):`
        : `  ${missing.length} student(s) in the roster are not in the file (kept – use --sync to deactivate them):`);
      console.table(missing.map((m) => ({ email: m.email, name: m.name, class: m.class })));
    }

    if (dryRun) {
      console.log('Dry run – nothing was changed.');
    } else {
      await client.query('begin');
      await client.query(
        `insert into quiz.roster (email, name, class_id)
         select * from unnest($1::text[], $2::text[], $3::smallint[])
         on conflict (email) do update
            set name = excluded.name, class_id = excluded.class_id, is_active = true, updated_at = now()
          where (quiz.roster.name, quiz.roster.class_id, quiz.roster.is_active)
                is distinct from (excluded.name, excluded.class_id, true)`,
        [students.map((s) => s.email), students.map((s) => s.name), students.map((s) => s.class_id)]);
      if (sync && missing.length) {
        await client.query(
          'update quiz.roster set is_active = false, updated_at = now() where email = any($1::text[])',
          [missing.map((m) => m.email)]);
      }
      await client.query('commit');
      console.log('Roster saved.');
    }

    // students with progress that cannot log in (typo in the file, wrong address, removed)
    const orphans = (await client.query(
      'select email, name, class, answers from quiz.v_students_not_on_roster')).rows;
    if (orphans.length) {
      console.log(`\n${orphans.length} existing student(s) are NOT in the roster and cannot log in` +
        ' (fix the email in the file if it is a typo – their progress is kept):');
      console.table(orphans);
    }
  }
} catch (e) {
  try { await client.query('rollback'); } catch {}
  console.error(`FAILED: ${e.message}`);
  if (/roster/.test(e.message) && /does not exist/.test(e.message))
    console.error('Run supabase/updates/010_roster.sql first:  npm run q:import -- supabase/updates/010_roster.sql');
  exitCode = 1;
}
await client.end();
process.exit(exitCode);
