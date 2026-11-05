// Builds an in-memory Postgres (PGlite) with Quizilla's real schema: the base migration, the seed
// and every numbered update in supabase/updates/, in order – like the production database.
// Nothing here talks to Supabase.
import { PGlite } from '@electric-sql/pglite';
import { readFileSync, readdirSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
export const read = (p) => readFileSync(join(ROOT, p), 'utf8');
export const updateFiles = () =>
  readdirSync(join(ROOT, 'supabase', 'updates')).filter((f) => /^\d{3}_.*\.sql$/.test(f)).sort();

/** A fresh database with all updates applied. `skip`: update files to leave out (applied later by the test). */
export async function replay({ skip = [] } = {}) {
  const db = new PGlite();
  await db.exec('create role anon nologin; create role authenticated nologin;');
  await db.exec(read('supabase/migrations/20261021000000_init.sql'));
  await db.exec(read('supabase/seed.sql'));
  for (const f of updateFiles()) if (!skip.includes(f)) await db.exec(read(`supabase/updates/${f}`));
  await db.exec('grant usage on schema public to anon;');
  return db;
}

/** Helpers bound to one database. `as(role)` switches the role like the app (anon) or back (null). */
export function helpers(db) {
  return {
    row: async (sql, params = []) => (await db.query(sql, params)).rows[0],
    rpc: async (sql, params = []) => (await db.query(sql, params)).rows[0].r,
    /** The error message (= the API error code) of a failing statement, or null if it succeeded. */
    error: async (sql, params = []) => {
      try { await db.query(sql, params); return null; } catch (e) { return e.message; }
    },
    as: (role) => db.exec(role ? `set role ${role}` : 'reset role'),
    addRoster: async (rows) => {
      for (const [email, name, className] of rows) {
        await db.query(
          `insert into quiz.roster (email, name, class_id)
           values ($1, $2, (select id from quiz.classes where name = $3)) on conflict do nothing`,
          [email, name, className]);
      }
    },
  };
}
