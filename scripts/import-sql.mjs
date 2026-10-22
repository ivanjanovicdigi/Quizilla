#!/usr/bin/env node
// Runs SQL files directly against the Supabase database – no SQL Editor, no size limit.
//
//   npm run q:import -- supabase/updates/008_questions_all.sql
//
// Needs the database connection string once, in .env.local (never committed):
//   SUPABASE_DB_URL=postgresql://postgres.xxxx:YOUR-DB-PASSWORD@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
// Supabase dashboard → Connect (top bar) → "Session pooler" → copy the URI and put your database password in.
import { readFileSync, existsSync } from 'node:fs';
import { join, basename } from 'node:path';
import pg from 'pg';
import { ROOT } from './lib/batch.mjs';

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

const files = process.argv.slice(2).filter((a) => !a.startsWith('--'));
if (!files.length) {
  console.error('Usage: npm run q:import -- <file.sql> [more files…]');
  process.exit(1);
}
const url = envValue('SUPABASE_DB_URL');
if (!url) {
  console.error('SUPABASE_DB_URL is missing. Add it to .env.local:');
  console.error('  SUPABASE_DB_URL=postgresql://postgres.xxxx:YOUR-DB-PASSWORD@aws-0-….pooler.supabase.com:5432/postgres');
  console.error('Supabase dashboard → Connect → "Session pooler" → copy the URI and fill in the database password.');
  process.exit(1);
}
if (url.includes('[YOUR-PASSWORD]')) {
  console.error('Replace [YOUR-PASSWORD] in SUPABASE_DB_URL with your database password.');
  process.exit(1);
}

const local = /@(localhost|127\.0\.0\.1)[:/]/.test(url) || url.includes('host=/');
const client = new pg.Client({ connectionString: url, ssl: local ? false : { rejectUnauthorized: false } });

try {
  await client.connect();
} catch (e) {
  console.error(`Cannot connect to the database: ${e.message}`);
  if (/password/i.test(e.message)) console.error('Check the password in SUPABASE_DB_URL (Supabase → Project Settings → Database → reset it if you forgot it).');
  process.exit(1);
}

let failed = false;
for (const file of files) {
  const sql = readFileSync(file, 'utf8');
  process.stdout.write(`${basename(file)} (${(sql.length / 1024 / 1024).toFixed(1)} MB)… `);
  const t0 = Date.now();
  try {
    const res = await client.query(sql);
    const results = Array.isArray(res) ? res : [res];
    const last = [...results].reverse().find((r) => r.rows && r.rows.length && r.fields?.length);
    console.log(`done in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
    if (last) console.table(last.rows);
  } catch (e) {
    failed = true;
    console.log('FAILED');
    console.error(`  ${e.message}`);
    console.error('  Nothing from this file was saved (the script runs in one transaction).');
    try { await client.query('rollback'); } catch {}
    break;
  }
}
await client.end();
process.exit(failed ? 1 : 0);
